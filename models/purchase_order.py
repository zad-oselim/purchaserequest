from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.constrains('product_qty')
    def _check_qty(self):
        for line in self:
            if line.order_id.purchase_request_id:
                pr_line = line.order_id.purchase_request_id.line_ids.filtered(lambda l: l.product_id == line.product_id)
                if pr_line and line.quantity > pr_line.quantity:
                    raise ValidationError('PO quantity cannot exceed PR quantity')
