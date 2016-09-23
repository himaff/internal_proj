# -*- coding: utf-8 -*-
{
    'name': 'Footer mail remove',
    'version': '1.0.0',
    'category': 'email',
    'sequence': 4,
    'author': 'Africa performances',
    'summary': 'modify email footer',
    'description': """
email footer
======================================

this app by odoo
    """,
    'depends': ["base", "mail"],
    'data': [
        "invoice_report.xml",
        ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
