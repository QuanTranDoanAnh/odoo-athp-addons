from odoo import fields, models, api

class StockRequestLine(models.Model):
    _name = 'athp.stock.request.line'

    product_id = fields.Many2one('product.product', string="Product")
    product_uom_id = fields.Many2one('product.uom', string="Unit of Measure")
    product_uom_qty = fields.Float(string="Requested Quantity")
    stock_request_id = fields.Many2one('athp.stock.request', string="Stock Request")
    state = fields.Selection(string="State", selection=[
        ('draft', "Draft"),
        ('submitted', "Submitted"),
        ('confirmed', "Validated"),
        ('done', "Done"),
        ('canceled', "Canceled")
    ], copy=False, default='draft', index=True, readonly=True)
    location_id = fields.Many2one('stock.location', string="Source Location")
    location_dest_id = fields.Many2one('stock.location', string="Destination Location")    
    source_document_notes = fields.Text(string="Source Document Notes")
    barcode = fields.Char(string="Barcode", readonly=False, store=False, related='product_id.barcode')
    partner_ext_code = fields.Char(string="Partner Code", readonly=False, store=False, related='product_id.partner_ext_code')

    @api.onchange('barcode')
    def _product_by_barcode(self):
        product_rec = self.env['product.product']
        if self.barcode:
            product = product_rec.search([('barcode','=',self.barcode)])
            if product:
                self.product_id = product[0].id
    
    @api.onchange('partner_ext_code')
    def _product_by_partner_ext_code(self):
        product_rec = self.env['product.product']
        if self.partner_ext_code:
            product = product_rec.search([('partner_ext_code','=',self.partner_ext_code)])
            if product:
                self.product_id = product[0].id