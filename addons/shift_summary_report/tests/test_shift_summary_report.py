from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.fields import Date


class TestShiftSummaryReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ShiftReport = cls.env['shift.summary.report']

        cls.report = cls.ShiftReport.create({
            'name': 'Test Shift Report',
            'date': Date.today(),
            'shift_name': 'day',
            'director_email': 'director@factory.com',
            'planned_qty': 500.0,
            'produced_qty': 450.0,
            'scrap_qty': 18.0,
            'critical_downtime_minutes': 25.0,
            'notes': 'Test shift comments',
        })

    def test_01_metrics_calculation(self):
        """Test calculation of scrap percentage and plan execution coefficient."""
        # scrap_percentage = (18 / 450) * 100 = 4.0%
        # plan_execution_rate = (450 / 500) * 100 = 90.0%
        self.assertAlmostEqual(self.report.scrap_percentage, 4.0, places=2)
        self.assertAlmostEqual(self.report.plan_execution_rate, 90.0, places=2)

        # Test zero division edge case
        zero_report = self.ShiftReport.create({
            'planned_qty': 0.0,
            'produced_qty': 0.0,
            'scrap_qty': 0.0,
        })
        self.assertEqual(zero_report.scrap_percentage, 0.0)
        self.assertEqual(zero_report.plan_execution_rate, 0.0)

    def test_02_action_confirm_and_send(self):
        """Test transition to confirmed state, sent_date population, and default title generation."""
        draft_report = self.ShiftReport.create({
            'name': 'Новый рапорт смены',
            'date': Date.today(),
            'shift_name': 'night',
            'director_email': 'director@test.com',
            'planned_qty': 100.0,
            'produced_qty': 100.0,
        })
        self.assertEqual(draft_report.state, 'draft')
        self.assertFalse(draft_report.sent_date)

        draft_report.action_confirm_and_send()

        self.assertEqual(draft_report.state, 'confirmed')
        self.assertTrue(draft_report.sent_date)
        self.assertTrue(draft_report.name.startswith('Рапорт смены за'))

    def test_03_non_negative_validation(self):
        """Test validation rules against negative values for quantities and downtime."""
        with self.assertRaises(ValidationError):
            self.ShiftReport.create({
                'planned_qty': -10.0,
            })

        with self.assertRaises(ValidationError):
            self.ShiftReport.create({
                'produced_qty': -5.0,
            })

        with self.assertRaises(ValidationError):
            self.ShiftReport.create({
                'scrap_qty': -1.0,
            })

        with self.assertRaises(ValidationError):
            self.ShiftReport.create({
                'critical_downtime_minutes': -15.0,
            })

    def test_04_reset_to_draft(self):
        """Test resetting report status to draft."""
        self.report.action_confirm_and_send()
        self.assertEqual(self.report.state, 'confirmed')

        self.report.action_reset_to_draft()
        self.assertEqual(self.report.state, 'draft')
