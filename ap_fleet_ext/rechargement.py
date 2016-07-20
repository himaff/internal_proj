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
		'vehicle': fields.char('Vehicule', size=128, required=True),
		'user': fields.char('Utilisateur', size=128, required=True),
		'amount_before_reloading': fields.float('Solde avant rechargement', digits=(2,1)),
		'reloading': fields.float('Rechargement', digits=(2,1)),
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