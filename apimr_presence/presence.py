# coding: utf8
import openerp
from openerp import api
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import time
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    drop_view_if_exists,
)
#import datetime
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class hr_attendance(osv.osv):
    _inherit = "hr.attendance"
    _rec_name= 'day'



    def _launcher(self, cr, uid, ids, fieldnames, args, context=None):

        #raise osv.except_osv(_('Error!'), _(fieldnames))
    	return self._hours_compute(cr, uid, ids, fieldnames, args, context=context)

    def _hours_compute(self, cr, uid, ids, fieldnames, args, context=None):
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
            res[obj.id]['week']= 'Week '+ str(datetime.strptime(obj.day,'%Y-%m-%d').isocalendar()[1])
        #raise osv.except_osv(_('Error!'), _(res))
        return res

    @api.one
    @api.onchange('day')
    def onchange_day_change_name(self):
        date=self.day
        heure=time.strftime('%H:%M:%S',time.localtime())
        self.name=date+' '+heure
 

    @api.one
    @api.depends('work')
    def _worked_hours_compute(self):
        self.worked_hours=self.work

    _columns = {

    	'day': fields.date('Date', required=True, select=1),
    	'statut': fields.selection([('day', 'Présent(e) toute la journée'), ('middle', 'Présent(e) une demi journée')], 'Status', required=True),
    	'week': fields.function(_launcher, type='char', string='Week', store=True, multi=True),
    	'work': fields.integer('Heures', required=True),
        'worked_hours': fields.float(string='Worked Hours', store=True , readonly=True, compute='_worked_hours_compute', track_visibility='always'),
    	'action': fields.selection([('sign_in', 'Sign In'), ('sign_out', 'Sign Out'), ('action','Action')], 'Action'),
        'worked_hours': fields.function(_launcher, type='integer', string='Worked Hours', store=True, multi=True),
        'worked_day': fields.function(_launcher, type='integer', string='Worked Hours day', store=True, multi=True),
        'worked_miday': fields.function(_launcher, type='integer', string='Worked Hours mi-day', store=True, multi=True),
    }

    _defaults = {
        'day': time.strftime('%Y-%m-%d',time.localtime()),
    }


    def _altern_si_so(self, cr, uid, ids, context=None):
        return True
    _constraints = [(_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]
    

    def changeStatus(self, cr, uid, ids, status, context=None):
    	if status:
    		values={}
	    	if status=='day':
	    		heure=8
	    	if status=='middle':
	    		heure=4
	    	values = {'work': heure,}
	        return {'value': values}

    
class hr_timesheet_sheet_sheet_day(osv.osv):
    _inherit = "hr_timesheet_sheet.sheet.day"


    _depends = {
        'account.analytic.line': ['date', 'unit_amount'],
        'hr.analytic.timesheet': ['line_id', 'sheet_id'],
        'hr.attendance': ['statut', 'day', 'sheet_id'],
    }

    def init(self, cr):
        drop_view_if_exists(cr, 'hr_timesheet_sheet_sheet_day')
        cr.execute("""create or replace view hr_timesheet_sheet_sheet_day as
            SELECT
                id,
                name,
                sheet_id,
                total_timesheet,
                total_attendance,
                cast(round(cast(total_attendance - total_timesheet as Numeric),2) as Double Precision) AS total_difference
            FROM
                ((
                    SELECT
                        MAX(id) as id,
                        name,
                        sheet_id,
                        timezone,
                        SUM(total_timesheet) as total_timesheet,
                        CASE WHEN SUM(orphan_attendances) != 0
                            THEN (SUM(total_attendance) +
                                CASE WHEN current_date <> name
                                    THEN 1440
                                    ELSE (EXTRACT(hour FROM current_time AT TIME ZONE 'UTC' AT TIME ZONE coalesce(timezone, 'UTC')) * 60) + EXTRACT(minute FROM current_time AT TIME ZONE 'UTC' AT TIME ZONE coalesce(timezone, 'UTC'))
                                END
                                )
                            ELSE SUM(total_attendance)
                        END  as total_attendance
                    FROM
                        ((
                            select
                                min(hrt.id) as id,
                                p.tz as timezone,
                                l.date::date as name,
                                s.id as sheet_id,
                                sum(l.unit_amount) as total_timesheet,
                                0 as orphan_attendances,
                                0.0 as total_attendance
                            from
                                hr_analytic_timesheet hrt
                                JOIN account_analytic_line l ON l.id = hrt.line_id
                                LEFT JOIN hr_timesheet_sheet_sheet s ON s.id = hrt.sheet_id
                                JOIN hr_employee e ON s.employee_id = e.id
                                JOIN resource_resource r ON e.resource_id = r.id
                                LEFT JOIN res_users u ON r.user_id = u.id
                                LEFT JOIN res_partner p ON u.partner_id = p.id
                            group by l.date::date, s.id, timezone
                        ) union (
                            select
                                -min(a.id) as id,
                                p.tz as timezone,
                                (a.name AT TIME ZONE 'UTC' AT TIME ZONE coalesce(p.tz, 'UTC'))::date as name,
                                s.id as sheet_id,
                                0.0 as total_timesheet,
                                SUM(CASE WHEN a.action = 'sign_in' THEN -1 ELSE 0 END) as orphan_attendances,
                                SUM(a.work) as total_attendance
                            from
                                hr_attendance a
                                LEFT JOIN hr_timesheet_sheet_sheet s
                                ON s.id = a.sheet_id
                                JOIN hr_employee e
                                ON a.employee_id = e.id
                                JOIN resource_resource r
                                ON e.resource_id = r.id
                                LEFT JOIN res_users u
                                ON r.user_id = u.id
                                LEFT JOIN res_partner p
                                ON u.partner_id = p.id
                            group by (a.name AT TIME ZONE 'UTC' AT TIME ZONE coalesce(p.tz, 'UTC'))::date, s.id, timezone
                        )) AS foo
                        GROUP BY name, sheet_id, timezone
                )) AS bar""")
