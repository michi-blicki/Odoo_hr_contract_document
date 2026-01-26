from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrContractDocumentWizard(models.TransientModel):
    _name = 'hr.contract.document.wizard'
    _description = 'Generate Contract Document Wizard'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contract',
        required=True,
        readonly=True
    )
    
    template_id = fields.Many2one(
        'hr.contract.template',
        string='Template',
        required=True,
        domain="[('active', '=', True)]"
    )
    
    template_type = fields.Selection(
        related='template_id.template_type',
        string='Template Type',
        readonly=True
    )
    
    language = fields.Selection(
        related='template_id.language',
        string='Language',
        readonly=True
    )
    
    document_name = fields.Char(
        string='Document Name',
        compute='_compute_document_name',
        store=True,
        readonly=False
    )

    @api.depends('contract_id', 'template_id')
    def _compute_document_name(self):
        for wizard in self:
            if wizard.contract_id and wizard.template_id:
                wizard.document_name = f"{wizard.template_id.name} - {wizard.contract_id.employee_id.name}"
            else:
                wizard.document_name = ''

    def action_generate(self):
        """Generate the document"""
        self.ensure_one()
        
        if not self.template_id:
            raise UserError(_('Please select a template.'))
        
        # Generate document
        document = self.template_id.generate_document(self.contract_id)
        
        # Override name if customized
        if self.document_name and self.document_name != document.name:
            document.name = self.document_name
        
        # Open the created document
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract.document',
            'view_mode': 'form',
            'res_id': document.id,
            'target': 'current',
        }
