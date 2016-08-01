# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv
from openerp import tools
from openerp.modules.module import get_module_resource
from openerp.tools.translate import _
import time
import datetime

#declaration de la base stockant les informations des employés occasionnels
class apgebat_poc(osv.osv):
    _name = 'apgebat.poc'
    _order = 'name asc'
#gestion des images pour la vue kanban
    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)

    _columns = {
        'name': fields.char('Name', required=True),
        'worker_reg': fields.char('Worker registration', size=128),
        'worker_nat': fields.many2one('res.country', 'Nationality', required=True),
        'worker_nic': fields.char('ID of national identity card', size=128, required=True),
        'worker_birth': fields.date('Date of birth', required=True),
        'worker_placebirth': fields.char('Place of birth', size=128, required=True),
        'worker_marital': fields.selection([('single','Single'),('married','Married'),('divorced','Divorced'),
              ('widow-er','Widow(er)')],'Marital status', required=True),
        'worker_children': fields.integer('Number of children', required=False,),
        'worker_gender': fields.selection([('male','Male'),
              ('female','Female')],'Gender', required=True),
        'ref_act': fields.many2one('project.project', 'Reference site'),
        'worker_postal': fields.char('Postal address', size=128),
        'worker_phone': fields.char('Phone number', size=128, required=True),
        'worker_living': fields.char('Home', size=128, required=True),
        'worker_study': fields.char('Level of study', size=128),
        'worker_spec': fields.char('Speciality', size=128, required=True),
        'worker_team': fields.char('Team', size=128),
        'worker_datein': fields.date('date of inauguration', required=True),
        'type_contrat': fields.selection([('day','Daily'),('week','Weekly'),('month','Monthly')],'Contract type'),
        'worker_intern': fields.boolean('traineeship'),
        'worker_sal': fields.float('salary or bonus (F CFA)', required=True),
        'worker_pers_emerg': fields.char('Name', size=128, required=True),
        'details': fields.text('Description'),
        'worker_numb_emerg': fields.char('Phone number', size=128, required=True),
        'active': fields.boolean('Active', help="If a casual staff is not active, it will not be displayed in POC"),
         # image: all image fields are base64 encoded and PIL-supported
        'image': fields.binary("Photo",
            help="This field holds the image used as photo for the employee, limited to 1024x1024px."),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized photo", type="binary", multi="_get_image",
            store = {
                'hr.employee': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized photo of the employee. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved. "\
                 "Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized photo", type="binary", multi="_get_image",
            store = {
                'hr.employee': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized photo of the employee. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
    }
        
    def _get_default_image(self, cr, uid, context=None):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))
#recuperer les information sur l'utilisateur a partir de son id
    def info_user(self, cr, uid, worker_id, context=None):
        users = self.read(cr, uid, worker_id,['name', 'worker_sal','type_contrat', 'worker_intern','worker_spec'])
        return users

   


    _defaults = {
        'image': _get_default_image,
        'active' : True
    }

    _sql_constraints = [
        ('uniq_cni', 'unique(worker_nic)', "A ID of national identity card already exists with this number in your business. National identity card's ID must be unique!"),
    ]











#declaration de la base pour stocker les presence des employés

class apgebat_poc_tally(osv.osv):
    _name = 'apgebat.poc.tally'
    _order = 'name asc'

    _columns = {
        'name': fields.many2one('apgebat.poc','Name', required=True),
        'tally_spec': fields.related('name','worker_spec', readonly=True, type='char', relation='apgebat.poc', string='Speciality'),
        'tally_site': fields.many2one('project.project', 'Reference site', required=True),
        'tally_work': fields.boolean('Presence'),
        'datein': fields.date('Date', required=True),
        'fictif': fields.char('ok'),
        'state' : fields.selection([('draft', 'Unpaid'),('paye', 'Paid'),], 'State', readonly=True)
    }
#group les infos par site
    def info_site(self, cr, uid, filterdate, context=None):
        site = self.read_group(cr,uid,[('tally_work','=',True), ('id','=',filterdate)], ['name','tally_site'], ['tally_site'])
        return site
#groupe par travailleur
    def worker_task(self, cr, uid, site, context=None):
        result = self.read_group(cr,uid,[('tally_work','=',True),('tally_site','=',site)], ['name'], ['name'])
        return result
        
