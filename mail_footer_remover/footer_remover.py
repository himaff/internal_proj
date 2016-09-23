# coding: utf8
from openerp.osv import osv
from openerp import tools, SUPERUSER_ID
#from openerp import models, api

class mail_mail(osv.Model):
    _inherit = 'mail.mail'

    def send_get_mail_body(self, cr, uid, mail, partner=None, context=None):
        """Return a specific ir_email body. The main purpose of this method
        is to be inherited to add custom content depending on some module."""
        body = mail.body_html

        return body

#pour masker le footer send by your compagny et odoo


#class FooterlessNotification(models.Model):
 #   _inherit = 'mail.notification'

 #   @api.model
 #   def get_signature_footer(self, user_id, res_model=None, res_id=None, context=None, user_signature=True):
  #      return ""