# -*- coding: utf-8 -*-
{
    'name': 'fleet extension',
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
    'depends': ['base',],
    'data': [
        'movement.xml',
		'reparation.xml',
		'ravitaillement.xml',
		'rechargement.xml',
		
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}