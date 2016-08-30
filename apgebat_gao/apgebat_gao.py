# -*- coding: utf-8 -*-

import openerp
from openerp import api
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import time
import datetime
import calendar
import logging
_logger = logging.getLogger(__name__)

class ap_gao(osv.osv):
    _name = 'ap.gao'
    _order = 'name asc'

    @api.one
    @api.depends('estimation_id.total_ds', 'estimation_id.total_bpu')
    def _compute_amount(self):
        self.amount_ht_ds = sum(line.total_ds for line in self.estimation_id)
        self.amount_ht_dqe = sum(line.total_bpu for line in self.estimation_id)




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
        'project_id': fields.many2one('project.project', 'project', readonly=True),
        'date_begin': fields.date('Date of start of work'),
        'date_end': fields.date('Date of Completion'),
        #'market': fields.float('Market value'),
        'total_ds': fields.float(''),
        'delai': fields.char('Completion time', readonly=True),
        'note': fields.text('Description'),
        'amount_ht_ds': fields.float(string='Amount total DS', digits=dp.get_precision('Account'),
        store=True , readonly=True, compute='_compute_amount', help="The amount total of Amount DS.", track_visibility='always'),
        'amount_ht_dqe': fields.float(string='Amount total DQE', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="The amount total of amount DQE.", track_visibility='always'),
        'state' : fields.selection([('draft', 'Draft'),('cons', 'Consultation'), ('plan', 'Planning'),('submit', 'Submission'), ('accept', 'Accepted'), ('accepted', 'Created project'), ('reject', 'Rejected'),('cancel', 'Canceled')], 'state'),

        
    }

    _defaults = {
        'state' : 'draft',
        'status' : 'encours',
        'delai': '0 mois et 0 jour'
    }

   # _sql_constraints = [
   #     ('uniq_name', 'unique(name)', "A student already exists with this name in Performances Académie. student's name must be unique!"),
   # ]
  
    def dummy(self, cr, uid, ids, context=None):
        return True

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
            'tender_id': tender.id,
            'use_tasks': True,
            'user_id': uid,
            'partner_id': tender.owner.id,
            'date_start': tender.date_begin,
            'date': tender.date_end,
            'date_begin': tender.date_begin,
            'date_end': tender.date_end,
            
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
       
        return None

    def _create_project(self, cr, uid, ids, inv_values, context=None):
        pro_obj = self.pool.get('project.project')
        pro_id = pro_obj.create(cr, uid, inv_values, context=context)
        # add the invoice to the sales order's invoices
        self.write(cr, uid, ids, {'project_id': pro_id}, context=context)
        tender=self.browse(cr, uid, ids, context=None)
        #raise osv.except_osv(_('Error'), _(tender.estimation_id.id))
        for lot in tender.lot_id:
            self.pool.get('ap.gao.attr').write(cr, uid, lot.id, {'project_id': pro_id})
        for estim in tender.estimation_id:
            self.pool.get('ap.gao.estim').write(cr, uid, estim.id, {'project_id': pro_id})
        for send in tender.doc_send:
            self.pool.get('ir.attachment').write(cr, uid, send.id, {'projectdocsen_id': pro_id})
        for recu in tender.doc_rec:
            self.pool.get('ir.attachment').write(cr, uid, recu.id, {'projectdocrec_id': pro_id})
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




    def save_note(self, cr, uid, ids, note, context=None):
        tender=self.browse(cr, uid, ids, context=context)
        if tender.project_id:
            cr.execute('''UPDATE project_project SET note = %s WHERE tender_id=%s''', (note, ids[0]))
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
        if day_val>1:
            daily = "%s mois et %s jours" % (month_val, day_val)
        else:
            daily = "%s mois et %s jour" % (month_val, day_val)
        values = {'delai': daily,}
        if ids:
            cr.execute('''UPDATE ap_gao SET delai = %s WHERE id=%s''', (daily, ids[0]))
            if begin and end:
                cr.execute('''UPDATE project_project SET date_begin = %s, date_end = %s, delai = %s WHERE tender_id=%s''', (begin, end, daily, ids[0]))
            elif begin:
                cr.execute('''UPDATE project_project SET date_begin = %s, delai = %s WHERE tender_id=%s''', (begin, daily, ids[0]))
            elif end:
                cr.execute('''UPDATE project_project SET date_end = %s, delai = %s WHERE tender_id=%s''', (end, daily, ids[0]))
        return {'value': values}

    



