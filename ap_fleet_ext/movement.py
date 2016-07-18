# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class movement(osv.osv):
    _name = 'movement'
    _order = 'applicant'

    _columns = {
        'applicant': fields.char('Nature operation', size=128, required=True),		
        'project_name': fields.many2one('project.project', 'projet'),
        'operation_nature': fields.char('Nature operation', size=128, required=True),
		'license_plate': fields.char('immatriculation vehicule', size=128, required=True),
        'driver_id': fields.many2one('hr.employee', 'Conducteur'),
        'start_date': fields.date('date depart', required=True),
        'return_date': fields.date('date retour', required=True),
		'km_start': fields.char('Km depart', size=128, required=True),
		'return_km': fields.char('Km retour', size=128, required=True),
		'traveled_km': fields.char('Km parcourus', size=128, required=True),
		'leasing_duraton': fields.char('Duree location', size=128, required=True),
		'price_list': fields.char('Tarif', size=128, required=True),
		'leasing_amount': fields.char('montant location', size=128, required=True),
		'maintenance_amount': fields.char('montant entretien', size=128, required=True),
    }

    _defaults = {
        'active' : True
    }

    _sql_constraints = [
        ('uniq_license_plate', 'unique(license_plate)', "A movement already exists with this license_plate in database. license_plate must be unique!"),
        ('uniq_driver_id', 'unique(driver_id)', "A driver_id already exists with this name in database. driver_id must be unique!"),
    ]