# -*- coding: utf-8 -*-
{
    'name': 'ap change numfiscal',
    'version': '1.0.0',
    'category': 'Liste',
    'sequence': 3,
    'author': 'Africa performances',
    'summary': 'change numero fiscal',
    'description': """
Management of numero fiscal
=======================================

This App change numero fiscal in N° TVA Intracommunautaire
    """,
    'depends': ['base', 'account'],
    'data': ['ap_change_numfiscal.xml','report_change_numfiscal.xml',],
    'installable': True,
    'application': False,
    'auto_install': False,
}