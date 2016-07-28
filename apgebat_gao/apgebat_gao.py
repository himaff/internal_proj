# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import datetime
import calendar

class ap_gao(osv.osv):
    _name = 'ap.gao'
    _order = 'name asc'

    def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
        """ Wrapper because of direct method passing as parameter for function fields """
        #raise osv.except_osv(_('Error!'), _(context))
        return self._amount_all(cr, uid, ids, field_name, arg, context=context)

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_ht_ds': 0.0,
                'amount_ht_dqe': 0.0,
            }
            val = val1 = val2 = 0.0
            for estim in order.estimation_id:
                res[estim.id] = {
                    'pu_ds': 0.0,
                    'ecart': 0.0,
                    'ratio': 0.0,
                    'coef': 0.0,
                    'total_ds': 0.0,
                    'total_bpu': 0.0,
                    'amount_total': 0.0,
                }
                val2 += estim.total_bpu
                val += estim.total_ds
                for line in estim.mat_line:
                    val1 += line.mat_total
                    
                res[estim.id]['pu_ds'] = val1
                res[estim.id]['total_ds'] = estim.quantity * val1
                res[estim.id]['total_bpu'] = estim.quantity * estim.bpu
                res[estim.id]['ecart'] = res[estim.id]['total_bpu'] - res[estim.id]['total_ds']
                if res[estim.id]['total_bpu'] and res[estim.id]['total_ds']:
                    res[estim.id]['ratio'] = (res[estim.id]['total_ds'] / res[estim.id]['total_bpu']) * 100
                    res[estim.id]['coef'] = ((res[estim.id]['total_bpu'] - res[estim.id]['total_ds']) / res[estim.id]['total_ds']) * 100
                else:
                    res[estim.id]['ratio'] = 0
                    res[estim.id]['coef'] = 0
                res[estim.id]['amount_total'] = res[estim.id]['total_bpu']
             
            res[order.id]['amount_ht_dqe'] = val2
            res[order.id]['amount_ht_ds'] = val
        raise osv.except_osv(_('Error!'), _(res))
        return res




    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('ap.gao.estim').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()


    _columns = {
        'code': fields.char('N° tender'),
        'name': fields.char('Tenden title', required=True),
        'type': fields.selection([('Direct','Direct tender'),('restricted','Restricted tender')],'Type', required=True),
        'date_depot': fields.datetime('Deposit date'),
        'date_ouvert': fields.datetime('Opening date'),
        'copy': fields.integer('Copy number'),
        'owner': fields.many2one('res.partner', 'Building owner', required=True, domain="[('customer','=',True)]"),
        'owner_address': fields.char('Instead of deposit'),
        'owner_contact': fields.related('owner','phone',readonly=True, type='char', relation='res.partner', string='Building owner phone'),
        'masterwork': fields.many2one('res.partner', 'Master work', required=True, domain="[('customer','=',True)]"),
        'master_address': fields.related('masterwork','city',readonly=True, type='char', relation='res.partner', string='Masterwork address'),
        'master_contact': fields.related('masterwork','phone',readonly=True, type='char', relation='res.partner', string='Masterwork phone'),
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
        'delai': fields.char('Completion time', readonly=True),
        'note': fields.text('Description'),
        'amount_ht_ds': fields.function(_amount_all_wrapper, string='Amount total DS',
            store={
                'ap.gao': (lambda self, cr, uid, ids, c={}: ids, ['estimation_id'], 10),
                'ap.gao.estim': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_ht_dqe': fields.function(_amount_all_wrapper, string='Amount total DQE',
            store={
                'ap.gao': (lambda self, cr, uid, ids, c={}: ids, ['estimation_id'], 10),
                'ap.gao.estim': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount with tax.", track_visibility='always'),
        'state' : fields.selection([('draft', 'Draft'),('cons', 'Consultation'), ('plan', 'Planning'),('submit', 'Submission'), ('accept', 'Accepted'), ('accepted', 'Created project'), ('reject', 'Rejected'),('cancel', 'Canceled')]),

        
    }

    _defaults = {
        'state' : 'draft',
        'status' : 'encours',
        'delai': '0 month and 0 day'
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



    def button_dummy(self, cr, uid, ids, context=None):

        return True

    def delayer(self, cr, uid, ids, begin, end, context=None):
        daily = ""
        if begin:
            dateBegin = datetime.datetime.strptime(begin,'%Y-%m-%d')
        else:
            dateBegin = datetime.datetime.strptime(time.strftime('%Y-%m-%d',time.localtime()), "%Y-%m-%d")
        if end:
            dateEnd = datetime.datetime.strptime(end,'%Y-%m-%d')
        else:
            dateEnd = datetime.datetime.strptime(time.strftime('%Y-%m-%d',time.localtime()), "%Y-%m-%d")

        day_ecart= dateEnd - dateBegin
        yearBegin = dateBegin.year
        monthBegin = dateBegin.month
        dayBegin = dateBegin.day 
        dayOfMonth = calendar.mdays
        delaiDay = day_ecart.days
        month_val = 0
        day_val = 0
        i = 0

        while delaiDay > 0:
            if calendar.isleap(yearBegin + i):
                dayOfMonth[2] = 29
            else:
                dayOfMonth[2] = 28

            for month in range(12):
                if month+1 >= monthBegin:
                    if delaiDay >= dayOfMonth[month]:
                        delaiDay -= dayOfMonth[month]
                        month_val += 1
                    else:
                        day_val += delaiDay
                        delaiDay = 0


            i += 1
            monthBegin = 1
        if month_val>1:
            if day_val>1:
                daily = "%s months and %s days" % (month_val, day_val)
            else:
                daily = "%s months and %s day" % (month_val, day_val)
        else:
            if day_val>1:
                daily = "%s month and %s days" % (month_val, day_val)
            else:
                daily = "%s month and %s day" % (month_val, day_val)
        values = {'delai': daily,}
        if ids:
            cr.execute('''UPDATE ap_gao SET delai = %s WHERE id=%s''', (daily, ids[0]))
        return {'value': values}

    



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

    def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
        """ Wrapper because of direct method passing as parameter for function fields """
        #raise osv.except_osv(_('Error!'), _(field_name))
        return self._amount_all(cr, uid, ids, field_name, arg, context=context)

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        #raise osv.except_osv(_('Error!'), _(field_name))
        res = {}
        estim=self.browse(cr, uid, ids, context=None)
        for order in self.pool.get('ap.gao').browse(cr, uid, estim.tender_id, context=None):
            res[order.id] = {
                'amount_ht_ds': 0.0,
                'amount_ht_dqe': 0.0,
            }
            val = val2 = 0.0
            for estim in order.estimation_id:
                res[estim.id] = {
                    'pu_ds': 0.0,
                    'ecart': 0.0,
                    'ratio': 0.0,
                    'coef': 0.0,
                    'total_ds': 0.0,
                    'total_bpu': 0.0,
                    'amount_total': 0.0,
                }
                val2 += estim.total_bpu
                val += estim.total_ds
                val1 = 0.0
                for line in estim.mat_line:
                    val1 += line.mat_total
                    
                res[estim.id]['pu_ds'] = val1
                res[estim.id]['total_ds'] = estim.quantity * val1
                res[estim.id]['total_bpu'] = estim.quantity * estim.bpu
                res[estim.id]['ecart'] = res[estim.id]['total_bpu'] - res[estim.id]['total_ds']
                if res[estim.id]['total_bpu'] and res[estim.id]['total_ds']:
                    res[estim.id]['ratio'] = (res[estim.id]['total_ds'] / res[estim.id]['total_bpu']) * 100
                    res[estim.id]['coef'] = ((res[estim.id]['total_bpu'] - res[estim.id]['total_ds']) / res[estim.id]['total_ds']) * 100
                else:
                    res[estim.id]['ratio'] = 0
                    res[estim.id]['coef'] = 0
                res[estim.id]['amount_total'] = res[estim.id]['total_bpu']
             
            res[order.id]['amount_ht_dqe'] = val2
            res[order.id]['amount_ht_ds'] = val
        raise osv.except_osv(_('Error!'), _(res))
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('ap.gao.mat').browse(cr, uid, ids, context=context):
            raise osv.except_osv(_('Error!'), _(line))
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'type': fields.selection([('vue','Vue'),('child','Details')],'Type', required=True),
        'sequences': fields.integer('Item N°', required=True),
        'parent_id': fields.many2one('ap.gao.estim', 'Parent', ondelete="cascade", domain="[('type','=','vue')]"),
        'code': fields.char('Batch number'),
        'lot_id': fields.many2one('ap.gao.attr', 'Lot of tender', required=True),
        'price_line': fields.char('Name', required=True),
        'pu_ds': fields.function(_amount_all_wrapper, string='Unit price DS',
            store={
                'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
                'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'bpu': fields.float('Unit Price BPU'),
        'ecart': fields.function(_amount_all_wrapper, string='Gap',
            store={
                'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
                'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'ratio': fields.function(_amount_all_wrapper, string='Ratio DS/DQE (%)',
            store={
                'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
                'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'coef': fields.function(_amount_all_wrapper, string='Coef. of sale',
            store={
                'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
                'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'tender_id': fields.integer('tender_id'),
        #'priceline_id': fields.many2one('ap.gao.prix', 'Price line'),
        'unite_id': fields.many2one('product.uom', 'Product UoM'),
        'total_ds': fields.function(_amount_all_wrapper, string='Amount DS',
            store={
                'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
                'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'total_bpu': fields.function(_amount_all_wrapper, string='Amount DQE',
            store={
                'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
                'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'amount_total': fields.function(_amount_all_wrapper, string='Total',
            store={
                'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
                'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'mat_line': fields.one2many('ap.gao.mat', 'estim_id', string='Materials'),
        'quantity': fields.float('Quantity'),
        
        
        

    }

    #creer une fonction pour filtrer les valeurs de parent_id afin d'afficher uniquement les valeurs qui concerne notre vue

   

    def valeur(self, cr, uid, ids, puds, pubpu, prevu, context=None):
        ds=0
        dqe=0
        values={}
        if prevu and puds:
            ds=puds*prevu
            values={'total_ds':ds,}
        if prevu and pubpu:
            dqe=pubpu*prevu
            values={'total_bpu':dqe,}
        if ds and dqe:
            ecart=dqe-ds
            ratio=(ds/dqe)*100
            coef=((dqe-ds)/ds)*100

            values={'total_ds':ds, 'total_bpu':dqe, 'ecart':ecart, 'ratio':ratio, 'coef':coef}
        return {'value': values}

    def button_dummy(self, cr, uid, ids, context=None):
        return True







class ap_gao_mat(osv.osv):
    _name = 'ap.gao.mat'
    _order = 'product_id asc'


    _columns = {
        'quantity': fields.float('Quantity'),
        'pu_composant': fields.float('price component'),
        'unite_id': fields.many2one('product.uom', 'Product UoM'),
        'product_id': fields.many2one('product.template', 'equipments / materials'),
        'mat_total': fields.float('Amount total'),
        'estim_id': fields.integer('estim'),
        

    }


    def calcul_mat_total(self, cr, uid, ids, pu, qte, context=None):
        total=pu*qte
        values = {'mat_total': total,}
        return {'value': values}

    def button_dummy(self, cr, uid, ids, context=None):
            return True

     #   if mat_total:
     #       raise osv.except_osv(_('Error!'), _(context))
      #      ds+=mat_total
      #      values = {'pu_ds': ds,}
      #      return {'value': values}
      #  return True

    




class ap_gao_doc_received(osv.osv):
    _inherit='ir.attachment'

    _columns = {

        'status': fields.integer('Status'),
        'tendersen_id': fields.integer('tender_id'),
        'tenderrec_id': fields.integer('tender_id'),
        'date': fields.date('Date'),

    }

    _defaults = {
        'date': time.strftime('%Y-%m-%d',time.localtime()),
    }