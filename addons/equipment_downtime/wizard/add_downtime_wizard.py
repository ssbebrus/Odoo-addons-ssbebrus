from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AddDowntimeWizard(models.TransientModel):
    _name = 'add.downtime.wizard'
    _description = 'Add Equipment Downtime Wizard'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    duration = fields.Float(string='Duration (Minutes)', required=True, default=15.0)
    reason_id = fields.Many2one('downtime.reason', string='Reason', required=True)
    notes = fields.Text(string='Notes')

    @api.constrains('duration')
    def _check_duration(self):
        for record in self:
            if record.duration <= 0:
                raise UserError(_('Длительность простоя должна быть больше нуля.'))

    def action_add_downtime(self):
        self.ensure_one()
        if self.duration <= 0:
            raise UserError(_('Длительность простоя должна быть больше нуля.'))

        self.env['equipment.downtime'].create({
            'workcenter_id': self.workcenter_id.id,
            'date': self.date,
            'duration': self.duration,
            'reason_id': self.reason_id.id,
            'notes': self.notes,
        })
        return {'type': 'ir.actions.act_window_close'}
