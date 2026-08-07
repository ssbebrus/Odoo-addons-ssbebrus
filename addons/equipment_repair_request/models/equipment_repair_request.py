from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EquipmentRepairRequest(models.Model):
    _name = 'equipment.repair.request'
    _description = 'Equipment Repair Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'stop_datetime desc, id desc'

    name = fields.Char(
        string='Номер заявки',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: fields.Datetime.now().strftime('REP-%Y%m%d-%H%M%S')
    )
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Станок / Рабочий центр',
        required=True,
        tracking=True
    )
    shop_section = fields.Char(
        string='Цех / Участок',
        compute='_compute_shop_section',
        store=True,
        readonly=False,
        help='Участок или цех, в котором установлен данный станок'
    )
    stop_datetime = fields.Datetime(
        string='Время остановки',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Предварительный комментарий о поломке',
        required=True,
        tracking=True,
        help='Описание выявленных неполадок (например, «Протекает масло в гидравлике»)'
    )
    state = fields.Selection([
        ('needs_repair', 'Требуется ремонт'),
        ('in_progress', 'В работе'),
        ('done', 'Завершен'),
        ('cancel', 'Отменен'),
    ], string='Статус', default='needs_repair', required=True, tracking=True)

    assignee_id = fields.Many2one(
        'res.users',
        string='Ответственный слесарь-ремонтник',
        tracking=True,
        domain=lambda self: [('groups_id', 'in', [
            self.env.ref('equipment_repair_request.group_repair_mechanic', raise_if_not_found=False) and self.env.ref('equipment_repair_request.group_repair_mechanic').id or False,
            self.env.ref('equipment_repair_request.group_chief_mechanic', raise_if_not_found=False) and self.env.ref('equipment_repair_request.group_chief_mechanic').id or False,
            self.env.ref('base.group_user').id
        ])]
    )
    reporter_id = fields.Many2one(
        'res.users',
        string='Заявитель (Начальник цеха / Рабочий)',
        default=lambda self: self.env.user,
        tracking=True
    )
    downtime_id = fields.Many2one(
        'equipment.downtime',
        string='Связаный простой',
        ondelete='set null'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Компания',
        default=lambda self: self.env.company
    )

    @api.depends('workcenter_id')
    def _compute_shop_section(self):
        for record in self:
            if record.workcenter_id:
                # Use workcenter code, category name, or default shop name
                cat_name = record.workcenter_id.category_id.name if hasattr(record.workcenter_id, 'category_id') and record.workcenter_id.category_id else ''
                code = record.workcenter_id.code or ''
                if cat_name:
                    record.shop_section = f"Цех {cat_name}"
                elif code:
                    record.shop_section = f"Участок {code}"
                else:
                    record.shop_section = "Основной механический цех"
            else:
                record.shop_section = "Не указан"

    def action_assign_mechanic(self):
        """Open wizard or directly assign mechanic."""
        self.ensure_one()
        return {
            'name': 'Назначить слесаря-ремонтника',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.mechanic.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_assignee_id': self.assignee_id.id,
            }
        }

    def action_start_repair(self):
        """Move request to 'In Progress' status."""
        for record in self:
            if not record.assignee_id:
                raise UserError(_("Пожалуйста, назначьте ответственного слесаря-ремонтника перед переводом в статус «В работе»."))
            record.write({'state': 'in_progress'})
            record.message_post(
                body=_("Заявка переведена в статус «В работе». Ответственный: <b>%s</b>") % record.assignee_id.name
            )

    def action_complete_repair(self):
        """Mark repair as completed."""
        for record in self:
            record.write({'state': 'done'})
            record.message_post(body=_("Ремонт станка успешно завершен."))

    def action_cancel(self):
        """Cancel repair request."""
        for record in self:
            record.write({'state': 'cancel'})
            record.message_post(body=_("Заявка на ремонт отменена."))
