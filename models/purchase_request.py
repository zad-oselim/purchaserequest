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
    # purchase_manager_group = fields.Many2many('res.users', string='Purchase Managers')
    # rejection_reason = fields.Text(string="Rejection Reason", readonly=True, )
    rejection_reason_ids = fields.One2many(comodel_name="my.wizard", inverse_name="rejection_reason_id",
                                           string="Rejection Reasons", required=False, )
    order_lines_ids = fields.One2many(comodel_name="purchase.request.line", inverse_name="purchase_request_id",
                                      string="Order Lines", )
    total_price = fields.Float(string="Total Price", compute="get_total", )
    state = fields.Selection(selection=[('draft', 'Draft'), ('to_be_approved', 'To Be Approved'),
                                        ('approve', 'Approve'), ('reject', 'Reject'),
                                        ('cancel', 'Cancel'), ], required=True, default="draft", tracking=True,
                             readonly=True, track_visibility='onchange', )

    def create_purchase_order(self):
        return {
            'name': _('New Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

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
        partner_ids = self.manager_users()
        for r in self:
            r.state = "approve"
            subject = f"Purchase Request ( {self.request_name} ) has been approved"
            body = f"Dear all,\n\nThe following purchase request has been approved: {self.request_name} \n\nBest " \
                   f"regards,\nAdmin"
            mail_values = {
                'subject': subject,
                'body': body,
                'recipient_ids': [(4, pid) for pid in partner_ids],
            }
            self.env['mail.mail'].create(mail_values).send()

    def manager_users(self):
        group_ids = [self.env.ref('purchase.group_purchase_manager').id]
        partner_ids = []
        if len(group_ids) > 0:
            for group_id in group_ids:
                for user in self.env['res.users'].search([("groups_id", "=", group_id)]):
                    partner_ids.append(user.partner_id.id)
        return partner_ids

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

    def action_confirm_rejection(self):
        # Set the rejection reason field and reject the purchase request
        self.rejection_reason_ids = self.env.context.get('rejection_reason')
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

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     purchase_request_ids = fields.Many2many('purchase.request', string='Purchase Requests')
#
#     @api.model
#     def create(self, vals):
#         sale_order = super(SaleOrder, self).create(vals)
#         if 'purchase_request_ids' in vals:
#             purchase_requests = self.env['purchase.request'].browse(vals['purchase_request_ids'])
#             purchase_requests.write({'sale_order_id': sale_order.id})
#         return sale_order
