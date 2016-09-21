# -*- coding: utf-8 -*-
import os
import tempfile
from tempfile import TemporaryFile
import xlrd

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

class importe(osv.osv_memory):
    _name='importe'

    def imported_line(self, cr, uid, ids, context=None):
        this = self.pool.get('gao.xls.report.file').browse(cr, uid, ids[0], context)
        #recuperation de l'extension du fichier 
        fileformat = os.path.splitext(this.file_name)[-1][1:].lower()
        if fileformat!='xls':
            raise osv.except_osv(_('Erreur de fichier'), _("L'extension de fichier autorisé est le 'XLS'.\n Veillez choisir le bon fichier ou téléchargez le modèle"))
        else:
            import unicodedata
            #fichier stocker dans le dossier temp et renommer en file.xls
            file_path = tempfile.gettempdir()+'/file.xls'
            data = this.file
            f = open(file_path,'wb')
            f.write(data.decode('base64'))
            f.close()
            #ouverture u fichier pour la lecture
            book = xlrd.open_workbook(file_path)
            ao=self.pool.get('ap.gao').browse( cr, uid, [context['active_id']])
            seq=[]
            for estim in ao.estimation_id:
                seq.append(estim.sequences)
            #raise osv.except_osv(_('Erreur de fichier'), _(max(seq)+1))
            i=0
            start=0
            for lot in ao.lot_id:
                
                try:
                    sheet = book.sheet_by_name(str(lot.code)) # ou: sheet_by_index(0)
                except Exception, msg:
                    raise osv.except_osv(_('Erreur de fichier'), _("Le lot '"+lot.code+"' est introuvable dans le fichier" ))
                row= ""
                
                for row_index in xrange(1, sheet.nrows):
                    i+=1
                    ligneid=""
                    if seq and i==1:
                        start=max(seq)+1
                    elif i==1:
                        start=1
                    #ds=0
                    num = sheet.cell(rowx=row_index,colx=0).value
                    nom = sheet.cell(rowx=row_index,colx=1).value
                    unite = sheet.cell(rowx=row_index,colx=2).value
                    qte = sheet.cell(rowx=row_index,colx=3).value
                    #parent = sheet.cell(rowx=row_index,colx=5).value
                    #types="child"
                    types="draft"
                    #enf={}
                    #for row in xrange(row_index+1, sheet.nrows):
                     #   try:
                    #        if int(sheet.cell(rowx=row,colx=5).value) == row_index+1:
                     #           types = 'vue'
                     #       except ValueError: pass

                    #k = sheet.cell(rowx=row_index,colx=6).value
                    #raise osv.except_osv(_('Erreur de fichier'), _("num "+num+"\n nom"+nom+"\n unit"+unite+"\n qte"+qte+"\n parent"+parent+"\n k"+k+"\n typ"+types))
                    verif=''
                    if nom:
                        #raise osv.except_osv(_('Erreur de fichier'), _("num "+num+"\n nom "+nom+"\n unit "+unite+"\n qte "+str(qte)+"\n typ "+types+"\n seq "+str(start)+"\n tender_id "+str(ao.id)))
                        if num:
                            verif=self.pool.get('ap.gao.estim').search(cr, uid, [('code', '=', num), ('tender_id', '=', ao.id)])
                            if verif:
                                seq=self.pool.get('ap.gao.estim').browse(cr, uid, verif[0]).sequences
                                #raise osv.except_osv(_("Erreur d'import"), _("Le n° de prix '"+str(num)+"' est déja utilisé à la séquence "+str(seq))) ajouter plus tard
                        else:
                            verif=self.pool.get('ap.gao.estim').search(cr, uid, [('price_line', '=', nom), ('tender_id', '=', ao.id), ('lot_id', '=', lot.id)])
                            if verif:
                                seq=self.pool.get('ap.gao.estim').browse(cr, uid, verif[0]).sequences
                                #raise osv.except_osv(_("Erreur d'import"), _("L'intitulé de la ligne de prix '"+str(nom)+"' est déja utilisé à la séquence "+str(seq))) ajouter plus tard
                           
                        ligneid=self.pool.get('ap.gao.estim').create(cr, uid, {'type': types, 'sequences': start, 'code': num,'lot_id': lot.id, 'price_line': nom,'quantity': qte, 'unite_id': unite ,'tender_id': ao.id})#a retirer dans le cas ou le cas mmo est actif
                        #if parent:
                            #if str(parent) in enf:
                            #    ligneid=self.pool.get('ap.gao.estim').create(cr, uid, {'type': types, 'sequences': start, 'parent_id': enf[str(parent)],'code': num,'lot_id': lot.id, 'price_line': nom,'quantity': qte,'tender_id': ao.id})
                        #else:
                           # ligneid=self.pool.get('ap.gao.estim').create(cr, uid, {'type': types, 'sequences': start, 'code': num,'lot_id': lot.id, 'price_line': nom,'quantity': qte,'tender_id': ao.id})
                        
                        #if types=='vue':
                        #    enf[str(row_index+1)]=ligneid[0]
                        #else:
                         #   mmo = book.sheet_by_name(str('MMO'))
                         #   for rows in xrange(1, mmo.nrows):
                         #       try:
                          #              if sheet.cell(rowx=rows,colx=4).value == num:
                          #              qty=sheet.cell(rowx=rows,colx=1).value
                          #              pu=sheet.cell(rowx=rows,colx=3).value
                           #             unit=sheet.cell(rowx=rows,colx=2).value
                           #             prod=sheet.cell(rowx=rows,colx=0).value
                           #             total=float(pu)*float(qty)
                            #            self.pool.get('ap.gao.mat').create(cr, uid, {'quantity': qty,'pu_composant': pu,'unite_id': unit,'product_id': prod,'mat_total': total,'estim_id': ligneid[0]})
                            #            ds+=total
                            #    except ValueError: pass
                            #if ds:
                             #   self.pool.get('ap.gao.estim').write(cr, uid, ligneid, {'pu_ds': ds,'bpu':ds*k, 'ecart': ds*k-ds, 'coef':k, 'rent':((ds*k-ds)/ds)*100 ,'total_ds':qte*ds ,'total_bpu':qte*ds*k})

                        start+=1


                    #if type(value) is unicode:
                    #    value = unicodedata.normalize('NFKD', value).encode('ascii','ignore')
                   # row += "{0} - ".format(value)
                #raise osv.except_osv(_('Erreur'), _(row)) 