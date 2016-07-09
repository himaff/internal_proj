# -*- coding: utf-8 -*-
{
    'name': 'AP PAC',
    'version': '1.0.0',
    'category': 'Liste',
    'sequence': 3,
    'author': 'Africa performances',
   'icon': '/ap_pac/static/src/img/icon.png',
    'summary': 'Manage members of website PAC',
    'description': """
Manage several members
======================================

This App for manage members of africa performances website PAC
    """,
    'depends': ["base"],
    'data': [
        'ap_pac.xml',
        'perfac.xml',
        'report/report.xml',
        'perfac1.xml',
        'report/report1.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}