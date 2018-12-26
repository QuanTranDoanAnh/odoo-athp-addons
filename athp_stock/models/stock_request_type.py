from odoo import models, fields, api

class StockRequestType(models.Model):
    _name = "athp.stock.request.type"
    _description = "The request type determines the document number"
    _order = 'sequence, id'

    name = fields.Char('Request Types Name', required=True, translate=True)
    color = fields.Integer('Color')
    sequence = fields.Integer('Sequence', help="Used to order the 'All Request Types' kanban view")
    sequence_id = fields.Many2one('ir.sequence', 'Reference Sequence', required=True)
    default_location_src_id = fields.Many2one(
        'stock.location', 'Default Source Location',
        help="This is the default source location when you create a picking manually with this operation type. It is possible however to change it or that the routes put another location. If it is empty, it will check for the supplier location on the partner. ")
    default_location_dest_id = fields.Many2one(
        'stock.location', 'Default Destination Location',
        help="This is the default destination location when you create a picking manually with this operation type. It is possible however to change it or that the routes put another location. If it is empty, it will check for the customer location on the partner. ")
    code = fields.Selection([('incoming', 'Inbound'), ('outgoing', 'Outbound'), ('internal', 'Internal Transfer')], 'Type of Operation', required=True)
    active = fields.Boolean('Active', default=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse', ondelete='cascade',
        default=lambda self: self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1))
