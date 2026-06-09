# SPDX-License-Identifier: LGPL-3.0-or-later
import base64
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrContractDocumentExtension(models.Model):
    """
    Extension of hr.contract to integrate contract document templates.
    
    Adds reference to contract document templates and enables
    PDF generation from templates for contracts.
    """
    _inherit = "hr.contract"

    document_template_id = fields.Many2one(
        "hr.contract.document.template",
        string="Contract Document Template",
        help="Select the contract document template to use for this contract. "
             "Leave empty if using standard contract type.",
        tracking=True,
    )

    # ----------------------------------------------------------
    #                       BUSINESS LOGIC
    # ----------------------------------------------------------

    def action_generate_contract_document(self):
        """
        Generate and attach PDF document from selected template.
        
        Creates a PDF from the selected contract document template
        with placeholders resolved to actual contract/employee data.
        Attaches the PDF to this contract.
        """
        for contract in self:
            if not contract.document_template_id:
                raise ValidationError(
                    _("No contract document template selected. "
                      "Please select a template before generating the document.")
                )

            template = contract.document_template_id

            # Validate template is active
            if template.state != "active":
                raise ValidationError(
                    _("The selected template is not in 'Active' state. "
                      "Please activate the template before using it.")
                )

            # Validate all snippets have valid placeholders
            template.validate_placeholders(contract=contract)

            # Render template content with contract data
            html_content = template._render_template_content(contract)

            # Generate PDF via QWeb report
            pdf_binary, _report_type = self.env["ir.actions.report"]._render_qweb_pdf(
                "hr_contract_document.report_contract_document",
                [contract.id],
                data={"html_content": html_content},
            )

            # Create attachment record
            generated_at = datetime.now().strftime("%Y-%m-%d_%H%M")
            filename = (
                f"Contract_{contract.employee_id.name}_"
                f"v{template.version}_{generated_at}.pdf"
            ).replace(" ", "_")

            self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "res_model": "hr.contract",
                    "res_id": contract.id,
                    "type": "binary",
                    "datas": base64.b64encode(pdf_binary),
                    "mimetype": "application/pdf",
                    "description": (
                        f"Contract document generated from template "
                        f"'{template.name}' v{template.version}"
                    ),
                }
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Contract Document Generated"),
                "message": _("PDF has been generated and attached to the contract."),
                "type": "success",
                "sticky": False,
            },
        }
