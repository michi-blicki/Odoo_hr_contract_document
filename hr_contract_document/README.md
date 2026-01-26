# HR Contract Document Management

## Overview

This Odoo 18 Community Edition addon extends the `hr_contract` module with a comprehensive document and template management system for employment contracts.

## Features

### 📋 Contract Templates
- **Structured Templates**: Create and manage reusable contract templates
- **Version Control**: Track template versions for audit and history
- **Multi-language Support**: Create templates in different languages
- **Template Types**: Support for employment contracts, amendments, termination letters, and more
- **Dynamic Placeholders**: Use `${field_name}` syntax to insert dynamic data

### 🧩 Text Blocks
- **Reusable Content**: Create text blocks for common clauses and sections
- **Categorization**: Organize blocks by category (header, clause, condition, footer, signature)
- **Multi-language**: Support for translated text blocks
- **Easy Reference**: Use `${text_block.code}` to insert blocks into templates

### 📄 Document Generation
- **Automatic Generation**: Generate documents from templates with one click
- **Placeholder Replacement**: Automatically replace all placeholders with actual data
- **Document States**: Track document lifecycle (Draft, Ready, Signed, Cancelled)
- **Version Tracking**: Keep track of which template version was used
- **Regeneration**: Update document content if template changes (only for draft documents)

### ✍️ Signature Management
- **Digital Signatures**: Store employee and employer signatures
- **Signature Dates**: Track when documents were signed
- **State Management**: Control document flow through different states

### 🖨️ Print & Export
- **PDF Export**: Generate professional PDF documents
- **Print Ready**: Format documents for printing
- **Signature Inclusion**: Include signatures in printed documents

## Available Placeholders

### Employee Fields
- `${employee.name}` - Employee name
- `${employee.identification_id}` - ID number
- `${employee.address_home_id.street}` - Street
- `${employee.address_home_id.city}` - City
- `${employee.address_home_id.zip}` - ZIP code
- `${employee.birthday}` - Birth date
- `${employee.work_email}` - Work email
- `${employee.mobile_phone}` - Mobile phone

### Contract Fields
- `${contract.name}` - Contract reference
- `${contract.date_start}` - Start date
- `${contract.date_end}` - End date
- `${contract.wage}` - Wage
- `${contract.job_id.name}` - Job position
- `${contract.department_id.name}` - Department
- `${contract.resource_calendar_id.name}` - Working schedule

### Company Fields
- `${company.name}` - Company name
- `${company.street}` - Company street
- `${company.city}` - Company city
- `${company.zip}` - Company ZIP
- `${company.country_id.name}` - Company country
- `${company.phone}` - Company phone
- `${company.email}` - Company email

### Other
- `${current_date}` - Current date
- `${text_block.code}` - Insert text block content

## Usage

### 1. Create Text Blocks (Optional)
1. Go to **HR > Contracts > Contract Documents > Text Blocks**
2. Click **Create**
3. Fill in:
   - Name: A descriptive name
   - Code: A unique code (e.g., `confidentiality_clause`)
   - Category: Select appropriate category
   - Language: Select language
   - Content: Enter the text content (HTML supported)
4. Save

### 2. Create Contract Template
1. Go to **HR > Contracts > Contract Documents > Templates**
2. Click **Create**
3. Fill in:
   - Template Name: e.g., "Standard Employment Contract"
   - Version: e.g., "1.0"
   - Template Type: Select type
   - Language: Select language
   - Description: Describe the template
4. In the **Template Content** tab:
   - Enter your template content using HTML
   - Use placeholders like `${employee.name}` for dynamic data
   - Use `${text_block.code}` to insert text blocks
5. (Optional) In the **Text Blocks** tab:
   - Select text blocks to associate with this template
6. Save

### 3. Generate Document from Contract
1. Go to **HR > Contracts > Contracts**
2. Open an existing contract
3. Click on the **Documents** tab
4. Click **Generate New Document**
5. Select a template
6. Customize the document name if needed
7. Click **Generate Document**
8. Review the generated document with all placeholders replaced

### 4. Manage Document Lifecycle
1. Open a generated document
2. Review the content
3. Click **Set Ready** when the document is ready for signature
4. Upload employee and employer signatures in the **Signatures** tab
5. Click **Mark as Signed** when both parties have signed
6. Print or export to PDF using the **Print** button

## Installation

1. Copy the `hr_contract_document` folder to your Odoo addons directory
2. Update the apps list: **Apps > Update Apps List**
3. Search for "HR Contract Document Management"
4. Click **Install**

## Dependencies

- `base`
- `hr`
- `hr_contract`

## Technical Details

### Models

#### `hr.contract.template`
Main model for contract templates with versioning and multi-language support.

#### `hr.contract.text.block`
Reusable text snippets that can be referenced in templates.

#### `hr.contract.document`
Generated documents with tracking, signatures, and state management.

#### `hr.contract` (extended)
Extended to include document management functionality.

### Security

The module uses Odoo's standard HR contract security groups:
- **HR Contract User**: Can view templates and text blocks, create/edit documents
- **HR Contract Manager**: Full access to all features

## Demo Data

The module includes demo data with:
- 3 sample text blocks (confidentiality, termination, signature)
- 1 sample employment contract template

To see the demo data, install the module with demo data enabled.

## Version History

### Version 1.0.0
- Initial release
- Template management with versioning
- Text block system
- Document generation with placeholder replacement
- Multi-language support
- Signature management
- PDF export

## Support

For issues, questions, or contributions, please contact the module author.

## License

LGPL-3

## Author

Michi Blicki
