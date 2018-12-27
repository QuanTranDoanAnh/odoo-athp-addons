from odoo import fields, models, api
from odoo.exceptions import UserError

class UnregisteredProductLines(models.Model):
    _name = 'athp.stock.request.unregproductline'

    partner_ext_code = fields.Char(string="Partner Code")
    name = fields.Char(string="")
    product_uom_id = fields.Many2one('product.uom', string="Unit of Measure")
    product_uom_qty = fields.Float(string="Requested Quantity")
    stock_request_id = fields.Many2one('athp.stock.request', string="Stock Request")
    location_id = fields.Many2one('stock.location', string="Source Location")
    location_dest_id = fields.Many2one('stock.location', string="Destination Location")
    source_document_notes = fields.Text(string="Source Document Notes")

    def accept_unreg(self):
        for unreg in self:
            product_rec = self.env['product.product']
            product = product_rec.create({
                'name': unreg.name,
                'partner_ext_code': unreg.partner_ext_code,
                'uom_id': unreg.product_uom_id.id,
                'uom_po_id': unreg.product_uom_id.id,
                'owner_id': self.stock_request_id.partner_id.id
            })
            if product and product.id:
                request_line = self.env['athp.stock.request.line'].create({
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'product_uom_qty': unreg.product_uom_qty,
                    'stock_request_id': self.stock_request_id.id,
                    'state': self.stock_request_id.state,
                    'location_id': self.stock_request_id.location_id.id,
                    'location_dest_id': self.stock_request_id.location_dest_id.id,
                    'source_document_notes': self.source_document_notes
                })
                if request_line and request_line.id:
                    self.stock_request_id.write({'stock_request_line_ids': [(4, request_line.id)]})
                self.unlink()
            else:
                raise UserError("Cannot accept unregistered products")

