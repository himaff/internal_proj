# -*- coding: utf-8 -*-
{
    'name': 'AP OM',
    'version': '1.0.0',
    'category': 'Liste',
    'sequence': 3,
    'author': 'Africa performances',
    'summary': 'Management of the orders',
    'description': """
Manage several members
=======================================

This App for manage members of africa performances website PAC
    """,
    'depends': ['base','hr_expense','fleet'],
    'data': [
        'ap_om.xml',
		'ap_om_report.xml',
		'report_mission.xml',
		
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}