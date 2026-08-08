from odoo import api, fields, models, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    repair_request_ids = fields.One2many(
        'equipment.repair.request',
        'workcenter_id',
        string='Заявки на ремонт'
    )
    repair_request_count = fields.Integer(
        string='Заявки на ремонт',
        compute='_compute_repair_request_count'
    )

    @api.depends('repair_request_ids')
    def _compute_repair_request_count(self):
        for record in self:
            record.repair_request_count = len(record.repair_request_ids)

    def action_view_repair_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Заявки на ремонт: {self.name}',
            'res_model': 'equipment.repair.request',
            'view_mode': 'kanban,list,form',
            'domain': [('workcenter_id', '=', self.id)],
            'context': {'default_workcenter_id': self.id},
        }

    def action_report_breakdown(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Сообщить о поломке станка',
            'res_model': 'equipment.repair.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workcenter_id': self.id,
                'default_stop_datetime': fields.Datetime.now(),
                'default_description': 'Протекает масло в гидравлике',
            }
        }
