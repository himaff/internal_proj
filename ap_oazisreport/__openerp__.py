# -*- encoding: utf-8 -*-
########################
#
#Author: Africa Performances and Marc Hilarion AFFECHI
#
#########################
{
    'name': 'Report custom for oazis',
    'version': '1.0',
    'author': 'Africa Performances',
    'category': 'sale',
    'icon': '/ap_invoice/static/description/icon.png',
    'sequence': 3,
    'website': 'http://www.africaperformances-ci.com/',
    'description': """
* custom report_invoice
* custom report_saleorder
""",
    'depends': ['ap_object_amount_text', 'stock',],
    'data': ['ap_invoice.xml','ap_sale.xml','ap_delivery.xml','ap_paperformat.xml',],
	'auto_install': False,
    'installable': True,
    'application': False,	
}


