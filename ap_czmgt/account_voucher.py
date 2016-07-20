# -*- coding: utf-8 -*-
# © <2016> <Africa Performances>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import time
from lxml import etree

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw
import openerp

class account_voucher(osv.osv):
    _name = 'account.voucher'
    _inherit = 'account.voucher'

# Modification of the initial on change method specific for cz_view
