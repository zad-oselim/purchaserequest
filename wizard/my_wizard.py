from odoo import api, fields, models


class MyWizard(models.TransientModel):
    _name = 'my.wizard'
    _description = 'My Wizard'
    rejection_reason = fields.Text(string="Rejection Reason", required=True, )
    rejection_reason_id = fields.Many2one(comodel_name="purchase.request", string="Rejection Reason ID",
                                          required=False, )

    # Add more fields as required

    def action_confirm(self):
        # Get the active purchase request
        request = self.env['purchase.request'].browse(self.env.context.get('active_id'))

        # Set the rejection reason and reject the purchase request
        # request.write({'rejection_reason': self.rejection_reason, 'state': 'reject'})

        reasons = self.env["my.wizard"].create({
            "rejection_reason_id": request.id,
            "rejection_reason": self.rejection_reason
        })

        # request.button_reject()

        return {'type': 'ir.actions.act_window',
                "res_model": "purchase.request",
                "res_id": request.id,
                "view_mode": "form",
                "target": "main"}
