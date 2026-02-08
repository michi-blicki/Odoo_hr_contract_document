# SPDX-License-Identifier: LGPL-3.0-or-later
import re
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrContractDocumentSnippet(models.Model):
    _name = "hr.contract.document.snippet"
    _description = "HR Contract Document Snippet"
    _inherit = ["mail.thread"]
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    content_html = fields.Html(string="Content", sanitize=True, widget='summernote')
    is_mandatory = fields.Boolean(default=False)
    placeholder_fields = fields.Char(string="Placeholders", compute="_compute_placeholders", store=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("review", "In Review"),
            ("active", "Active"),
            ("archived", "Archived"),
        ],
        default="draft",
    )
    version = fields.Integer(default=1)
    template_id = fields.Many2one("hr.contract.document.template", string="Template")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    # ----------------------------------------------------------
    #                       BUSINESS LOGIC
    # ----------------------------------------------------------

    def action_send_to_review(self):
        """Move snippet from Draft to Review state."""
        for snippet in self:
            if snippet.state == "draft":
                snippet.state = "review"
                snippet.version += 1

    def action_activate(self):
        """Move snippet from Review to Active state."""
        for snippet in self:
            if snippet.state == "review":
                snippet.state = "active"
                snippet.version += 1

    def action_archive(self):
        """Archive the snippet (mark as archived)."""
        for snippet in self:
            if snippet.state in ("draft", "review", "active"):
                snippet.state = "archived"

    def action_reset_to_draft(self):
        """Reset snippet from Review/Active back to Draft state."""
        for snippet in self:
            if snippet.state in ("review", "active"):
                snippet.state = "draft"

    # ----------------------------------------------------------
    #                       COMPUTATIONS
    # ----------------------------------------------------------

    @api.depends("content_html")
    def _compute_placeholders(self):
        """Extract placeholder keys from content."""
        for rec in self:
            rec.placeholder_fields = ", ".join(rec._extract_placeholders())

    # ----------------------------------------------------------
    #                       UTILITIES
    # ----------------------------------------------------------

    def _extract_placeholders(self):
        if not self.content_html:
            return []
        return re.findall(r"\$\{([\w_]+)\}", self.content_html)

    def _render_placeholder_content(self, context: dict):
        """Replace placeholders in HTML content using context values."""
        html = self.content_html or ""
        placeholders = self._extract_placeholders()
        for ph in placeholders:
            value = self._resolve_placeholder_value(ph, context)
            html = html.replace(f"${{{ph}}}", str(value) if value is not None else "")
        return html

    def _resolve_placeholder_value(self, ph: str, ctx: dict):
        """Resolve placeholder value based on predefined keys."""
        employee = ctx.get("employee")
        contract = ctx.get("contract")

        mapping = {
            "employee_name": employee.name if employee else "",
            "employee_job_title": employee.job_id.name if employee and employee.job_id else "",
            "contract_date_start": contract.date_start if contract else "",
            "contract_date_end": contract.date_end if contract else "",
            "contract_wage": contract.wage if contract else "",
            "contract_company": contract.company_id.name if contract and contract.company_id else "",
        }
        return mapping.get(ph)
