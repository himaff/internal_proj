# -*- coding: utf-8 -*-

import openerp
from openerp import models, fields, api, _
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime

    

class ap_change_posfiscal(osv.osv):
    _name='res.partner'
    _inherit ='res.partner'

    _columns = {
        'reverse_charge_vat': fields.many2one('account.fiscal.position', 'Reverse charge V.A.T N°'),
    }


class ap_change_numfiscal(osv.osv):
    _name='account.invoice'
    _inherit ='account.invoice'

    _columns = {
        'reverse_charge_vat': fields.many2one('account.fiscal.position', 'Reverse charge V.A.T N°'),
    }
	
	
class ap_suprim_numfiscal(osv.osv):
    _name='account.invoice'
    _inherit ='account.invoice'
	
    def _compute_payments(self):
        fiscal_position = fields.many2one('account.fiscal.position', string='Fiscal Position',
        readonly=True, states={'draft': [('readonly', False)]})
	



	
	
		



    
   