from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.fields import Datetime, Date


class TestEquipmentRepairRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Workcenter = cls.env['mrp.workcenter']
        cls.Reason = cls.env['downtime.reason']
        cls.Downtime = cls.env['equipment.downtime']
        cls.RepairRequest = cls.env['equipment.repair.request']
        cls.AssignWizard = cls.env['assign.mechanic.wizard']

        cls.workcenter = cls.Workcenter.create({
            'name': 'ЧПУ Станок Milling-01',
            'code': 'CNC-TEST-01',
        })
        cls.reason_breakdown = cls.Reason.create({
            'name': 'Поломка оборудования',
            'code': 'BREAKDOWN',
        })
        cls.mechanic_user = cls.env.user

    def test_01_auto_repair_request_on_emergency_downtime(self):
        """Test creating an emergency downtime automatically creates a repair request with state 'needs_repair'."""
        downtime = self.Downtime.create({
            'workcenter_id': self.workcenter.id,
            'date': Date.today(),
            'duration': 90.0,
            'reason_id': self.reason_breakdown.id,
            'notes': 'Протекает масло в гидравлике',
        })

        requests = self.RepairRequest.search([('downtime_id', '=', downtime.id)])
        self.assertEqual(len(requests), 1, "Should create exactly 1 repair request on breakdown downtime creation")
        req = requests[0]
        self.assertEqual(req.state, 'needs_repair')
        self.assertEqual(req.workcenter_id, self.workcenter)
        self.assertIn('Протекает масло в гидравлике', req.description)

    def test_02_mechanic_assignment_and_state_change(self):
        """Test assigning a mechanic and transitioning state to 'in_progress'."""
        req = self.RepairRequest.create({
            'workcenter_id': self.workcenter.id,
            'stop_datetime': Datetime.now(),
            'description': 'Сбой датчика уровня масла',
            'state': 'needs_repair',
        })
        self.assertEqual(req.state, 'needs_repair')
        self.assertFalse(req.assignee_id)

        # Directly changing or using action without assignee raises error
        with self.assertRaises(UserError):
            req.action_start_repair()

        # Assign mechanic and start repair
        req.write({'assignee_id': self.mechanic_user.id})
        req.action_start_repair()
        self.assertEqual(req.state, 'in_progress')

        # Complete repair
        req.action_complete_repair()
        self.assertEqual(req.state, 'done')

    def test_03_wizard_mechanic_assignment(self):
        """Test assign.mechanic.wizard assigns mechanic and sets state to 'in_progress'."""
        req = self.RepairRequest.create({
            'workcenter_id': self.workcenter.id,
            'stop_datetime': Datetime.now(),
            'description': 'Протекает масло в гидравлике',
            'state': 'needs_repair',
        })

        wizard = self.AssignWizard.create({
            'request_id': req.id,
            'assignee_id': self.mechanic_user.id,
            'comment': 'Выехать срочно с ремкомплектом гидравлики',
        })
        wizard.action_confirm()

        self.assertEqual(req.assignee_id, self.mechanic_user)
        self.assertEqual(req.state, 'in_progress')

    def test_04_workcenter_repair_request_count(self):
        """Test workcenter repair request count compute and breakdown reporting action."""
        self.assertEqual(self.workcenter.repair_request_count, 0)
        self.RepairRequest.create({
            'workcenter_id': self.workcenter.id,
            'stop_datetime': Datetime.now(),
            'description': 'Тестовая заклинившая направляющая',
        })
        self.assertEqual(self.workcenter.repair_request_count, 1)

        action = self.workcenter.action_report_breakdown()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'equipment.repair.request')
