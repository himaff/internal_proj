# -*- coding: utf-8 -*-
{
    'name': 'fleet extension',
    'version': '1.0.0',
    'category': 'Liste',
    'sequence': 3,
    'author': 'Africa performances',
    'summary': 'Management of the vehicle',
    'description': """
Management of vehicle
=======================================

This App for manage vehicle 
    """,
    'depends': ['base','fleet'],
    'data': [
	    'movement.xml',
		'ravitaillement.xml',
		'rechargement.xml',
        'reparation.xml',
		
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}