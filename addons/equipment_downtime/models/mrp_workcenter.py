from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    downtime_ids = fields.One2many('equipment.downtime', 'workcenter_id', string='Downtimes')
    total_downtime_minutes = fields.Float(string='Total Downtime (min)', compute='_compute_total_downtime_minutes', store=True)
    downtime_count = fields.Integer(string='Downtime Count', compute='_compute_downtime_count')
    net_working_time = fields.Float(
        string='Net Working Time (min)',
        compute='_compute_downtime_metrics',
        help='Net available working time after deducting forced equipment downtimes.'
    )
    downtime_adjusted_oee = fields.Float(
        string='Adjusted OEE (%)',
        compute='_compute_downtime_metrics',
        help='Overall Equipment Effectiveness (%) excluding forced downtime from operator penalty.'
    )
    downtime_reason_summary = fields.Text(
        string='Reason Breakdown Summary',
        compute='_compute_downtime_reason_summary',
        help='Percentage breakdown of downtime reasons for this work center.'
    )

    @api.depends('downtime_ids.duration', 'downtime_ids.reason_id')
    def _compute_downtime_reason_summary(self):
        for record in self:
            total = sum(record.downtime_ids.mapped('duration'))
            if not total:
                record.downtime_reason_summary = "Нет зарегистрированных простоев."
                continue

            reason_totals = {}
            for dt in record.downtime_ids:
                reason_name = dt.reason_id.name or "Не указано"
                reason_totals[reason_name] = reason_totals.get(reason_name, 0.0) + dt.duration

            lines = []
            for name, dur in sorted(reason_totals.items(), key=lambda x: x[1], reverse=True):
                pct = round((dur / total) * 100.0, 1)
                lines.append(f"{name}: {pct:.1f}% ({int(dur)} мин)")
            record.downtime_reason_summary = "\n".join(lines)

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

    def action_open_downtime_reason_pie(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Причины простоя: {self.name}',
            'res_model': 'equipment.downtime',
            'view_mode': 'graph,pivot,list',
            'views': [
                (self.env.ref('equipment_downtime.view_equipment_downtime_reason_pie_graph').id, 'graph'),
                (self.env.ref('equipment_downtime.view_equipment_downtime_monthly_pivot').id, 'pivot'),
                (self.env.ref('equipment_downtime.view_equipment_downtime_tree').id, 'list'),
            ],
            'domain': [('workcenter_id', '=', self.id)],
            'context': {
                'search_default_group_by_reason': 1,
                'default_workcenter_id': self.id,
            },
        }

