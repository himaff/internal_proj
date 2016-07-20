# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class ravitaillemet(osv.osv):
    _name = 'ravitaillement'
    _order = 'license_plate'

    _columns = {
	    'vehicle': fields.char('Vehicule', size=128, required=True),
        'license_plate': fields.char('Immatriculation vehicule', size=128, required=True),
		'vehicle_consumption': fields.char('Consommation du vehicule', size=128, required=True),
        'vehicle_refueling': fields.char('ravitaillement', size=128, required=True),
        'previous_refueling_km': fields.char('Kilometrage au ravitaillement precedent', size=128, required=True),
        'current_refueling_km': fields.char('Kilometrage au ravitaillement actuel', size=128, required=True),		
    }

    _defaults = {
        'active' : True
    }

    _sql_constraints = [
        ('uniq_license_plate', 'unique(license_plate)', "A ravitaillement already exists with this license_plate in database. license_plate must be unique!"),
    ]