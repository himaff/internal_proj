# -*- coding: utf-8 -*-
{
    'name': 'Demande d\'achat en interne',
    'version': '1.0.0',
    'category': 'achat',
    'sequence': 3,
    'author': 'Africa performances',
   'icon': '/apgebat_ach/static/description/icon.png',
    'summary': 'achat',
    'description': """
gestion des demande d'achat en interne
======================================

This App for manage members of africa performances website PAC
    """,
    'depends': ["base", "purchase", "project", "hr", "apgebat_gao"],
    'data': [
        'apgebat_ach.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}