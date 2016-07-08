# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class ap_pac(osv.osv):
    _name = 'ap.pac'
    _order = 'name asc'

    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'student_pname': fields.char('Public name', size=128, required=True),
        'student_email': fields.char('Email', size=128, required=True),
        'student_country': fields.char('Country', size=128, required=True),
        'student_city': fields.char('City', size=128, required=True),
        'student_gender': fields.selection([('masculin','Masculin'),
              ('feminin','Féminin')],'Gender', required=True),
        'student_birth': fields.date('Birth', required=True),
        'active': fields.boolean('Active', help="If a student is not active, it will not be displayed in PAC"),
    }

    _defaults = {
        'active' : True
    }

    _sql_constraints = [
        ('uniq_name', 'unique(student_pname)', "A student already exists with this name in Performances Académie. student's name must be unique!"),
        ('uniq_mail', 'unique(student_email)', "A mail already exists with this name in Performances Académie. student's email must be unique!"),
    ]