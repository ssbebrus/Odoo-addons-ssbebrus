from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssignMechanicWizard(models.TransientModel):
    _name = 'assign.mechanic.wizard'
    _description = 'Wizard for Assigning Mechanic to Repair Request'

    request_id = fields.Many2one(
        'equipment.repair.request',
        string='Заявка на ремонт',
        required=True,
        ondelete='cascade'
    )
    assignee_id = fields.Many2one(
        'res.users',
        string='Ответственный слесарь-ремонтник',
        required=True
    )
    comment = fields.Text(
        string='Комментарий / Наряд-задание'
    )

    def action_confirm(self):
        self.ensure_one()
        if not self.assignee_id:
            raise UserError(_("Пожалуйста, выберите слесаря-ремонтника."))
        
        self.request_id.write({
            'assignee_id': self.assignee_id.id,
            'state': 'in_progress',
        })
        
        msg = _("🛠️ <b>Назначен ответственный слесарь-ремонтник:</b> %s.<br/>Заявка переведена в статус <b>«В работе»</b>.") % self.assignee_id.name
        if self.comment:
            msg += _("<br/><b>Инструкция:</b> %s") % self.comment
            
        self.request_id.message_post(body=msg)
        return {'type': 'ir.actions.act_window_close'}
