from odoo import fields, models


class DowntimeReason(models.Model):
    _name = 'downtime.reason'
    _description = 'Downtime Reason'

    name = fields.Char(string='Reason', required=True, translate=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
