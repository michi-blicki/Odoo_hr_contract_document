from odoo import models, fields, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    document_ids = fields.One2many(
        'hr.contract.document',
        'contract_id',
        string='Documents',
        help='Documents generated for this contract'
    )
    
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count'
    )

    @api.depends('document_ids')
    def _compute_document_count(self):
        """Compute number of documents for this contract"""
        for record in self:
            record.document_count = len(record.document_ids)

    def action_view_documents(self):
        """Action to view contract documents"""
        self.ensure_one()
        action = self.env.ref('hr_contract_document.action_hr_contract_document').read()[0]
        action['domain'] = [('contract_id', '=', self.id)]
        action['context'] = {'default_contract_id': self.id}
        return action

    def action_generate_document(self):
        """Action to generate a new document from template"""
        self.ensure_one()
        
        # Open wizard to select template
        return {
            'name': _('Generate Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract.document.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
            }
        }
