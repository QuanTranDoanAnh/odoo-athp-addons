from odoo import fields, models, api, _
import datetime
from odoo.exceptions import ValidationError, UserError

class StockRequest(models.Model):
    _name = 'athp.stock.request'

    def _default_request_type_id(self):
        default_request_type_code = self.env.context.get('default_request_type_code', False)
        if default_request_type_code:
            warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
            return self.env['athp.stock.request.type'].search([('code','=',default_request_type_code),('warehouse_id','=',warehouse_id.id)])[0].id
        return False

    name = fields.Char('Reference', default='/')
    partner_id = fields.Many2one('res.partner', string="Partner",
        required=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('stock.move'),
        index=True, required=True)
    doc_num = fields.Char(string="Document Number",
        required=True)
    partner_req_date = fields.Date(string="Partner Request Date", required=True, default=lambda self: self._default_partner_req_date())
    driver_name = fields.Char(string="Driver Name")
    truck_reg_num = fields.Char(string="Truck Registration Number")
    driver_id_num = fields.Char(string="Driver Identity Number")
    notes = fields.Text(string="Notes")
    partner_person_name = fields.Char(string="Partner Contact Name")
    person_responsible = fields.Many2one('res.users', string="Person In Responsible")
    request_type_id = fields.Many2one('athp.stock.request.type', string="Request Type", 
        default=_default_request_type_id,
        required=True)
    request_type_code = fields.Selection([
        ('incoming', "Inbound"),
        ('outgoing', "Outbound"),
        ('internal', "Internal Transfer")
    ], related='request_type_id.code', readonly=True)
    state = fields.Selection(string="State", selection=[
        ('draft', "Draft"),
        ('submitted', "Submitted"),
        ('confirmed', "Validated"),
        ('done', "Done"),
        ('canceled', "Canceled")
    ], default='draft')
    location_id = fields.Many2one('stock.location', string="Source Location")
    location_dest_id = fields.Many2one('stock.location', string="Destination Location")
    stock_request_line_ids = fields.One2many('athp.stock.request.line', 'stock_request_id', string="Request Lines")
    stock_request_unregproductline_ids = fields.One2many('athp.stock.request.unregproductline', 'stock_request_id', string="Unregistered Product Lines")
    stock_picking_ids = fields.One2many('stock.picking', 'stock_request_id', string="Stock Pickings")
    submission_date = fields.Datetime(default=None)
    validation_date = fields.Datetime(default=None)
    completion_date = fields.Datetime(default=None)
    has_unreg_products = fields.Boolean(compute='_count_unreg_products', store=False)
    has_stock_pickings = fields.Boolean(compute='_count_stock_pickings', store=False)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    @api.onchange('request_type_id')
    def _onchange_request_type_id(self):
        # Set default picking type id
        picking_types = self.env['stock.picking.type'].search([('code','=', self.request_type_id.code)])
        if picking_types:
            self.picking_type_id = picking_types[0].id
    
    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        if self.picking_type_id:
            if self.picking_type_id.default_location_src_id:
                location_id = self.picking_type_id.default_location_src_id.id
            elif self.partner_id:
                location_id = self.partner_id.property_stock_supplier.id
            else:
                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

            if self.picking_type_id.default_location_dest_id:
                location_dest_id = self.picking_type_id.default_location_dest_id.id
            elif self.partner_id:
                location_dest_id = self.partner_id.property_stock_customer.id
            else:
                location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

            if self.state == 'draft':
                self.location_id = location_id
                self.location_dest_id = location_dest_id

    @api.depends('stock_request_unregproductline_ids')
    def _count_unreg_products(self):
        self.has_unreg_products = len(self.stock_request_unregproductline_ids) > 0

    @api.depends('stock_picking_ids')
    def _count_stock_pickings(self):
        self.has_stock_pickings = len(self.stock_picking_ids) > 0

    @api.multi
    def _default_partner_req_date(self):
        cur_date = datetime.datetime.now().date()
        new_date = cur_date + datetime.timedelta(days=1)
        return new_date

    @api.model
    def create(self, vals):
        # TDE FIXME: clean that brol
        defaults = self.default_get(['name', 'request_type_id'])
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('request_type_id', defaults.get('request_type_id')):
            vals['name'] = self.env['athp.stock.request.type'].browse(vals.get('request_type_id', defaults.get('request_type_id'))).sequence_id.next_by_id()
        if vals.get('doc_num', '/') and defaults.get('doc_num', '/') == '/':
            vals['doc_num'] = vals['name']   
        res = super(StockRequest, self).create(vals)
        return res

    def action_submit(self):
        self._merge_registered_unregproductlines()
        self.write({'state': 'submitted', 'submission_date': fields.Datetime.now()})
        return self
    
    def action_confirm(self):
        self._check_unreg_products()
        self._create_todo_stock_picking()
        self.write({'state': 'confirmed', 'validation_date': fields.Datetime.now()})
        return self
    
    def action_execute(self):
        done = True
        for picking in self.stock_picking_ids:
            if picking.state != 'done':
                done = False
                break
        if done:
            self.write({'state': 'done', 'completion_date': fields.Datetime.now()})
    
    def _check_unreg_products(self):
        for req in self:
            count_unreg = len(req.stock_request_unregproductline_ids)
            if count_unreg > 0:
                raise ValidationError(_("There are {} products still being unregistered. You need to process them.").format(count_unreg))

    def _merge_registered_unregproductlines(self):
        Product = self.env['product.product']
        RequestLine = self.env['athp.stock.request.line']
        for unreg in self.stock_request_unregproductline_ids:
            if unreg.partner_ext_code:
                product = Product.search([('partner_ext_code','=', unreg.partner_ext_code),('owner_id','=',self.partner_id.id)], limit=1)
                if product:
                    # add to request line and delete from unregistered product list
                    line = RequestLine.create({
                        'product_id': product.id,
                        'product_uom_id': unreg.product_uom_id.id,
                        'product_uom_qty': unreg.product_uom_qty,
                        'stock_request_id': self.id,
                        'state': self.state,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'source_document_notes': unreg.source_document_notes
                    })
                    if line:
                        self.write({'stock_request_line_ids': [(4, line.id)]})
                        unreg.unlink()


    def _create_todo_stock_picking(self):
        self.ensure_one()
        # create picking
        Picking = self.env['stock.picking']
        picking = Picking.create(self._prepare_picking_values())
        if not picking:
            raise UserError(_("Cannot create a stock picking from this request"))
        # create stock moves for this picking
        Move = self.env['stock.move']
        for line in self.stock_request_line_ids:
            move = Move.create({
                'name': '/',
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom_id.id,
                'product_uom_qty': line.product_uom_qty
            })
            if not move:
                raise UserError(_("Cannot add a stock move line for the product {}.").format(line.product_id.name))
            picking.write({'move_lines': [(4,move.id)]})
        self.write({'stock_picking_ids':[(4, picking.id)]})

    def _prepare_picking_values(self):
        """ Prepares a new picking for this stock request as it could not be assigned to
        another picking. This method is designed to be inherited. """
        return {
            'origin': self.doc_num,
            'company_id': self.company_id.id,
            'move_type': 'direct',
            'partner_id': self.partner_id.id,
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'picking_type_code': self.request_type_code
        }