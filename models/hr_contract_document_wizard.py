# SPDX-License-Identifier: LGPL-3.0-or-later
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrContractCreateWizard(models.TransientModel):
    _name = "hr.contract.create.wizard"
    _description = "Wizard: Create Contract from Template"

    template_id = fields.Many2one("hr.contract.document.template", required=True, string="Document Template")
    contract_id = fields.Many2one("hr.contract", string="Target Contract")
    optional_snippet_ids = fields.Many2many(
        "hr.contract.document.snippet", string="Optional Snippets"
    )
    optional_attachment_ids = fields.Many2many(
        "hr.contract.document.attachment", string="Optional Attachments"
    )

    def action_generate_contract_pdf(self):
        """Render and attach contract PDF using selected template."""
        self.ensure_one()
        contract = self.contract_id
        template = self.template_id

        if template.state != "active":
            raise ValidationError(_("The selected template is not active."))

        template.validate_placeholders(contract=contract)
        html_content = template._render_template_content(contract)
        pdf = self.env["ir.actions.report"]._render_qweb_pdf(
            "hr_contract_document.report_contract_document",
            [contract.id],
            data={"html": html_content},
        )[0]

        # store rendered pdf as attachment
        self.env["ir.attachment"].create(
            {
                "name": f"Contract_{contract.name}_v{template.version}.pdf",
                "res_model": "hr.contract",
                "res_id": contract.id,
                "type": "binary",
                "datas": pdf.encode("base64"),
                "mimetype": "application/pdf",
            }
        )
        return {"type": "ir.actions.act_window_close"}
