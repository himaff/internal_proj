# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class ap_gao(osv.osv):
    _name = 'ap.gao'
    _order = 'name asc'

    _columns = {
        'code': fields.char('N° tender'),
        'name': fields.char('Tenden title', required=True),
        'type': fields.selection([('Direct','Direct tender'),('restricted','Restricted tender')],'Type', required=True),
        'date_depot': fields.datetime('Deposit date'),
        'date_ouvert': fields.datetime('Opening date'),
        'copy': fields.integer('Copy number'),
        'owner': fields.many2one('res.partner', 'Building owner', required=True, domain="[('customer','=',True)]"),
        'owner_address': fields.char('Instead of deposit'),
        'owner_contact': fields.char('Contact'),
        'masterwork': fields.many2one('res.partner', 'Master work', required=True, domain="[('customer','=',True)]"),
        'master_address': fields.char('Address'),
        'master_contact': fields.char('Contact'),
        'date_meeting': fields.datetime('Date of preparatory meeting'),
        'lot_id': fields.one2many('ap.gao.attr', 'tender_id', string='Award prizes'),
        'estimation_id': fields.one2many('ap.gao.estim', 'tender_id', string='Estimates'),
        'doc_rec': fields.one2many('ir.attachment', 'tenderrec_id', 'Documents received'),
        'doc_send': fields.one2many('ir.attachment', 'tendersen_id', 'Documents sended'),
        'project_id': fields.many2one('project.project', 'project', readonly=True, copy=False,),
        'date_begin': fields.date('Date of start of work'),
        'date_end': fields.date('Date of Completion'),
        'market': fields.float('Market value'),
        'total_ds': fields.float(''),
        'delai': fields.float('Completion time'),
        'note': fields.text('Description'),
        'amount_ht': fields.float('Untaxed'),
        'amount_tva': fields.float('Tax'),
        'amount_ttc': fields.float('Total'),
        'state' : fields.selection([('draft', 'Draft'),('cons', 'Consultation'), ('plan', 'Planning'),('submit', 'Submission'), ('accept', 'Accepted'), ('accepted', 'Created project'), ('reject', 'Rejected'),('cancel', 'Canceled')]),

        
    }

    _defaults = {
        'state' : 'draft',
        'status' : 'encours'
    }

   # _sql_constraints = [
   #     ('uniq_name', 'unique(name)', "A student already exists with this name in Performances Académie. student's name must be unique!"),
   # ]
  

    def poster(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cons'})

    def accord(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'plan'})

    def submited(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'submit'})

    def accepted(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'accept'})

    def rejected(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'reject'})

    def cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'})

    def canceled(self, cr, uid, ids, context=None):
        self.pool.get('project.project').unlink(cr, uid, context['open_project'])
        self.write(cr, uid, ids, {'state': 'cancel'})

    def draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'})

    def _prepare_advance_tender_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        tender = self.browse(cr, uid, ids[0], context)

        result = []
        inv_values = {
            'name': tender.name,
            'use_tasks': True,
            'user_id': uid,
            'partner_id': tender.owner.id,
            'date_start': tender.date_begin,
            'date': tender.date_end,
            
        }
        result.append(inv_values)
        return result


    def create_project(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        inv_ids = []
        for inv_values in self._prepare_advance_tender_vals(cr, uid, ids, context=context):
            inv_ids.append(self._create_project(cr, uid, ids, inv_values, context=context))
        self.write(cr, uid, ids, {'state': 'accepted'})
        if context.get('open_project', False):
            return self.open_project(cr, uid, ids, inv_ids[0], context=context)
        #return {'type': 'ir.actions.act_window_close'}
        return None

    def _create_project(self, cr, uid, ids, inv_values, context=None):
        pro_obj = self.pool.get('project.project')
        pro_id = pro_obj.create(cr, uid, inv_values, context=context)
        # add the invoice to the sales order's invoices
        self.write(cr, uid, ids, {'project_id': pro_id}, context=context)
        return pro_id

    def affiche(self, cr, uid, ids, context=None):
        return self.open_project(cr, uid, ids, context['open_project'], context=context)

    def open_project(self, cr, uid, ids, project_id, context=None):
        """ open a view on one of the given invoice_ids """
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'project', 'edit_project')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'project', 'view_project')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Tender project'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'project.project',
            'res_id': project_id,
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'type': 'ir.actions.act_window',
        }




