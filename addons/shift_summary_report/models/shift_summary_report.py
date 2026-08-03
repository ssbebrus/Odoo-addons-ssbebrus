from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ShiftSummaryReport(models.Model):
    _name = 'shift.summary.report'
    _description = 'Shift Summary Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Title',
        required=True,
        default='Новый рапорт смены',
        tracking=True
    )
    date = fields.Date(
        string='Shift Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    shift_name = fields.Selection(
        [
            ('day', 'Day Shift'),
            ('night', 'Night Shift'),
            ('shift_1', 'Shift 1'),
            ('shift_2', 'Shift 2'),
        ],
        string='Shift',
        required=True,
        default='day',
        tracking=True
    )
    manager_id = fields.Many2one(
        'res.users',
        string='Shop Floor Manager',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    director_email = fields.Char(
        string='Plant Director Email',
        required=True,
        default='director@factory.com',
        help='Email address where the shift report will be sent automatically.',
        tracking=True
    )
    planned_qty = fields.Float(
        string='Planned Volume (pcs)',
        default=0.0,
        help='Target planned production quantity for the shift.',
        tracking=True
    )
    produced_qty = fields.Float(
        string='Total Produced Volume (pcs)',
        default=0.0,
        help='Actual total production output quantity for the shift.',
        tracking=True
    )
    scrap_qty = fields.Float(
        string='Scrap Quantity (pcs)',
        default=0.0,
        help='Quantity of scrapped/defective parts.',
        tracking=True
    )
    critical_downtime_minutes = fields.Float(
        string='Critical Downtime (min)',
        default=0.0,
        help='Duration of critical equipment downtime in minutes.',
        tracking=True
    )
    scrap_percentage = fields.Float(
        string='Scrap Percentage (%)',
        compute='_compute_metrics',
        store=True,
        help='Percentage of defective items out of total production output.',
        tracking=True
    )
    plan_execution_rate = fields.Float(
        string='Plan Execution Coefficient (%)',
        compute='_compute_metrics',
        store=True,
        help='Ratio of actual produced quantity vs planned quantity in percent.',
        tracking=True
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed & Sent'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True
    )
    sent_date = fields.Datetime(
        string='Sent Date',
        readonly=True,
        copy=False
    )
    notes = fields.Text(
        string='Shift Summary Notes'
    )

    @api.depends('planned_qty', 'produced_qty', 'scrap_qty')
    def _compute_metrics(self):
        for record in self:
            if record.produced_qty > 0:
                record.scrap_percentage = round((record.scrap_qty / record.produced_qty) * 100.0, 2)
            else:
                record.scrap_percentage = 0.0

            if record.planned_qty > 0:
                record.plan_execution_rate = round((record.produced_qty / record.planned_qty) * 100.0, 2)
            else:
                record.plan_execution_rate = 0.0

    @api.constrains('planned_qty', 'produced_qty', 'scrap_qty', 'critical_downtime_minutes')
    def _check_non_negative_values(self):
        for record in self:
            if record.planned_qty < 0:
                raise ValidationError('Planned quantity cannot be negative.')
            if record.produced_qty < 0:
                raise ValidationError('Produced quantity cannot be negative.')
            if record.scrap_qty < 0:
                raise ValidationError('Scrap quantity cannot be negative.')
            if record.critical_downtime_minutes < 0:
                raise ValidationError('Critical downtime duration cannot be negative.')

    def action_confirm_and_send(self):
        """Confirm shift results, auto-generate title, send email report to director, log in chatter."""
        template = self.env.ref('shift_summary_report.email_template_shift_report', raise_if_not_found=False)
        for record in self:
            if record.name == 'Новый рапорт смены' or not record.name:
                record.name = f"Рапорт смены за {record.date}"

            record.write({
                'state': 'confirmed',
                'sent_date': fields.Datetime.now(),
            })

            if template and record.director_email:
                template.send_mail(record.id, force_send=True)

            msg_body = (
                f"<b>Рапорт смены за {record.date} подтвержден и отправлен директору.</b><br/>"
                f"• Общий объем выпуска: {record.produced_qty} шт.<br/>"
                f"• Процент брака: {record.scrap_percentage}%<br/>"
                f"• Время критических простоев: {record.critical_downtime_minutes} мин.<br/>"
                f"• Коэффициент выполнения плана: {record.plan_execution_rate}%"
            )
            record.message_post(body=msg_body, message_type='notification')
        return True

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        return True
