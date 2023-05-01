from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    # _inherit = 'purchase.order.line'

    purchase_request_id = fields.Many2one(comodel_name="purchase.request", string="Purchase Request", )
    product_id = fields.Many2one(comodel_name="product.product", string="Product ID", required=True)
    description = fields.Char(string="Description", related="product_id.name")
    quantity = fields.Float(string="Quantity", default=1)
    cost_price = fields.Float(string="Cost Price", readonly=1, related="product_id.standard_price")
    price = fields.Float(string="Price", readonly=1, compute="get_price")

    @api.constrains('quantity')
    def _check_qty(self):
        for line in self:
            if line.purchase_request_id:
                pr_line = line.purchase_request_id.order_lines_ids.filtered(
                    lambda l: l.product_id == line.product_id)
                if pr_line and line.quantity > pr_line.quantity:
                    raise ValidationError('PO quantity cannot exceed PR quantity')

    @api.depends("quantity", "cost_price")
    def get_price(self):
        for rec in self:
            rec.price = rec.quantity * rec.cost_price

    # @api.constrains('quantity')
    # def _check_qty(self):
    #     for line in self:
    #         if line.order_id.purchase_request_id:
    #             pr_line = line.order_id.purchase_request_id.line_ids.filtered(lambda l: l.product_id == line.product_id)
    #             if pr_line and line.quantity > pr_line.quantity:
    #                 raise ValidationError('PO quantity cannot exceed PR quantity')
