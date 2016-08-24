# -*- coding: utf-8 -*-

import openerp
from openerp import models, fields, api, _
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime

    
class ap_change_numfiscal(osv.osv):
    _name='res.partner'
    _inherit ='res.partner'

    _columns = {
        'vat': fields.char('Reverse charge V.A.T N°', help="Tax Identification Number. Check the box if this contact is subjected to taxes. Used by the some of the legal statements."),
    }
	
	
	
	



	
	
		



    
   