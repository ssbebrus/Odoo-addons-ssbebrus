from odoo import fields, models


class EquipmentDowntime(models.Model):
    _name = 'equipment.downtime'
    _description = 'Equipment Downtime'
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, default=lambda self: fields.Datetime.now().strftime('DT-%Y%m%d-%H%M%S'))
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    duration = fields.Float(string='Duration (Minutes)', required=True)
    reason_id = fields.Many2one('downtime.reason', string='Reason', required=True, ondelete='restrict')
    notes = fields.Text(string='Notes')
    user_id = fields.Many2one('res.users', string='Recorded By', default=lambda self: self.env.user)
