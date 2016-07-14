# -*- coding: utf-8 -*-
{
    'name': 'CASUAL',
    'version': '1.0.0',
    'category': 'RH',
    'sequence': 4,
    'author': 'Africa performances',
   'icon': '/ap_pac/static/src/img/icon.png',
    'summary': 'management of casual staff',
    'description': """
Manage several members
======================================

This App for manage cusual staff of your business
    """,
    'depends': ["base", "project", "hr"],
    'data': [
        'apgebat_poc.xml',
        'wizard/schedule_week.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}