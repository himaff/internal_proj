# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import datetime
import calendar
import logging
_logger = logging.getLogger(__name__)

class apgao_ligne_att(osv.osv):
	_name='apgao.line.att'

	_columns = {
        'code': fields.char('N°'),
        'lines': fields.char('Designation'),
#QDE du marché
        'unit_id': fields.many2one('product.uom', 'U'),
        'quantity': fields.float('Qty'),
        'unit_price': fields.float('UP'),
        'total_dqe': fields.float('Total'),
#qté de puis la creation
        'qte_m1': fields.float('M-1'),
        'qte_m': fields.float('M'),
        'qte_cumul': fields.float('Accrued'),
#montant depuis la creation
        'montant_m1': fields.float('M-1'),
        'montant_m': fields.float('M'),
        'montant_cumul': fields.float('Accrued'),
#le taux 
        'taux': fields.float('Rate'),

        'att_id': fields.many2one('apgebat.attachment', 'attachement'),
        'type': fields.selection([('vue','Vue'), ('child', 'Details')]),
        'sequence': fields.integer('seq'),
    }


class apgebat_attachment(osv.osv):
    _name='apgebat.attachment'

    _columns = {

        'name': fields.char('Untitled attachement'),
        'date_planned': fields.date('predicted date'),
        'state': fields.selection([('draft', 'Draft'),('end', 'Finish')], 'State'),
        'project_id': fields.many2one('project.project', 'project'),
        'line_attach': fields.one2many('apgao.line.att', 'att_id'),
        'att_pos': fields.integer('Position')
    }

    _defaults = {
        'date_planned': time.strftime('%Y-%m-%d',time.localtime()),
        'state': 'draft',
    }


    def importer(self, cr, uid, ids, context=None):
    	att=self.browse(cr, uid, ids, context=context)
    	attids = self.pool.get('apgao.line.att').search(cr, uid,[('att_id', '=', ids[0])])
    	self.pool.get('apgao.line.att').unlink(cr, uid, attids)
        atts_prec= self.search(cr, uid,[('project_id', '=', att.project_id.id),('state','=', 'end')])
        #recherche des bons de commande concernant le projet
        bc_ids=self.pool.get('purchase.order').search(cr, uid,[('project_id', '=', att.project_id.id),('state','in', ['approved','done'])])
        ligne_val={}
        ligne_qte={}
        #pour chaque bon de commande approuved on recupere la facture concerné et on verifie quel est validé
        for bc in self.pool.get('purchase.order').browse(cr, uid, bc_ids, context=context):
            fact_id=self.pool.get('account.invoice').search(cr, uid,[('origin', '=', bc.name),('state','in', ['open','paid'])])
            if fact_id:
                #si la facture est validé on recupere les lignes du bon de commande
                for bc_line in self.pool.get('purchase.order.line').search(cr, uid,[('order_id', '=', bc.id)]):
                    line=self.pool.get('purchase.order.line').browse(cr, uid, bc_line, context=context)
                    if line.lot_ligne in ligne_val:
                        ligne_val[line.lot_ligne]+=line.price_subtotal
                        ligne_qte[line.lot_ligne]+=line.product_qty
                    else:
                        ligne_val[line.lot_ligne]=line.price_subtotal
                        ligne_qte[line.lot_ligne]=line.product_qty
        #dj
        if atts_prec:
            #corriger toute cette zone selon le calcul du bas en else
            cr.execute('''SELECT id, MAX(att_pos) FROM apgebat_attachment WHERE id= %s''', (atts_prec,))
            prec_att_id = cr.fetchone()[0]
            #prec_att=self.browse(cr, uid, prec_att_id, context=context)
            for estim in att.project_id.estimation_id:
                if estim.price_line in ligne_val:
                    mont_cumul=ligne_val[estim.price_line]
                    qte_cumul=ligne_qte[estim.price_line]
                else:
                    mont_cumul=0.0
                    qte_cumul=0.0
                prec_att_line_id=self.pool.get('apgao.line.att').search(cr, uid,[('att_id', '=', prec_att_id), ('lines', '=', estim.price_line)])
                if prec_att_line_id:
                    att_line_prec=self.browse(cr, uid, prec_att_line_id, context=context)
                    qm1 = att_line_prec.qte_cumul
                    m1 = att_line_prec.montant_cumul
                else:
                    qm1 = 0.0
                    m1 = 0.0

                self.pool.get('apgao.line.att').create(cr, uid, { 'lines': estim.price_line, 'type': estim.type, 'unit_id': int(estim.unite_id), 'quantity': estim.quantity, 'unit_price': estim.bpu, 'total_dqe': estim.total_bpu, 'sequence': estim.sequences, 'qte_m1': qm1, 'qte_cumul': qte_cumul, 'montant_m1': m1, 'montant_cumul': mont_cumul , 'att_id' : ids[0]})

        else:
            #gerer les calculs de la periode M
            for estim in att.project_id.estimation_id:
                if estim.price_line in ligne_val:
                    mont_cumul=ligne_val[estim.price_line]
                    qte_cumul=0.0
                else:
                    mont_cumul=0.0
                    qte_cumul=0.0
               
                cr.execute('''INSERT INTO apgao_line_att (lines, type, quantity, sequence, unit_price, total_dqe, qte_cumul, montant_cumul, att_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''', (estim.price_line, estim.type, estim.quantity, estim.sequences, estim.bpu, estim.total_bpu, qte_cumul, mont_cumul, ids[0]))
    	        cr.execute('''SELECT id FROM apgao_line_att ORDER BY id DESC''')
                #recupere le dernier id inseré
                id_new = cr.fetchone()[0] 
                if estim.unite_id.id:
                    cr.execute('''UPDATE apgao_line_att SET unit_id = %s WHERE id=%s''', (estim.unite_id.id, id_new))
        return True



