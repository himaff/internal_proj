# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import logging
_logger = logging.getLogger(__name__)

class apgebat_ach(osv.osv):
    _name = 'apgebat.ach'
   # _order = 'name asc'


    def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
        """ Wrapper because of direct method passing as parameter for function fields """
        #raise osv.except_osv(_('Error!'), _(context))
        return self._amount_all(cr, uid, ids, field_name, arg, context=context)

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_ht': 0.0,
            }
            val1 = 0.0
            #raise osv.except_osv(_('Error!'), _(order.type))
            if order.type=="ordinary":
                for line in order.purchase_line:
                    val1 += line.price_subtotal
            elif order.type=="technical":
                for line in order.purchase_line1:
                    val1 += line.price_subtotal
            res[order.id]['amount_ht'] = val1
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('internal.order.line').browse(cr, uid, ids, context=context):
            result[line.internal_id] = True
        return result.keys()

    def button_dummy(self, cr, uid, ids, context=None):

        return True




    _columns = {
        'accept': fields.selection([('reject','reject'), ('valid', 'valid'), ('end', 'end')],'accept'),
        'type': fields.selection([('ordinary','Ordinary purchases'),('technical','Technical purchasing')],'Type', required=True),
        'project_id': fields.many2one('project.project', 'Project', domain="[('tender_id', '!=', False)]"),
        'master': fields.many2one('res.users', 'Project leader', required=True),
        'employee_ids': fields.many2many('hr.employee', 'purchase_employee_rel', 'purchase_id', 'employee_id', string="Contributor"),
        'department_id': fields.many2one('hr.department', 'Department', required=True),
        'dateout': fields.datetime('Date'),
        'datein': fields.date('Delivery date'),
        'purchase_line': fields.one2many('internal.order.line', 'internal_id', string="ordinary line"),
        'purchase_line1': fields.one2many('internal.order.line', 'internal_id1', string="technical line"),
        'amount_ht': fields.function(_amount_all_wrapper, string='Total',
            store={
                'apgebat.ach': (lambda self, cr, uid, ids, c={}: ids, ['purchase_line','purchase_line1'], 10),
                'internal.order.line': (_get_order, ['price_unit', 'product_qty'], 10),
            }, multi='sums', help="The amount without tax.", track_visibility='always'),
        'state': fields.selection([('draft','Draft'), ('sent', 'Sent'), ('cancel', 'Canceled')], 'States'),
        'statet': fields.selection([('draft', 'Draft'), ('sent', 'Sent'), ('approuved', 'Approuved'), ('reject', 'Rejected')], 'States'),
    }

    _defaults = {
        'dateout': time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()),
        'master': lambda self, cr, uid, ctx: uid,
        'state': 'draft',
        'accept': 'reject',
        'statet': 'draft'
       # 'employee_ids': lambda self, cr, uid, ctx: self.pool.get('res.users').browse(cr, uid, uid, ctx).partner_id.id,


    }

    def rejected(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'statet': 'reject'})

    def valided(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'statet': 'sent', 'state': 'sent'})

    def cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel', 'statet': 'draft'})

    def draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'})


    def _prepare_advance_quotation_vals(self, cr, uid, ids, lineids, context=None):
        if context is None:
            context = {}
        request = self.browse(cr, uid, ids, context)
        for infos in self.pool.get('internal.order.line').browse(cr, uid, lineids, context):
            frseur=infos.supplier
            #raise osv.except_osv(_('Error!'), _(int(infos.supplier)))
        result = []
        inv_values = {
            
            'partner_id': int(frseur),
            'date_order': request.dateout,
            'location_id': 12,
            'pricelist_id': 2,
            
        }
        result.append(inv_values)
        return result

    def _prepare_advance_quotation_line_vals(self, cr, uid, ids, lineids, context=None):
      
        result = []
        for infos in self.pool.get('internal.order.line').browse(cr, uid, lineids, context):

            line_values = {
                'order_id': ids,
                'product_id': int(infos.product_id),
                'name': infos.name,
                'date_planned': infos.date_planned,
                'product_qty': infos.product_qty,
                'price_unit': infos.price_unit,
                
            }
            result.append(line_values)
        return result


    def create_quotation(self, cr, uid, ids, lineids, context=None):
        """ create invoices for the active sales orders """
        lin_ids=[]
        for inv_values in self._prepare_advance_quotation_vals(cr, uid, ids, lineids, context=context):
            inv_id=self._create_quotation(cr, uid, ids, inv_values, context=context)
            for line_values in self._prepare_advance_quotation_line_vals(cr, uid, inv_id, lineids, context=context):
                lin_ids.append(self._create_quotation_line(cr, uid, ids, line_values, context=context))
        
        return None

    def _create_quotation(self, cr, uid, ids, inv_values, context=None):
        pro_obj = self.pool.get('purchase.order')
        pro_id = pro_obj.create(cr, uid, inv_values, context=context)
        # add the invoice to the sales order's invoices
        return pro_id
    def _create_quotation_line(self, cr, uid, ids, line_values, context=None):
        pur_obj = self.pool.get('purchase.order.line')
        #_logger.error("total : %r", pur_obj.create(cr, uid, line_values, context=context))
        pur_id=pur_obj.create(cr, uid, line_values, context=context)
        # add the invoice to the sales order's invoices
        return pur_id

    def accepted_request(self, cr, uid, ids, context=None):
        line_ids=[]
        achat=self.browse(cr, uid, ids, context=context)
        for line in achat.purchase_line:
            if line.valid == True and line.etat !='oui':
                line_ids.append(line.id)
        if line_ids:
            group_id=self.pool.get('internal.order.line').read_group(cr,uid,[('id','in',line_ids)], ['supplier'], ['supplier'])

            for suppliers in group_id:
                #raise osv.except_osv(_('Error!'), _(suppliers['__domain'][0]))
                lineids=self.pool.get('internal.order.line').search(cr, uid,[suppliers['__domain'][0],('id', 'in', line_ids)])
                self.create_quotation(cr, uid, ids, lineids, context=context)
                self.pool.get('internal.order.line').write(cr, uid, lineids, {'etat': 'oui'})
                group_id=self.pool.get('internal.order.line').read_group(cr,uid,[('id','in',line_ids)], ['supplier'], ['supplier'])
            ligne=[]
            for line in achat.purchase_line:
                if line.valid == False and line.etat !='oui':
                    ligne.append(line.id)
            if len(ligne)>0:
                self.write(cr, uid, ids, {'accept': 'reject'})
            else:
                self.write(cr, uid, ids, {'accept': 'end', 'statet': 'approuved'})

    
    #def line_update(self, cr, uid, ids, types, context=None):
     #   self.pool.get('internal.order.line').line_updater(cr, uid, ids, types, context=context)

    def call_onchange_project(self, cr, uid, ids, project_id, context=None):
        self.pool.get('internal.order.line').onchange_project(cr, uid, ids, 'ok', project_id, context=context)

        

   # _sql_constraints = [
   #     ('uniq_mail', 'unique(student_email)', "A mail already exists with this name in Performances Académie. student's email must be unique!"),
   # ]


