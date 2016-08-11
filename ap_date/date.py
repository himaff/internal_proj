# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime

    
class purchase_order(osv.osv):
    _inherit ='purchase.order'
	
    _columns={
        'date_order':fields.date('Order Date', required=True, states={'confirmed':[('readonly',True)],
                                                                      'approved':[('readonly',True)]},
                                 select=True, help="Depicts the date where the Quotation should be validated and converted into a Purchase Order, by default it's the creation date.",
                                 copy=False),
    }

	
    
class sale_order(osv.osv):
    _inherit ='sale.order'
  
    _columns={
        'date_order': fields.date('Date', required=True, readonly=True, select=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False),
    }

    
   