#requete pour faire le tri des informations et les stocker dans une table pour la vue payment
    def sql_bd_union(self, cr, uid, ids, filterdate, begin, end, context=None):
        res = {}
        #vide la table pour accueillir les new données
        cr.execute('''DELETE FROM apgebat_poc_payment''')
        cr.execute('''DELETE FROM apgebat_poc_payment_worker''')
        bd_site = self.pool.get('apgebat.poc.tally').info_site(cr, uid, filterdate)
        #raise osv.except_osv(_('Error!'), _(bd_site))
        if bd_site :
            nbr_site=len(bd_site)
            
            for x in range(nbr_site):
                cr.execute('''SELECT name FROM apgebat_poc_tally WHERE tally_work=%s AND tally_site=%s GROUP BY name''', (True, bd_site[x]['tally_site'][0]))
                worker_id =  [i[0] for i in cr.fetchall()]
                bd_worker = self.pool.get('apgebat.poc').info_user(cr, uid, worker_id)
                nbr_worker=len(bd_worker)
                paiesite=int(0)
                pre=[]
                jr=[]
                spec=[]
                worker_name=[]
                pay=[]
                statusw=[]
                taskid=[]
                stats=0
                #boucles pour enregistrer les données dans la base par site
                for o in range(nbr_worker):

                    cr.execute('''SELECT id, state FROM apgebat_poc_tally WHERE tally_work=%s AND tally_site=%s AND name=%s ''', (True, bd_site[x]['tally_site'][0],worker_id[o]))
                    task =  [i for i in cr.fetchall()]
                    task_status=[]
                    task_id=[]
                    for b in range(len(task)):
                        task_id.append(task[b][0])
                        task_status.append(task[b][1])
                    #raise osv.except_osv(_('Error!'), _(task_id))
                    nbre_task=len(task_id)
                    contrat=''
                    day=''
                    paie=0
                    stat=int(0)
                   
                    for a in range(nbre_task):
                        if task_status[a]=='paye':
                            stat+=0
                            if a+1 == nbre_task and stat==0:
                                if bd_worker[o]['type_contrat']=='day':
                                    day=round(bd_worker[o]['worker_sal'],2)
                                elif bd_worker[o]['type_contrat']=='week':
                                    day=round(bd_worker[o]['worker_sal']/7,2)
                                else:
                                    day=round(bd_worker[o]['worker_sal']/30,2)
                                paie='payé'
                        else:
                            stat+=1

                            if a+1 == nbre_task:
                                if bd_worker[o]['type_contrat']=='day':
                                    day=round(bd_worker[o]['worker_sal'],2)
                                    paie=round(day * stat,2)
                                elif bd_worker[o]['type_contrat']=='week':
                                    day=round(bd_worker[o]['worker_sal']/7,2)
                                    paie=round(day * stat,2)
                                else:
                                    day=round(bd_worker[o]['worker_sal']/30,2)
                                    paie=round(day * stat,2)

                    jr.append(day)
                    pre.append(stat)
                    spec.append(bd_worker[o]['worker_spec'])
                    pay.append(paie)
                    worker_name.append(bd_worker[o]['name'])
                    stats+=stat
                    if stats == 0:
                        status='paye'
                        statusw.append('paye')
                    else:
                        status='draft'
                        statusw.append('draft')
                    if isinstance(paie,float):
                        paiesite+= paie
                    taskid+= task_id

                #if not paiesite:
                    #paiesite="Payé"
                #raise osv.except_osv(_('Error'), _(jr))
                worker_list_id = self.pool.get('apgebat.poc.tally').worker_task(cr, uid, bd_site[x]['tally_site'][0])
                cr.execute('''INSERT INTO apgebat_poc_payment (site, worker_count, paie, site_build, state, task, begindate, enddate) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)''',(bd_site[x]['tally_site'][1], len(worker_list_id), paiesite, True, status, taskid, begin, end))
                cr.execute('''SELECT id FROM apgebat_poc_payment ORDER BY id DESC''')
                #recupere le dernier id inseré
                id_new = cr.fetchone()[0] 
                #stock tout les employés en fonction de leur site
                for s in range(len(worker_list_id)):
                    cr.execute('''INSERT INTO apgebat_poc_payment_worker (worker, sal, presence, spec, site_id, paie) VALUES(%s, %s, %s, %s, %s, %s)''',(worker_name[s], jr[s], pre[s], spec[s], id_new, pay[s]))
                id_new=''
                        
        
        return res

    _defaults = {
        'datein' : time.strftime('%Y-%m-%d',time.localtime()),
        #'fictif' : _sql_bd_union,
        'state' : 'draft',
        'tally_work' : True
    }


    def on_change_name(self, cr, uid, ids, name, context=None):
        values = {}
        if name:
            bd_worker = self.pool.get('apgebat.poc').browse(cr, uid, name, context=context)
            values = {'tally_site': bd_worker.ref_act,}
        return {'value': values}

    def build_ctx_periods(self, cr, uid, period_from_id, period_to_id, site=None):
        if period_from_id == period_to_id:
            return [period_from_id]
       
        if period_from_id > period_to_id:
            raise osv.except_osv(_('Error!'), _('Start period should precede then end period.'))
        if site:
            return self.search(cr, uid, [('datein', '>=', period_from_id), ('datein', '<=', period_to_id), ('tally_work', '=', True), ('tally_site', '=', site[0])])
        else:
            return self.search(cr, uid, [('datein', '>=', period_from_id), ('datein', '<=', period_to_id), ('tally_work', '=', True)])







