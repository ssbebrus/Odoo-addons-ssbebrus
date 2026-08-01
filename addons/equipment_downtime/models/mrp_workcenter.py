from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    downtime_ids = fields.One2many('equipment.downtime', 'workcenter_id', string='Downtimes')
    total_downtime_minutes = fields.Float(string='Total Downtime (min)', compute='_compute_total_downtime_minutes', store=True)
    downtime_count = fields.Integer(string='Downtime Count', compute='_compute_downtime_count')
    net_working_time = fields.Float(
        string='Net Working Time (min)',
        compute='_compute_downtime_metrics',
        store=True,
        help='Net available working time after deducting forced equipment downtimes.'
    )
    downtime_adjusted_oee = fields.Float(
        string='Adjusted OEE (%)',
        compute='_compute_downtime_metrics',
        store=True,
        help='Overall Equipment Effectiveness (%) excluding forced downtime from operator penalty.'
    )

    @api.depends('downtime_ids.duration')
    def _compute_total_downtime_minutes(self):
        for record in self:
            record.total_downtime_minutes = sum(record.downtime_ids.mapped('duration'))

    @api.depends('downtime_ids')
    def _compute_downtime_count(self):
        for record in self:
            record.downtime_count = len(record.downtime_ids)

    @api.depends('total_downtime_minutes')
    def _compute_downtime_metrics(self):
        for record in self:
            # Nominal standard shift time is 480 minutes (8 hours)
            nominal_shift_minutes = 480.0
            downtime = record.total_downtime_minutes or 0.0
            net_time = max(0.0, nominal_shift_minutes - downtime)
            record.net_working_time = net_time
            if nominal_shift_minutes > 0:
                record.downtime_adjusted_oee = round((net_time / nominal_shift_minutes) * 100.0, 2)
            else:
                record.downtime_adjusted_oee = 100.0

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

    def action_open_add_downtime_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Downtime',
            'res_model': 'add.downtime.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workcenter_id': self.id,
            },
        }
