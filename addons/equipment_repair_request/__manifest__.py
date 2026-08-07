{
    'name': 'Equipment Repair Requests',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Instant breakdown notifications and repair request management for chief mechanic',
    'depends': [
        'mrp',
        'mail',
        'equipment_downtime',
    ],
    'data': [
        'security/equipment_repair_security.xml',
        'security/ir.model.access.csv',
        'wizard/assign_mechanic_wizard_views.xml',
        'views/equipment_repair_request_views.xml',
        'views/mrp_workcenter_views.xml',
        'data/repair_request_demo.xml',
    ],
    'demo': [
        'data/repair_request_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
