from odoo import api, fields, models, _


class POWizard(models.TransientModel):
    _name = 'po.wizard'
    request_id = fields.Many2one('purchase.request', string='Purchase Request', )
    request_name = fields.Char(string="Request Name", required=True, related='request_id.request_name', )
    user_id = fields.Many2one(comodel_name="res.users", string="Requested by", required=True,
                              default=lambda self: self.env.user, related='request_id.user_id', )
    start_date = fields.Date(string="Start Date", default=fields.Date.today, related='request_id.start_date', )

    end_date = fields.Date(string="End Date", required=True, related='request_id.end_date', )
    total_price = fields.Float(string="Total Price", compute="get_total", related='request_id.total_price', )
    order_lines_ids = fields.Many2many(comodel_name="purchase.request.line", inverse_name="purchase_request_id",
                                       string="Order Lines", compute="order_line_ids", readonly=False, )
    confirmed_po_qty = fields.Float(string='Confirmed PO Quantity', compute='_compute_confirmed_po_qty')

    def _compute_confirmed_po_qty(self):
        for request in self:
            confirmed_qty = 0.0
            for po in request.order_lines_ids.filtered(lambda p: p.state == 'approve'):
                for line in po.order_line:
                    if line.product_id in request.order_lines_ids.product_id:
                        confirmed_qty += line.quantity
            request.confirmed_po_qty = confirmed_qty

    def create_purchase_order(self):
        PurchaseOrder = self.env['purchase.order']
        for wizard in self:
            po_vals = {
                'partner_id': wizard.user_id.partner_id.id,
                'order_line': []
            }
            for line in wizard.order_lines_ids:
                po_vals['order_line'].append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                }))
            po = PurchaseOrder.create(po_vals)
            # wizard.request_id.po_ids |= po

    @api.onchange('request_id')
    def onchange_request_id(self):
        for wizard in self:
            if wizard.request_id:
                wizard.order_lines_ids = [(5, 0, 0)]
                for line in wizard.request_id.order_lines_ids:
                    remaining_qty = line.quantity - wizard.confirmed_po_qty
                    if remaining_qty > 0:
                        wizard.order_lines_ids += wizard.order_lines_ids.new({
                            'product_id': line.product_id.id,
                            'quantity': remaining_qty,
                        })

    @api.depends('request_id.order_lines_ids')
    def order_line_ids(self):
        self.order_lines_ids = self.request_id.order_lines_ids.ids
