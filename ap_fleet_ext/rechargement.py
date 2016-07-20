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
		'amount_before_reloading': fields.char('Somme avant rechargement', size=128, required=True),
		'reloading': fields.char('Rechargement', size=128, required=True),
		'bonus_fcfa': fields.char('Bonus en FCFA', size=128, required=True),
		'amount_after_reloading': fields.char('Somme apres rechargement', size=128, required=True),
    }

    _defaults = {
        'active' : True
    }

    _sql_constraints = [
        ('uniq_card_number', 'unique(card_number)', "A rechargement already exists with this card_number in database. card_number must be unique!"),
    ]