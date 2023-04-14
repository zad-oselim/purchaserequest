from odoo import api, fields, models


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'

    purchase_request_id = fields.Many2one(comodel_name="purchase.request", string="Purchase Request", )
    product_id = fields.Many2one(comodel_name="product.product", string="Product ID", required=True)
    description = fields.Char(string="Description", related="product_id.name")
    quantity = fields.Float(string="Quantity", default=1)
    cost_price = fields.Float(string="Cost Price", readonly=1, related="product_id.standard_price")
    price = fields.Float(string="Price", readonly=1, compute="get_price")

    @api.depends("quantity", "cost_price")
    def get_price(self):
        for rec in self:
            rec.price = rec.quantity * rec.cost_price


    # def product_id_changes(self):
    #     for lp in self:
    #         if len(self.product_id) == 0:


