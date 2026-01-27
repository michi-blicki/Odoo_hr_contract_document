# SPDX-License-Identifier: LGPL-3.0-or-later
from odoo import fields, models


class HrContractDocumentSignerRule(models.Model):
    _name = "hr.contract.document.signer.rule"
    _description = "HR Contract Document Signer Rule"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    relation_rule = fields.Char(
        string="Signer Relation Rule",
        help="Python-like path expression, e.g. 'employee.parent_id.user_id'"
    )
    is_mandatory = fields.Boolean(default=True)
    template_id = fields.Many2one("hr.contract.document.template", string="Template")
