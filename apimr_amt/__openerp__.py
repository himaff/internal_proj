# -*- coding: utf-8 -*-
{
    'name': 'Amortissement IMR',
    'version': '1.0.0',
    'category': 'Account',
    'sequence': 4,
    'author': 'Africa performances',
    'summary': 'management of casual staff',
    'description': """
Manage several members
======================================

This App for account asset and update amort date at 31/12
    """,
    'depends': ["base", "account", "account_asset"],
    'data': [
        'amt_rename.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}