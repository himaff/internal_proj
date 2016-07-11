# -*- coding: utf-8 -*-
# © <2016> <Africa Performances>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import openerp
from openerp import tools, api
from openerp.osv import fields, osv, orm
from openerp.osv.expression import get_unaccent_wrapper

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import email_re, email_split

from lxml import etree
import math
import pytz
import urlparse

from datetime import datetime
from operator import itemgetter

# Account module inherit in voucher and account journal

class account_journal(osv.osv):
    _name = "account.journal"
    _inherit = "account.journal"

    _columns = {
        'section_id': fields.many2one('crm.case.section','Team', help="CZ Team")
    }
	
    def on_change_journal_section_id(self, cr, uid, ids, user_id, context=None):
        values = {}
        if user_id:
            user = self.pool.get('res_users').browse(cr, uid, user_id, context=context)
            values = {'section_id': user.default_section_id,}
        return {'value': values}

class account_voucher(osv.osv):
    _name = "account.voucher"
    _inherit = "account.voucher"

    _columns = {
        'user_id': fields.many2one('res.users','User', readonly=True, help="User CZ"),
        'section_id': fields.many2one('crm.case.section','Team', readonly=True, help="CZ Team")
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }
    
    def on_change_voucher_section_id(self, cr, uid, ids, user_id, context=None):
        values = {}
        if user_id:
            user = self.pool.get('crm.case.section').browse(cr, uid, user_id, context=context)
            values = {'section_id': user.section_id,}
        return {'value': values}
	
# Warehouse module inherit in warehouse, location, picking type, picking and stock move
	
class stock_warehouse(osv.osv):
    _name = "stock.warehouse"
    _inherit = "stock.warehouse"

    _columns = {
        'user_id': fields.many2one('res.users','User', help="User CZ"),
        'section_id': fields.many2one('crm.case.section','Team', readonly=True, help="CZ Team")
    }
    
    def on_change_warehouse_section_id(self, cr, uid, ids, user_id, context=None):
        values = {}
        if user_id:
            user = self.pool.get('crm.case.section').browse(cr, uid, user_id, context=context)
            values = {'section_id': user.section_id,}
        return {'value': values}

class stock_location(osv.osv):
    _name = "stock.location"
    _inherit = "stock.location"

    _columns = {
        'user_id': fields.many2one('res.users','User', help="User CZ"),
        'section_id': fields.many2one('crm.case.section','Team', readonly=True, help="CZ Team")
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }
    
    def on_change_location_section_id(self, cr, uid, ids, user_id, context=None):
        values = {}
        if user_id:
            user = self.pool.get('crm.case.section').browse(cr, uid, user_id, context=context)
            values = {'section_id': user.section_id,}
        return {'value': values}

class stock_picking_type(osv.osv):
    _name = "stock.picking.type"
    _inherit = "stock.picking.type"

    _columns = {
        'user_id': fields.many2one('res.users','User', help="User CZ"),
        'section_id': fields.many2one('crm.case.section','Team', help="CZ Team")
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }
    
    def on_change_picking_type_section_id(self, cr, uid, ids, user_id, context=None):
        values = {}
        if user_id:
            user = self.pool.get('crm.case.section').browse(cr, uid, user_id, context=context)
            values = {'section_id': user.section_id,}
        return {'value': values}

class stock_picking(osv.osv):
    _name = "stock.picking"
    _inherit = "stock.picking"

    _columns = {
        'user_id': fields.many2one('res.users','User', readonly=True, help="User CZ"),
        'section_id': fields.many2one('crm.case.section','Team', readonly=True, help="CZ Team")
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }
    
    def on_change_voucher_section_id(self, cr, uid, ids, user_id, context=None):
        values = {}
        if user_id:
            user = self.pool.get('crm.case.section').browse(cr, uid, user_id, context=context)
            values = {'section_id': user.section_id,}
        return {'value': values}

class stock_move(osv.osv):
    _name = "stock.move"
    _inherit = "stock.move"

    _columns = {
        'user_id': fields.many2one('res.users','User', readonly=True, help="User CZ"),
        'section_id': fields.many2one('crm.case.section','Team', readonly=True, help="CZ Team")
    }
	
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
    }
    
    def on_change_voucher_section_id(self, cr, uid, ids, user_id, context=None):
        values = {}
        if user_id:
            user = self.pool.get('crm.case.section').browse(cr, uid, user_id, context=context)
            values = {'section_id': user.section_id,}
        return {'value': values}