from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.fields import Date


class TestEquipmentDowntime(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Reason = cls.env['downtime.reason']
        cls.Workcenter = cls.env['mrp.workcenter']
        cls.Downtime = cls.env['equipment.downtime']
        cls.Wizard = cls.env['add.downtime.wizard']

        cls.reason_breakdown = cls.Reason.create({
            'name': 'Test Breakdown',
            'code': 'TEST_BREAKDOWN',
        })

        cls.workcenter = cls.Workcenter.create({
            'name': 'Test CNC Machine',
            'code': 'TEST-CNC-01',
            'time_efficiency': 100.0,
        })

    def test_01_downtime_creation_and_workcenter_total(self):
        """Test creating equipment downtime updates workcenter totals."""
        self.assertEqual(self.workcenter.total_downtime_minutes, 0.0)
        self.assertEqual(self.workcenter.downtime_count, 0)

        self.Downtime.create({
            'workcenter_id': self.workcenter.id,
            'date': Date.today(),
            'duration': 60.0,
            'reason_id': self.reason_breakdown.id,
            'notes': 'Test spindle overheat',
        })

        self.assertEqual(self.workcenter.total_downtime_minutes, 60.0)
        self.assertEqual(self.workcenter.downtime_count, 1)

    def test_02_net_working_time_and_adjusted_oee(self):
        """Test calculation of net working time and adjusted OEE percentage."""
        self.Downtime.create({
            'workcenter_id': self.workcenter.id,
            'date': Date.today(),
            'duration': 120.0,
            'reason_id': self.reason_breakdown.id,
        })

        # Nominal time = 480 min. Downtime = 120 min. Net time = 360 min.
        # Adjusted OEE = (360 / 480) * 100 = 75.0%
        self.assertEqual(self.workcenter.net_working_time, 360.0)
        self.assertAlmostEqual(self.workcenter.downtime_adjusted_oee, 75.0, places=2)

    def test_03_wizard_validation_and_execution(self):
        """Test wizard validation for duration > 0 and successful creation."""
        wizard_invalid = self.Wizard.create({
            'workcenter_id': self.workcenter.id,
            'duration': 0.0,
            'reason_id': self.reason_breakdown.id,
        })
        with self.assertRaises(UserError):
            wizard_invalid.action_add_downtime()

        wizard_valid = self.Wizard.create({
            'workcenter_id': self.workcenter.id,
            'duration': 45.0,
            'reason_id': self.reason_breakdown.id,
            'notes': 'Valid downtime entry via wizard',
        })
        action = wizard_valid.action_add_downtime()
        self.assertEqual(action.get('type'), 'ir.actions.act_window_close')
