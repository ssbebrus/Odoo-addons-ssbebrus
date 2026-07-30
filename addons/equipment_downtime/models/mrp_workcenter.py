from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    downtime_ids = fields.One2many('equipment.downtime', 'workcenter_id', string='Downtimes')
    total_downtime_minutes = fields.Float(string='Total Downtime (min)', compute='_compute_total_downtime_minutes', store=True)
    downtime_count = fields.Integer(string='Downtime Count', compute='_compute_downtime_count')

    @api.depends('downtime_ids.duration')
    def _compute_total_downtime_minutes(self):
        for record in self:
            record.total_downtime_minutes = sum(record.downtime_ids.mapped('duration'))

    @api.depends('downtime_ids')
    def _compute_downtime_count(self):
        for record in self:
            record.downtime_count = len(record.downtime_ids)

    def action_view_downtimes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipment Downtimes',
            'res_model': 'equipment.downtime',
            'view_mode': 'list,form',
            'domain': [('workcenter_id', '=', self.id)],
            'context': {'default_workcenter_id': self.id},
        }
