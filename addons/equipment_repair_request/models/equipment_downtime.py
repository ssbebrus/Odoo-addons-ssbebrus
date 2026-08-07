from odoo import api, fields, models, _


class EquipmentDowntime(models.Model):
    _inherit = 'equipment.downtime'

    repair_request_ids = fields.One2many(
        'equipment.repair.request',
        'downtime_id',
        string='Заявки на ремонт'
    )
    repair_request_count = fields.Integer(
        string='Количество заявок на ремонт',
        compute='_compute_repair_request_count'
    )

    @api.depends('repair_request_ids')
    def _compute_repair_request_count(self):
        for record in self:
            record.repair_request_count = len(record.repair_request_ids)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # Check if reason indicates a breakdown or breakdown keyword, or create automatic repair request
            reason_name = (record.reason_id.name or '').lower()
            is_breakdown = 'поломк' in reason_name or 'аварий' in reason_name or 'ремонт' in reason_name or record.reason_id.code == 'BREAKDOWN'
            
            # If it's a breakdown or if notes are provided, automatically generate a repair request card
            if is_breakdown or record.notes:
                req_vals = {
                    'workcenter_id': record.workcenter_id.id,
                    'stop_datetime': fields.Datetime.now(),
                    'description': record.notes or _("Аварийная остановка станка: %s") % record.reason_id.name,
                    'state': 'needs_repair',
                    'downtime_id': record.id,
                    'reporter_id': record.user_id.id if record.user_id else self.env.user.id,
                }
                repair_req = self.env['equipment.repair.request'].create(req_vals)
                
                # Notify chief mechanic group via chatter
                try:
                    chief_group = self.env.ref('equipment_repair_request.group_chief_mechanic', raise_if_not_found=False)
                    if chief_group and chief_group.users:
                        partner_ids = chief_group.users.mapped('partner_id').ids
                        repair_req.message_post(
                            body=_("🚨 <b>АВАРИЙНАЯ ОСТАНОВКА СТАНКА!</b><br/>Зафиксирован простаивающий рабочий центр: <b>%s</b>.<br/>Причина: %s.<br/>Комментарий: %s") % (
                                record.workcenter_id.name,
                                record.reason_id.name,
                                record.notes or 'Не указан'
                            ),
                            partner_ids=partner_ids,
                            subtype_xmlid='mail.mt_comment'
                        )
                except Exception:
                    pass
        return records

    def action_view_repair_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Заявки на ремонт',
            'res_model': 'equipment.repair.request',
            'view_mode': 'kanban,list,form',
            'domain': [('downtime_id', '=', self.id)],
            'context': {'default_downtime_id': self.id, 'default_workcenter_id': self.workcenter_id.id},
        }
