{
    'name': 'Equipment Downtime Tracking',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Track equipment downtime and reasons for OEE calculation',
    'depends': [
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/downtime_reason_data.xml',
        'views/downtime_reason_views.xml',
        'views/equipment_downtime_views.xml',
        'views/mrp_workcenter_views.xml',
        'wizard/add_downtime_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
