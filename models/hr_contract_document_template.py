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
    snippet_ids = fields.One2many(
        "hr.contract.document.snippet", "template_id", string="Text Snippets"
    )
    attachment_ids = fields.One2many(
        "hr.contract.document.attachment", "template_id", string="Attachments"
    )
    signer_rule_ids = fields.One2many(
        "hr.contract.document.signer.rule", "template_id", string="Signer Rules"
    )

    css_style = fields.Text(string="Custom CSS for Report")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
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

    def validate_placeholders(self):
        """Ensure all placeholders from snippets exist in known contract context."""
        allowed_keys = self._get_allowed_placeholder_keys()
        for snip in self.snippet_ids:
            unknown = [ph for ph in snip._extract_placeholders() if ph not in allowed_keys]
            if unknown:
                raise ValidationError(
                    _("Invalid placeholders in snippet %s: %s") % (snip.name, ", ".join(unknown))
                )

    @api.model
    def _get_allowed_placeholder_keys(self):
        """Define whitelisted placeholders based on hr.contract + hr.employee fields."""
        return [
            "employee_name",
            "employee_job_title",
            "contract_date_start",
            "contract_date_end",
            "contract_wage",
            "contract_company",
        ]

    def _render_template_content(self, contract):
        """Render all snippets and return concatenated HTML for QWeb."""
        ctx = {
            "employee": contract.employee_id,
            "contract": contract,
        }
        html_parts = []
        for snip in self.snippet_ids.sorted("sequence"):
            html_parts.append(snip._render_placeholder_content(ctx))
        return "\n".join(html_parts)
