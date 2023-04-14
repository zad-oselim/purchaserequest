from odoo import api, fields, models


class MyWizard(models.TransientModel):
    _name = 'my.wizard'
    _description = 'My Wizard'
    rejection_reason = fields.Text(string="Rejection Reason", required=True, )

    # Add more fields as required

    def action_confirm(self):
        # Get the active purchase request
        request = self.env['purchase.request'].browse(self.env.context.get('active_id'))

        # Set the rejection reason and reject the purchase request
        request.write({'rejection_reason': self.rejection_reason, 'state': 'reject'})
        request.button_reject()

        return {'type': 'ir.actions.act_window_close'}
