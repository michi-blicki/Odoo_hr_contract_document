# SPDX-License-Identifier: LGPL-3.0-or-later
from odoo import fields, models


class HrContractDocumentAttachment(models.Model):
    _name = "hr.contract.document.attachment"
    _description = "HR Contract Document Attachment"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True)
    document_ref_id = fields.Many2one("ir.attachment", string="Attachment Reference")
    version = fields.Char(string="Version Tag")
    is_mandatory = fields.Boolean(default=False)
    language = fields.Selection(
        [("de", "German"), ("en", "English"), ("fr", "French"), ("it", "Italian")],
        string="Language",
    )
    state = fields.Selection(
        [("active", "Active"), ("archived", "Archived")],
        default="active",
    )
    template_id = fields.Many2one("hr.contract.document.template", string="Parent Template")
