# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class reparation(osv.osv):
    _name = 'reparation'
    _order = 'license_plate'

    _columns = {
	    'reparation_date': fields.date('Date de reparation', required=True),
		'license_plate': fields.char('Immatriculation vehicule', size=128, required=True),
		'vehicle': fields.char('Vehicule', size=128, required=True),
		'intervention_type': fields.char('Type intervention', size=128, required=True),
		'designation': fields.char('Designation', size=128, required=True),
		'unit': fields.char('Unite', size=128, required=True),
		'quantity': fields.char('Quantite', size=128, required=True),
		'buyer': fields.char('Acheteur', size=128, required=True),
		'supplier': fields.char('Fournisseur', size=128, required=True),
		'invoice_number': fields.char('Numero facture', size=128, required=True),
		'amount': fields.float('Montant', digits=(2,1)),
		'amount_after_discount': fields.float('Montant apres remise', digits=(2,1)),
		'tva': fields.float('Tva 18%', digits=(2,1)),
		'amount_ttc': fields.float('Montant TTC', digits=(2,1)),
    }

    _defaults = {
        'active' : True
    }

    _sql_constraints = [
        ('uniq_license_plate', 'unique(license_plate)', "A movement already exists with this license_plate in database. license_plate must be unique!"),
    ]
	
    def calcul_montant_ttc(self, cr, uid, ids, montant, context=None):
        tva=montant*0.18
        ttc=montant+tva
        valeur={'tva':tva,'amount_ttc':ttc}
        return {"value":valeur}