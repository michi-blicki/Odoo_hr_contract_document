from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrContractTextBlock(models.Model):
    _name = 'hr.contract.text.block'
    _description = 'Contract Text Block'
    _order = 'category, sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help='Name of the text block'
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        help='Unique code used to reference this text block in templates (e.g., clause_1)'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence for ordering text blocks'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to archive the text block'
    )
    
    category = fields.Selection([
        ('header', 'Header'),
        ('clause', 'Contract Clause'),
        ('condition', 'Condition'),
        ('footer', 'Footer'),
        ('signature', 'Signature Block'),
        ('other', 'Other'),
    ], string='Category', required=True, default='clause',
       help='Category of the text block')
    
    content = fields.Html(
        string='Content',
        required=True,
        translate=True,
        help='Text block content'
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help='Description of the text block purpose'
    )
    
    language = fields.Selection(
        selection='_get_languages',
        string='Language',
        required=True,
        default='en_US',
        help='Language of the text block'
    )
    
    template_ids = fields.Many2many(
        'hr.contract.template',
        string='Used in Templates',
        help='Templates using this text block'
    )
    
    usage_count = fields.Integer(
        string='Usage Count',
        compute='_compute_usage_count'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    _sql_constraints = [
        ('code_unique', 'unique(code, language)',
         'A text block with this code and language already exists!')
    ]

    def _get_languages(self):
        """Get installed languages"""
        return self.env['res.lang'].get_installed()

    @api.depends('template_ids')
    def _compute_usage_count(self):
        """Compute number of templates using this text block"""
        for record in self:
            record.usage_count = len(record.template_ids)

    @api.constrains('content')
    def _check_content(self):
        """Validate that content is not empty"""
        for record in self:
            if not record.content or record.content.strip() == '<p><br></p>':
                raise ValidationError(_('Text block content cannot be empty.'))

    @api.constrains('code')
    def _check_code(self):
        """Validate code format"""
        for record in self:
            if not record.code:
                raise ValidationError(_('Text block code is required.'))
            if not record.code.replace('_', '').isalnum():
                raise ValidationError(_(
                    'Text block code must contain only alphanumeric characters and underscores.'
                ))

    def name_get(self):
        """Custom name_get to show code and name"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