class internal_order_line(osv.osv):
    _name = 'internal.order.line'

    _columns = {
        'lot_id':fields.many2one('ap.gao.attr', 'Lot Award'),
        'lignes_id':fields.many2one('ap.gao.estim', 'Line rates'),
        'product_id':fields.many2one('product.template', 'Article'),
        'name': fields.char('Description', required=True),
        'date_planned': fields.date('predicted date', required=True),
        'product_qty': fields.float('Quantity', required=True),
        'price_unit': fields.float('Unit price', required=True),
        'valid': fields.boolean('Approuved'),
        'etat': fields.selection([('non', 'Not Approuved'), ('oui', 'Approuved')], 'State'),
        'supplier': fields.many2one('res.partner', 'Supplier', domain=[('supplier', '=', True)]),
        'price_subtotal': fields.float('Subtotal'),
        'internal_id': fields.integer('internal'),
        'internal_id1': fields.integer('internal'),
        #'updater': fields.selection([('ordinary','Ordinary purchases'),('technical','Technical purchasing')],'Type', required=True),

    }

    _defaults = {
        'product_qty': 1.0,
        'etat': 'non',
    }


    def onchange_product(self, cr, uid, ids, product_id, context=None):
        produit= self.pool.get('product.template').browse(cr, uid, product_id, context=None)
        pri_ach = produit.standard_price
        desc = produit.name
        date = time.strftime('%Y-%m-%d',time.localtime())
        values = {'name': desc, 'date_planned': date, 'price_unit': pri_ach}
        return {'value': values}

    def cal_subtotal(self, cr, uid, ids, qte, price, context=None):
        montant= qte*price
        values = {'price_subtotal': montant}
        return {'value': values}


    def call_accept(self, cr, uid, ids, value, context=None):
        line = self.browse(cr,uid, ids)
        idsi = self.search(cr, uid,[('internal_id', '=', line.internal_id)])
        valide=False
        for lines in self.browse(cr, uid, idsi, context=None):
            if lines.id!=ids and lines.valid and lines.etat!='oui':
                valide=True
        if valide and value:
            valide=True
        if value:
            valide=True
        if valide:
            self.pool.get('apgebat.ach').write(cr, uid, line.internal_id,{'accept': 'valid'})
        else:
            self.pool.get('apgebat.ach').write(cr, uid, line.internal_id,{'accept': 'reject'})

    #def line_updater(self, cr, uid, ids, types, context=None):
     #   values = {'updater': types}
     #   return {'value': values}

    def onchange_project(self,cr,uid,ids, lot_id, project_id=None, context=None):
        #raise osv.except_osv(_('Error!'), _(context['project_id']))
        if lot_id!='ok' and lot_id:
            self.onchange_lot(cr,uid,ids, lot_id,context=context)
        else:
            if lot_id=='ok' and project_id==False:
                return {}
            else:
                if project_id:
                    lotattr_obj = self.pool.get('ap.gao.attr')
                    tender_id = self.pool.get('ap.gao').search(cr,uid, [('project_id','=',project_id)])
                    lotattr_ids = lotattr_obj.search(cr,uid, [('tender_id','=',tender_id)])
                    return {'domain':{'lot_id':[('id','in',lotattr_ids)]}}
                else:
                    lotattr_obj = self.pool.get('ap.gao.attr')
                    tender_id = self.pool.get('ap.gao').search(cr,uid, [('project_id','=',context['project_id'])])
                    lotattr_ids = lotattr_obj.search(cr,uid, [('tender_id','=',tender_id)])
                    return {'domain':{'lot_id':[('id','in',lotattr_ids)]}}

    def onchange_lot(self,cr,uid,ids, lot_id,context=None):
        estim_obj = self.pool.get('ap.gao.estim')
        estim_ids = estim_obj.search(cr,uid, [('lot_id','=',lot_id), ('type','=','child')])
        if estim_ids:
            return {'domain':{'lignes_id':[('id','in',estim_ids)]}}

    def onchange_ligne(self,cr,uid,ids, ligne_id,context=None):
        #if ligne_id:
            #raise osv.except_osv(_('Error!'), _())
        mat_obj = self.pool.get('ap.gao.mat')
        mat_ids = mat_obj.search(cr,uid, [('estim_id','=',ligne_id)])
        prod_group=self.pool.get('ap.gao.mat').read_group(cr,uid,[('id','in',mat_ids)], ['product_id'], ['product_id'])
        pro=[]
        if prod_group:
            for product in prod_group:
                pro.append(product['product_id'][0])
        return {'domain':{'product_id':[('id','in',pro)]}}