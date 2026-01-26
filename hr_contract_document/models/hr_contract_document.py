from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrContractDocument(models.Model):
    _name = 'hr.contract.document'
    _description = 'Contract Document'
    _order = 'create_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Document Name',
        required=True,
        tracking=True,
        help='Name of the document'
    )
    
    contract_id = fields.Many2one(
        'hr.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Related employment contract'
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        related='contract_id.employee_id',
        store=True,
        readonly=True
    )
    
    template_id = fields.Many2one(
        'hr.contract.template',
        string='Template',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Template used to generate this document'
    )
    
    template_version = fields.Char(
        string='Template Version',
        required=True,
        help='Version of the template at generation time'
    )
    
    content = fields.Html(
        string='Document Content',
        required=True,
        help='Generated document content with replaced placeholders'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready for Signature'),
        ('signed', 'Signed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True, tracking=True)
    
    language = fields.Selection(
        selection='_get_languages',
        string='Language',
        required=True,
        default='en_US',
        help='Language of the document'
    )
    
    document_date = fields.Date(
        string='Document Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True,
        help='Date when the document was created'
    )
    
    signature_date = fields.Date(
        string='Signature Date',
        tracking=True,
        help='Date when the document was signed'
    )
    
    employee_signature = fields.Binary(
        string='Employee Signature',
        attachment=True,
        help='Employee signature image'
    )
    
    employer_signature = fields.Binary(
        string='Employer Signature',
        attachment=True,
        help='Employer/Company signature image'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional notes or comments'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='contract_id.company_id',
        store=True,
        readonly=True
    )
    
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Attachments',
        domain=[('res_model', '=', 'hr.contract.document')],
        help='Additional attachments related to this document'
    )

    def _get_languages(self):
        """Get installed languages"""
        return self.env['res.lang'].get_installed()

    @api.constrains('signature_date', 'document_date')
    def _check_signature_date(self):
        """Validate signature date is not before document date"""
        for record in self:
            if record.signature_date and record.document_date:
                if record.signature_date < record.document_date:
                    raise ValidationError(_(
                        'Signature date cannot be before document date.'
                    ))

    def action_set_ready(self):
        """Set document state to ready for signature"""
        for record in self:
            record.state = 'ready'

    def action_set_signed(self):
        """Set document state to signed"""
        for record in self:
            if not record.signature_date:
                record.signature_date = fields.Date.today()
            record.state = 'signed'

    def action_set_draft(self):
        """Set document state back to draft"""
        for record in self:
            record.state = 'draft'

    def action_cancel(self):
        """Cancel the document"""
        for record in self:
            record.state = 'cancelled'

    def action_regenerate(self):
        """Regenerate document content from template"""
        self.ensure_one()
        if self.state == 'signed':
            raise ValidationError(_(
                'Cannot regenerate a signed document. Please create a new version.'
            ))
        
        # Regenerate content
        new_content = self.template_id.replace_placeholders(
            self.template_id.content, 
            self.contract_id
        )
        
        self.write({
            'content': new_content,
            'template_version': self.template_id.version,
        })
        
        return True

    def action_print_document(self):
        """Print the document"""
        self.ensure_one()
        return self.env.ref('hr_contract_document.action_report_contract_document').report_action(self)

    def action_view_contract(self):
        """View the related contract"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
            'target': 'current',
        }
