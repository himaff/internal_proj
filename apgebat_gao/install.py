# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class tender_type(osv.osv):
    _name='tender.type'

    _columns = {
        'name': fields.char('Nom'),
        'code': fields.char('code'),
    }

class tender_installer(osv.osv_memory):
    _name='tender.installer'

    _columns = {
        'activity': fields.many2many('group.proj.dep', 'group_rel', 'group_id', 'name', 'Tenders type')
    }


    def action_next(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        data = self.read(cr, uid, ids, context=context)[0]

        for act in data['activity']:
            acti=self.pool.get('group.proj.dep').browse(cr, uid, act)
            self.pool.get('tender.type').create(cr, uid, {'name':acti.name, 'code':acti.code,})
        return self.pool.get('res.config')._next(cr, uid, context=None)

class group_by_proj_dep(osv.osv_memory):
    _name='group.proj.dep'

    _columns = {
        'name': fields.char('groupe'),
        'code': fields.char('code'),
    }