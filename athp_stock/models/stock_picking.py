from odoo import fields, models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    stock_request_id = fields.Many2one('athp.stock.request', string="Stock Request")