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
		'vehicle_consumption': fields.float('Consommation du vehicule', digits=(2,1)),
        'vehicle_refueling': fields.float('Ravitaillement', digits=(2,1)),
        'previous_refueling_km': fields.float('Kilometrage au ravitaillement precedent', digits=(2,1)),
        'current_refueling_km': fields.float('Kilometrage au ravitaillement actuel', digits=(2,1)),		
    }

    _defaults = {
        'active' : True
    }

    _sql_constraints = [
        ('uniq_license_plate', 'unique(license_plate)', "A ravitaillement already exists with this license_plate in database. license_plate must be unique!"),
    ]
	
	
class ravitaillement_fleet(osv.osv):
    _name ='fleet.vehicle.log.fuel'
    _inherit ='fleet.vehicle.log.fuel'
	
    _columns={
        'vehicle_refueling': fields.float('vehicle refueling', digits=(2,1)),
        'previous_refueling_km': fields.float('previous refueling km', digits=(2,1)),
        'current_refueling_km': fields.float('current refueling km', digits=(2,1)),
        'vehicle_consumption': fields.float('vehicle consumption', digits=(2,1)),		
    }	
	
	
	