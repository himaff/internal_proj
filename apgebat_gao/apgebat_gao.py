# -*- coding: utf-8 -*-
from lxml import etree
import xlwt
from cStringIO import StringIO
import base64
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


schu=["","UN ","DEUX ","TROIS ","QUATRE ","CINQ ","SIX ","SEPT ","HUIT ","NEUF "]
schud=["DIX ","ONZE ","DOUZE ","TREIZE ","QUATORZE ","QUINZE ","SEIZE ","DIX SEPT ","DIX HUIT ","DIX NEUF "]
schd=["","DIX ","VINGT ","TRENTE ","QUARANTE ","CINQUANTE ","SOIXANTE ","SOIXANTE ","QUATRE VINGT ","QUATRE VINGT "]


def convNombre2lettres(nombre):
    s=''
    reste=nombre
    i=1000000000 
    while i>0:
        y=reste/i
        if y!=0:
            centaine=y/100
            dizaine=(y - centaine*100)/10
            unite=y-centaine*100-dizaine*10
            if centaine==1:
                s+="CENT "
            elif centaine!=0:
                s+=schu[centaine]+"CENT "
                if dizaine==0 and unite==0: s=s[:-1]+"S " 
            if dizaine not in [0,1]: s+=schd[dizaine] 
            if unite==0:
                if dizaine in [1,7,9]: s+="DIX "
                elif dizaine==8: s=s[:-1]+"S "
            elif unite==1:   
                if dizaine in [1,9]: s+="ONZE "
                elif dizaine==7: s+="ET ONZE "
                elif dizaine in [2,3,4,5,6]: s+="ET UN "
                elif dizaine in [0,8]: s+="UN "
            elif unite in [2,3,4,5,6,7,8,9]: 
                if dizaine in [1,7,9]: s+=schud[unite] 
                else: s+=schu[unite] 
            if i==1000000000:
                if y>1: s+="MILLIARDS "
                else: s+="MILLIARD "
            if i==1000000:
                if y>1: s+="MILLIONS "
                else: s+="MILLION "
            if i==1000:
                s+="MILLE "
        #end if y!=0
        reste -= y*i
        dix=False
        i/=1000;
    #end while
    if len(s)==0: s+="ZERO "
    return s

class gao_xls_report_file(osv.osv_memory):
    _name = 'gao.xls.report.file'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(gao_xls_report_file, self).default_get(cr, uid, fields, context=context)
        res.update({'file_name': context.get('file_name', 'DEMO')+'.xls'})
        res.update({'import_name': context.get('import_name', 'modele')+'.xls'})

        if context.get('file'):
            res.update({'file': context['file']})
        if context.get('link_import'):
            res.update({'link_import': context['link_import']})
        return res


    _columns = {
        'file': fields.binary('File', filters='*.xls'),
        'file_name': fields.char('File Name', size=64),
        'link_import': fields.binary('File', filters='*.xls'),
        'import_name': fields.char('File Name', size=64),
    }

    _defaults = {'import_name': 'le modèle'}

    def loadmodel(self, cr, uid, ids, context=None):
        self.pool.get('importe').model_importe(cr, uid, ids, context=context)

    def imported(self, cr, uid, ids, context=None):
        self.pool.get('importe').imported_line(cr, uid, ids, context=context)
        
    


