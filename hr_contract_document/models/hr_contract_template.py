from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class HrContractTemplate(models.Model):
    _name = 'hr.contract.template'
    _description = 'Contract Template'
    _order = 'sequence, name, version desc'
    _rec_name = 'display_name'

    name = fields.Char(
        string='Template Name',
        required=True,
        translate=True,
        help='Name of the contract template'
    )
    version = fields.Char(
        string='Version',
        required=True,
        default='1.0',
        help='Template version number'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence for ordering templates'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to archive the template'
    )
    template_type = fields.Selection([
        ('employment', 'Employment Contract'),
        ('amendment', 'Contract Amendment'),
        ('termination', 'Termination Letter'),
        ('other', 'Other Document'),
    ], string='Template Type', required=True, default='employment')
    
    language = fields.Selection(
        selection='_get_languages',
        string='Language',
        required=True,
        default='en_US',
        help='Language of the template'
    )
    
    content = fields.Html(
        string='Template Content',
        required=True,
        translate=True,
        help='Template content with placeholders. Use ${field_name} for placeholders.'
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help='Description of the template purpose and usage'
    )
    
    placeholder_help = fields.Html(
        string='Available Placeholders',
        compute='_compute_placeholder_help',
        help='List of available placeholders'
    )
    
    text_block_ids = fields.Many2many(
        'hr.contract.text.block',
        string='Text Blocks',
        help='Reusable text blocks that can be referenced in the template'
    )
    
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    _sql_constraints = [
        ('name_version_unique', 'unique(name, version, language)',
         'A template with this name, version and language already exists!')
    ]

    @api.depends('name', 'version')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} (v{record.version})"

    def _get_languages(self):
        """Get installed languages"""
        return self.env['res.lang'].get_installed()

    def _compute_placeholder_help(self):
        """Generate help text for available placeholders"""
        help_text = """
        <h4>Available Placeholders:</h4>
        <h5>Employee Fields:</h5>
        <ul>
            <li>${employee.name} - Employee name</li>
            <li>${employee.identification_id} - ID number</li>
            <li>${employee.address_home_id.name} - Home address</li>
            <li>${employee.address_home_id.street} - Street</li>
            <li>${employee.address_home_id.city} - City</li>
            <li>${employee.address_home_id.zip} - ZIP code</li>
            <li>${employee.birthday} - Birth date</li>
            <li>${employee.work_email} - Work email</li>
            <li>${employee.mobile_phone} - Mobile phone</li>
        </ul>
        <h5>Contract Fields:</h5>
        <ul>
            <li>${contract.name} - Contract reference</li>
            <li>${contract.date_start} - Start date</li>
            <li>${contract.date_end} - End date</li>
            <li>${contract.wage} - Wage</li>
            <li>${contract.job_id.name} - Job position</li>
            <li>${contract.department_id.name} - Department</li>
            <li>${contract.resource_calendar_id.name} - Working schedule</li>
        </ul>
        <h5>Company Fields:</h5>
        <ul>
            <li>${company.name} - Company name</li>
            <li>${company.street} - Company street</li>
            <li>${company.city} - Company city</li>
            <li>${company.zip} - Company ZIP</li>
            <li>${company.country_id.name} - Company country</li>
            <li>${company.phone} - Company phone</li>
            <li>${company.email} - Company email</li>
        </ul>
        <h5>Text Blocks:</h5>
        <p>Use ${text_block.code} to insert text block content</p>
        <h5>Current Date:</h5>
        <ul>
            <li>${current_date} - Current date</li>
        </ul>
        """
        for record in self:
            record.placeholder_help = help_text

    def _compute_document_count(self):
        """Compute number of documents using this template"""
        for record in self:
            record.document_count = self.env['hr.contract.document'].search_count([
                ('template_id', '=', record.id)
            ])

    @api.constrains('content')
    def _check_content(self):
        """Validate that content is not empty"""
        for record in self:
            if not record.content or record.content.strip() == '<p><br></p>':
                raise ValidationError(_('Template content cannot be empty.'))

    def action_view_documents(self):
        """Action to view documents created from this template"""
        self.ensure_one()
        action = self.env.ref('hr_contract_document.action_hr_contract_document').read()[0]
        action['domain'] = [('template_id', '=', self.id)]
        action['context'] = {'default_template_id': self.id}
        return action

    def get_placeholder_values(self, contract):
        """
        Get placeholder values for a contract
        Returns a dictionary of placeholder keys and their values
        """
        self.ensure_one()
        
        values = {}
        
        if not contract:
            return values
        
        # Employee fields
        if contract.employee_id:
            employee = contract.employee_id
            
            # Format birthday safely
            birthday_str = ''
            if employee.birthday:
                try:
                    birthday_str = employee.birthday.strftime('%d.%m.%Y')
                except (AttributeError, ValueError):
                    birthday_str = str(employee.birthday) if employee.birthday else ''
            
            values.update({
                'employee.name': employee.name or '',
                'employee.identification_id': employee.identification_id or '',
                'employee.birthday': birthday_str,
                'employee.work_email': employee.work_email or '',
                'employee.mobile_phone': employee.mobile_phone or '',
            })
            
            # Home address
            if employee.address_home_id:
                address = employee.address_home_id
                values.update({
                    'employee.address_home_id.name': address.name or '',
                    'employee.address_home_id.street': address.street or '',
                    'employee.address_home_id.city': address.city or '',
                    'employee.address_home_id.zip': address.zip or '',
                })
        
        # Contract fields
        # Format dates safely
        date_start_str = ''
        if contract.date_start:
            try:
                date_start_str = contract.date_start.strftime('%d.%m.%Y')
            except (AttributeError, ValueError):
                date_start_str = str(contract.date_start) if contract.date_start else ''
        
        date_end_str = ''
        if contract.date_end:
            try:
                date_end_str = contract.date_end.strftime('%d.%m.%Y')
            except (AttributeError, ValueError):
                date_end_str = str(contract.date_end) if contract.date_end else ''
        
        values.update({
            'contract.name': contract.name or '',
            'contract.date_start': date_start_str,
            'contract.date_end': date_end_str,
            'contract.wage': f"{contract.wage:,.2f}" if contract.wage else '0.00',
            'contract.job_id.name': contract.job_id.name if contract.job_id else '',
            'contract.department_id.name': contract.department_id.name if contract.department_id else '',
            'contract.resource_calendar_id.name': contract.resource_calendar_id.name if contract.resource_calendar_id else '',
        })
        
        # Company fields
        company = contract.company_id or self.env.company
        values.update({
            'company.name': company.name or '',
            'company.street': company.street or '',
            'company.city': company.city or '',
            'company.zip': company.zip or '',
            'company.country_id.name': company.country_id.name if company.country_id else '',
            'company.phone': company.phone or '',
            'company.email': company.email or '',
        })
        
        # Current date
        values['current_date'] = fields.Date.today().strftime('%d.%m.%Y')
        
        return values

    def replace_placeholders(self, content, contract):
        """
        Replace placeholders in content with actual values
        """
        self.ensure_one()
        
        if not content:
            return content
        
        # Get placeholder values
        values = self.get_placeholder_values(contract)
        
        # Replace text block placeholders first
        for text_block in self.text_block_ids:
            pattern = r'\$\{text_block\.' + re.escape(text_block.code) + r'\}'
            content = re.sub(pattern, text_block.content or '', content)
        
        # Replace field placeholders
        for key, value in values.items():
            pattern = r'\$\{' + re.escape(key) + r'\}'
            content = re.sub(pattern, str(value), content)
        
        return content

    def generate_document(self, contract):
        """
        Generate a document from this template for the given contract
        """
        self.ensure_one()
        
        # Replace placeholders
        content = self.replace_placeholders(self.content, contract)
        
        # Create document
        document = self.env['hr.contract.document'].create({
            'name': f"{self.name} - {contract.employee_id.name}",
            'contract_id': contract.id,
            'template_id': self.id,
            'template_version': self.version,
            'content': content,
            'language': self.language,
        })
        
        return document
