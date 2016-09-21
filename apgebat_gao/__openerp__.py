# -*- coding: utf-8 -*-
{
    'name': 'AP Gestion des appels d\'offres',
    'version': '1.0.2',
    'category': 'Liste',
    'sequence': 3,
    'author': 'Africa performances',
   'icon': '/apgebat_gao/static/description/icon.png',
    'summary': ' manage its subscription to tenders',
    'description': """
Manage subscription to tenders
======================================

This application allows a company to manage its subscription to tenders.
it recapitulates all the points relating to the tender ( cost , price, Elements folder and other documents)
and allows the manager to monitor the dedicated team throughout this process.
    """,
    'depends': ["base","account","sale", "document", "stock", "project"],
    'data': [
        'apgebat_gao.xml',
        'import.xml',
        'install/install.xml',
        'security/ir.model.access.csv',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