class ap_gao(osv.osv):
    _name = 'ap.gao'
    _order = 'name asc'

    @api.one
    @api.depends('estimation_id.total_ds', 'estimation_id.total_bpu','estimation_id1.total_dsf', 'estimation_id1.total_bpuf','estimation_id1.total_dst', 'estimation_id1.total_bput')
    def _compute_amount(self):
        if self.tender_type.code=='elec':
            self.amount_ht_dsf = sum(line.total_dsf for line in self.estimation_id1)
            self.amount_ht_dst = sum(line.total_dst for line in self.estimation_id1)
            self.amount_ht_ds = self.amount_ht_dsf+self.amount_ht_dst
            
            self.amount_ht_dqef = sum(line.total_bpuf for line in self.estimation_id1)
            self.amount_ht_dqet = sum(line.total_bput for line in self.estimation_id1)
            self.amount_ht_dqe = self.amount_ht_dqef+self.amount_ht_dqet

        else:
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
        'estimation_id1': fields.one2many('ap.gao.estim', 'tender_id', string='Estimates'),
        'doc_rec': fields.one2many('ir.attachment', 'tenderrec_id', 'Documents received'),
        'doc_send': fields.one2many('ir.attachment', 'tendersen_id', 'Documents sended'),
        'project_id': fields.many2one('project.project', 'project', readonly=True),
        'date_begin': fields.date('Date of start of work'),
        'date_end': fields.date('Date of Completion'),
        'tender_type': fields.many2one('tender.type', 'Activity type', required=True),
        'total_ds': fields.float(''),
        'delai': fields.char('Completion time', readonly=True),
        'note': fields.text('Description'),
        'amount_ht_ds': fields.float(string='Amount total DS', digits=dp.get_precision('Account'),
        store=True , readonly=True, compute='_compute_amount', help="The amount total of Amount DS.", track_visibility='always'),
        'amount_ht_dsf': fields.float(string='Amount total DS supplies', digits=dp.get_precision('Account'),
        store=True , readonly=True, compute='_compute_amount', help="The amount total of Amount DS.", track_visibility='always'),
        'amount_ht_dst': fields.float(string='Amount total DS works', digits=dp.get_precision('Account'),
        store=True , readonly=True, compute='_compute_amount', help="The amount total of Amount DS.", track_visibility='always'),
        'amount_ht_dqe': fields.float(string='Amount total DQE', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="The amount total of amount DQE.", track_visibility='always'),
        'amount_ht_dqef': fields.float(string='Amount total DQE supplies', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="The amount total of amount DQE.", track_visibility='always'),
        'amount_ht_dqet': fields.float(string='Amount total DQE works', digits=dp.get_precision('Account'),
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


    #def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):   
     #   if not context: context = {}
        
      


  
    def dummy(self, cr, uid, ids, context=None):
        return True

    def poster(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cons'})

    def accord(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'plan'})

    def submited(self, cr, uid, ids, context=None):
        estim=self.pool.get('ap.gao.estim').search(cr, uid, [('tender_id', '=', ids[0]), ('type', '=', 'draft')])
        if estim:
            raise osv.except_osv(_("Ligne d'estimation"), _("Toutes les lignes de prix ne sont pas validées"))
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
            'tender_type': tender.tender_type.name
            
        }
        result.append(inv_values)
        return result


    def create_project(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        inv_ids = []
        estim=self.pool.get('ap.gao.estim').search(cr, uid, [('tender_id', '=', ids[0]), ('type', '=', 'draft')])
        if estim:
            raise osv.except_osv(_("Ligne d'estimation"), _("Toutes les lignes de prix ne sont pas validées"))
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

    def importestim(self, cr, uid, ids, context=None):
        fl = StringIO()
        if context is None: context = {}
        #creation du modele d'import
        ao=self.browse( cr, uid, ids)
        style= xlwt.easyxf('font:height 180, colour_index black, name Calibri, bold on; align: vert centre, horiz right;pattern: pattern solid, fore_colour gray25 ;')
        wbk = xlwt.Workbook(encoding="UTF-8")
        for lots in ao.lot_id:
            lot= wbk.add_sheet(lots.code, cell_overwrite_ok=True)#creation de la feuille  
            lot.write(0, 0, 'N°', style)
            lot.write(0, 1, 'Ligne de prix', style)
            lot.write(0, 2, 'Unité', style)
            lot.write(0, 3, 'Quantité', style)
            #lot.write(0, 4, 'Parent', style)
            #lot.write(0, 5, 'K', style)
        
        #lot= wbk.add_sheet("MMO", cell_overwrite_ok=True)#creation de la feuille  
        #lot.write(0, 0, 'Article', style)
        #lot.write(0, 1, 'Quantité', style)
        #lot.write(0, 2, 'Unité', style)
        #lot.write(0, 3, 'Prix unitaire', style)
        #lot.write(0, 4, 'N° ligne de prix', style) 

        wbk.save(fl) # for save le fichier
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        ctx = dict(context)
        ctx.update({'link_import': buf, 'import_name': 'le modèle'})
        
        if context is None:
            context = {}
        data = {}
        res = self.read(cr, uid, ids, [], context=context)
        res = res and res[0] or {}
        data['form'] = res
        try:
            form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'apgebat_gao', 'importestim_form')[1]
        except ValueError:
            form_id = False
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'gao.xls.report.file',
        'views': [(form_id, 'form')],
        'target': 'new',
        'context': ctx,
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



    def print_dqexlselec(self, cr, uid, ids, context=None):
        #popup de notification type warning
        
        return {
                'type': 'ir.actions.client',
                'tag': 'action_notify',
                'name': 'Warning',
                'params': {
                   'title': 'Postage Cancellation Failed',
                   'text': 'Shipment is outside the void period.',
                   'sticky': False
                }
                }
        ao=self.browse(cr, uid, ids)
        fl = StringIO()
        if context is None: context = {}
        wbk = xlwt.Workbook(encoding="UTF-8")
        
        font = xlwt.Font()
        font.bold = True
        #num_format pour afficher tiret a la place de zero
        #.num_format_str='_("$"* #,##0.00_);_("$"* (#,##0.00);_("$"* "-"??_);_(@_)'
        #xlwt.add_palette_colour("vert_claire", 0x21)
        #wbk.set_colour_RGB(0x21, 146, 208, 80)
        borders = xlwt.Borders()
        bold_style = xlwt.XFStyle()
        bold_style.font= font
        style = xlwt.easyxf('align:wrap no')
        style6=xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: wrap No;border:  right thin, bottom thin;align: vert centre, horiz center')
        style7=xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: wrap No;border:  right medium, bottom thin;align: vert centre, horiz center')
        new_style6=xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: wrap No;border:  right thin')
        new_style7=xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: wrap No;border:  right medium', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)')
        new_style6en=xlwt.easyxf('font:height 180, colour_index black, name Arial; align: wrap No;border:  right thin')
        new_style7en=xlwt.easyxf('font:height 180, colour_index black, name Arial; align: wrap No;border:  right medium', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)')
        new_style6env=xlwt.easyxf('font:height 180, colour_index black, name Arial; align: wrap No;pattern: pattern solid, fore_colour gray25 ;')
        new_style7env=xlwt.easyxf('font:height 180, colour_index black, name Arial; align: wrap No;pattern: pattern solid, fore_colour gray25 ;border:  right medium')
        entete=xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin;align: vert centre, horiz center')#fusionne des lignes (l1, l2, c1, c2)
        bordtop = xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top medium, right thin, bottom thin;align: vert centre, horiz center')
        stotal = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top thin, right thin;pattern: pattern solid, fore_colour gray25;')
        stotalf = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top thin, right thin;pattern: pattern solid, fore_colour gray25;')
        footer = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top thin')
        footers = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top thin, right thin;')
        footerss = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top thin, right thin, bottom thin;')
        basdepage1=xlwt.easyxf('font:height 200, colour_index black, name Arial; align: wrap No;align: vert centre, horiz right')
        basdepage2=xlwt.easyxf('font:height 200, colour_index black, name Arial; align: wrap No;align: vert centre, horiz left')
        i=0
        for lots in ao.lot_id:
            i+=1
            vars()["lot{}".format(i)] = wbk.add_sheet(lots.code, cell_overwrite_ok=True)#creation de la feuille
            lot=eval("lot{}".format(i))

            lot.col(1).width= 500*25 #size de la column
            lot.col(0).width= 500*4 #size de la column
            lot.col(3).width= 500*3 #size de la column
            lot.col(6).width= 500*3 #size de la column
            lot.col(5).width= 500*9 #size de la column
            lot.col(8).width= 500*9 #size de la column
            
            #1pt=20
            #entete du DQE en vert
            lot.write_merge(0, 2, 0, 8, 'DQE '+lots.code, entete)

            #tableau des lignes
                #entete du tableau
            lot.write_merge(3, 4, 0, 0, 'N°', bordtop)
            lot.write_merge(3, 4, 1, 1, 'DESIGNATION', bordtop)
            lot.write_merge(3, 4, 2, 2, 'UNITE', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top medium, right medium, bottom thin;align: vert centre, horiz center'))
            lot.write_merge(3, 3, 3, 5, 'FOURNITURES', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top medium, right medium, bottom thin;align: vert centre, horiz center'))
            lot.write(4,3,'Qté', style6)
            lot.write(4,4,'Prix unitaire', style6)
            lot.write(4,5,'Prix total', style7)
            lot.write_merge(3, 3, 6, 8, 'TRAVAUX', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top medium, right medium, bottom thin;align: vert centre, horiz center'))
            lot.write(4,6,'Qté', style6)
            lot.write(4,7,'Prix unitaire', style6)
            lot.write(4,8,'Prix total', style7)

            parent_code=''
            par={}
            vue={}
            seq={}
            formuledqef={}
            formuledqet={}
            recapf={}
            recapt={}
            c=0
            a=0
            b=4
            nbr=0
            lisum=[]
            estimation_id=self.pool.get('ap.gao.estim').search(cr, uid,[('tender_id', '=', ao.id), ('lot_id', '=', lots.id)], order='sequences' )
            for estim in self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id):
                
                a+=1
                b+=1
                if estim.type=="vue":
                #ligne de tableau 'parent'
                    lot.write(b, 0, estim.code and estim.code or '', new_style6)
                    lot.write(b, 1, estim.price_line, new_style6)
                    lot.write(b, 2, '', new_style7)
                    lot.write(b, 3, '', new_style6)
                    lot.write(b, 4, '', new_style6)
                    lot.write(b, 5, '', new_style7)
                    lot.write(b, 6, '', new_style6)
                    lot.write(b, 7, '', new_style6)
                    lot.write(b, 8, '', new_style7)

                    
                    #on recupere lid du la vue actuel
                    parent=estim.id
                    #on cherche tous ses enfants directe etant de type parent
                    enfid=self.pool.get('ap.gao.estim').read_group(cr,uid,[('parent_id', '=', parent), ('type', '=', 'vue')], ['parent_id'], ['parent_id'])
                    #s'il y en a alors on stocke le nombre dans un var sinon -15
                    if enfid:
                        enfpar=enfid[0]['parent_id_count']
                    else:
                        enfpar=-15
                    #on recupere tout les enfants de la vue(vue ou details)
                    enf=self.pool.get('ap.gao.estim').read_group(cr,uid,[('parent_id', '=', parent)], ['parent_id'], ['parent_id'])
                    if enf:
                        parent_code=estim.code
                        niv1=0
                        niv2=0
                        niv3=0
                        niv4=0
                        niv5=0
                        for enf in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', parent)]):
                            niv1+=1
                            for enf1 in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', enf)]):
                                niv2+=1
                                for enf2 in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', enf1)]):
                                    niv3+=1
                                    for enf3 in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', enf2)]):
                                        niv4+=1
                                        for enf4 in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', enf3)]):
                                            niv5+=1
                        #on a le nbre total de descendant sur 5 generations
                        nbr=niv1+niv2+niv3+niv4+niv5
                        #si cette vue est enfant dune autre alors on stock dans par
                        if estim.parent_id:
                            par[str(nbr)+estim.price_line+str(a)]=str(estim.code)
                        else:
                            vue[str(nbr)]=str(estim.code)

                else:

                #ligne de tableau 'enfant'
                    lot.write(b, 0, estim.code and estim.code or '', new_style6en)
                    lot.write(b, 1, estim.price_line, new_style6en)
                    lot.write(b, 2, estim.unite_id and estim.unite_id or '', new_style7en)
                    if estim.bpu_f:
                        lot.write(b, 3, estim.quantity, new_style6en)
                        lot.write(b, 4, estim.bpu_f, new_style6en)
                        lot.write(b, 5, xlwt.Formula("D"+str(b+1)+"*E"+str(b+1)), new_style7en)
                    else:
                        lot.write(b, 3, '', new_style6env)
                        lot.write(b, 4, '', new_style6env)
                        lot.write(b, 5, '', new_style7env)

                    if estim.bpu_t:
                        lot.write(b, 6, estim.quantity, new_style6en)
                        lot.write(b, 7, estim.bpu_t, new_style6en)
                        lot.write(b, 8, xlwt.Formula("G"+str(b+1)+"*H"+str(b+1)), new_style7en)
                    else:
                        lot.write(b, 6, '', new_style6env)
                        lot.write(b, 7, '', new_style6env)
                        lot.write(b, 8, '', new_style7env)



                #ligne de tableau sous total 'parent'
                new_style6g=xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: wrap No;border: right thin, bottom medium')
                new_style7g=xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: wrap No;border: right medium, bottom medium')
                            
                if vue: 
                    for x in range(1, a):

                        if estim.parent_id:
                            for y in range(1, a):
                                if str(x)+estim.parent_id.price_line+str(y) in par:
                                    if par[str(x)+estim.parent_id.price_line+str(y)]:
                                        if a-y==x:
                                             #ligne sous total
                                            b+=1
                                            c+=1
                    
                                            
                                            lot.write(b, 0, '', new_style6)
                                            lot.write(b, 1, 'TOTAL '+par[str(x)+estim.parent_id.price_line+str(y)], new_style6)
                                            lot.write(b, 2, '', new_style7)
                                            lot.write(b, 3, '', new_style6)
                                            lot.write(b, 4, '', new_style6)
                                            lot.write(b, 5, xlwt.Formula("SUM(F"+str(b+1-x)+":F"+str(b)+")"), new_style7)
                                            lot.write(b, 6, '', new_style6)
                                            lot.write(b, 7, '', new_style6)
                                            lot.write(b, 8, xlwt.Formula("SUM(I"+str(b+1-x)+":I"+str(b)+")"), new_style7)
                                            b+=1
                                            lot.write(b, 0, '', new_style6)
                                            lot.write(b, 1, '', new_style6)
                                            lot.write(b, 2, '', new_style7)
                                            lot.write(b, 3, '', new_style6)
                                            lot.write(b, 4, '', new_style6)
                                            lot.write(b, 5, '', new_style7)
                                            lot.write(b, 6, '', new_style6)
                                            lot.write(b, 7, '', new_style6)
                                            lot.write(b, 8, '', new_style7)
                                            
                                            par[str(x)+estim.parent_id.price_line+str(y)]=''
                                            #raise osv.except_osv(_('eri'), _(estim.parent_id.price_line))
                                            recapf[estim.parent_id.price_line]="F"+str(b)
                                            recapt[estim.parent_id.price_line]="I"+str(b)
                                            if estim.parent_id.parent_id.code in formuledqef:
                                                formuledqef[estim.parent_id.parent_id.code]+= "+F"+str(b)
                                                formuledqet[estim.parent_id.parent_id.code]+= "+I"+str(b)
                                                
                                            else:
                                                formuledqef[estim.parent_id.parent_id.code]= "F"+str(b)
                                                formuledqet[estim.parent_id.parent_id.code]= "I"+str(b)

                                                

                        if str(x) in vue:
                            if vue[str(x)] and (enfpar==c or enfpar==-15):
                                b+=1

                                lot.write(b, 0, '', new_style6)
                                lot.write(b, 1, 'TOTAL '+vue[str(x)], new_style6)
                                lot.write(b, 2, '', new_style7)
                                lot.write(b, 3, '', new_style6)
                                lot.write(b, 4, '', new_style6)
                                lot.write(b, 6, '', new_style6)
                                lot.write(b, 7, '', new_style6)
                                if vue[str(x)] in formuledqef:
                                    lot.write(b, 5, xlwt.Formula(formuledqef[vue[str(x)]]), new_style7)
                                    lot.write(b, 8, xlwt.Formula(formuledqet[vue[str(x)]]), new_style7)
                                else:
                                    if x>0:
                                        lot.write(b, 5, xlwt.Formula("SUM(F"+str(b+1-x)+":F"+str(b)+")"), new_style7)       
                                        lot.write(b, 8, xlwt.Formula("SUM(I"+str(b+1-x)+":I"+str(b)+")"), new_style7)
                                    else: 
                                        lot.write(b, 5, 0, new_style7)       
                                        lot.write(b, 8, 0, new_style7)
                                            
                                b+=1
                                lot.write(b, 0, '', new_style6g)
                                lot.write(b, 1, '', new_style6g)
                                lot.write(b, 2, '', new_style7g)
                                lot.write(b, 3, '', new_style6g)
                                lot.write(b, 4, '', new_style6g)
                                lot.write(b, 5, '', new_style7g)
                                lot.write(b, 6, '', new_style6g)
                                lot.write(b, 7, '', new_style6g)
                                lot.write(b, 8, '', new_style7g)
                                
                                lisum.append(b+1)
                                a=0
                                nbr=0
                                vue[x]=''
                                c=0
                                if vue[str(x)] in formuledqef:
                                    recapf[estim.parent_id.parent_id.price_line]="F"+str(b)
                                    recapt[estim.parent_id.parent_id.price_line]="I"+str(b)
                                else:
                                    recapf[estim.parent_id.price_line]="F"+str(b)
                                    recapt[estim.parent_id.price_line]="I"+str(b)


                #ligne de tableau le footer
            lot.write(b+1, 0, '', footer)
            lot.write(b+1, 1, '', footer)
            lot.write(b+1, 2, '', footer)
            lot.write(b+1, 3, '', footer)
            lot.write(b+1, 4, '', footer)
            lot.write(b+1, 5, '', footer)
            lot.write(b+1, 6, '', footer)
            lot.write(b+1, 7, '', footer)
            lot.write(b+1, 8, '', footer)
            #fin du tableau

            #bas de page
            #new tableau recapitulatif
            #raise osv.except_osv(_('iig'), _(recapt))
            b+=3
            lot.write_merge(b, b, 0, 8, 'RECAPITULATIF', entete)
            b+=1
            lot.write(b, 0, '', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top thin, right thin;align: vert centre, horiz center'))
            lot.write_merge(b, b, 1, 2, '', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top thin, right thin;align: vert centre, horiz center'))
            lot.write_merge(b, b, 3, 5, '', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top thin, right thin;align: vert centre, horiz center'))
            lot.write_merge(b, b, 6, 8, '', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top thin, right thin;align: vert centre, horiz center'))
            bordlign = xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: right thin;align: vert centre, horiz right', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)')
            bordlignl = xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: right thin;align: vert centre, horiz left')
            bordlignc = xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: right thin;align: vert centre, horiz center')
            d=0
            vuetotal=[]
            
            for estima in self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id):
                if estima.type=='vue':
                    b+=1
                    d+=1
                    if estima.parent_id:
                        lot.write(b, 0, '', bordlignc)
                        lot.write_merge(b, b, 1, 2, estima.code and estima.code+' '+estima.price_line or estima.price_line, xlwt.easyxf('font: name Arial,height 180, color-index black;border: right thin;align: vert centre, horiz left'))
                        if estima.price_line in recapf:
                            lot.write_merge(b, b, 3, 5, xlwt.Formula(recapf[estima.price_line]), xlwt.easyxf('font: name Arial,height 180, color-index black;border: right thin;align: vert centre, horiz right', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)'))
                            lot.write_merge(b, b, 6, 8, xlwt.Formula(recapt[estima.price_line]), xlwt.easyxf('font: name Arial,height 180, color-index black;border: right thin;align: vert centre, horiz right', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)'))
                        else:
                            lot.write_merge(b, b, 3, 5, '', xlwt.easyxf('font: name Arial,height 180, color-index black;border: right thin;align: vert centre, horiz right'))
                            lot.write_merge(b, b, 6, 8, '', xlwt.easyxf('font: name Arial,height 180, color-index black;border: right thin;align: vert centre, horiz right'))

                    else:
                        lot.write(b, 0, estima.code and estima.code or '', bordlignc)
                        lot.write_merge(b, b, 1, 2, estima.price_line, bordlignl)
                        if estima.price_line in recapf:
                            lot.write_merge(b, b, 3, 5, xlwt.Formula(recapf[estima.price_line]), bordlign)
                            lot.write_merge(b, b, 6, 8, xlwt.Formula(recapt[estima.price_line]), bordlign)
                        else:
                            lot.write_merge(b, b, 3, 5, '', bordlign)
                            lot.write_merge(b, b, 6, 8, '', bordlign)
                        vuetotal.append(b+1)
            b+=1
            nbrvue=len(vuetotal)
            a=0
            t=''
            f=''
            for l in vuetotal:
                a+=1
                if a==1:
                    f+='D'+str(l)
                    t+='G'+str(l)
                else:
                    f+='+D'+str(l)
                    t+='+G'+str(l)
            lot.write(b, 0, "", xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top thin, bottom thin;align: vert centre, horiz left'))
            lot.write_merge(b, b, 1, 2, "TOTAUX", xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: right thin, top thin, bottom thin;align: vert centre, horiz left'))
            lot.write_merge(b, b, 3, 5, xlwt.Formula(f and f or '0'), xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: right thin, top thin, bottom thin;align: vert centre, horiz right', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)'))
            lot.write_merge(b, b, 6, 8, xlwt.Formula(t and t or '0'), xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: right thin, top thin, bottom thin;align: vert centre, horiz right', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)'))
            b+=1
            lot.write(b, 0, '', bordlignc)
            lot.write_merge(b, b, 1, 2, '', )
            lot.write_merge(b, b, 6, 8, '', bordlign)
            b+=1
            lot.write(b, 0, '', bordlignc)
            lot.write(b, 1, 'TOTAL FOURNITURES ET TRAVAUX', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;align: vert centre, horiz left'))
            lot.write_merge(b, b, 6, 8, xlwt.Formula("D"+str(b-1)+"+G"+str(b-1)), bordlign)
            b+=1
            lot.write(b, 0, '', bordlignc)
            lot.write(b, 1, 'Transport', xlwt.easyxf('font: name Arial,height 180, color-index black;align: vert centre, horiz left'))
            lot.write_merge(b, b, 6, 8, 0, xlwt.easyxf('font: name Arial,height 180, color-index black;border: right thin;align: vert centre, horiz right', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)'))
            b+=1
            lot.write(b, 0, '', bordlignc)
            lot.write(b, 1, 'S/ TOTAL HT', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;align: vert centre, horiz left'))
            lot.write_merge(b, b, 6, 8, xlwt.Formula("G"+str(b-1)+"+G"+str(b)), bordlign)
            b+=1
            lot.write(b, 0, '', bordlignc)
            lot.write(b, 1, 'TVA', xlwt.easyxf('font: name Arial,height 180, color-index black;align: vert centre, horiz left'))
            lot.write(b, 2, 0.18, xlwt.easyxf('font: name Arial,height 180, color-index black;align: vert centre, horiz left', num_format_str='0%'))
            lot.write_merge(b, b, 6, 8, xlwt.Formula("G"+str(b)+"*C"+str(b+1)), xlwt.easyxf('font: name Arial,height 180, color-index black;border: right thin;align: vert centre, horiz right', num_format_str='_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"_);_(@_)'))
            b+=1
            lot.write(b, 0, '', bordlignc)
            lot.write(b, 1, 'TOTAL  TTC', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;align: vert centre, horiz left'))
            lot.write_merge(b, b, 6, 8, xlwt.Formula("G"+str(b-1)+"+G"+str(b)), bordlign)

            b+=1

            lot.write_merge(b, b, 0, 8, '', footer)
            #date=time.strftime('%d %B %Y',time.localtime())
            #text=str(date).encode('utf-8')
            #text=unicode(text, encoding='utf-8', errors='ignore')
            
            #date_format.
            basdepage3=xlwt.easyxf('font:height 200, colour_index black, name Arial; align: wrap No;align: vert centre, horiz left', num_format_str='dd mmmm yyyy')
        
            lot.write_merge(b+2, b+2, 7, 8, 'Le Soumissionnaire', basdepage2)

        
            
        wbk.save(fl) # for save le fichier
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        ctx = dict(context)
        ctx.update({'file': buf, 'file_name': context.get('file_name', 'test')})
        if context is None:
            context = {}
        data = {}
        res = self.read(cr, uid, ids, [], context=context)
        res = res and res[0] or {}
        data['form'] = res
        try:
            form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'apgebat_gao', 'xls_form')[1]
        except ValueError:
            form_id = False
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'gao.xls.report.file',
        'views': [(form_id, 'form')],
        'target': 'new',
        'context': ctx,
        }






    def print_dqexlsgc(self, cr, uid, ids, context=None):
        ao=self.browse(cr, uid, ids)
        fl = StringIO()
        if context is None: context = {}
        wbk = xlwt.Workbook(encoding="UTF-8")
        
        font = xlwt.Font()
        font.bold = True
        #xlwt.add_palette_colour("vert_claire", 0x21)
        #wbk.set_colour_RGB(0x21, 146, 208, 80)
        borders = xlwt.Borders()
        bold_style = xlwt.XFStyle()
        bold_style.font= font
        style = xlwt.easyxf('align:wrap no')
        new_style6=xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: wrap No;border: top hair, right hair')
        new_style7=xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: wrap No;border: top hair, right medium')
        new_style6en=xlwt.easyxf('font:height 180, colour_index black, name Arial; align: wrap No;border: top hair, right hair')
        new_style7en=xlwt.easyxf('font:height 180, colour_index black, name Arial; align: wrap No;border: top hair, right medium')
        entete=xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;pattern: pattern solid, fore_colour lime ;border: bottom thin')#fusionne des lignes (l1, l2, c1, c2)
        bordtop = xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top medium, right hair;align: vert centre, horiz center')
        stotal = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top hair, right hair;pattern: pattern solid, fore_colour gray25;')
        stotalf = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top hair, right medium;pattern: pattern solid, fore_colour gray25;')
        footer = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top medium, right thin;')
        footers = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top thin, right thin;')
        footerss = xlwt.easyxf('font:height 180, colour_index black, name Arial, bold on; align: vert centre, horiz right;border: top thin, right thin, bottom thin;')
        basdepage1=xlwt.easyxf('font:height 200, colour_index black, name Arial; align: wrap No;align: vert centre, horiz right')
        basdepage2=xlwt.easyxf('font:height 200, colour_index black, name Arial; align: wrap No;align: vert centre, horiz left')
        i=0
        for lots in ao.lot_id:
            i+=1
            vars()["lot{}".format(i)] = wbk.add_sheet(lots.code, cell_overwrite_ok=True)#creation de la feuille
            lot=eval("lot{}".format(i))
            lot.col(1).width= 500*41 #size de la column
            lot.col(0).width= 500*8 #size de la column
            
            #1pt=20
            #entete du DQE en vert
            lot.write_merge(0, 0, 0, 6, ao.name, entete)
            lot.write_merge(1, 1, 0, 6, lots.code+': '+lots.lot_name, xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin;align: vert centre, horiz center')) 
            lot.write_merge(2, 2, 0, 6, 'SERIE :', xlwt.easyxf('font: name Arial,height 220, color-index black, bold on;border: bottom thin;align: vert centre, horiz center'))
            lot.write_merge(3, 3, 0, 6, 'DETAIL QUANTITATIF ET ESTIMATIF', xlwt.easyxf('font: name Arial,height 280, color-index black, bold on, underline single;align: vert centre, horiz center'))
            
            #tableau des lignes
                #entete du tableau
            lot.write_merge(5, 6, 0, 0, 'N° PRIX', bordtop)
            lot.write_merge(5, 6, 1, 1, 'DESIGNATION', bordtop)
            lot.write_merge(5, 6, 2, 2, 'QUANTITE', bordtop)
            lot.write_merge(5, 6, 3, 3, 'UNITE', bordtop)
            lot.write_merge(5, 6, 4, 4, '', bordtop)
            lot.write_merge(5, 5, 5, 6, 'PRIX EN F CFA HT/HD', xlwt.easyxf('font: name Arial,height 180, color-index black, bold on;border: top medium, right medium;align: vert centre, horiz center'))
            lot.write(6,5,'Prix unitaire', new_style6)
            lot.write(6,6,'Prix total', new_style7)

            parent_code=''
            a=0
            b=6
            nbr=0
            lisum=[]
            estimation_id=self.pool.get('ap.gao.estim').search(cr, uid,[('tender_id', '=', ao.id), ('lot_id', '=', lots.id)], order='sequences' )
            for estim in self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id):
                
                a+=1
                b+=1
                if estim.type=="vue":
                #ligne de tableau 'parent'
                    lot.write(b, 0, estim.code and estim.code or '', new_style6)
                    lot.write(b, 1, estim.price_line, new_style6)
                    lot.write(b, 2, '', new_style6)
                    lot.write(b, 3, '', new_style6)
                    lot.write(b, 4, '', new_style6)
                    lot.write(b, 5, '', new_style6)
                    lot.write(b, 6, '', new_style7)
                    if not estim.parent_id:
                        parent=estim.id
                        enf=self.pool.get('ap.gao.estim').read_group(cr,uid,[('parent_id', '=', parent)], ['parent_id'], ['parent_id'])
                        if enf:
                            parent_code=estim.code
                            niv1=0
                            niv2=0
                            niv3=0
                            niv4=0
                            niv5=0
                            
                            for enf in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', parent)]):
                                niv1+=1
                                for enf1 in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', enf)]):
                                    niv2+=1
                                    for enf2 in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', enf1)]):
                                        niv3+=1
                                        for enf3 in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', enf2)]):
                                            niv4+=1
                                            for enf4 in self.pool.get('ap.gao.estim').search(cr, uid,[('parent_id', '=', enf3)]):
                                                niv5+=1
                            nbr=niv1+niv2+niv3+niv4+niv5
                            
                else:

                #ligne de tableau 'enfant'
                    lot.write(b, 0, estim.code and estim.code or '', new_style6en)
                    lot.write(b, 1, estim.price_line, new_style6en)
                    lot.write(b, 2, estim.quantity, new_style6en)
                    lot.write(b, 3, estim.unite_id and estim.unite_id or '', new_style6en)
                    lot.write(b, 4, '', new_style6en)
                    lot.write(b, 5, estim.bpu, new_style6en)
                    lot.write(b, 6, xlwt.Formula("C"+str(b+1)+"*F"+str(b+1)), new_style7en)

                #ligne de tableau sous total 'parent'
                if parent_code and nbr==a-1:
                    b+=1
                    lot.write_merge(b, b, 0, 3, 'SOUS TOTAL '+parent_code, stotal)
                    lot.write(b, 4, '', stotal)
                    lot.write(b, 5, '', stotal)
                    lot.write(b, 6, xlwt.Formula("SUM(G"+str(b-nbr+1)+":G"+str(b)+")"), stotalf)
                    lisum.append(b+1)
                    a=0
                    nbr=0


                #ligne de tableau le footer
            lot.write_merge(b+1, b+1, 0, 3, 'TOTAL '+lots.lot_name+', HT/HD', footer)
            lot.write(b+1, 4, '', footer)
            lot.write(b+1, 5, '', footer)
            val=''
            x=1
            for lig in lisum:
                if len(lisum)==x:
                    val+="G"+str(lig)
                else:
                    val+="G"+str(lig)+"+"
                x+=1
            if val:
                lot.write(b+1, 6, xlwt.Formula(val), footer)
            else:
                if b>=7:
                    lot.write(b+1, 6, xlwt.Formula('SUM(G8:G'+str(b+1)+')'), footer)
                else:
                    lot.write(b+1, 6, 0, footer)

            lot.write_merge(b+2, b+2, 0, 3, 'TVA (18%)', footers)
            lot.write(b+2, 4, '', footers)
            lot.write(b+2,5, '', footers)
            lot.write(b+2,6, xlwt.Formula("G"+str(b+2)+"*0.18"), footers)

            lot.write_merge(b+3, b+3, 0, 3, 'TOTAL '+lots.lot_name+', TTC', footerss)
            lot.write(b+3, 4, '', footerss)
            lot.write(b+3, 5, '', footerss)
            lot.write(b+3, 6, xlwt.Formula("G"+str(b+2)+"+G"+str(b+3)), footerss)
            #fin du tableau

            #bas de page
            #date=time.strftime('%d %B %Y',time.localtime())
            #text=str(date).encode('utf-8')
            #text=unicode(text, encoding='utf-8', errors='ignore')
            date_format = xlwt.XFStyle()
            #date_format.
            basdepage3=xlwt.easyxf('font:height 200, colour_index black, name Arial; align: wrap No;align: vert centre, horiz left', num_format_str='dd mmmm yyyy')
        
            lot.write(b+6, 1, 'Fait à Abidjan, le ', basdepage1)
            lot.write_merge(b+6, b+6, 2, 3, xlwt.Formula('now()'), basdepage3)
            lot.write(b+8, 2, 'Le Soumissionnaire', basdepage2)

        
            
        wbk.save(fl) # for save le fichier
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        ctx = dict(context)
        ctx.update({'file': buf, 'file_name': context.get('file_name', 'test')})
        if context is None:
            context = {}
        data = {}
        res = self.read(cr, uid, ids, [], context=context)
        res = res and res[0] or {}
        data['form'] = res
        try:
            form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'apgebat_gao', 'xls_form')[1]
        except ValueError:
            form_id = False
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'gao.xls.report.file',
        'views': [(form_id, 'form')],
        'target': 'new',
        'context': ctx,
        }





    #generateur de rapport xls
    def print_dqexls(self, cr, uid, ids, context=None):
        ao=self.browse(cr, uid, ids)
        if ao.tender_type.code=="elec":
            #raise osv.except_osv(_('eir'), _(ao.tender_type.code))
            return self.print_dqexlselec(cr, uid, ids, context=context)
        else:
            return self.print_dqexlsgc(cr, uid, ids, context=context)

        

    def print_bpuxlsgc(self, cr, uid, ids, context=None):
        ao=self.browse(cr, uid, ids)

        fl = StringIO()
        if context is None: context = {}
        wbk = xlwt.Workbook(encoding="UTF-8")
        
        font = xlwt.Font()
        font.bold = True
        entete=xlwt.easyxf('font: name Calibri,height 320, color-index black, bold on;pattern: pattern solid, fore_colour gray25;align: vert centre, horiz centre')#fusionne des lignes (l1, l2, c1, c2)
        bordtop = xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top thin, right thin;align: wrap on, vert centre, horiz center')
        linevue = xlwt.easyxf('font: name Calibri,height 240, color-index black, bold on;border: top thin, right thin;')
        linechild = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin;align: wrap on')
        lastline = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin,bottom thin, left thin;align: wrap on')
        linechild1 = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin;align: wrap on, vert centre, horiz center')
        lastline1 = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin,bottom thin, left thin;align: wrap on, vert centre, horiz center')
        
        i=0
        for lots in ao.lot_id:
            i+=1
            vars()["lot{}".format(i)] = wbk.add_sheet(lots.code, cell_overwrite_ok=True)#creation de la feuille
            lot=eval("lot{}".format(i))

            lot.col(1).width= 500*38
            lot.col(2).width= 500*11
            lot.col(3).width= 500*28 #size de la column
            lot.col(0).width= 500*8
            

            #entete de la page
            lot.write_merge(0, 0, 0, 3, ao.name, entete)
            lot.write_merge(2, 2, 0, 3, "BORDEREAU DE PRIX UNITAIRE("+lots.code+")", xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;align: vert centre, horiz centre'))#fusionne des lignes (l1, l2, c1, c2)  

            #entete tableau
            lot.write(6, 0, "N°", bordtop)
            lot.write(6, 1, "DESIGNATION", bordtop)
            lot.write(6, 2, "MONTANT EN CHIFFRE", bordtop)
            lot.write(6, 3, "MONTANT EN LETTRES", bordtop)

            #si ligne parent
            estimation_id=self.pool.get('ap.gao.estim').search(cr, uid,[('tender_id', '=', ao.id), ('lot_id', '=', lots.id)], order='sequences' )
            o=0
            b=6
            for estim in self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id):
                o+=1
                b+=1
                if estim.type=="vue":
                    lot.write(b, 0, estim.code and estim.code or '', linevue)
                    lot.write(b, 1, estim.price_line, linevue)
                    lot.write(b, 2, "", linevue)
                    lot.write(b, 3, "", linevue)
                else:
                    #si ligne enfant
                    lot.write(b, 0, estim.code and estim.code or '', linechild)
                    lot.write(b, 1, estim.price_line, linechild)
                    lot.write(b, 2, estim.bpu, linechild1)
                    lot.write(b, 3, convNombre2lettres(int(estim.bpu)).lower(), linechild1)
                          
                if len(self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id))==o:
                    #derniere ligne
                    lot.write(b, 0, estim.code and estim.code or '', lastline)
                    lot.write(b, 1, estim.price_line, lastline)
                    lot.write(b, 2, estim.bpu, lastline1)
                    lot.write(b, 3, convNombre2lettres(int(estim.bpu)).lower(), lastline1)

        
        wbk.save(fl) # for save le fichier
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        ctx = dict(context)
        ctx.update({'file': buf, 'file_name': context.get('file_name', 'DEMO')})
        if context is None:
            context = {}
        data = {}
        res = self.read(cr, uid, ids, [], context=context)
        res = res and res[0] or {}
        data['form'] = res
        try:
            form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'apgebat_gao', 'xls_form')[1]
        except ValueError:
            form_id = False
        #raise osv.except_osv(_('euru'), _(context.get('file_name', 'DEMO')))
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'gao.xls.report.file',
        'views': [(form_id, 'form')],
        'target': 'new',
        'context': ctx,
        }


    def print_bpuxlselec(self, cr, uid, ids, context=None):
        ao=self.browse(cr, uid, ids)
        fl = StringIO()
        if context is None: context = {}
        wbk = xlwt.Workbook(encoding="UTF-8")
        
        font = xlwt.Font()
        font.bold = True
        entete=xlwt.easyxf('font: name Calibri,height 320, color-index black, bold on;pattern: pattern solid, fore_colour gray25;align: vert centre, horiz centre')#fusionne des lignes (l1, l2, c1, c2)
        bordtop = xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top thin, right thin, bottom thin;align: wrap on, vert centre, horiz center')
        linevue = xlwt.easyxf('font: name Calibri,height 240, color-index black, bold on;border: right thin;')
        linechild = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: right thin;align: wrap on')
        lastline = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin,bottom thin, left thin;align: wrap on')
        lastlinev = xlwt.easyxf('font: name Calibri,height 240, color-index black;border:top no_line, right thin,bottom thin, left thin;align: wrap on;pattern: pattern solid, fore_colour gray40;')
        lastline0 = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: right thin, bottom thin, left thin;align: wrap on')
        linechild1 = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin, bottom thin;align: wrap on, vert centre, horiz center')
        linechild1v = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top no_line, right thin;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour gray40;')
        lastline1 = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin,bottom thin, left thin;align: wrap on, vert centre, horiz center')
        
        i=0
        for lots in ao.lot_id:
            i+=1
            vars()["lot{}".format(i)] = wbk.add_sheet(lots.code, cell_overwrite_ok=True)#creation de la feuille
            lot=eval("lot{}".format(i))

            lot.col(0).width= 500*4
            lot.col(1).width= 500*25
            lot.col(2).width= 500*2
            lot.col(3).width= 500*25 #size de la column
            lot.col(4).width= 500*7
            lot.col(5).width= 500*25
            lot.col(6).width= 500*7
            

            #entete de la page
            lot.write_merge(0, 0, 0, 6, ao.name, entete)
            lot.write_merge(2, 2, 0, 6, "BORDEREAU DE PRIX UNITAIRE("+lots.code+")", xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;align: vert centre, horiz centre'))#fusionne des lignes (l1, l2, c1, c2)  

            #entete tableau
            lot.write_merge(4, 5, 0, 0, "N°", bordtop)
            lot.write_merge(4, 5, 1, 1, "DESIGNATION", bordtop)
            lot.write_merge(4, 5, 2, 2, "U", bordtop)
            lot.write_merge(4, 4, 3, 4, "FOURNITURES", bordtop)
            lot.write(5, 3, "PU en lettres", bordtop)
            lot.write(5, 4, "PU en chiffres", bordtop)
            lot.write_merge(4, 4, 5, 6, "TRAVAUX", bordtop)
            lot.write(5, 5, "PU en lettres", bordtop)
            lot.write(5, 6, "PU en chiffres", bordtop)

            #si ligne parent
            estimation_id=self.pool.get('ap.gao.estim').search(cr, uid,[('tender_id', '=', ao.id), ('lot_id', '=', lots.id)], order='sequences' )
            o=0
            b=5
            for estim in self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id):
                o+=1
                b+=1
                if estim.type=="vue":
                    lot.write(b, 0, estim.code and estim.code or '', linevue)
                    lot.write(b, 1, estim.price_line, linevue)
                    lot.write(b, 2, '', linevue)
                    lot.write(b, 3, "", linevue)
                    lot.write(b, 4, '', linevue)
                    lot.write(b, 5, "", linevue)
                    lot.write(b, 6, '', linevue)

                else:
                    #si ligne enfant
                    lot.write(b, 0, estim.code and estim.code or '', linechild)
                    lot.write(b, 1, estim.price_line, linechild)
                    lot.write(b, 2, estim.unite_id and estim.unite_id or '', xlwt.easyxf('font: name Calibri,height 240, color-index black;border: right thin;align: wrap on, vert centre, horiz center'))
                    if estim.bpu_f:
                        lot.write(b, 3, convNombre2lettres(int(estim.bpu_f)).lower(), linechild1)
                        lot.write(b, 4, estim.bpu_f, linechild1)
                    else:
                        lot.write(b, 3, '', linechild1v)
                        lot.write(b, 4, '', linechild1v)
                    if estim.bpu_t:
                        lot.write(b, 5, convNombre2lettres(int(estim.bpu_t)).lower(), linechild1)
                        lot.write(b, 6, estim.bpu_t, linechild1)
                    else:
                        lot.write(b, 5, '', linechild1v)
                        lot.write(b, 6, '', linechild1v)

                          
                if len(self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id))==o:
                    #derniere ligne
                    lot.write(b, 0, estim.code and estim.code or '', lastline0)
                    lot.write(b, 1, estim.price_line, lastline0)
                    lot.write(b, 2, estim.unite_id and estim.unite_id or '', lastline0)
                    if estim.bpu_f:
                        lot.write(b, 3, convNombre2lettres(int(estim.bpu_f)).lower(), lastline)
                        lot.write(b, 4, estim.bpu_f, lastline)
                    else:
                        lot.write(b, 3, '', lastlinev)
                        lot.write(b, 4, '', lastlinev)
                    if estim.bpu_t:
                        lot.write(b, 5, convNombre2lettres(int(estim.bpu_t)).lower(), lastline)
                        lot.write(b, 6, estim.bpu_t, lastline)
                    else:
                        lot.write(b, 5, '', lastlinev)
                        lot.write(b, 6, '', lastlinev)


                lot.normal_magn = 90
        wbk.save(fl) # for save le fichier
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        ctx = dict(context)
        ctx.update({'file': buf, 'file_name': context.get('file_name', 'DEMO')})
        if context is None:
            context = {}
        data = {}
        res = self.read(cr, uid, ids, [], context=context)
        res = res and res[0] or {}
        data['form'] = res
        try:
            form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'apgebat_gao', 'xls_form')[1]
        except ValueError:
            form_id = False
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'gao.xls.report.file',
        'views': [(form_id, 'form')],
        'target': 'new',
        'context': ctx,
        }




    def print_bpuxls(self, cr, uid, ids, context=None):
        ao=self.browse(cr, uid, ids)
        if ao.tender_type.code=="elec":
            #raise osv.except_osv(_('eir'), _(ao.tender_type.code))
            return self.print_bpuxlselec(cr, uid, ids, context=context)
        else:
            return self.print_bpuxlsgc(cr, uid, ids, context=context)




    def print_dsxlsgc(self, cr, uid, ids, context=None):
        ao=self.browse(cr, uid, ids)

        fl = StringIO()
        if context is None: context = {}
        wbk = xlwt.Workbook(encoding="UTF-8")
        
        font = xlwt.Font()
        font.bold = True
        entete=xlwt.easyxf('font: name Calibri,height 320, color-index black, bold on;align: vert centre, horiz left')#fusionne des lignes (l1, l2, c1, c2)
        bordtop = xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right thin;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour gray25;')
        bordtopt = xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right thin;align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_colour gray25;')
        bordtop2 = xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right medium, left medium;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour gray25;')
        bordtop1 = xlwt.easyxf('font: name Calibri,height 280, color-index red, bold on;border: top medium, bottom medium,  right medium, left medium;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour yellow;')
        lignes=xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top thin, bottom thin, right thin;')
        ligne1=xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top thin, bottom thin, right medium, left medium;')
        lignen=xlwt.easyxf('font: name Calibri,height 280, color-index black;border: top thin, bottom thin, right thin;')
        lignen1=xlwt.easyxf('font: name Calibri,height 280, color-index black;border: top thin, bottom thin, right medium, left medium;')
        
        lot= wbk.add_sheet('DS', cell_overwrite_ok=True)#creation de la feuille

        lot.col(1).width= 500*38
        lot.col(5).width= 500*11
        lot.col(3).width= 500*10 #size de la column
        lot.col(0).width= 500*4
        lot.col(2).width= 500*4
        lot.col(6).width= 500*10
        lot.col(7).width= 500*7
        lot.row(7).height_mismatch = True
        lot.row(7).height= 20*26
        

        #entete de la page
        lot.write_merge(0, 0, 0, 5, ao.name, entete)
        lot.write_merge(1, 1, 0, 2, 'Ville :', entete)
        lot.write_merge(2, 2, 0, 2, 'Ministère :', entete)
        lot.write_merge(3, 3, 0, 2, 'Site :', entete)
        lot.write_merge(4, 4, 0, 2, 'Ouvrage :', entete)


        lot.write_merge(5, 5, 0, 5, "ouvrage", xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;align: vert centre, horiz centre'))#fusionne des lignes (l1, l2, c1, c2)  

        #entete tableau
        lot.write(7, 0, "N°", bordtop)
        lot.write(7, 1, "DESIGNATION DES OUVRAGES", bordtop)
        lot.write(7, 2, "U", bordtop)
        lot.write(7, 3, "PU en FCFA", bordtop)
        lot.write(7, 4, "QTE", bordtop)
        lot.write(7, 5, "MONTANT HT", bordtop)
        lot.write(7, 6, "MONTANT DS", bordtop1)
        lot.write(7, 7, "TAUX", bordtop1)           
                        


        #si ligne parent
        i=0
        a=0
        b=7
        for lots in ao.lot_id:
            i+=1 
            
            
            lisum=[]
            estimation_id=self.pool.get('ap.gao.estim').search(cr, uid,[('tender_id', '=', ao.id), ('lot_id', '=', lots.id)], order='sequences' )
            nbr=len(estimation_id)
            
            for estim in self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id):

                
                if not a:
                    b+=1
                    lot.write(b, 0, '', lignes)
                    lot.write(b, 1, lots.code+'-'+lots.lot_name, lignes)
                    lot.write(b, 2, '', lignes)
                    lot.write(b, 3, '', lignes)
                    lot.write(b, 4, '', lignes)
                    lot.write(b, 5, '', lignes)
                    lot.write(b, 6, '', ligne1)
                    lot.write(b, 7, '', ligne1)
                a+=1
                b+=1
                if estim.type=="vue":
                #ligne de tableau 'parent'
                    lot.write(b, 0, estim.code and estim.code or '', lignen)
                    if estim.parent_id:
                        lot.write(b, 1, estim.price_line.lower(), lignen)
                    else:
                        lot.write(b, 1, estim.price_line.upper(), lignen)
                    lot.write(b, 2, '', lignen)
                    lot.write(b, 3, '', lignen)
                    lot.write(b, 4, '', lignen)
                    lot.write(b, 5, '', lignen)
                    lot.write(b, 6, '', lignen1)
                    lot.write(b, 7, '', lignen1)
                    
                            
                else:

                #ligne de tableau 'enfant'
                    lot.write(b, 0, estim.code and estim.code or '', lignen)
                    lot.write(b, 1, estim.price_line, lignen)
                    lot.write(b, 2, estim.unite_id and estim.unite_id or '', lignen)
                    lot.write(b, 3, estim.bpu, lignen)
                    lot.write(b, 4, estim.quantity, lignen)
                    lot.write(b, 5, xlwt.Formula("D"+str(b+1)+"*E"+str(b+1)), lignen)
                    lot.write(b, 6, estim.total_ds, lignen1)
                    lot.write(b, 7, xlwt.Formula("G"+str(b+1)+"/F"+str(b+1)+""), xlwt.easyxf('font: name Calibri,height 280, color-index black;border: top thin, bottom thin, right medium, left medium;', num_format_str='0.00%'))

                #ligne de tableau sous total 'parent'
                if nbr==a:
                    b+=1
                    lot.write(b, 0, '', bordtop)
                    lot.write(b, 1, 'TOTAL '+lots.code+ ' : '+lots.lot_name, bordtopt)
                    lot.write(b, 2, '', bordtop)
                    lot.write(b, 3, '', bordtop)
                    lot.write(b, 4, '', bordtop)
                    lot.write(b, 5, xlwt.Formula("SUM(F"+str(b-nbr+1)+":F"+str(b)+")"), bordtop)
                    lot.write(b, 6, xlwt.Formula("SUM(G"+str(b-nbr+1)+":G"+str(b)+")"), bordtop2)
                    lot.write(b, 7, xlwt.Formula("G"+str(b+1)+"/F"+str(b+1)+""), xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right medium, left medium;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour gray25;', num_format_str='0.00%'))
                    lisum.append(b+1)
                    a=0
                    nbr=0


            #ligne de tableau le footer
        

        
        wbk.save(fl) # for save le fichier
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        ctx = dict(context)
        ctx.update({'file': buf, 'file_name': context.get('file_name', 'DEMO')})
        if context is None:
            context = {}
        data = {}
        res = self.read(cr, uid, ids, [], context=context)
        res = res and res[0] or {}
        data['form'] = res
        try:
            form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'apgebat_gao', 'xls_form')[1]
        except ValueError:
            form_id = False
        #raise osv.except_osv(_('euru'), _(context.get('file_name', 'DEMO')))
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'gao.xls.report.file',
        'views': [(form_id, 'form')],
        'target': 'new',
        'context': ctx,
        }




    def print_dsxlselec(self, cr, uid, ids, context=None):
        ao=self.browse(cr, uid, ids)

        fl = StringIO()
        if context is None: context = {}
        wbk = xlwt.Workbook(encoding="UTF-8")
        
        font = xlwt.Font()
        font.bold = True
        entete=xlwt.easyxf('font: name Calibri,height 320, color-index black, bold on;align: vert centre, horiz left')#fusionne des lignes (l1, l2, c1, c2)
        bordtop = xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right thin;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour gray25;')
        bordtopt = xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right thin;align: wrap on, vert centre, horiz left;pattern: pattern solid, fore_colour gray25;')
        bordtop2 = xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right medium, left medium;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour gray25;')
        bordtop1 = xlwt.easyxf('font: name Calibri,height 280, color-index red, bold on;border: top medium, bottom medium,  right medium, left medium;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour yellow;')
        lignes=xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top thin, bottom thin, right thin;')
        ligne1=xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top thin, bottom thin, right medium, left medium;')
        lignen=xlwt.easyxf('font: name Calibri,height 280, color-index black;border: top thin, bottom thin, right thin;')
        lignenv=xlwt.easyxf('font: name Calibri,height 280, color-index black;border: right thin;pattern: pattern solid, fore_colour gray_ega;')
        lignen1=xlwt.easyxf('font: name Calibri,height 280, color-index black;border: top thin, bottom thin, right medium, left medium;')
        lignen1v=xlwt.easyxf('font: name Calibri,height 280, color-index black;border: right medium, left medium;pattern: pattern solid, fore_colour gray_ega;')
        
        lot= wbk.add_sheet('DS', cell_overwrite_ok=True)#creation de la feuille

        lot.col(0).width= 500*4
        lot.col(1).width= 500*36
        lot.col(2).width= 500*3
        lot.col(3).width= 500*4
        lot.col(4).width= 500*7 #size de la column
        lot.col(5).width= 500*9
        lot.col(6).width= 500*10
        lot.col(7).width= 500*7
        lot.col(8).width= 500*7
        lot.col(9).width= 500*9
        lot.col(10).width= 500*10
        
        lot.row(7).height_mismatch = True
        lot.row(7).height= 20*26
        

        #entete de la page
        lot.write_merge(0, 0, 0, 11, ao.name, entete)
        lot.write_merge(1, 1, 0, 2, 'Ville :', entete)
        lot.write_merge(2, 2, 0, 2, 'Ministère :', entete)
        lot.write_merge(3, 3, 0, 2, 'Site :', entete)
        lot.write_merge(4, 4, 0, 2, 'Ouvrage :', entete)


        lot.write_merge(5, 5, 0, 11, "ouvrage", xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;align: vert centre, horiz centre'))#fusionne des lignes (l1, l2, c1, c2)  

        #entete tableau
        lot.write_merge(7, 8, 0, 0, "N°", bordtop)
        lot.write_merge(7, 8, 1, 1, "DESIGNATION DES OUVRAGES", bordtop)
        lot.write_merge(7, 8, 2, 2, "U", bordtop)
        lot.write_merge(7, 8, 3, 3, "QTE", bordtop)
        lot.write_merge(7, 7, 4, 7, "FOURNITURES", bordtop)
        lot.write(8, 4, "PU en FCFA", bordtop)
        lot.write(8, 5, "MONTANT HT", bordtop)
        lot.write(8, 6, "MONTANT DS", bordtop1)
        lot.write(8, 7, "TAUX", bordtop1)
        lot.write_merge(7, 7, 8, 11, "TRAVAUX", bordtop)
        lot.write(8, 8, "PU en FCFA", bordtop)
        lot.write(8, 9, "MONTANT HT", bordtop)
        lot.write(8, 10, "MONTANT DS", bordtop1)
        lot.write(8, 11, "TAUX", bordtop1) 

                        


        #si ligne parent
        i=0
        a=0
        b=8
        for lots in ao.lot_id:
            i+=1 
            
            
            lisum=[]
            estimation_id=self.pool.get('ap.gao.estim').search(cr, uid,[('tender_id', '=', ao.id), ('lot_id', '=', lots.id)], order='sequences' )
            nbr=len(estimation_id)
            for estim in self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id):

                
                if not a:
                    b+=1
                    lot.write(b, 0, '', lignes)
                    lot.write(b, 1, lots.code+'-'+lots.lot_name, lignes)
                    lot.write(b, 2, '', lignes)
                    lot.write(b, 3, '', lignes)
                    lot.write(b, 4, '', lignes)
                    lot.write(b, 5, '', lignes)
                    lot.write(b, 6, '', ligne1)
                    lot.write(b, 7, '', ligne1)
                    lot.write(b, 8, '', lignes)
                    lot.write(b, 9, '', lignes)
                    lot.write(b, 10, '', ligne1)
                    lot.write(b, 11, '', ligne1)
                a+=1
                b+=1
                if estim.type=="vue":
                #ligne de tableau 'parent'
                    lot.write(b, 0, estim.code and estim.code or '', lignen)
                    if estim.parent_id:
                        lot.write(b, 1, estim.price_line.lower(), lignen)
                    else:
                        lot.write(b, 1, estim.price_line.upper(), lignen)
                    lot.write(b, 2, '', lignen)
                    lot.write(b, 3, '', lignen)
                    lot.write(b, 4, '', lignen)
                    lot.write(b, 5, '', lignen)
                    lot.write(b, 6, '', lignen1)
                    lot.write(b, 7, '', lignen1)
                    lot.write(b, 8, '', lignen)
                    lot.write(b, 9, '', lignen)
                    lot.write(b, 10, '', lignen1)
                    lot.write(b, 11, '', lignen1)
                    
                            
                else:

                #ligne de tableau 'enfant'
                    lot.write(b, 0, estim.code and estim.code or '', lignen)
                    lot.write(b, 1, estim.price_line, lignen)
                    lot.write(b, 2, estim.unite_id and estim.unite_id or '', lignen)
                    lot.write(b, 3, estim.quantity, lignen)
                    if estim.bpu_f:
                        lot.write(b, 4, estim.bpu_f, lignen)
                        lot.write(b, 5, xlwt.Formula("D"+str(b+1)+"*E"+str(b+1)), lignen)
                        lot.write(b, 6, estim.total_dsf, lignen1)
                        lot.write(b, 7, xlwt.Formula("G"+str(b+1)+"/F"+str(b+1)+""), xlwt.easyxf('font: name Calibri,height 280, color-index black;border: top thin, bottom thin, right medium, left medium;', num_format_str='0.00%'))
                    else:
                        lot.write(b, 4, '', lignenv)
                        lot.write(b, 5, '', lignenv)
                        lot.write(b, 6, '', lignen1v)
                        lot.write(b, 7, '', xlwt.easyxf('font: name Calibri,height 280, color-index black;border: right medium, left medium;pattern: pattern solid, fore_colour gray_ega;', num_format_str='0.00%'))
                    if estim.bpu_t:
                        lot.write(b, 8, estim.bpu_t, lignen)
                        lot.write(b, 9, xlwt.Formula("I"+str(b+1)+"*D"+str(b+1)), lignen)
                        lot.write(b, 10, estim.total_dst, lignen1)
                        lot.write(b, 11, xlwt.Formula("K"+str(b+1)+"/J"+str(b+1)+""), xlwt.easyxf('font: name Calibri,height 280, color-index black;border: top thin, bottom thin, right medium, left medium;', num_format_str='0.00%'))
                    else:
                        lot.write(b, 8, '', lignenv)
                        lot.write(b, 9, '', lignenv)
                        lot.write(b, 10, '', lignen1v)
                        lot.write(b, 11, '', xlwt.easyxf('font: name Calibri,height 280, color-index black;border: right medium, left medium;pattern: pattern solid, fore_colour gray_ega;', num_format_str='0.00%'))
                    
                #ligne de tableau sous total 'parent'
                if nbr==a:
                    b+=1
                    lot.write(b, 0, '', bordtop)
                    lot.write(b, 1, 'TOTAL '+lots.code+ ' : '+lots.lot_name, bordtopt)
                    lot.write(b, 2, '', bordtop)
                    lot.write(b, 3, '', bordtop)
                    lot.write(b, 4, '', bordtop)
                    lot.write(b, 5, xlwt.Formula("SUM(F"+str(b-nbr+1)+":F"+str(b)+")"), bordtop)
                    lot.write(b, 6, xlwt.Formula("SUM(G"+str(b-nbr+1)+":G"+str(b)+")"), bordtop2)
                    lot.write(b, 7, xlwt.Formula("G"+str(b+1)+"/F"+str(b+1)+""), xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right medium, left medium;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour gray25;', num_format_str='0.00%'))
                    lot.write(b, 8, '', bordtop)
                    lot.write(b, 9, xlwt.Formula("SUM(J"+str(b-nbr+1)+":J"+str(b)+")"), bordtop)
                    lot.write(b, 10, xlwt.Formula("SUM(K"+str(b-nbr+1)+":K"+str(b)+")"), bordtop2)
                    lot.write(b, 11, xlwt.Formula("K"+str(b+1)+"/J"+str(b+1)+""), xlwt.easyxf('font: name Calibri,height 280, color-index black, bold on;border: top medium, bottom medium, right medium, left medium;align: wrap on, vert centre, horiz center;pattern: pattern solid, fore_colour gray25;', num_format_str='0.00%'))
                    lisum.append(b+1)
                    a=0
                    nbr=0


            #ligne de tableau le footer
        

        lot.normal_magn = 80
        wbk.save(fl) # for save le fichier
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        ctx = dict(context)
        ctx.update({'file': buf, 'file_name': context.get('file_name', 'DEMO')})
        if context is None:
            context = {}
        data = {}
        res = self.read(cr, uid, ids, [], context=context)
        res = res and res[0] or {}
        data['form'] = res
        try:
            form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'apgebat_gao', 'xls_form')[1]
        except ValueError:
            form_id = False
        #raise osv.except_osv(_('euru'), _(context.get('file_name', 'DEMO')))
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'gao.xls.report.file',
        'views': [(form_id, 'form')],
        'target': 'new',
        'context': ctx,
        }

    def print_dsxls(self, cr, uid, ids, context=None):
        ao=self.browse(cr, uid, ids)
        if ao.tender_type.code=="elec":
            #raise osv.except_osv(_('eir'), _(ao.tender_type.code))
            return self.print_dsxlselec(cr, uid, ids, context=context)
        else:
            return self.print_dsxlsgc(cr, uid, ids, context=context)

        



