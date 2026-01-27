# -*- coding: utf-8 -*-
{
    'name': "HR Contract Document Management",

    'summary': "Manage, version and print structured HR contract templates with dynamic placeholders",

    'description': """
        HR Contract Document Management Addon
        =====================================
        This module extends Odoo HR Contracts to support:
        - Version-controlled, multi-language contract templates
        - Dynamic placeholders for employee & contract data
        - Structured snippets and attachments
        - Integrated QWeb reporting for printable contract PDFs
        - Role-based access control for HR users, specialists & signers

        Main Features
        --------------
        • Create reusable contract templates per company/country
        • Define text snippets with validation of placeholders
        • Include mandatory and optional attachments
        • Add dynamic signer rules (HR Manager, Supervisor, etc.)
        • Generate PDF via wizard and automatically attach to contract
        • Multi-company and audit-friendly design

        Intended for enterprise HR departments automating legal document workflows.
    """,

    #
    # Issuer Specification
    'author': "Michael Blickenstorfer",
    'website': "https://www.blicki.ch",
    'license': "AGPL-3",
    #'price': 120.00,
    #'currency': "CHF",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources/Employees',
    'version': '18.0.0.1.0',
    'application': True,
    'auto_install': False,
    'installable': True,

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'hr',
        'hr_contract',
        'mail',
        'web',
    ],

    # always loaded
    'data': [
        'security/hr_contract_document_group.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.hr_contract_document.xml',
        'views/contract_document_menu.xml',
        'views/hr_contract_document_template_views.xml',
        'views/hr_contract_document_snippet_views.xml',
        'views/hr_contract_document_attachments_views.xml',
        'views/hr_contract_document_signer_rules_views.xml',
        'views/hr_contract_document_wizard_views.xml',
        'report/hr_contract_document_qweb_template.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'hr_contract_document/static/src/js/editor_placeholder_dropdown.js',
            'hr_contract_document/staic/src/css/contract_report.css',
        ],
    },

    'translation_files': [

    ],

    # only loaded in demonstration mode
    'demo': [
        
    ],

    #
    # Hooks
    'pre_init_hook': '_pre_init_hook',
    'post_init_hook': '_post_init_hook',
    'uninstall_hook': '_uninstall_hook',

}

