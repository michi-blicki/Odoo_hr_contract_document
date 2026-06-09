# SPDX-License-Identifier: LGPL-3.0-or-later
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrContractDocumentTemplate(models.Model):
    _name = "hr.contract.document.template"
    _description = "HR Contract Document Template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, version desc"

    name = fields.Char(string="Template Name", required=True, tracking=True)
    version = fields.Integer(string="Version", default=1, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("review", "In Review"),
            ("active", "Active"),
            ("archived", "Archived"),
        ],
        default="draft",
        string="Status",
        tracking=True,
    )
    snippet_ids = fields.Many2many(
        "hr.contract.document.snippet",
        "hr_contract_document_template_snippet_rel",
        "template_id",
        "snippet_id",
        string="Text Snippets",
    )
    attachment_ids = fields.One2many(
        "hr.contract.document.attachment", "template_id", string="Attachments"
    )
    signer_rule_ids = fields.One2many(
        "hr.contract.document.signer.rule", "template_id", string="Signer Rules"
    )

    css_style = fields.Text(string="Custom CSS for Report")
    company_ids = fields.Many2many(
        "res.company",
        "hr_contract_document_template_company_rel",
        "template_id",
        "company_id",
        string="Companies",
        default=lambda self: [(6, 0, [self.env.company.id])],
    )
    country_id = fields.Many2one("res.country", string="Country")
    active = fields.Boolean(default=True)

    # ----------------------------------------------------------
    #                       BUSINESS LOGIC
    # ----------------------------------------------------------

    def action_activate(self):
        """Activate the template and create new version if required."""
        for template in self:
            if template.state != "active":
                template.state = "active"
                template.version += 1

    def action_archive(self):
        """Archive the template."""
        for template in self:
            template.state = "archived"
            template.active = False

    def validate_placeholders(self, contract=None):
        """Validate {{ expression }} syntax and optionally test evaluation on a contract."""
        for snip in self.snippet_ids:
            for condition_expression in snip._extract_condition_expressions():
                try:
                    snip._validate_expression(condition_expression)
                    if contract:
                        snip._evaluate_condition_expression(condition_expression, contract)
                except ValidationError as exc:
                    raise ValidationError(
                        _("Invalid condition in snippet '%s': %s") % (snip.name, exc)
                    ) from exc
            for expression in snip._extract_expressions():
                try:
                    snip._validate_expression(expression)
                    if contract:
                        snip._evaluate_expression(expression, contract)
                except ValidationError as exc:
                    raise ValidationError(
                        _("Invalid expression in snippet '%s': %s") % (snip.name, exc)
                    ) from exc

    def _render_template_content(self, contract):
        """Render all snippets and return concatenated HTML for QWeb."""
        html_parts = []
        for snip in self.snippet_ids.sorted("sequence"):
            html_parts.append(snip._render_placeholder_content(contract))
        return "\n".join(html_parts)