class ap_gao_attr(osv.osv):
    _name = 'ap.gao.attr'
    _order = 'code asc'
    _rec_name='code'


    _columns = {
        'code': fields.char('Batch number', size=10, required=True),  #to do: interdire les caractere speciaux dans ce champ car il pose un probleme a la generation excel
        'lot_name': fields.char('Titled lot of tender'),
        'caution': fields.float('interim bail', required=True),
        'credit_line': fields.float('credit line'),
        'tender_id': fields.integer('tender_id'),
        'date_caution': fields.date('interim bail deadline'),
        'dqe': fields.float('DQE'),
        'dqe_f': fields.float('DQE supplies'),
        'dqe_t': fields.float('DQE works'),
        'project_id': fields.many2one('project.project', 'project', readonly=True),
        
    }







class ap_gao_estim(osv.osv):
    _name = 'ap.gao.estim'
    _order = 'price_line asc'
    _rec_name= 'price_line'


    @api.one
    @api.depends('mat_line.mat_total', 'mat_line.type', 'mat_line1.mat_total', 'mat_line1.type', 'coef', 'coef_f', 'coef_t', 'quantity', 'price_line', 'mat_line1.coef_line')
    def _compute_amount(self):
        trav=[]
        four=[]
        self.project_id=self.pool.get('ap.gao').browse(self._cr,  self._uid, [self.tender_id]).project_id.id
        if self.type_k:
            self.pu_ds = sum(line.mat_total for line in self.mat_line1)
            for line in self.mat_line1:
                if line.type=='trav':
                    trav.append(line.mat_total)
                if line.type=='four':
                    four.append(line.mat_total)
            self.pu_dsf = sum(four)
            self.pu_dst = sum(trav)
        else:
            self.pu_ds = sum(line.mat_total for line in self.mat_line)
            for line in self.mat_line:
                if line.type=='trav':
                    trav.append(line.mat_total)
                if line.type=='four':
                    four.append(line.mat_total)
            self.pu_dsf = sum(four)
            self.pu_dst = sum(trav)
        if self.type_k:
            tra=[]
            fou=[]
            for line in self.mat_line1:
                if line.type=='trav':
                    tra.append(line.coef_total)
                if line.type=='four':
                    fou.append(line.coef_total)
            self.bpu_f = sum(fou)
            self.bpu_t = sum(tra)
        else:
            self.bpu_f = self.pu_dsf*self.coef_f
            self.bpu_t = self.pu_dst*self.coef_t
        self.total_dsf = self.pu_dsf*self.quantity
        self.total_dst = self.pu_dst*self.quantity
        self.total_bpuf = self.bpu_f*self.quantity
        self.total_bput = self.bpu_t*self.quantity
        self.ecart_f = self.total_bpuf-self.total_dsf
        self.ecart_t = self.total_bput-self.total_dst
        typ=self.pool.get('ap.gao').browse(self._cr,  self._uid, [self.tender_id]).tender_type.code
        if typ=='elec':
            self.bpu = self.bpu_t+self.bpu_f
            self.total_ds = self.total_dsf+self.total_dst
            self.total_bpu = self.total_bput+self.total_bpuf
            self.ecart = self.total_bpu-self.total_ds
            idsi=self.search([('lot_id', '=', self.lot_id.id)])
            self.pool.get('ap.gao.attr').write(self._cr,  self._uid, [self.lot_id.id], {'dqe':sum(line.total_bpu for line in idsi), 'dqe_f': sum(line.total_bpuf for line in idsi), 'dqe_t': sum(line.total_bput for line in idsi)})
        else:
            if self.type_k:
                self.bpu = sum(line.coef_total for line in self.mat_line1)
            else:
                self.bpu = self.pu_ds*self.coef
            self.total_ds = self.pu_ds*self.quantity
            self.total_bpu = self.bpu*self.quantity
            self.ecart = self.total_bpu-self.total_ds

            idsi=self.search([('lot_id', '=', self.lot_id.id)])
            self.pool.get('ap.gao.attr').write(self._cr,  self._uid, [self.lot_id.id], {'dqe':sum(line.total_bpu for line in idsi)})

        if self.total_bpu and self.total_ds:
            self.rent = ((self.total_bpu-self.total_ds)/self.total_ds)*100
        #projet=self.pool.get('ap.gao').browse(self._cr,  self._uid, [self.tender_id]).project_id
        #if projet:
         #   self.project_id=projet.id



    _columns = {
        'type': fields.selection([('draft','Draft'), ('vue','Vue'),('child','Details')],'Type', required=True),
        'sequences': fields.integer('Item N°', required=True, help="the display sequence."),
        'parent_id': fields.many2one('ap.gao.estim', 'Parent', ondelete="cascade", domain="[('type','=','vue')]"),
        'code': fields.char('Batch number', help="the allocation batch number."),
        'lot_id': fields.many2one('ap.gao.attr', 'Lot of tender', required=True, help="Lot award."),
        'price_line': fields.char('Entitled', required=True, help="the name of the line price."),
        'quantity': fields.float('Qty', help="Quantity"),
        'pu_ds': fields.float(string='Unit price DS', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="The unit price DS of line.", track_visibility='always'),
        'pu_dsf': fields.float(string='Unit price DS supplies', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="The unit price DS of line.", track_visibility='always'),
        'pu_dst': fields.float(string='Unit price DS works', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="The unit price DS of line.", track_visibility='always'),
        'bpu': fields.float(string='Unit Price BPU', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The unit price BPU of line.", track_visibility='always'),
        'bpu_f': fields.float(string='Unit Price BPU supplies', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The unit price BPU of line.", track_visibility='always'),
        'bpu_t': fields.float(string='Unit Price BPU works', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The unit price BPU of line.", track_visibility='always'),
        'ecart': fields.float('Gap', help="Amount DQE - Amount DS.", track_visibility='always', store=True, readonly=True, compute='_compute_amount',),
        'ecart_f': fields.float('Gap supplies', help="Amount DQE - Amount DS.", track_visibility='always', store=True, readonly=True, compute='_compute_amount',),
        'ecart_t': fields.float('Gap works', help="Amount DQE - Amount DS.", track_visibility='always', store=True, readonly=True, compute='_compute_amount',),
        'coef': fields.float('K', help="    Amount DQE\n--------------- x 100\n    Amount DS.", track_visibility='always'),
        'coef_f': fields.float('K', help="    Amount DQE\n--------------- x 100\n    Amount DS.", track_visibility='always'),
        'coef_t': fields.float('K', help="    Amount DQE\n--------------- x 100\n    Amount DS.", track_visibility='always'),
        'rent': fields.float('Profit.', help="The profitability of line\n\n  Amount DQE - Amount DS\n----------------------- x 100\n     Amount DS.", track_visibility='always', store=True, readonly=True, compute='_compute_amount',),
        'tender_id': fields.integer('tender_id'),
        'unite_id': fields.char('UoM', size=6),

        'total_ds': fields.float(string='Amount DS', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The amount total DS of price line.", track_visibility='always'),
        'total_dsf': fields.float(string='Amount DS supplies', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The amount total DS of price line.", track_visibility='always'),
        'total_dst': fields.float(string='Amount DS works', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The amount total DS of price line.", track_visibility='always'),
        'total_bpu': fields.float(string='Amount DQE ', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The amount total BPU of price line.", track_visibility='always'),
        'total_bpuf': fields.float(string='Amount DQE supplies', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The amount total BPU of price line.", track_visibility='always'),
        'total_bput': fields.float(string='Amount DQE works', digits=dp.get_precision('Account'),
        store=True, compute='_compute_amount', help="The amount total BPU of price line.", track_visibility='always'),
        #'amount_total': fields.function(_amount_all_wrapper, string='Total',
         #   store={
         #       'ap.gao.estim': (lambda self, cr, uid, ids, c={}: ids, ['mat_line'], 10),
         #       'ap.gao.mat': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
         #   }, multi='sums', help="The amount total of material's line.", track_visibility='always'),
        'mat_line': fields.one2many('ap.gao.mat', 'estim_id', string='Materials'),
        'mat_line1': fields.one2many('ap.gao.mat', 'estim_id', string='Materials'),
        'filter': fields.boolean('filter_for_purchase'),
        'project_id': fields.many2one('project.project', 'project', store=True, compute='_compute_amount', track_visibility='always'),
        'type_k': fields.boolean('Check to use the coefficient k in the material lines')
        

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
    @api.depends('quantity', 'pu_composant', 'coef_line')
    def _compute_amount(self):
        self.mat_total = self.quantity*self.pu_composant
        self.coef_total = self.mat_total*self.coef_line

    _columns = {
        'quantity': fields.float('Quantity'),
        'pu_composant': fields.float('Unit price'),
        'unite_id': fields.char('Product UoM', size=6),
        'product_id': fields.many2one('product.template', 'equipments / materials'),
        'mat_total': fields.float(string='Amount Total', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', help="Amount total of materials line.", track_visibility='always'),
        'estim_id': fields.integer('estim'),
        'type': fields.selection([('trav', 'Work'), ('four', 'Supplies')], 'type'), #champ concernant les projets de type electricité
        'coef_line': fields.float('K', track_visibility='always'),
        'coef_total': fields.float(string='Line DQE', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always'),
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
        'estimation_id1': fields.one2many('ap.gao.estim', 'project_id', string='Estimates'),
        'doc_rec': fields.one2many('ir.attachment', 'projectdocrec_id', 'Documents received'),
        'doc_send': fields.one2many('ir.attachment', 'projectdocsen_id', 'Documents sended'),
        'date_begin': fields.date('Date of start of work'),
        'date_end': fields.date('Date of Completion'),
        'delai': fields.char('Completion time', readonly=True),
        'note': fields.text('Description'),
        'Provisional_date': fields.date('Date of provisional receipt'),
        'final_date': fields.date('Date of final acceptance'),
        'tender_type': fields.char('Type', readonly=True),


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

