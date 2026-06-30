{
    'name': 'HR Contract Document Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Contracts',
    'summary': 'Document and Template Management System for Employment Contracts',
    'description': """
HR Contract Document Management
================================

This module extends the hr_contract module with a powerful document and template 
management system for employment contracts.

Key Features:
-------------
* Structured, versioned contract templates
* Multilingual template support
* Reusable text building blocks
* Dynamic placeholders from employee and contract models
* Document generation with placeholder replacement
* Print and signature-ready documents
* Version tracking for contracts

Technical Details:
------------------
* Compatible with Odoo 18 Community Edition
* Extends hr_contract base module
* Provides complete document lifecycle management
    """,
    'author': 'Michi Blicki',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'hr_contract',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_template_views.xml',
        'views/hr_contract_text_block_views.xml',
        'views/hr_contract_document_views.xml',
        'views/hr_contract_views.xml',
        'wizard/hr_contract_document_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