class apgebat_poc_payment_wizard(osv.osv_memory):
    _name = 'apgebat.poc.payment.wizard'
    _order = 'site asc'

    _columns = {
        'site': fields.many2one('project.project', 'Reference site'),
        'beginweek': fields.date('Start date', required=True),
        'endweek': fields.date('End date', required=True),
    }

    _rec_name='site'
    def _calcul_week(self, cr, uid, context=None):
        date_1 = datetime.datetime.strptime(time.strftime('%Y-%m-%d',time.localtime()), "%Y-%m-%d")
        begin_date = date_1 - datetime.timedelta(days=7)
        return begin_date

    _defaults = {
        'beginweek' : _calcul_week,
    }

    def calcul_week(self, cr, uid, ids, beginweek, context=None):
        values = {}
        if beginweek:
            date_1 = datetime.datetime.strptime(beginweek, "%Y-%m-%d")
            end_date = date_1 + datetime.timedelta(days=7)
            values = {'endweek': end_date,}
        return {'value': values}

    def list_worker(self, cr, uid, ids, context=None):
        """
        Opens chart of Accounts
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        period_obj = self.pool.get('apgebat.poc.tally')
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]

        result = mod_obj.get_object_reference(cr, uid, 'apgebat_poc', 'action_apgebat_poc_payment')
        id = result and result[1] or False
        
        result = act_obj.read(cr, uid, [id], context=context)[0]

        result['periods'] = []
        period_from = data.get('beginweek', False) and data['beginweek'][0] or False
        period_to = data.get('endweek', False) and data['endweek'][0] or False
        if data['beginweek'] and data['endweek'] and data['site']:
            result['periods'] = period_obj.build_ctx_periods(cr, uid, data['beginweek'], data['endweek'], data['site'])
        else:
            result['periods'] = period_obj.build_ctx_periods(cr, uid, data['beginweek'], data['endweek'])
        period_obj.sql_bd_union(cr, uid, ids, result['periods'], data['beginweek'], data['endweek'])
        values = {'datein': result['periods'],}
        result['context'] = str({'periods': result['periods'],'value': values})
        #raise osv.except_osv(_('Error'), _(data['site']))
        return result

    






class apgebat_poc_payment(osv.osv):

    _name = 'apgebat.poc.payment'
    
    _columns = {
        'site': fields.char('Site', readonly=True),
        'worker': fields.char('Name'),
        'sal': fields.float('Daily wage'),
        'spec':fields.char('Speciality'),
        'paie': fields.float('To pay', readonly=True),
        'worker_count': fields.integer('Number of workers', readonly=True),
        'site_id': fields.char('site_id'),
        'site_build': fields.boolean('site?'),
        'workin': fields.one2many('apgebat.poc.payment.worker', 'site_id', string='Payment Lines', readonly=True),
        'state' : fields.selection([('draft', 'Unpaid'),('paye', 'Paid'),]),
        'task' : fields.char('task_id'),
        'begindate' : fields.date('Date'),
        'enddate' : fields.date('Date'),

    }
    _rec_name= 'site'

    _defaults = {
        'state' : 'draft',
    }

    def payer(self, cr, uid, ids, context=None):
        self.pool.get('apgebat.poc.payment').write(cr, uid, ids, {'state': 'paye'})
        pays = self.pool.get('apgebat.poc.payment').browse(cr, uid, ids, context=context)
        part1=pays.task.split('{')
        part2=part1[1].split('}')
        taskid=part2[0].split(',')
        for i in range(len(taskid)):
            self.pool.get('apgebat.poc.tally').write(cr, uid, int(taskid[i]), {'state': 'paye'})



    







class apgebat_poc_payment_worker(osv.osv):

    _name = 'apgebat.poc.payment.worker'
    
    _columns = {
        'worker': fields.char('Name'),
        'sal': fields.float('Daily wage'),
        'spec':fields.char('Speciality'),
        'paie': fields.char('To pay'),
        'presence': fields.integer('presence'),
        'site_id': fields.integer('site_id'),
    }
