# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class rechargement(osv.osv):
    _name = 'rechargement'
    _order = 'card_number'

    _columns = {
		'card_number': fields.char('Numero de la carte', size=128, required=True),
		'vehicle': fields.many2one('fleet.vehicle.model', 'Vehicule'),
		'license_plate': fields.many2one('fleet.vehicle.odometer', 'license plate'),
		'driver': fields.many2one('res.partner', 'Driver'),
		'amount_before_reloading': fields.float('Solde avant rechargement', digits=(2,1)),
		'reloading': fields.float('rechargement', digits=(2,1)),
		'bonus_fcfa': fields.float('Bonus en fcfa', digits=(2,1)),
		'amount_after_reloading': fields.float('Solde apres rechargement', digits=(2,1)),
		'amount_reload_total': fields.float('Montant total des rechargement', digits=(2,1)),
		'total_bonus_fcfa': fields.float('Bonus total en fcfa', digits=(2,1)),
		'total_balance_after_reload': fields.float('Solde total apres rechargement', digits=(2,1)),
    }

    _defaults = {
        'active' : True
    }

    _sql_constraints = [
        ('uniq_card_number', 'unique(card_number)', "A rechargement already exists with this card_number in database. card_number must be unique!"),
    ]
	
    def calcul_solde(self, cr, uid, ids, rechargement, context=None):
        bonus=rechargement+0
        solde=rechargement+bonus
        valeur={'bonus_fcfa':bonus,'amount_after_reloading':solde}
        return {"value":valeur}