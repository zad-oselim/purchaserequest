# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError


# noinspection PyTypeChecker
class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'request_name'

    request_name = fields.Char(string="Request Name", required=True, )
    user_id = fields.Many2one(comodel_name="res.users", string="Requested by", required=True,
                              default=lambda self: self.env.user, )
    start_date = fields.Date(string="Start Date", default=fields.Date.today, )

    end_date = fields.Date(string="End Date", required=True, )
    purchase_manager_group = fields.Many2many('res.users', string='Purchase Managers')
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True, )
    order_lines_ids = fields.One2many(comodel_name="purchase.request.line", inverse_name="purchase_request_id",
                                      string="Order Lines", )
    total_price = fields.Float(string="Total Price", compute="get_total", )
    state = fields.Selection(selection=[('draft', 'Draft'), ('to_be_approved', 'To Be Approved'),
                                        ('approve', 'Approve'), ('reject', 'Reject'),
                                        ('cancel', 'Cancel'), ], required=True, default="draft", tracking=True,
                             readonly=True, track_visibility='onchange', )
    confirmed_po_qty = fields.Float(string='Confirmed PO Quantity', compute='_compute_confirmed_po_qty')

    def _compute_confirmed_po_qty(self):
        for request in self:
            confirmed_qty = 0.0
            # for po in request.order_lines_ids.filtered(lambda p: p.state == 'purchase'):
            for po in request.order_lines_ids:
                if request.state == "approve":
                    for line in po.purchase_request_id:
                        if line.product_id in request.order_lines_ids.product_id:
                            confirmed_qty += line.quantity
            request.confirmed_po_qty = confirmed_qty

    def create_purchase_order(self):
        PurchaseOrder = self.env['purchase.order']
        for request in self:
            po_vals = {
                'purchase_request_id': request.id,
                'purchase_request_id': []
            }
            for line in request.order_lines_ids:
                remaining_qty = line.quantity - request.confirmed_po_qty
                if remaining_qty > 0:
                    po_vals['purchase_request_id'].append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'quantity': remaining_qty,
                        'product_uom': line.product_uom_id.id,
                        'price_unit': line.price_unit,
                        'taxes_id': [(6, 0, line.taxes_id.ids)]
                    }))
            po = PurchaseOrder.create(po_vals)
            request.order_lines_ids |= po

    # def button_create_po_visible(self):
    #     self.ensure_one()
    #     return self.confirmed_po_qty < sum(self.mapped('order_lines_ids.quantity'))

    def button_draft(self):
        for r in self:
            r.state = "draft"

    def button_to_be_approved(self):
        for re in self:
            if len(re.order_lines_ids) > 0:
                re.state = "to_be_approved"
            else:
                raise UserError(_('Please insert one product id at least'))
                # or
                # raise ValidationError(_('End Date Should Be Greater Than Start Date!'))

    def button_approve(self):
        for r in self:
            r.state = "approve"
            subject = f"Purchase Request ( {self.request_name} ) has been approved"
            body = f"Dear all,\n\nThe following purchase request has been approved: {self.request_name} \n\nBest " \
                   f"regards,\nAdmin"
            email_to = self.purchase_manager_group.mapped('email')
            mail_values = {
                'email_to': ','.join(email_to),
                'subject': subject,
                'body': body,
            }
            self.env['mail.mail'].create(mail_values).send()

    def button_reject(self):
        view_id = self.env.ref('purchaserequest.view_my_wizard_form').id
        return {
            'name': _('Reject Purchase Request'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'purchase.request.wizard',
            'views': [(view_id, 'form')],
            'target': 'new',
        }

    def action_report(self):
        report = self.env.ref('purchaserequest.report_purchase_request').render(self.ids)
        pdf = self.env['report'].pdfmerge([report])
        return self.env['report'].report_action(pdf, 'purchase_request_report')

    def action_confirm_rejection(self):
        # Set the rejection reason field and reject the purchase request
        self.rejection_reason = self.env.context.get('rejection_reason')
        self.button_reject()

    def button_cancel(self):
        for r in self:
            r.state = "cancel"

    @api.depends('order_lines_ids')
    def get_total(self):
        for r in self:
            r.total_price = 0.0
            for line in r.order_lines_ids:
                r.total_price += line.price

    @api.constrains('start_date', 'end_date')
    def date(self):
        for r in self:
            if r.start_date > r.end_date:
                raise UserError(_('End Date must be greater than Start Date'))
