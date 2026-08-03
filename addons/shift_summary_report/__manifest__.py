{
    'name': 'Shift Summary Report for Director',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Automatic shift summary report generation and director notification',
    'depends': [
        'mrp',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'data/shift_summary_report_demo.xml',
        'views/shift_summary_report_views.xml',
    ],
    'demo': [
        'data/shift_summary_report_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