class internal_purchase_request_wizard(osv.osv_memory):
    _name='internal.purchase.request.wizard'
    _columns = {

        'project_id': fields.many2one('project.project', 'project', domain="[('tender_id', '!=', False)]", required=True),
        'selector': fields.selection([('project', 'Purchase by project'),('line', 'Purchase by price line'),('mat', 'Purchase by materials')], 'Purchase request method', required=True)
    }

    def selector_choice(self, cr, uid, ids, context=None):

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        data = self.read(cr, uid, ids, context=context)[0]

       
        if data['selector']=='line':
            project_id=data['project_id'][0]
            ir_model_data = self.pool.get('ir.model.data')
            form_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_gao_ext', 'purchase_line_form')
            form_id = form_res and form_res[1] or False
            
            return {
                'name': _('Purchases by lines'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'project.project',
                'res_id': project_id,
                'view_id': False,
                'views': [(form_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
            }



        if data['selector']=='project':

            proj=self.pool.get('project.project').browse(cr, uid, data['project_id'][0])
            prod={}
            for line in proj.estimation_id:
                for mat in line.mat_line:
                    if mat.product_id in prod:
                        prod[mat.product_id]+=mat.quantity*line.quantity
                    else:
                        prod[mat.product_id]=mat.quantity*line.quantity
            #raise osv.except_osv(_('Error'), _(prod))
            ach_id = self.pool.get('apgebat.ach').create(cr, uid, {'project_id': proj.id, 'dateout':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()), 'type': 'technical', 'master': uid, 'department_id': 1})
            total=0.0
            for product in prod:
                #
                produit=self.pool.get('product.template').browse(cr, uid, product.id)
                self.pool.get('internal.order.line').create(cr, uid, {'product_id': product.id, 'name': produit.name, 'date_planned': time.strftime('%Y-%m-%d',time.localtime()), 'product_qty': prod[product], 'price_unit': produit.standard_price, 'price_subtotal': prod[product]*produit.standard_price, 'internal_id1': ach_id})
                total+=prod[product]*produit.standard_price
            cr.execute('''UPDATE apgebat_ach SET amount_ht=%s WHERE id= %s''', (total, ach_id))
            
            ir_model_data = self.pool.get('ir.model.data')
            form_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_ach', 'apgebat_ach_form')
            form_id = form_res and form_res[1] or False
            #raise osv.except_osv(_('Error'), _(ach_id))
            return {
                'name': _('Purchases project'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'apgebat.ach',
                'res_id': ach_id,
                'view_id': False,
                'views': [(form_id, 'form')],
                'type': 'ir.actions.act_window',
            }




        #a traiter dans quelque instant
        if data['selector']=='mat':
            project_id=data['project_id'][0]
            estim_id = self.pool.get('ap.gao.estim').search(cr, uid, [('project_id', '=', project_id), ('type', '=', 'child')])
            #raise osv.except_osv(_('Error'), _(estim_id))
            ir_model_data = self.pool.get('ir.model.data')
            form_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_gao_ext', 'purchase_mat_form')
            form_id = form_res and form_res[1] or False
            
            return {
                'name': _('Purchases by materials'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'ap.gao.estim',
                'res_id': estim_id[0],
                'view_id': False,
                'views': [(form_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': { 'estim': estim_id, 'nbr': 0, 'project_id': project_id}
            }

       

class ap_gao_estim(osv.osv):
    _inherit = 'ap.gao.estim'
    _columns = {

        'qte_request': fields.float('Desired qty', required=True),
    }

    _defaults = {

        'qte_request': 0.0,
    }

    def test(self, cr, uid, ids, context=None):
        nbr=context['nbr']
        nbr+=1
        estim_id=context['estim']
        if nbr+1 <= len(estim_id):
            ir_model_data = self.pool.get('ir.model.data')
            form_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_gao_ext', 'purchase_mat_form')
            form_id = form_res and form_res[1] or False
            
            return {
                'name': _('Purchases by materials'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'ap.gao.estim',
                'res_id': estim_id[nbr],
                'view_id': False,
                'views': [(form_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': { 'estim': estim_id, 'nbr': nbr}
            }
        else:
            if nbr+1 >= len(estim_id):
                proj=self.pool.get('project.project').browse(cr, uid, context['project_id'])                     
                #raise osv.except_osv(_('Error'), _(prod))
                ach_id = self.pool.get('apgebat.ach').create(cr, uid, {'project_id': proj.id, 'dateout':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()), 'type': 'technical', 'master': uid, 'department_id': 1})
                total=0.0
                for line in proj.estimation_id:
                    for mat in line.mat_line:
                    #
                        produit=self.pool.get('product.template').browse(cr, uid, mat.product_id.id)
                        if mat.qte_request:
                            self.pool.get('internal.order.line').create(cr, uid, {'lot_id': line.lot_id.id, 'lignes_id': line.id,'product_id': produit.id, 'name': produit.name, 'date_planned': mat.date_planed, 'product_qty': mat.qte_request, 'price_unit': produit.standard_price, 'price_subtotal': mat.qte_request*produit.standard_price, 'internal_id1': ach_id})
                            total+=mat.qte_request*produit.standard_price
                cr.execute('''UPDATE apgebat_ach SET amount_ht=%s WHERE id= %s''', (total, ach_id))
                
                ir_model_data = self.pool.get('ir.model.data')
                form_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_ach', 'apgebat_ach_form')
                form_id = form_res and form_res[1] or False
                #raise osv.except_osv(_('Error'), _(ach_id))
                return {
                    'name': _('Purchases Materials'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'apgebat.ach',
                    'res_id': ach_id,
                    'view_id': False,
                    'views': [(form_id, 'form')],
                    'type': 'ir.actions.act_window',
                }



class ap_gao_inherit_project(osv.osv):
    _inherit='project.project'

    _columns = {

        'att_list': fields.one2many('apgebat.attachment', 'project_id', 'Attachements'),
        
    }
    
    def selector_choice(self, cr, uid, ids, context=None):

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        data = self.read(cr, uid, ids, context=context)[0]

        #a traiter dans quelque instant problem avec les lignes de prix et lot d'attribution et les contributeurs aussi le departement_id
        prod={}
        for estim in self.pool.get('ap.gao.estim').browse(cr, uid, data['estimation_id']):
            for mat in estim.mat_line:
                if mat.product_id in prod:
                    prod[mat.product_id]+=mat.quantity*estim.qte_request
                else:
                    prod[mat.product_id]=mat.quantity*estim.qte_request
        #raise osv.except_osv(_('Error'), _(data['id']))
        ach_id = self.pool.get('apgebat.ach').create(cr, uid, {'project_id': data['id'], 'dateout':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()), 'type': 'technical', 'master': uid, 'department_id': 1})
        total=0.0
        for product in prod:
            #
            produit=self.pool.get('product.template').browse(cr, uid, product.id)
            if prod[product]:
                self.pool.get('internal.order.line').create(cr, uid, {'product_id': product.id, 'name': produit.name, 'date_planned': time.strftime('%Y-%m-%d',time.localtime()), 'product_qty': prod[product], 'price_unit': produit.standard_price, 'price_subtotal': prod[product]*produit.standard_price, 'internal_id1': ach_id})
                total+=prod[product]*produit.standard_price
        cr.execute('''UPDATE apgebat_ach SET amount_ht=%s WHERE id= %s''', (total, ach_id))
        #raise osv.except_osv(_('Error!'), _(estim))
        project_id=data['id']
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_ach', 'apgebat_ach_form')
        form_id = form_res and form_res[1] or False
        
        return {
            'name': _('Purchases project'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'apgebat.ach',
            'res_id': ach_id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
        }

class ap_gao_mat(osv.osv):
    _inherit='ap.gao.mat'
    _columns = {

        'qte_request': fields.float('Desired qty', required=True),
        'date_planed': fields.date('predicted date', required=True),
    }

    _defaults = {

        'qte_request': 0.0,
        'date_planed': time.strftime('%Y-%m-%d',time.localtime()),
    }