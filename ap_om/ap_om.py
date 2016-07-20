# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class ap_om(osv.osv):
    _name = 'ap.om'
    _order = 'ref asc'

    _columns = {
        'name_id': fields.many2one('hr.employee', 'name of employee'),
        'ref': fields.char('Reference', size=128, required=True),
        'project_name': fields.many2one('project.project', 'project name'),
        'object': fields.char('object', size=128, required=True),
        'route_to_go': fields.char('road go', size=128, required=True),
        'route_return': fields.char('return route', size=128, required=True),
        'date_hour_depart': fields.date('date hour depart', required=True),
        'date_hour_return': fields.date('date hour return', required=True),
        'accompanying_person': fields.many2many('res.partner', '', 'name_id', 'partner_id', 'accompanying person', copy=False),
        'means_of_transport': fields.many2one('fleet.vehicle', 'means_of_transport'),
        'notes_de_frais': fields.many2one('hr.expense.expense', 'notes de frais', required=True),		
        'active': fields.boolean('Active', help="If a om is not active, it will not be displayed in om"),
    }

    _defaults = {
        'active' : True
    }

    _sql_constraints = [
        ('uniq_ref', 'unique(ref)', "A om already exists with this ref in database. ref must be unique!"),
        ('uniq_project_name', 'unique(project_name)', "A project_name already exists with this name in database. project_name must be unique!"),
    ]