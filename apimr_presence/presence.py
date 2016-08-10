# coding: utf8
import openerp
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import time
import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class hr_attendance(osv.osv):
    _inherit = "hr.attendance"

    def _launcher(self, cr, uid, ids, fieldnames, args, context=None):

        #raise osv.except_osv(_('Error!'), _(fieldnames))
    	return self._worked_hours_compute(cr, uid, ids, fieldnames, args, context=context)

    def _worked_hours_compute(self, cr, uid, ids, fieldnames, args, context=None):
        """For each hr.attendance record of action sign-in: assign 0.
        For each hr.attendance record of action sign-out: assign number of hours since last sign-in.
        """
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'worked_hours': 0,
                'worked_day': 0,
                'worked_miday': 0,
                'week':0,
            }
            if obj.statut=='day':
            	res[obj.id]['worked_day']= obj.work
            if obj.statut=='middle':
            	res[obj.id]['worked_miday']= obj.work
            res[obj.id]['worked_hours']= obj.work
            res[obj.id]['week']=datetime.datetime.strptime(obj.name,'%Y-%m-%d').isocalendar()[1]
        #raise osv.except_osv(_('Error!'), _(res))
        return res

 

    _columns = {

    	'name': fields.date('Date', required=True, select=1),
    	'statut': fields.selection([('day', 'Présent(e) toute la journée'), ('middle', 'Présent(e) une demi journée')], 'Status', required=True),
    	'week': fields.function(_launcher, type='integer', string='Week', store=True, multi=True),
    	'work': fields.integer('Heures', required=True),
    	'action': fields.selection([('sign_in', 'Sign In'), ('sign_out', 'Sign Out'), ('action','Action')], 'Action'),
        'worked_hours': fields.function(_launcher, type='integer', string='Worked Hours', store=True, multi=True),
        'worked_day': fields.function(_launcher, type='integer', string='Worked Hours day', store=True, multi=True),
        'worked_miday': fields.function(_launcher, type='integer', string='Worked Hours mi-day', store=True, multi=True),
    }

    _defaults = {
        'name': lambda *a: time.strftime('%Y-%m-%d'), #please don't remove the lambda, if you remove it then the current time will not change
    }


    def changeStatus(self, cr, uid, ids, status, context=None):
    	if status:
    		values={}
	    	if status=='day':
	    		heure=8
	    	if status=='middle':
	    		heure=4
	    	values = {'work': heure,}
	        return {'value': values}