from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    partner_ext_code = fields.Char(string='Product Code (Partner)')
