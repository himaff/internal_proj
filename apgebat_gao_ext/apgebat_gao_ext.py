# -*- coding: utf-8 -*-

import xlwt
from cStringIO import StringIO
import base64
import openerp
from openerp import api
from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import datetime
import calendar
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)
#from openerp.http import request
#from openerp import http
#import webbrowser
# you can find here: Request, OpenERPSession, id of action and other parameters


class apgebat_attachment_list(osv.osv):
    _name='apgebat.attachment.list'

    _columns = {

        'name': fields.char('Untitled attachement', required=True),
        'date_planned': fields.date('predicted date'),
        'project_id': fields.many2one('project.project', 'project'),
    }

    _defaults = {
        'date_planned': time.strftime('%Y-%m-%d',time.localtime()),
    }

class apgebat_attachment(osv.osv):
    _name='apgebat.attachment' 

    #pour save les type parent et aussi ajouter les attachements aux lots
  #  @api.one
  #  @api.depends('name')
   # def _compute_amount(self):
   #     self.amount_untaxed =

    #@api.one
    @api.onchange('project_id')
    def define_situation(self):
        if self.project_id:
            lot_ids=[]
            for lot in self.project_id.lot_id:
                lot_ids.append(lot.id)
            att_ids=[]
            for att in self.project_id.att_list:
                att_ids.append(att.id)
            self.lot_id='' 
            self.attachement_id=''
            return {'domain':{'lot_id':[('id','in',lot_ids)], 'attachement_id': [('id', 'in', att_ids)]}}

    @api.onchange('attachement_id', 'lot_id')
    def define_situation2(self):
        if self.lot_id or self.attachement_id:
            if not self.project_id:
                raise osv.except_osv(_('Project value'), _('Select a project primarily'))
        else:
            return {'domain':{'lot_id':[('id','=', [0])], 'attachement_id': [('id', '=', [0])]}}

    @api.one
    @api.depends('attachement_id', 'lot_id')
    def _get_name(self):
        #raise osv.except_osv(_('ur'), _(self.id))
        ida=self.search([('attachement_id', '=', self.attachement_id.id ), ('project_id', '=', self.project_id.id ), ('lot_id', '=', self.lot_id.id), ('id', '!=', self.id)])
        
        if ida:
            raise osv.except_osv(_('Lot selected'), _('This Lot is already for this attachment, please select other for your attachment define'))
        else:
            self.name = self.lot_id.code+'-'+self.attachement_id.name
      


    _columns = {

        'attachement_id': fields.many2one('apgebat.attachment.list','Untitled attachement', required=True),
        'lot_id': fields.many2one('ap.gao.attr', 'Lot', required=True),
        'date_planned': fields.date('predicted date'),
        'name': fields.char('name', compute=_get_name, store=True),
        'state': fields.selection([('draft', 'Draft'), ('sent', 'Envoyé'),('end', 'Finish'),('invoice', 'Invoiced')], 'State'),
        'project_id': fields.many2one('project.project', 'project', required=True),
        'line_attach': fields.one2many('apgao.line.att', 'att_id', ondelete="cascade"),
        'att_pos': fields.integer('Position'),
        
    }

    _defaults = {
        'date_planned': time.strftime('%Y-%m-%d',time.localtime()),
        'state': 'draft',
    }

    def send(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids,{'state': 'sent'})

    def valid(self, cr, uid, ids, context=None):
        att=self.browse(cr, uid, ids)
        while -1<1:
            att_ids=self.search(cr, uid, [('project_id', '=', att.project_id.id), ('state', 'in', ['end', 'invoice']), ('att_pos', '=', att.att_pos)])
            if att_ids:
                self.write(cr, uid, ids,{'att_pos': att.att_pos+1})
            else:
                 return self.write(cr, uid, ids,{'state': 'end'})


    def _create_project(self, cr, uid, ids, inv_values, context=None):
        inv_obj = self.pool.get('account.invoice')
        inv_id = inv_obj.create(cr, uid, inv_values, context=context)
        self.write(cr, uid, ids, {'state': 'invoice'})

        #creation des lignes de facture lié a l'aatachement.
        attach=self.browse(cr, uid, ids)
        compte=self.pool.get('gao.project.account.conf').browse(cr, uid, [1])
        total=0
        market=0
        val={}
        code={}
        seq={}#permet de gerer le positionnement sur les lignes de factures
        for ligne in attach.line_attach:
            if ligne.montant_m:
                total+=ligne.montant_m
            market+=ligne.total_dqe

        #attachement 
        val[attach.attachement_id.name]=total
        code[attach.attachement_id.name]=compte.line_attach.id
        seq[attach.attachement_id.name]=1
        #taux d'avance de demarrage
        t_avance=attach.project_id.avance
        avance=(total*t_avance)/100
        val['Avance de '+ str(t_avance) + '%']=avance*-1
        code['Avance de '+ str(t_avance) + '%']=compte.advance.id
        seq['Avance de '+ str(t_avance) + '%']=2
        #retenue de garanti
        t_retenu=attach.project_id.garanti
        retenu=(total*t_retenu)/100
        val['Retenue de garantie de '+ str(t_retenu) + '%']=retenu*-1
        code['Retenue de garantie de '+ str(t_retenu) + '%']=compte.retenu.id
        seq['Retenue de garantie de '+ str(t_retenu) + '%']=3
        #risques
        t_risque=attach.project_id.risque
        risque=(total*t_risque)/100
        val['Risques de '+ str(t_risque) + '%']=risque*-1
        code['Risques de '+ str(t_risque) + '%']=compte.risk.id
        seq['Risques de '+ str(t_risque) + '%']=4

        #retard
        if datetime.datetime.strptime(attach.date_planned,'%Y-%m-%d') < datetime.datetime.strptime(time.strftime('%Y-%m-%d',time.localtime()), "%Y-%m-%d"):
            t_retard=attach.project_id.retard
            retard=(total*t_retard)/100
            val['Pénalités de retard de '+ str(t_retard) + '%']=retard*-1
            code['Pénalités de retard de '+ str(t_retard) + '%']=compte.penalite.id
            seq['Pénalités de retard de '+ str(t_retard) + '%']=5
        i=1
        #for cle,value in seq.items():
        for nam in sorted(val, key=seq.__getitem__):
            #raise osv.except_osv(_('eirri'), _(i)) 
            if val[nam]:
                if code[nam]:
                    account=code[nam]
                    self.pool.get('account.invoice.line').create(cr, uid, {'name': nam, 'quantity': 1, 'price_unit':val[nam], 'price_subtotal':val[nam], 'invoice_id':inv_id, 'account_id': account})
                else:
                    self.pool.get('account.invoice.line').create(cr, uid, {'name': nam, 'quantity': 1, 'price_unit':val[nam], 'price_subtotal':val[nam], 'invoice_id':inv_id})
                
                i+=1

        #raise osv.except_osv(_('eerr'), _(inv_id))
        market_TTC=market + market*0.18
        advance_TTC=((market * t_avance)/100)+((market*t_avance*0.18)/100)
        cr.execute('''UPDATE account_invoice SET market_value=%s, advance_begin=%s WHERE id=%s''', (market_TTC,advance_TTC, inv_id))
        #inv_obj.write(cr, uid, inv_id, {'market_value': market_TTC, 'advance_begin': advance_TTC})    
        return inv_id

    def create_invoice(self, cr, uid, ids, context=None):
        attach=self.browse(cr, uid, ids)
        
        client=attach.project_id.partner_id.id
        compte_client=attach.project_id.partner_id.property_account_receivable.id
        journal_id=self.pool.get('account.journal').search(cr, uid, [('type', '=', 'sale')])
        journal=journal_id[0]
        origin='AO/'+ attach.project_id.tender_id.code
        types='out_invoice'
        #valeur du marché
        #montant de lavance de demarrage
        inv_values = {
            'partner_id': client,
            'account_id': compte_client,
            'journal_id': journal,
            'user_id': uid,
            'origin': origin,
            'type': types,
            'att_id': ids[0],
            'project_id': attach.project_id.id,
            'comment': attach.attachement_id.name,
            'lot_id': attach.lot_id.id
            
        }

        inv_ids = self._create_project(cr, uid, ids, inv_values, context=context)

        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_form')
        form_id = form_res and form_res[1] or False
        return {
            'name': _('Tender project'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'res_id': inv_ids,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
        }




    def importer(self, cr, uid, ids, context=None):
    	att=self.browse(cr, uid, ids, context=context)
    	attids = self.pool.get('apgao.line.att').search(cr, uid,[('att_id', '=', ids[0])])
        attenfids = self.pool.get('ap.gao.ext.mat').search(cr, uid,[('att_line_id', 'in', attids)])
        self.pool.get('ap.gao.ext.mat').unlink(cr, uid, attenfids)
    	self.pool.get('apgao.line.att').unlink(cr, uid, attids)
        atts_prec= self.search(cr, uid,[('project_id', '=', att.project_id.id),('state','in', ['end','invoice'])])
        #recherche des bons de commande concernant le projet
        bc_ids=self.pool.get('purchase.order').search(cr, uid,[('project_id', '=', att.project_id.id),('state','in', ['approved','done'])])
        ligne_qte={}
        #pour chaque bon de commande approuved on recupere la facture concerné et on verifie quel est validé
        for bc in self.pool.get('purchase.order').browse(cr, uid, bc_ids, context=context):
            fact_id=self.pool.get('account.invoice').search(cr, uid,[('origin', '=', bc.name),('state','in', ['open','paid'])])
            
            if fact_id:
                #si la facture est validé on recupere les lignes du bon de commande
                for bc_line in self.pool.get('purchase.order.line').search(cr, uid,[('order_id', '=', bc.id)]):
                    
                    line=self.pool.get('purchase.order.line').browse(cr, uid, bc_line, context=context)
                  
                    for lot in line.internal_line_id.lot_id:
                        
                        if att.lot_id.id==lot.id:
                            #pour chaque ligne fait la somme des qté commandé
                            pu=0
                            if line.lot_ligne in ligne_qte:
                                #aussi on recupere le prix unitaire du produit lors de la creation de LAO
                                ligneid= self.pool.get('ap.gao.estim').search(cr, uid,[('project_id', '=', att.project_id.id), ('price_line', '=', line.lot_ligne)])
                                for mat in self.pool.get('ap.gao.estim').browse(cr, uid, ligneid, context=context).mat_line:
                                    if mat.product_id.id == line.product_id.id:
                                        matid=self.pool.get('ap.gao.ext.mat').search(cr, uid,[('estim', 'in', ligneid), ('product_id','=', mat.product_id.id), ('att_line_id','=', False)])
                                        if matid:
                                            pu=mat.pu_composant
                                            val=self.pool.get('ap.gao.ext.mat').browse(cr, uid, matid)
                                            self.pool.get('ap.gao.ext.mat').write(cr, uid, matid, {'qte_cons' : val.qte_cons+line.product_qty, 'taux': (val.qte_cons+line.product_qty*pu)/mat.mat_total})
                                                                    
                                        else:
                                            if mat.product_id.name == line.name:
                                                pu=mat.pu_composant
                                                self.pool.get('ap.gao.ext.mat').create(cr, uid, { 'product_id': mat.product_id.id, 'quantity': mat.quantity, 'unite_id': mat.unite_id.id, 'qte_cons' : line.product_qty, 'taux': (line.product_qty*pu)/mat.mat_total, 'estim': ligneid[0] })
                                            
                                #si la ligne a deja été quantifié alors on ajoute les nouvelles quantité la concernant
                                ligne_qte[line.lot_ligne]+=line.product_qty*pu
                            else:

                                ligneid= self.pool.get('ap.gao.estim').search(cr, uid,[('project_id', '=', att.project_id.id), ('price_line', '=', line.lot_ligne)])
                                for mat in self.pool.get('ap.gao.estim').browse(cr, uid, ligneid, context=context).mat_line:
                                    if mat.product_id.name == line.name:
                                        pu=mat.pu_composant
                                        self.pool.get('ap.gao.ext.mat').create(cr, uid, { 'product_id': mat.product_id.id, 'quantity': mat.quantity, 'unite_id': mat.unite_id.id, 'qte_cons' : line.product_qty, 'taux': (line.product_qty*pu)/mat.mat_total, 'estim': ligneid[0] })
                                ligne_qte[line.lot_ligne]=line.product_qty*pu
                        #raise osv.except_osv(_('Error!'), _(ligne_qte))
        #dj
        #raise osv.except_osv(_('test'), _(ligne_qte))
        if atts_prec:

            #raise osv.except_osv(_('Error!'), _(tuple(atts_prec)))
            #corriger toute cette zone selon le calcul du bas en else
            cr.execute('''SELECT id, max(att_pos) FROM apgebat_attachment WHERE id in %s group by id order by att_pos desc''', (tuple(atts_prec),))
            prec_att_id = cr.fetchone()[0]
            
            #ne pas oublier att_pos de parent +1 a ajouter sur la nouvelle generation
            att_pos=self.browse(cr, uid, prec_att_id, context=context).att_pos+1
            for estim in att.project_id.estimation_id:
                if att.lot_id.id==estim.lot_id.id:
                    if estim.price_line in ligne_qte:
                        qte_cumul=ligne_qte[estim.price_line]/estim.pu_ds
                        mont_cumul=qte_cumul*estim.bpu
                    else:
                        mont_cumul=0.0
                        qte_cumul=0.0
                    prec_att_line_id=self.pool.get('apgao.line.att').search(cr, uid,[('att_id', '=', prec_att_id), ('lines', '=', estim.price_line)])
                    if prec_att_line_id:
                        att_line_prec=self.pool.get('apgao.line.att').browse(cr, uid, prec_att_line_id, context=context)
                        qm1 = att_line_prec.qte_cumul
                        m1 = qm1*estim.bpu
                    else:
                        qm1 = 0.0
                        m1 = 0.0
                    if mont_cumul:
                        taux= mont_cumul/estim.total_bpu
                    else:
                        taux=0.0
                    qm=qte_cumul-qm1
                    m=mont_cumul-m1
                    self.write(cr, uid, ids, {'att_pos': att_pos})
                    if estim.parent_id:
                        cr.execute('''INSERT INTO apgao_line_att (code, lines, type, quantity, sequence, unit_price, total_dqe, qte_m1, qte_m, qte_cumul, montant_m1, montant_m, montant_cumul, taux, att_id, parent_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (estim.code, estim.price_line, estim.type, estim.quantity, estim.sequences, estim.bpu, estim.total_bpu, qm1, qm, qte_cumul, m1, m, mont_cumul, taux, ids[0], estim.parent_id.id))
                    else:
                        cr.execute('''INSERT INTO apgao_line_att (code, lines, type, quantity, sequence, unit_price, total_dqe, qte_m1, qte_m, qte_cumul, montant_m1, montant_m, montant_cumul, taux, att_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (estim.code, estim.price_line, estim.type, estim.quantity, estim.sequences, estim.bpu, estim.total_bpu, qm1, qm, qte_cumul, m1, m, mont_cumul, taux, ids[0]))
                    
                    cr.execute('''SELECT id FROM apgao_line_att ORDER BY id DESC''')
                    #recupere le dernier id inseré
                    id_new = cr.fetchone()[0]
                    matid=self.pool.get('ap.gao.ext.mat').search(cr, uid,[('estim', '=', estim.id)])
                    self.pool.get('ap.gao.ext.mat').write(cr, uid, matid, {'att_line_id' : id_new})
                    for matids in self.pool.get('ap.gao.mat').search(cr, uid,[('estim_id', '=', estim.id)]):
                        mat=self.pool.get('ap.gao.mat').browse(cr, uid, matids)
                        if matid and mat:
                            for matext in self.pool.get('ap.gao.ext.mat').browse(cr, uid, matid):
                                
                                #raise osv.except_osv(_('eru'), _(matext.product_id))
                                if mat.product_id.id==matext.product_id.id:
                                    mat=''
                                    break 
                        if mat:
                            self.pool.get('ap.gao.ext.mat').create(cr, uid, { 'product_id':mat.product_id.id, 'quantity': mat.quantity, 'unite_id': mat.unite_id.id, 'qte_cons': 0, 'taux': 0, 'estim': estim.id, 'att_line_id': id_new})
                               
                    if estim.unite_id.id:
                        cr.execute('''UPDATE apgao_line_att SET unit_id = %s WHERE id=%s''', (estim.unite_id.id, id_new))


        else:
            #pour chaque ligne de prix inserer les valeurs dans la table
            for estim in att.project_id.estimation_id:
                if att.lot_id.id==estim.lot_id.id:
                #raise osv.except_osv(_('Error!'), _(estim))
                    if estim.price_line in ligne_qte:
                        if estim.pu_ds:
                            qte_cumul=ligne_qte[estim.price_line]/estim.pu_ds
                        else:
                            raise osv.except_osv(_('Valeur incorrect'), _('Le Prix unitaire DS ne peut etre egal a zero. ref:'+estim.price_line))

                        mont_cumul=qte_cumul*estim.bpu
                        #raise osv.except_osv(_('Error!'), _(qte_cumul))
                    else:
                        mont_cumul=0.0
                        qte_cumul=0.0
                    #raise osv.except_osv(_('Error!'), _(qte_cumul))
                    if mont_cumul:
                        if estim.total_bpu:
                            taux= mont_cumul/estim.total_bpu
                        else:
                            raise osv.except_osv(_('Valeur incorrect'), _('Le total BPU(DQE) ne peut etre egal a zero. ref:'+estim.price_line))
                    else:
                        taux=0.0
                    self.write(cr, uid, ids, {'att_pos': 1})
                    if estim.parent_id:
                        cr.execute('''INSERT INTO apgao_line_att (code, lines, type, quantity, sequence, unit_price, total_dqe, qte_m, qte_cumul, montant_m, montant_cumul, taux, att_id, parent_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (estim.code, estim.price_line, estim.type, estim.quantity, estim.sequences, estim.bpu, estim.total_bpu, qte_cumul, qte_cumul, mont_cumul, mont_cumul, taux, ids[0], estim.parent_id.id ))
                    else:
                        cr.execute('''INSERT INTO apgao_line_att (code, lines, type, quantity, sequence, unit_price, total_dqe, qte_m, qte_cumul, montant_m, montant_cumul, taux, att_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', (estim.code, estim.price_line, estim.type, estim.quantity, estim.sequences, estim.bpu, estim.total_bpu, qte_cumul, qte_cumul, mont_cumul, mont_cumul, taux, ids[0]))
                    
                    cr.execute('''SELECT id FROM apgao_line_att ORDER BY id DESC''')
                    #recupere le dernier id inseré
                    id_new = cr.fetchone()[0]
                    matid=self.pool.get('ap.gao.ext.mat').search(cr, uid,[('estim', '=', estim.id)])
                    self.pool.get('ap.gao.ext.mat').write(cr, uid, matid, {'att_line_id' : id_new})
                    for matids in self.pool.get('ap.gao.mat').search(cr, uid,[('estim_id', '=', estim.id)]):
                        mat=self.pool.get('ap.gao.mat').browse(cr, uid, matids)
                        if matid:
                            for matext in self.pool.get('ap.gao.ext.mat').browse(cr, uid, matid):
                                #_logger.error("mat : %r ", mat)
                                #_logger.error("matext : %r ", matext)
                                if matext and mat:

                                    if mat.product_id.id== matext.product_id.id:
                                        mat=''
                        if mat:
                            self.pool.get('ap.gao.ext.mat').create(cr, uid, { 'product_id':mat.product_id.id, 'quantity': mat.quantity, 'unite_id': mat.unite_id.id, 'qte_cons': 0, 'taux': 0, 'estim': estim.id, 'att_line_id': id_new})
                                
                    if estim.unite_id.id:
                        cr.execute('''UPDATE apgao_line_att SET unit_id = %s WHERE id=%s''', (estim.unite_id.id, id_new))
        
        #webbrowser.open('http://127.0.0.1:8069/report/pdf/sale.report_saleorder/1', 'c:/sale.pdf')
        #webbrowser.open(http.request.httprequest.host+'/report/pdf/sale.report_saleorder/1')
        #raise osv.except_osv(_('request!'), _(http.request.httprequest.host+'/report/pdf/sale.report_saleorder/1'))
        return True





    def print_attxls(self, cr, uid, ids, context=None):
        att=self.browse(cr, uid, ids)
        fl = StringIO()
        if context is None: context = {}
        wbk = xlwt.Workbook(encoding="UTF-8")
        
        font = xlwt.Font()
        font.bold = True
        entete=xlwt.easyxf('font: name Calibri,height 320, color-index black, bold on;align: vert centre, horiz centre;border: bottom medium, left medium, right medium;')#fusionne des lignes (l1, l2, c1, c2)
        bordtopor = xlwt.easyxf('font: name Arial,height 280, color-index black, bold on;border: top medium, right medium, bottom medium, left medium;align: vert centre, horiz center;pattern: pattern solid, fore_colour gold ;')
        bordtopbl = xlwt.easyxf('font: name Arial,height 280, color-index black, bold on;border: top medium, right medium, bottom medium, left medium;align: vert centre, horiz center;pattern: pattern solid, fore_colour pale_blue ;')
        sbord = xlwt.easyxf('font: name Arial,height 280, color-index black, bold on;border: bottom thin, right thin;align: vert centre, horiz center;pattern: pattern solid, fore_colour pale_blue ;')
        lipar = xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right thin;')
        lienf = xlwt.easyxf('font: name Arial,height 240, color-index black;border: bottom thin, right thin;')
        liht = xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right thin;')
        
        linechild = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin;align: wrap on')
        lastline = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin,bottom thin, left thin;align: wrap on')
        linechild1 = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin;align: wrap on, vert centre, horiz center')
        lastline1 = xlwt.easyxf('font: name Calibri,height 240, color-index black;border: top thin, right thin,bottom thin, left thin;align: wrap on, vert centre, horiz center')
        
        
        lot = wbk.add_sheet(att.lot_id.code, cell_overwrite_ok=True)#creation de la feuille

        lot.col(0).width= 500*4
        lot.col(1).width= int(500*47.16)

        lot.col(2).width= int(500*4.90) #size de la column
        lot.col(3).width= int(500*7.33)
        lot.col(4).width= int(500*10.21)
        lot.col(5).width= int(500*10.21)

        lot.col(6).width= int(500*4.50)
        lot.col(7).width= int(500*4.50)
        lot.col(8).width= int(500*7.65)

        lot.col(9).width= int(500*10.21)
        lot.col(10).width= int(500*10.21)
        lot.col(11).width= int(500*10.21)

        lot.col(12).width= int(500*5.46)
      

        #entete de la page
        lot.write_merge(0, 0, 2, 10, att.attachement_id.name , entete)
        
        #entete tableau
                                              
                                                    
        lot.write_merge(2, 3, 0, 0, "N°", bordtopor)
        lot.write_merge(2, 3, 1, 1, "DESIGNATION", bordtopor)
        lot.write_merge(2, 2, 2, 5, "DQE DU MARCHE", bordtopbl)
        #sous elements DQE DU MARCHE
        lot.write(3, 2, "Unité", sbord)
        lot.write(3, 3, "Quantité", sbord)
        lot.write(3, 4, "Prix Unitaire", sbord)
        lot.write(3, 5, "Prix Total", xlwt.easyxf('font: name Arial,height 280, color-index black, bold on;border: bottom thin, right medium;align: vert centre, horiz center;pattern: pattern solid, fore_colour pale_blue ;'))

        lot.write_merge(2, 2, 6, 8, "QUANTITES", bordtopbl)
        #sous element QUANTITES
        lot.write(3, 6, "M-1", sbord)
        lot.write(3, 7, "M", sbord)
        lot.write(3, 8, "CUMULE", xlwt.easyxf('font: name Arial,height 280, color-index black, bold on;border: bottom thin, right medium;align: vert centre, horiz center;pattern: pattern solid, fore_colour pale_blue ;'))

        lot.write_merge(2, 2, 9, 11, "MONTANTS", bordtopbl)
        #sosu elements MONTANTS
        lot.write(3, 9, "M-1", sbord)
        lot.write(3, 10, "M", sbord)
        lot.write(3, 11, "CUMULE", sbord)

        lot.write_merge(2, 3, 12, 12, "TAUX", bordtopbl)

        line_id=self.pool.get('apgao.line.att').search(cr, uid,[('att_id', '=', att.id)], order='sequence' )
        par={}
        vue={}
        seq={}
        formuledqe={}
        formulem1={}
        formulem={}
        formulecum={}
        a=0
        b=3
        c=0
        for line in self.pool.get('apgao.line.att').browse(cr, uid, line_id):
            a+=1
            b+=1
            #ligne du tableau 
            if line.type=="vue":
                   
                    #ligne parent
                lot.write(b, 0, line.code, lipar)
                lot.write(b, 1, line.lines.upper(), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on, underline single;border: bottom thin, right thin;'))
                lot.write(b, 2, line.unit_id and  line.unit_id.name or '', lipar)
                lot.write(b, 3, '', lipar)
                lot.write(b, 4, '', lipar)
                lot.write(b, 5, '', xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                lot.write(b, 6, '', lipar)
                lot.write(b, 7, '', lipar)
                lot.write(b, 8, '', xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                lot.write(b, 9, '', lipar)
                lot.write(b, 10, '', lipar)
                lot.write(b, 11, '', xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                lot.write(b, 12, '', xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                
                parent=self.pool.get('ap.gao.estim').search(cr, uid,[('price_line', '=', line.lines), ('type', '=', 'vue'), ('sequences', '=', line.sequence)])
                enfid=self.pool.get('ap.gao.estim').read_group(cr,uid,[('parent_id', '=', parent[0]), ('type', '=', 'vue')], ['parent_id'], ['parent_id'])
                if enfid:
                    enfpar=enfid[0]['parent_id_count']
                else:
                    enfpar=-15
                enf=self.pool.get('ap.gao.estim').read_group(cr,uid,[('parent_id', '=', parent[0])], ['parent_id'], ['parent_id'])

                if enf:

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
                    if line.parent_id:
                        par[str(nbr)+line.lines+str(a)]=line.code+' / '+line.lines
                    else:
                        vue[str(nbr)]=line.code+' / '+line.lines

            else:
                 #ligne enfant
                lot.write(b, 0, line.code, lienf)
                lot.write(b, 1, line.lines.capitalize(), lienf)
                lot.write(b, 2, line.unit_id and  line.unit_id.name or '', lienf)
                lot.write(b, 3, line.quantity, lienf)
                lot.write(b, 4, line.unit_price, lienf)
                lot.write(b, 5, xlwt.Formula("D"+str(b+1)+"*E"+str(b+1)+""), xlwt.easyxf('font: name Arial,height 240, color-index black;border: bottom thin, right medium;'))
                lot.write(b, 6, line.qte_m1, lienf)
                lot.write(b, 7, line.qte_m, lienf)
                lot.write(b, 8, xlwt.Formula("G"+str(b+1)+"+H"+str(b+1)+""), xlwt.easyxf('font: name Arial,height 240, color-index black;border: bottom thin, right medium;'))
                lot.write(b, 9, xlwt.Formula("G"+str(b+1)+"*E"+str(b+1)+""), lienf)
                lot.write(b, 10,  xlwt.Formula("E"+str(b+1)+"*H"+str(b+1)+""), lienf)
                lot.write(b, 11, xlwt.Formula("K"+str(b+1)+"*J"+str(b+1)+""), xlwt.easyxf('font: name Arial,height 240, color-index black;border: bottom thin, right medium;'))
                lot.write(b, 12, xlwt.Formula("L"+str(b+1)+"/F"+str(b+1)+""), xlwt.easyxf('font: name Arial,height 240, color-index black;border: bottom thin, right medium;'))
                if line.parent_id.price_line in formuledqe:
                    formuledqe[line.parent_id.price_line]+= "+F"+str(b+1)
                    formulem1[line.parent_id.price_line]+= "+J"+str(b+1)
                    formulem[line.parent_id.price_line]+= "+K"+str(b+1)
                    formulecum[line.parent_id.price_line]+= "+L"+str(b+1)
                else:
                    formuledqe[line.parent_id.price_line]= "F"+str(b+1)
                    formulem1[line.parent_id.price_line]= "J"+str(b+1)
                    formulem[line.parent_id.price_line]= "K"+str(b+1)
                    formulecum[line.parent_id.price_line]= "L"+str(b+1)

            if vue: 
                for x in range(1, a):

                    if line.parent_id:
                        for y in range(1, a):
                            if str(x)+line.parent_id.price_line+str(y) in par:
                                if par[str(x)+line.parent_id.price_line+str(y)]:
                                    if a-y==x:
                                         #ligne sous total
                                        b+=1
                                        c+=1
                                        lot.write(b, 0, "", lipar)
                                        lot.write(b, 1, "TOTAL "+par[str(x)+line.parent_id.price_line+str(y)]+"".upper(), lipar)
                                        lot.write(b, 2, "", lipar)
                                        lot.write(b, 3, "", lipar)
                                        lot.write(b, 4, "", lipar)
                                        if line.parent_id.price_line in formuledqe:
                                            lot.write(b, 5, xlwt.Formula(formuledqe[line.parent_id.price_line]), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                                            lot.write(b, 9, xlwt.Formula(formulem1[line.parent_id.price_line]), lipar)
                                            lot.write(b, 10, xlwt.Formula(formulem[line.parent_id.price_line]), lipar)
                                            lot.write(b, 11, xlwt.Formula(formulecum[line.parent_id.price_line]), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                                        
                                        else:
                                            lot.write(b, 5, 0, xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                                            lot.write(b, 9, 0, lipar)
                                            lot.write(b, 10, 0, lipar)
                                            lot.write(b, 11, 0, xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                                        
                                        lot.write(b, 6, "", lipar)
                                        lot.write(b, 7, "", lipar)
                                        lot.write(b, 8, "", xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                                        lot.write(b, 12, xlwt.Formula("L"+str(b+1)+"/F"+str(b+1)+""), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                                        par[str(x)+line.parent_id.price_line+str(y)]=''
                                        
                                        if line.parent_id.parent_id.price_line in formuledqe:
                                            formuledqe[line.parent_id.parent_id.price_line]+= "+F"+str(b)
                                            formulem1[line.parent_id.parent_id.price_line]+= "+J"+str(b)
                                            formulem[line.parent_id.parent_id.price_line]+= "+K"+str(b)
                                            formulecum[line.parent_id.parent_id.price_line]+= "+L"+str(b)
                                        else:
                                            formuledqe[line.parent_id.parent_id.price_line]= "F"+str(b)
                                            formulem1[line.parent_id.parent_id.price_line]= "J"+str(b)
                                            formulem[line.parent_id.parent_id.price_line]= "K"+str(b)
                                            formulecum[line.parent_id.parent_id.price_line]= "L"+str(b)

            
                    if str(x) in vue:
                        if vue[str(x)] and (enfpar==c or enfpar==-15):
                            b+=1
                             #ligne sous total
                        
                            lot.write(b, 0, "", lipar)
                            lot.write(b, 1, "TOTAL "+vue[str(x)]+"".upper(), lipar)
                            lot.write(b, 2, "", lipar)
                            lot.write(b, 3, "", lipar)
                            lot.write(b, 4, "", lipar)
                            
                            if vue[str(x)].split(' / ')[1] in formuledqe:
                                lot.write(b, 5, xlwt.Formula(formuledqe[vue[str(x)].split(' / ')[1]]), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                                lot.write(b, 9, xlwt.Formula(formulem1[vue[str(x)].split(' / ')[1]]), lipar)
                                lot.write(b, 10, xlwt.Formula(formulem[vue[str(x)].split(' / ')[1]]), lipar)
                                lot.write(b, 11, xlwt.Formula(formulecum[vue[str(x)].split(' / ')[1]]), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                            
                            else:
                                lot.write(b, 5, 0, xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                                lot.write(b, 9, 0, lipar)
                                lot.write(b, 10, 0, lipar)
                                lot.write(b, 11, 0, xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                            
                            lot.write(b, 6, "", lipar)
                            lot.write(b, 7, "", lipar)
                            lot.write(b, 8, "", xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                            lot.write(b, 12, xlwt.Formula("L"+str(b+1)+"/F"+str(b+1)+""), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
                            vue[x]=''
                            a=0
                            c=0
                            
                            if "TOTAL GENERAL HT" in formuledqe:
                                formuledqe["TOTAL GENERAL HT"]+= "+F"+str(b)
                                formulem1["TOTAL GENERAL HT"]+= "+J"+str(b)
                                formulem["TOTAL GENERAL HT"]+= "+K"+str(b)
                                formulecum["TOTAL GENERAL HT"]+= "+L"+str(b)
                            else:
                                formuledqe["TOTAL GENERAL HT"]= "F"+str(b)
                                formulem1["TOTAL GENERAL HT"]= "J"+str(b)
                                formulem["TOTAL GENERAL HT"]= "K"+str(b)
                                formulecum["TOTAL GENERAL HT"]= "L"+str(b)
                            break
                
         #ligne total ht

        lot.write(b, 0, "", lipar)
        lot.write_merge(b, b, 1, 5, "", xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
        lot.write_merge(b, b, 6, 8, "", xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
        lot.write_merge(b, b, 9, 11, "", xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
        lot.write(b, 12, "", xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom thin, right medium;'))
        b+=1                   
        lot.write(b, 0, "", liht)
        lot.write(b, 1, "TOTAL GENERAL HT ", liht)
        lot.write(b, 2, "", liht)
        lot.write(b, 3, "", liht)
        lot.write(b, 4, "", liht)
        if "TOTAL GENERAL HT" in formuledqe:
            lot.write(b, 5, xlwt.Formula(formuledqe["TOTAL GENERAL HT"]), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right medium;'))
            lot.write(b, 9, xlwt.Formula(formulem1["TOTAL GENERAL HT"]), liht)
            lot.write(b, 10, xlwt.Formula(formulem["TOTAL GENERAL HT"]), liht)
            lot.write(b, 11, xlwt.Formula(formulecum["TOTAL GENERAL HT"]), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right medium;'))
        
        else:
            if b>7:
                lot.write(b, 5, xlwt.Formula("SUM(F7:F"+str(b)+")"), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right medium;'))
                lot.write(b, 9, xlwt.Formula("SUM(J7:J"+str(b)+")"), liht)
                lot.write(b, 10, xlwt.Formula("SUM(K7:K"+str(b)+")"), liht)
                lot.write(b, 11, xlwt.Formula("SUM(L7:L"+str(b)+")"), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right medium;'))
                
            else:
                lot.write(b, 5, 0, xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right medium;'))
                lot.write(b, 9, 0, liht)
                lot.write(b, 10, 0, liht)
                lot.write(b, 11, 0, xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right medium;'))
                                
        lot.write(b, 6, "", liht)
        lot.write(b, 7, "", liht)
        lot.write(b, 8, "", xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right medium;'))
        lot.write(b, 12, xlwt.Formula("L"+str(b+1)+"/F"+str(b+1)+""), xlwt.easyxf('font: name Arial,height 240, color-index black, bold on;border: bottom medium, right medium;'))




        lot.normal_magn = 60

        
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







class apgao_ligne_att(osv.osv):
    _name='apgao.line.att'

    _columns = {
        'code': fields.char('N°', size=20), #to do: interdire les caractere speciaux dans ce champ car il pose un probleme a la generation excel
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

        'parent_id': fields.many2one('ap.gao.estim', 'parent'),
        'att_id': fields.many2one('apgebat.attachment', 'attachement'),
        'mat_id': fields.one2many('ap.gao.ext.mat', 'att_line_id', ondelete="cascade"),
        'type': fields.selection([('vue','Vue'), ('child', 'Details')]),
        'sequence': fields.integer('seq')
    }

    def onchange_qte(self, cr, uid, ids, qtemn, qtem, pu, dqe, context=None):
        qte_cumul= 0
        mont_cumul=0
        montant_m=0
        taux=0
        qte_cumul=qtem+qtemn
        #raise osv.except_osv(_('ere'), _(ids[0]))
        montant_m=qtem*pu
        mont_cumul=qte_cumul*pu
        taux= mont_cumul/dqe
        cr.execute('''UPDATE apgao_line_att SET qte_cumul = %s, montant_cumul = %s, montant_m = %s, taux = %s WHERE id=%s''', (qte_cumul,mont_cumul,montant_m,taux, ids[0]))
        values = {'qte_cumul': qte_cumul, 'montant_cumul': mont_cumul, 'montant_m': montant_m, 'taux':taux}
        return {'value': values}



class internal_purchase_request_wizard(osv.osv_memory):
    _name='internal.purchase.request.wizard'
    _columns = {

        'project_id': fields.many2one('project.project', 'project', domain="[('tender_id', '!=', False)]", required=True),
        'selector': fields.selection([('line', 'Purchase by price line'),('mat', 'Purchase by materials')], 'Purchase request method', required=True)
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

    def _delivery_count(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        for project in self.browse(cr, uid, ids, context=context):
            res[project.id]={
                'situation_count': 0,
                'purchase_count':0
            }
            ach=self.pool.get('apgebat.ach').search(cr, uid, [('project_id','=', ids[0]), ('state', '=','sent')])
            res[project.id]['purchase_count']=len(ach)
            sit=self.pool.get('apgebat.attachment').search(cr, uid, [('project_id','=', ids[0]), ('state', 'in',['sent','end','invoice'])])
            res[project.id]['situation_count']=len(sit)
        return res


    _columns = {

        'att_list': fields.one2many('apgebat.attachment.list', 'project_id', 'Attachements'),
        'avance': fields.float('Advance payment %'),
        'garanti': fields.float('Holdback %'),
        'risque': fields.float('risks %'),
        'remise': fields.float('Discounts %'),
        'retard': fields.float('Late penalties %'),
        'situation_count': fields.function(_delivery_count, string='# of situation Order', type='integer', multi=True),
        'purchase_count': fields.function(_delivery_count, string='# of purchase Order', type='integer',multi=True),
        
    }

    #_defaults = {

    #    'debit': 
    #    'credit':
    #}
    def project_purchase_valid(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_ach', 'apgebat_ach_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_ach', 'apgebat_ach_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Internal purchase request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'apgebat.ach',
            'view_id': 'apgebat_ach_tree',
            'views': [(tree_id, 'tree'),(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': "[('project_id', '=', context.get('c_project', False)),('state', '=','sent')]",
            'target': 'new'
        }


    def project_situation_valid(self, cr, uid, ids, context=None):
        #raise osv.except_osv(_('jfjfj'), _(context.get('c_project', False)))
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_gao_ext', 'situation_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'apgebat_gao_ext', 'view_situation')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Situation'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'apgebat.attachment',
            'view_id': 'view_situation',
            'views': [(tree_id, 'tree'),(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': "[('project_id', '=', context.get('c_project', False)),('state', 'in',['sent','end','invoice'])]",
            'context': "{'search_default_group_att': 1}",
            'target': 'new'
        }
    
    def choice_purchase(self, cr, uid, ids, context=None):

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        data = self.read(cr, uid, ids, context=context)[0]

        #on recherche id de lutilisateur en tant qu'employé afin de recuperer son departement
        #
        employe=self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        if employe:
            employee = self.pool.get('hr.employee').browse(cr, uid, employe, context=context)
            department=employee.department_id.id
            ach_id = self.pool.get('apgebat.ach').create(cr, uid, {'project_id': data['id'], 'dateout':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()), 'type': 'technical', 'master': uid, 'department_id': department})
        
        else:
            ach_id = self.pool.get('apgebat.ach').create(cr, uid, {'project_id': data['id'], 'dateout':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()), 'type': 'technical', 'master': uid})
        
        #on va recuperer toutes les qté demande et lancer une demande d'achat
        prod={}
        total=0.0
        for estim in self.pool.get('ap.gao.estim').browse(cr, uid, data['estimation_id']):
            #pour chaque ligne de prix on recupere ses lignes de prix afin de determiner la qté commandée
            for mat in estim.mat_line:
                if mat.product_id.id in prod:
                    prod[mat.product_id]+=mat.quantity*estim.qte_request
                else:
                    prod[mat.product_id]=mat.quantity*estim.qte_request
        
            
            for product in prod:
                #
                produit=self.pool.get('product.template').browse(cr, uid, product.id)
                #raise osv.except_osv(_('Error!'), _(prod))
                if prod[product]:                         
                    self.pool.get('internal.order.line').create(cr, uid, {'lot_id': estim.lot_id.id, 'lignes_id': estim.id, 'product_id': product.id, 'name': produit.name, 'date_planned': time.strftime('%Y-%m-%d',time.localtime()), 'product_qty': prod[product], 'price_unit': produit.standard_price, 'price_subtotal': prod[product]*produit.standard_price, 'internal_id1': ach_id})
                    total+=prod[product]*produit.standard_price
            prod={}
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



class ap_gaoext_materials(osv.osv):
    _name = 'ap.gao.ext.mat'
    _columns = {

        'product_id': fields.many2one('product.template', 'equipments / materials'),
        'quantity': fields.float('Quantity'),
        'unite_id': fields.many2one('product.uom', 'UoM'),
        'qte_cons': fields.float('Consumed'),
        'taux': fields.float('Rate'),
        'att_line_id': fields.integer('att'),
        'estim': fields.many2one('ap.gao.estim', 'Product UoM'),
    }

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'out_advance_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
}


class account_invoice(osv.osv):
    _inherit = "account.invoice"
  



    @api.multi
    def name_get(self):
        TYPES = {
            'out_invoice': _('Invoice'),
            'out_advance_invoice': _('Advance Invoice'),
            'in_invoice': _('Supplier Invoice'),
            'out_refund': _('Refund'),
            'in_refund': _('Supplier Refund'),
        }
        result = []
        for inv in self:
            result.append((inv.id, "%s %s" % (inv.number or TYPES[inv.type], inv.name or '')))
        return result


    @api.model
    def _default_journal(self):
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', filter(None, map(TYPE2JOURNAL.get, inv_types))),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)


    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        if self.type=="out_invoice" and self.project_id:
            retenu=0.0
            presta=0.0
            for line in self.invoice_line:
                if line.price_subtotal<0:
                    retenu+=line.price_subtotal
                else:
                    presta+=line.price_subtotal
            self.discount= (presta*self.project_id.remise)/100
            self.amount_holback = self.discount+retenu*-1
            #total des depenses ht toutes les prestation facturé+avance-retenu
            self.expense = self.advance_begin+presta+retenu
            self.expense_tva=self.expense*0.18
            self.expense_ttc=self.expense_tva+self.expense
            fact_ids=self.search([('type', '=', 'out_invoice'), ('project_id', '=', self.project_id.id), ('id', '!=', self.id)])
            #if fact_ids
            #raise osv.except_osv(_('eir'), _(fact_ids))
            avance=0
            for fact in fact_ids:
                for line in fact.invoice_line:
                    if 'Avance' in line.name:
                        avance+=line.price_subtotal
            self.total_acompte_prec=avance*-1+ avance*-1*0.18
            self.amount_total = self.expense_ttc - self.total_acompte_prec
            self.amount_untaxed = self.amount_total/1.18
            self.amount_tax = (self.amount_total/1.18)*0.18
            

        else:
            self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
            self.amount_tax = sum(line.amount for line in self.tax_line)
            self.amount_total = self.amount_untaxed + self.amount_tax



    _columns = {
        'att_id': fields.many2one('apgebat.attachment', 'Situation'),
        'project_id': fields.many2one('project.project', 'project'),
        'lot_id': fields.many2one('ap.gao.attr', 'Lot'),
        #'total_retenu': fields.float('Total holdback'),
        #'total_depense': fields.float('Total expenditure'),
        'type':  fields.selection([
            ('out_invoice','Customer Invoice'),
            ('out_advance_invoice','Customer Advance Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
        ], string='Type', readonly=True, index=True, change_default=True,
        default=lambda self: self._context.get('type', 'out_invoice'),
        track_visibility='always'),

        'market_value': fields.float('Market value TTC', digits=dp.get_precision('Account')),
        'advance_begin': fields.float('advance payment TTC', digits=dp.get_precision('Account')),
        'discount' : fields.float(string='Discount', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always'),
        'amount_holback' : fields.float(string='Total Holdback', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always'),
        'expense' : fields.float(string='Total of expenses HT', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always'),
        'expense_tva' : fields.float(string='TVA 18% of expenses', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always'),
        'expense_ttc' : fields.float(string='Total of expenses TTC', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always'),
        'total_acompte_prec': fields.float(string='Total previous installments', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always'),
    }
    

    @api.multi
    def onchange_company_id(self, company_id, part_id, type, invoice_line, currency_id):
        # TODO: add the missing context parameter when forward-porting in trunk
        # so we can remove this hack!
        self = self.with_context(self.env['res.users'].context_get())

        values = {}
        domain = {}

        if company_id and part_id and type:
            p = self.env['res.partner'].browse(part_id)
            if p.property_account_payable and p.property_account_receivable and \
                    p.property_account_payable.company_id.id != company_id and \
                    p.property_account_receivable.company_id.id != company_id:
                prop = self.env['ir.property']
                rec_dom = [('name', '=', 'property_account_receivable'), ('company_id', '=', company_id)]
                pay_dom = [('name', '=', 'property_account_payable'), ('company_id', '=', company_id)]
                res_dom = [('res_id', '=', 'res.partner,%s' % part_id)]
                rec_prop = prop.search(rec_dom + res_dom) or prop.search(rec_dom)
                pay_prop = prop.search(pay_dom + res_dom) or prop.search(pay_dom)
                rec_account = rec_prop.get_by_record(rec_prop)
                pay_account = pay_prop.get_by_record(pay_prop)
                if not rec_account and not pay_account:
                    action = self.env.ref('account.action_account_config')
                    msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                    raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

                if type in ('out_invoice', 'out_refund'):
                    acc_id = rec_account.id
                else:
                    acc_id = pay_account.id
                values= {'account_id': acc_id}

            if self:
                if company_id:
                    for line in self.invoice_line:
                        if not line.account_id:
                            continue
                        if line.account_id.company_id.id == company_id:
                            continue
                        accounts = self.env['account.account'].search([('name', '=', line.account_id.name), ('company_id', '=', company_id)])
                        if not accounts:
                            action = self.env.ref('account.action_account_config')
                            msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                            raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
                        line.write({'account_id': accounts[-1].id})
            else:
                for line_cmd in invoice_line or []:
                    if len(line_cmd) >= 3 and isinstance(line_cmd[2], dict):
                        line = self.env['account.account'].browse(line_cmd[2]['account_id'])
                        if line.company_id.id != company_id:
                            raise except_orm(
                                _('Configuration Error!'),
                                _("Invoice line account's company and invoice's company does not match.")
                            )

        if company_id and type:
            journal_type = TYPE2JOURNAL[type]
            journals = self.env['account.journal'].search([('type', '=', journal_type), ('company_id', '=', company_id)])
            if journals:
                values['journal_id'] = journals[0].id
            journal_defaults = self.env['ir.values'].get_defaults_dict('account.invoice', 'type=%s' % type)
            if 'journal_id' in journal_defaults:
                values['journal_id'] = journal_defaults['journal_id']
            if not values.get('journal_id'):
                field_desc = journals.fields_get(['type'])
                type_label = next(t for t, label in field_desc['type']['selection'] if t == journal_type)
                action = self.env.ref('account.action_account_journal_form')
                msg = _('Cannot find any account journal of type "%s" for this company, You should create one.\n Please go to Journal Configuration') % type_label
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
            domain = {'journal_id':  [('id', 'in', journals.ids)]}

        return {'value': values, 'domain': domain}


class account_invoice_line(osv.osv):
    _inherit= "account.invoice.line"

    @api.multi
    def onchange_account_id(self, product_id, partner_id, inv_type, fposition_id, account_id):
        context=self._context
        if not account_id:
            return {}
        unique_tax_ids = []
        account = self.env['account.account'].browse(account_id)
        if not product_id:
            fpos = self.env['account.fiscal.position'].browse(fposition_id)
            if context.get('type') != "out_advance_invoice":
                unique_tax_ids = fpos.map_tax(account.tax_ids).ids
                
        else:
            product_change_result = self.product_id_change(product_id, False, type=inv_type,
                partner_id=partner_id, fposition_id=fposition_id, company_id=account.company_id.id)
            if 'invoice_line_tax_id' in product_change_result.get('value', {}):
                unique_tax_ids = product_change_result['value']['invoice_line_tax_id']
        return {'value': {'invoice_line_tax_id': unique_tax_ids}}


class project_account_conf(osv.osv):
    _name='gao.project.account.conf'

    _columns = {

        'line_attach': fields.many2one('account.account', 'Account N° for situation'),
        'advance': fields.many2one('account.account', 'Account N° for advance'),
        'retenu': fields.many2one('account.account', 'Account N° for holdback'),
        'penalite': fields.many2one('account.account', 'Account N° for late penaltie'),
        'risk': fields.many2one('account.account', 'Account N° for risks'),
        'name':fields.char('nom'),
    }
      


class account_move(osv.osv):
    _inherit = "account.move"

    def post(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice = context.get('invoice', False)
        valid_moves = self.validate(cr, uid, ids, context)

        if not valid_moves:
            raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
        obj_sequence = self.pool.get('ir.sequence')
        for move in self.browse(cr, uid, valid_moves, context=context):
            if move.name =='/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.internal_number:
                    new_name = invoice.internal_number
                else:
                    if journal.sequence_id:
                        c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
                        if invoice.type == 'out_advance_invoice':
                            journal_seq=self.pool.get('ir.sequence').search(cr, uid, [('name', '=', 'Account Default advance Journal')])
                        else:
                            journal_seq=journal.sequence_id.id
                        new_name = obj_sequence.next_by_id(cr, uid, journal_seq, c)
                    else:
                        raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))
                
                if new_name:
                    self.write(cr, uid, [move.id], {'name':new_name})

        cr.execute('UPDATE account_move '\
                   'SET state=%s '\
                   'WHERE id IN %s',
                   ('posted', tuple(valid_moves),))
        self.invalidate_cache(cr, uid, ['state', ], valid_moves, context=context)
        return True


class gao_xls_report_file(osv.osv_memory):
    _inherit = 'gao.xls.report.file'