class ap_gao_attr(osv.osv):
    _name = 'ap.gao.attr'
    _order = 'name asc'

    _columns = {
        'code': fields.char('Batch number'),
        'name': fields.char('Titled lot of tender', required=True),
        'caution': fields.float('interim bail', required=True),
        'credit_line': fields.float('credit line'),
        'tender_id': fields.integer('tender_id'),
        
    }









class ap_gao_estim(osv.osv):
    _name = 'ap.gao.estim'
    _order = 'price_line asc'
    _rec_name= 'price_line'

    _columns = {
        'type': fields.selection([('vue','Vue'),('child','Details')],'Type', required=True),
        'sequences': fields.integer('Item N°'),
        'parent_id': fields.many2one('ap.gao.estim', 'Parent', ondelete="cascade", domain="[('type','=','vue')]"),
        'code': fields.char('Batch number', required=True),
        'price_line': fields.char('Issue price lines', required=True),
        'prevu': fields.float('Expected amount'),
        'pu_ds': fields.float('Unit price DS'),
        'bpu': fields.float('Unit Price BPU'),
        'ecart': fields.float('Gap'),
        'ratio': fields.float('Ratio DS/DQE'),
        'tender_id': fields.integer('tender_id'),
        'lot_id': fields.many2one('ap.gao.attr', 'Lot of tender', required=True),
        'priceline_id': fields.many2one('ap.gao.prix', 'Price line'),
        'unite_id': fields.many2one('product.uom', 'Product UoM'),
        'qte_ds': fields.integer('Amount DS'),
        'qte_bpu': fields.integer('Amount DQE'),
        

    }

    def valeur(self, cr, uid, ids, puds, pubpu, prevu, context=None):
        ds=0
        dqe=0
        values={}
        if prevu and puds:
            ds=puds*prevu
            values={'qte_ds':ds,}
        if prevu and pubpu:
            dqe=pubpu*prevu
            values={'qte_bpu':dqe,}
        if ds and dqe:
            ecart=dqe-ds
            ratio=(ds/dqe)*100
            values={'qte_ds':ds, 'qte_bpu':dqe, 'ecart':ecart, 'ratio':ratio}
        return {'value': values}

    def coucou(self, cr, uid, ids, context=None):
        raise osv.except_osv(_('Error!'), _('coucou.'))





class ap_gao_prix(osv.osv):
    _name = 'ap.gao.prix'
    _order = 'name asc'

    _columns = {
        'name': fields.char('wording of the price line', required=True),
        'mat_ds_val': fields.float('DS value of materials'),
        'mat_bpu_val': fields.float('BPU value of materials'),
        'coef': fields.float('Coefficient of sale'),
        'estim_id': fields.integer('estim'),



#choix   Type
#Many 2 one / ligne de prix  affiliation
#Many 2 many / ligne de materiaux, MMO   ligne de materiaux, MMO




    }








class ap_gao_mat(osv.osv):
    _name = 'ap.gao.mat'
    _order = 'name asc'

    _columns = {
        'quantity': fields.float('Quantity'),
        'pu_composant': fields.float('price component'),
        'unite_id': fields.many2one('product.uom', 'Product UoM', required=True),
        'product_id': fields.many2one('product.template', 'equipments / materials', required=True),
        

    }






class ap_gao_doc_received(osv.osv):
    _inherit='ir.attachment'

    _columns = {

        'status': fields.integer('Status'),
        'tendersen_id': fields.integer('tender_id'),
        'tenderrec_id': fields.integer('tender_id'),
        'date': fields.date('Date'),

    }