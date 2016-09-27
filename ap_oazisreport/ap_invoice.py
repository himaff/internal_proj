# -*- coding: utf-8 -*-

import openerp
from openerp import models, fields, api, _
from openerp.tools.translate import _
import time




class account_invoice(models.Model):
    _inherit = "account.invoice"
    def name_maj(self, val):
    	return str(val).upper()

    @api.one
    @api.depends('date_invoice')
    def _compute_date(self):
    	if self.date_invoice:
    		self.date_text=time.strftime('%d %B %Y',time.strptime(self.date_invoice,'%Y-%m-%d'))
    	else:
    		self.date_text=""

    date_text = fields.Char(string='date', store=True, readonly=True, compute='_compute_date', track_visibility='always')

   	