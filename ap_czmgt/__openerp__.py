# -*- coding: utf-8 -*-
{
    'name': 'AP CZ management',
    'version': '1.0.0',
    'category': 'account,stock',
    'sequence': 3,
    'author': 'Africa performances',
    'summary': 'Manage members of website PAC',
    'description': """
Manage several members
======================================

This App for manage members of africa performances website PAC
    """,
    'depends': ["base","account_accountant","stock"],
    'data': [
        'ap_csmgt.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}