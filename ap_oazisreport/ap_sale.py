# -*- coding: utf-8 -*-

import openerp
from openerp import api
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time





class sale_order(osv.osv):
    _inherit = "sale.order"


    def name_maj(self, val):
    	return str(val).upper()

    @api.one
    @api.depends('date_order')
    def _compute_date(self):
    	if self.date_order:
    		self.date_text=time.strftime('%d %B %Y',time.strptime(self.date_order,'%Y-%m-%d %H:%M:%S'))
    	else:
    		self.date_text=""

    _columns={
        'date_text': fields.char(string='date', store=True, readonly=True, compute='_compute_date', track_visibility='always')

    }
    


class stock_picking(osv.osv):
    _inherit = "stock.picking"

    @api.one
    @api.depends('date')
    def _compute_date(self):
        if self.date:
            self.date_text=time.strftime('%d %B %Y',time.strptime(self.date,'%Y-%m-%d %H:%M:%S'))
        else:
            self.date_text=""

    _columns = {
        'date_text': fields.char(string='date', store=True, readonly=True, compute='_compute_date', track_visibility='always')
        }


    def name_maj(self, val):
        return str(val).upper()


    def sale_val(self, val, product_id=None):
        sale_id=self.pool.get('sale.order').search(self._cr, self._uid, [('name', '=',  self.origin)])
        sale=self.pool.get('sale.order').browse(self._cr, self._uid, sale_id)
        if val=="object":
            return sale.object
        elif val=="username":
            return sale.user_id.name
        elif val=="userphone":
            return sale.user_id.phone
        elif val=="usermail":
            return sale.user_id.email
        elif val=="totalht":
            return sale.amount_untaxed
        elif val=="tax":
            return sale.amount_tax
        elif val=="totalttc":
            return sale.amount_total
        elif val=="amount_text":
            return sale.amount_text
        elif product_id :
            #raise osv.except_osv(_('jff'), _(val))
            
            for line in sale.order_line:
                if line.product_id.id==product_id:
                    #raise osv.except_osv(_('jff'), _(line.price_subtotal))
                    if val=="pu":
                        return line.price_unit
                    if val=="stotal":
                        #raise osv.except_osv(_('jff'), _(line.price_unit))
                        return line.price_subtotal
        else:
            return ""