class ap_gao_attr(osv.osv):
    _name = 'ap.gao.attr'
    _order = 'code asc'
    _rec_name='code'


    _columns = {
        'code': fields.char('Batch number'),
        'lot_name': fields.char('Titled lot of tender', required=True),
        'caution': fields.float('interim bail', required=True),
        'credit_line': fields.float('credit line'),
        'tender_id': fields.integer('tender_id'),
        'date_caution': fields.date('interim bail deadline'),
        'dqe': fields.float('DQE'),
        'project_id': fields.many2one('project.project', 'project', readonly=True),
        
    }







class ap_gao_estim(osv.osv):
    _name = 'ap.gao.estim'
    _order = 'price_line asc'
    _rec_name= 'price_line'

    @api.one
    @api.depends('mat_line.mat_total', 'coef', 'quantity')
    def _compute_amount(self):
        self.pu_ds = sum(line.mat_total for line in self.mat_line)
        self.bpu = self.pu_ds*self.coef
        self.total_ds = self.pu_ds*self.quantity
        self.total_bpu = self.bpu*self.quantity
        self.ecart = self.total_bpu-self.total_ds
        idsi=self.search([('lot_id', '=', self.lot_id.id)])
        self.pool.get('ap.gao.attr').write(self._cr,  self._uid, [self.lot_id.id], {'dqe':sum(line.total_bpu for line in idsi)})

        if self.total_bpu and self.total_ds:
            self.rent = ((self.total_bpu-self.total_ds)/self.total_ds)*100

        



    _columns = {
        'type': fields.selection([('vue','Vue'),('child','Details')],'Type', required=True),
        'sequences': fields.integer('Item N°', required=True, help="the display sequence."),
        'parent_id': fields.many2one('ap.gao.estim', 'Parent', ondelete="cascade", domain="[('type','=','vue')]"),
        'code': fields.char('Batch number', help="the allocation batch number."),
        'lot_id': fields.many2one('ap.gao.attr', 'Lot of tender', required=True, help="Lot award."),
        'price_line': fields.char('Entitled', required=True, help="the name of the line price."),
        'quantity': fields.float('Qty', help="Quantity"),
        'pu_ds': fields.float(string='Unit price DS', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="The unit price DS of line.", track_visibility='always'),
        'bpu': fields.float(string='Unit Price BPU', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The unit price BPU of line.", track_visibility='always'),
        'ecart': fields.float('Gap', help="Amount DQE - Amount DS.", track_visibility='always'),
        'coef': fields.float('K', help="    Amount DQE\n--------------- x 100\n    Amount DS.", track_visibility='always'),
        'rent': fields.float('Profit.', help="The profitability of line\n\n  Amount DQE - Amount DS\n----------------------- x 100\n     Amount DS.", track_visibility='always'),
        'tender_id': fields.integer('tender_id'),
        'unite_id': fields.many2one('product.uom', 'Product UoM'),
        'total_ds': fields.float(string='Amount DS', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The amount total DS of price line.", track_visibility='always'),
        'total_bpu': fields.float(string='Amount DQE', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The amount total BPU of price line.", track_visibility='always'),
        #'amount_total': fields.function(_amount_all_wrapper, string='Total',
         #   store={
         #       'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
         #       'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
         #   }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'mat_line': fields.one2many('ap.gao.mat', 'estim_id', string='Materials'),
        'filter': fields.boolean('filter_for_purchase'),
        'project_id': fields.many2one('project.project', 'project', readonly=True),
        

    }

    _defaults = {
        'filter': False
    }

    #creer une fonction pour filtrer les valeurs de parent_id afin d'afficher uniquement les valeurs qui concerne notre vue

   


    def lot_for_tender(self,cr,uid,ids, context=None):
        #raise osv.except_osv(_('Error!'), _())
        estim_obj = self.pool.get('ap.gao.estim')
        estim_ids = estim_obj.search(cr,uid, [('tender_id','=',context['tender']), ('type','=','vue')])
        lot_ids = self.pool.get('ap.gao.attr').search(cr,uid, [('tender_id','=',context['tender'])])
        return {'domain':{'parent_id':[('id','in',estim_ids)], 'lot_id':[('id','in',lot_ids)]}}






class ap_gao_mat(osv.osv):
    _name = 'ap.gao.mat'
    _order = 'product_id asc'

    @api.one
    @api.depends('quantity', 'pu_composant')
    def _compute_amount(self):
        self.mat_total = self.quantity*self.pu_composant

    _columns = {
        'quantity': fields.float('Quantity'),
        'pu_composant': fields.float('Unit price'),
        'unite_id': fields.many2one('product.uom', 'Product UoM'),
        'product_id': fields.many2one('product.template', 'equipments / materials'),
        'mat_total': fields.float(string='Amount Total', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="Amount total of materials line.", track_visibility='always'),
        'estim_id': fields.integer('estim'),

    }


    




class ap_gao_doc_received(osv.osv):
    _inherit='ir.attachment'

    _columns = {

        'status': fields.integer('Status'),
        'tendersen_id': fields.many2one('ap.gao', 'tender', readonly=True),
        'tenderrec_id': fields.many2one('ap.gao', 'tender', readonly=True),
        'date': fields.date('Date'),
        'projectdocsen_id': fields.many2one('project.project', 'project', readonly=True),
        'projectdocrec_id': fields.many2one('project.project', 'project', readonly=True),


    }

    _defaults = {
        'date': time.strftime('%Y-%m-%d',time.localtime()),
    }

class ap_gao_inherit_project(osv.osv):
    _inherit='project.project'

    _columns = {

        'tender_id': fields.many2one('ap.gao', 'Tender'),
        'lot_id': fields.one2many('ap.gao.attr', 'project_id', string='Award prizes'),
        'estimation_id': fields.one2many('ap.gao.estim', 'project_id', string='Estimates'),
        'doc_rec': fields.one2many('ir.attachment', 'projectdocrec_id', 'Documents received'),
        'doc_send': fields.one2many('ir.attachment', 'projectdocsen_id', 'Documents sended'),
        'date_begin': fields.date('Date of start of work'),
        'date_end': fields.date('Date of Completion'),
        'delai': fields.char('Completion time', readonly=True),
        'note': fields.text('Description'),
        'Provisional_date': fields.date('Date of provisional receipt'),
        'final_date': fields.date('Date of final acceptance'),


    }



    def save_note(self, cr, uid, ids, note, context=None):
        project=self.browse(cr, uid, ids, context=context)
        if project.tender_id:
            cr.execute('''UPDATE ap_gao SET note = %s WHERE project_id=%s''', (note, ids[0]))
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
        if day_val>1:
            daily = "%s mois et %s jours" % (month_val, day_val)
        else:
            daily = "%s mois et %s jour" % (month_val, day_val)
        values = {'delai': daily,}
        if ids:
            cr.execute('''UPDATE project_project SET delai = %s WHERE id=%s''', (daily, ids[0]))
            if begin and end:
                cr.execute('''UPDATE ap_gao SET date_begin = %s, date_end = %s, delai = %s WHERE project_id=%s''', (begin, end, daily, ids[0]))
            elif begin:
                cr.execute('''UPDATE ap_gao SET date_begin = %s, delai = %s WHERE project_id=%s''', (begin, daily, ids[0]))
            elif end:
                cr.execute('''UPDATE ap_gao SET date_end = %s, delai = %s WHERE project_id=%s''', (end, daily, ids[0]))
        return {'value': values}

