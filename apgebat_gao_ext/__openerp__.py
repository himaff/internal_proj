# -*- coding: utf-8 -*-
{
    'name': 'AP BTP Execution du projet',
    'version': '1.0.0',
    'category': 'Liste',
    'sequence': 3,
    'author': 'Africa performances',
   'icon': '/apgebat_gao_ext/static/description/icon.png',
    'summary': ' manage its subscription to tenders',
    'description': """
Manage subscription to tenders
======================================

This application allows a company to manage its subscription to tenders.
it recapitulates all the points relating to the tender ( cost , price, Elements folder and other documents)
and allows the manager to monitor the dedicated team throughout this process.
    """,
    'depends': ["base","apgebat_gao", "apgebat_ach"],
    'data': [
        'apgebat_gao_ext.xml',
        'data/gao_ext_data.xml',
        'security/ir.model.access.csv'
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}