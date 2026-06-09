# SPDX-License-Identifier: LGPL-3.0-or-later
import ast
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.models import BaseModel
from odoo.tools.safe_eval import safe_eval


class HrContractDocumentSnippet(models.Model):
    _name = "hr.contract.document.snippet"
    _description = "HR Contract Document Snippet"
    _inherit = ["mail.thread"]
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    content_html = fields.Html(string="Content", sanitize=True)
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
    force_page_break_before = fields.Boolean(
        string="Force Page Break Before",
        default=False,
        help="If enabled, this snippet starts on a new PDF page.",
    )
    company_ids = fields.Many2many(
        "res.company",
        "hr_contract_document_snippet_company_rel",
        "snippet_id",
        "company_id",
        string="Companies",
        default=lambda self: [(6, 0, [self.env.company.id])],
    )

    _EXPRESSION_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}", re.DOTALL)
    _CONDITION_TAG_PATTERN = re.compile(
        r"\{%\s*(if|elif|else|endif)(?:\s+(.*?))?\s*%\}", re.DOTALL
    )
    _ALLOWED_ROOT_NAMES = {"contract", "employee"}

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
        """Extract variable expressions from content."""
        for rec in self:
            rec.placeholder_fields = ", ".join(f"{{{{ {expr} }}}}" for expr in rec._extract_expressions())

    # ----------------------------------------------------------
    #                       UTILITIES
    # ----------------------------------------------------------

    def _extract_expressions(self):
        if not self.content_html:
            return []
        expressions = []
        for expression in self._EXPRESSION_PATTERN.findall(self.content_html):
            clean_expression = expression.strip()
            if clean_expression and clean_expression not in expressions:
                expressions.append(clean_expression)
        return expressions

    def _extract_condition_expressions(self):
        """Return all condition expressions from {% if %}/{% elif %} tags."""
        if not self.content_html:
            return []
        expressions = []
        for tag, expression in self._CONDITION_TAG_PATTERN.findall(self.content_html):
            if tag not in {"if", "elif"}:
                continue
            clean_expression = (expression or "").strip()
            if clean_expression and clean_expression not in expressions:
                expressions.append(clean_expression)
        return expressions

    def _extract_placeholders(self):
        """Backward-compatible alias for expression extraction."""
        return self._extract_expressions()

    def _validate_expression(self, expression: str):
        """Validate expression syntax and permitted root variables."""
        try:
            expr_ast = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise ValidationError(
                _("Invalid expression '{{ %s }}': %s") % (expression, exc.msg or str(exc))
            ) from exc

        found_names = {node.id for node in ast.walk(expr_ast) if isinstance(node, ast.Name)}
        disallowed_names = found_names - self._ALLOWED_ROOT_NAMES
        if disallowed_names:
            raise ValidationError(
                _(
                    "Expression '{{ %s }}' uses unsupported root variable(s): %s. "
                    "Use only 'contract' and/or 'employee'."
                )
                % (expression, ", ".join(sorted(disallowed_names)))
            )

        for node in ast.walk(expr_ast):
            if isinstance(node, ast.Call):
                raise ValidationError(
                    _("Expression '{{ %s }}' contains function calls, which are not allowed.")
                    % expression
                )
            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                raise ValidationError(
                    _(
                        "Expression '{{ %s }}' accesses private attributes, which are not allowed."
                    )
                    % expression
                )

    def _build_eval_context(self, contract):
        employee = contract.employee_id if contract else self.env["hr.employee"]
        return {
            "contract": contract,
            "employee": employee,
        }

    def _evaluate_expression(self, expression: str, contract):
        """Evaluate one expression in a restricted context."""
        self._validate_expression(expression)
        eval_context = self._build_eval_context(contract)
        try:
            return safe_eval(expression, eval_context, mode="eval", nocopy=True)
        except Exception as exc:
            raise ValidationError(
                _("Could not resolve expression '{{ %s }}': %s") % (expression, str(exc))
            ) from exc

    def _evaluate_condition_expression(self, expression: str, contract):
        """Evaluate one condition expression and coerce to bool."""
        value = self._evaluate_expression(expression, contract)
        return bool(value)

    def _format_expression_value(self, value):
        if value is None or value is False:
            return ""

        if isinstance(value, BaseModel):
            if not value:
                return ""
            if len(value) == 1:
                return value.display_name
            return ", ".join(value.mapped("display_name"))

        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(item) for item in value)

        return str(value)

    def _render_condition_blocks(self, html: str, contract):
        """Render {% if/elif/else/endif %} blocks before expression substitution."""
        tokens = []
        cursor = 0
        for match in self._CONDITION_TAG_PATTERN.finditer(html):
            if match.start() > cursor:
                tokens.append(("text", html[cursor : match.start()], None))
            tokens.append(("tag", match.group(1), (match.group(2) or "").strip()))
            cursor = match.end()
        if cursor < len(html):
            tokens.append(("text", html[cursor:], None))

        def parse_block(index, stop_tags):
            out = []
            while index < len(tokens):
                token_type, token_value, token_expr = tokens[index]
                if token_type == "text":
                    out.append(token_value)
                    index += 1
                    continue

                if token_value in stop_tags:
                    return "".join(out), index, token_value, token_expr

                if token_value == "if":
                    rendered, index = parse_if(index)
                    out.append(rendered)
                    continue

                raise ValidationError(
                    _("Unexpected condition tag '{%% %s %%}' in snippet '%s'.")
                    % (token_value, self.name)
                )

            if stop_tags:
                raise ValidationError(
                    _("Missing '{%% endif %%}' in snippet '%s'.") % self.name
                )
            return "".join(out), index, None, None

        def parse_if(index):
            branches = []
            _, tag, condition_expression = tokens[index]
            if not condition_expression:
                raise ValidationError(
                    _("Tag '{%% if %%}' requires a condition in snippet '%s'.") % self.name
                )
            index += 1

            while True:
                body, index, stop_tag, stop_expr = parse_block(index, {"elif", "else", "endif"})
                branches.append((condition_expression, body))

                if stop_tag == "elif":
                    condition_expression = (stop_expr or "").strip()
                    if not condition_expression:
                        raise ValidationError(
                            _("Tag '{%% elif %%}' requires a condition in snippet '%s'.")
                            % self.name
                        )
                    index += 1
                    continue

                else_body = ""
                if stop_tag == "else":
                    index += 1
                    else_body, index, stop_tag, _ = parse_block(index, {"endif"})

                if stop_tag != "endif":
                    raise ValidationError(
                        _("Missing '{%% endif %%}' in snippet '%s'.") % self.name
                    )

                for branch_condition, branch_body in branches:
                    if self._evaluate_condition_expression(branch_condition, contract):
                        return branch_body, index + 1
                return else_body, index + 1

        rendered_html, _, _, _ = parse_block(0, set())
        return rendered_html

    def _render_placeholder_content(self, contract):
        """Replace {{ expression }} blocks in HTML content using contract context."""
        html = self.content_html or ""
        html = self._render_condition_blocks(html, contract)

        def _replace_expression(match):
            expression = match.group(1).strip()
            if not expression:
                return ""
            value = self._evaluate_expression(expression, contract)
            return self._format_expression_value(value)

        return self._EXPRESSION_PATTERN.sub(_replace_expression, html)
