# -*- coding: utf-8 -*-
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

        if context.get('file'):
            res.update({'file': context['file']})
        return res


    _columns = {
        'file': fields.binary('File'),
        'file_name': fields.char('File Name', size=64),
    }



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





    #generateur de rapport xls
    def print_dqexls(self, cr, uid, ids, context=None):
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
        entete=xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;pattern: pattern solid, fore_colour dark_green_ega ;border: bottom thin')#fusionne des lignes (l1, l2, c1, c2)
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
                    lot.write(b, 0, estim.code, new_style6)
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
                    lot.write(b, 0, estim.code, new_style6en)
                    lot.write(b, 1, estim.price_line, new_style6en)
                    lot.write(b, 2, estim.quantity, new_style6en)
                    lot.write(b, 3, estim.unite_id.name, new_style6en)
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

    


    def print_bpuxls(self, cr, uid, ids, context=None):
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
                    lot.write(b, 0, estim.code, linevue)
                    lot.write(b, 1, estim.price_line, linevue)
                    lot.write(b, 2, "", linevue)
                    lot.write(b, 3, "", linevue)
                else:
                    #si ligne enfant
                    lot.write(b, 0, estim.code, linechild)
                    lot.write(b, 1, estim.price_line, linechild)
                    lot.write(b, 2, estim.bpu, linechild1)
                    lot.write(b, 3, convNombre2lettres(int(estim.bpu)).lower(), linechild1)
                          
                if len(self.pool.get('ap.gao.estim').browse(cr, uid, estimation_id))==o:
                    #derniere ligne
                    lot.write(b, 0, estim.code, lastline)
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
        return {
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'gao.xls.report.file',
        'views': [(form_id, 'form')],
        'target': 'new',
        'context': ctx,
        }



class ap_gao_attr(osv.osv):
    _name = 'ap.gao.attr'
    _order = 'code asc'
    _rec_name='code'


    _columns = {
        'code': fields.char('Batch number', size=20),  #to do: interdire les caractere speciaux dans ce champ car il pose un probleme a la generation excel
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

