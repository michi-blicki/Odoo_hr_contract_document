# Copilot Instructions – HR Contract Document Management Module

**Module**: `hr_contract_document`  
**Version**: 18.0.0.1.0  
**Odoo Edition**: Community Edition 18  
**Author**: Michael Blickenstorfer  
**License**: LGPL-3

---

## 📋 Module Overview

The **hr_contract_document** module is an advanced contract document management system for Odoo 18 Community Edition. It extends the built-in `hr_contract` module to provide:

- **Versioned, multi-language contract templates** with lifecycle management (Draft → Review → Active → Archived)
- **Reusable text snippets** with placeholder support for dynamic content injection
- **Structured attachments** (documents, policies) with version tracking
- **Dynamic signer rules** to automatically determine contract signers
- **QWeb-based PDF rendering** with automated attachment to contracts
- **Complete audit trail** with versioning and immutability guarantees
- **Role-based access control** (Specialist, Admin, User, Signer)

### Key Features
- ✅ Template versioning with auto-increment
- ✅ Placeholder resolution from `hr.employee` and `hr.contract` models
- ✅ Mandatory vs. optional snippets and attachments
- ✅ Multi-company and multi-language support
- ✅ Integrated signer workflow configuration (future e-signature integration)
- ✅ PDF generation via transient wizard model
- ✅ Full mail thread integration for tracking

---

## 🧱 Data Model Architecture

### Core Models

| Model Name | Table | Purpose |
|-----------|-------|---------|
| `hr.contract.document.template` | `hr_contract_document_template` | Top-level container for versioned contract templates |
| `hr.contract.document.snippet` | `hr_contract_document_snippet` | Reusable text blocks with placeholders (ordered by sequence) |
| `hr.contract.document.attachment` | `hr_contract_document_attachment` | Reference documents with language/version metadata |
| `hr.contract.document.signer.rule` | `hr_contract_document_signer_rule` | Dynamic signer configuration (future e-signature integration) |
| `hr.contract.create.wizard` | `hr_contract_create_wizard` | Transient model for PDF generation workflow |

### Key Field Reference

#### Template Model Fields
- `name` (Char, required): Display name with tracking
- `version` (Integer, default=1): Auto-incremented on state transitions
- `state` (Selection): draft → review → active → archived
- `snippet_ids` (One2many): Child snippets ordered by sequence
- `attachment_ids` (One2many): Related documents/files
- `signer_rule_ids` (One2many): Signer definitions
- `css_style` (Text): Custom CSS for QWeb rendering
- `company_id` (Many2one `res.company`): Multi-company support
- `country_id` (Many2one `res.country`): Optional localization
- `active` (Boolean): For archive support

#### Snippet Model Fields
- `name` (Char, required): Snippet title
- `content_html` (Html, sanitized): Editable content with `${placeholder}` syntax
- `sequence` (Integer): Display order (smaller = first)
- `is_mandatory` (Boolean): Cannot be excluded from contract
- `placeholder_fields` (Char, computed): Auto-extracted placeholder keys
- `state` (Selection): draft → review → active → archived
- `version` (Integer): Incremented on content edit
- `template_id` (Many2one): Parent template reference

#### Attachment Model Fields
- `name` (Char, required): Document name
- `document_ref_id` (Many2one `ir.attachment`): Reference to actual file
- `version` (Char): Version tag or identifier
- `is_mandatory` (Boolean): Required for template
- `language` (Selection): de, en, fr, it
- `state` (Selection): active / archived
- `template_id` (Many2one): Parent template

#### Signer Rule Model Fields
- `name` (Char, required): Role title (e.g., "HR Manager")
- `sequence` (Integer): Processing order
- `relation_rule` (Char): Python-like path expression (e.g., `employee.parent_id.user_id`)
- `is_mandatory` (Boolean): Signer approval required?
- `template_id` (Many2one): Parent template

### Model Relationships Diagram

```
hr.contract.document.template (1)
    ├─── 1:N hr.contract.document.snippet
    ├─── 1:N hr.contract.document.attachment
    └─── 1:N hr.contract.document.signer.rule

hr.contract.create.wizard (Transient)
    ├─── N:1 hr.contract.document.template
    ├─── N:1 hr.contract (target contract)
    └─── N:M hr.contract.document.snippet (optional)
    └─── N:M hr.contract.document.attachment (optional)
```

---

## 🔄 State Workflow for Snippets

Snippets follow a **managed lifecycle** with explicit state transitions:

### State Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SNIPPET LIFECYCLE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────┐                                                   │
│  │Draft │ ◄─────────────────────────────┐                  │
│  └──┬───┘                                 │                  │
│     │ "Send to Review"                    │ "Reset"         │
│     │ action_send_to_review()             │                  │
│     ▼                                      │                  │
│  ┌──────────┐                              │                  │
│  │  Review  │ ◄─────────────────────┐      │                  │
│  └──┬───────┘                        │     │                  │
│     │ "Activate"                      │ "Reset"              │
│     │ action_activate()               │     │                │
│     ▼                                  │     │                │
│  ┌──────────┐                         │     │                │
│  │  Active  │ ◄──────────────────────┘     │                │
│  └──┬───────┘                              │                │
│     │ "Archive"                            │                │
│     │ action_archive()                     │                │
│     ▼                                      │                │
│  ┌──────────┐                              │                │
│  │ Archived │ ─────────────────────────────┘                │
│  └──────────┘  (Requires manual reset)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Allowed Transitions

| Current State | Available Actions | Next State |
|---------------|-------------------|-----------|
| **Draft** | Send to Review | Review |
| | Reset to Draft | (no change) |
| | Archive | Archived |
| **Review** | Activate | Active |
| | Reset to Draft | Draft |
| | Archive | Archived |
| **Active** | Archive | Archived |
| | Reset to Draft | Draft |
| **Archived** | (no direct transitions) | — |

### Use Cases

- **Draft → Review**: Content ready for approval, waiting for sign-off
- **Review → Active**: Content approved, can be included in templates
- **Active → Archived**: Content obsolete, hide from new templates
- **Review/Active → Draft**: Make edits after review cycle

### Button Visibility in Form

Buttons are automatically shown/hidden based on current state using the `invisible` attribute:

```xml
<!-- Only visible when state == 'draft' -->
<button name="action_send_to_review" invisible="state != 'draft'"/>

<!-- Only visible when state == 'review' -->
<button name="action_activate" invisible="state != 'review'"/>

<!-- Visible except when already archived -->
<button name="action_archive" invisible="state not in ('draft', 'review', 'active')"/>

<!-- Only visible when in review or active -->
<button name="action_reset_to_draft" invisible="state not in ('review', 'active')"/>
```

---

### Syntax
Placeholders use the simple, readable syntax: `${placeholder_name}`

### Supported Placeholders (Whitelisted)
| Placeholder | Maps To | Type | Example |
|-------------|---------|------|---------|
| `${employee_name}` | `contract.employee_id.name` | String | "John Doe" |
| `${employee_job_title}` | `contract.employee_id.job_id.name` | String | "Software Engineer" |
| `${contract_date_start}` | `contract.date_start` | Date | "2024-01-15" |
| `${contract_date_end}` | `contract.date_end` | Date | "2025-12-31" |
| `${contract_wage}` | `contract.wage` | Float | "5000.00" |
| `${contract_company}` | `contract.company_id.name` | String | "ACME Corp" |

### Resolution Flow

1. **Extraction**: Regex pattern `r'\$\{([\w_]+)\}'` extracts all placeholder keys from HTML content
2. **Validation**: Upon snippet save, system verifies all placeholders exist in whitelist
3. **Resolution**: During PDF rendering, `_resolve_placeholder_value()` replaces tokens with actual values
4. **Rendering**: `_render_placeholder_content()` returns final HTML with substituted values

### Example

**Template Content**:
```html
<p>Der Mitarbeiter ${employee_name} tritt am ${contract_date_start} seine Stelle an.</p>
<p>Position: ${employee_job_title}</p>
<p>Arbeitgeber: ${contract_company}</p>
```

**After Resolution**:
```html
<p>Der Mitarbeiter John Doe tritt am 2024-01-15 seine Stelle an.</p>
<p>Position: Software Engineer</p>
<p>Arbeitgeber: ACME Corp</p>
```

---

## 🔒 Security & Access Control

### User Groups (Defined in `hr_contract_document_groups.xml`)

| Group | ID | Purpose | Capabilities |
|-------|-----|---------|--------------|
| **HR Document Specialist** | `group_hr_contract_document_specialist` | Design & maintain templates | Full CRUD on templates, snippets, attachments, signer rules |
| **HR Administrator** | `group_hr_contract_document_admin` | Create contracts from templates | Read templates; Full CRUD on wizard; Create contracts |
| **HR User** | `group_hr_contract_document_user` | View-only access | Read-only on all models |
| **Signer/Manager** | `group_hr_contract_document_signer` | Sign contracts | Read-only on templates & related docs |

### Access Control Matrix (ir.model.access.csv)

```
Specialist:  [create] [read] [write] [unlink] on Templates/Snippets/Attachments/Signer Rules
Admin:       [read]         on Templates/Snippets/Attachments
             [create] [read] [write]        on Wizard
User:        [read]         on all models
Signer:      [read]         on all models
```

### Record Rules (`ir_rule.hr_contract_document.xml`)

- **Company Isolation**: Users see only templates/snippets from their assigned company
- **Active Records Only**: Archived templates/snippets hidden by default
- **Template Versioning**: Each version pinned to immutable state

---

## 📂 File & Directory Structure

```
hr_contract_document/
├── __init__.py                                 # Module initialization + hooks
├── __manifest__.py                             # Module metadata & dependencies
├── README.md                                   # User-facing documentation
├── copilot-instructions.md                     # This file
│
├── models/
│   ├── __init__.py                             # Model imports
│   ├── hr_contract_document_template.py        # Template model + business logic
│   ├── hr_contract_document_snippet.py         # Snippet model + placeholder engine
│   ├── hr_contract_document_attachment.py      # Attachment model
│   ├── hr_contract_document_signer_rule.py     # Signer rule model
│   └── hr_contract_document_wizard.py          # Transient wizard for PDF generation
│
├── views/
│   ├── contract_document_menu.xml              # Main menu structure
│   ├── hr_contract_document_template_views.xml # Template form & list views
│   ├── hr_contract_document_snippet_views.xml  # Snippet form & list views
│   ├── hr_contract_document_attachment_views.xml # Attachment form & list views
│   ├── hr_contract_document_signer_rule_views.xml # Signer rule views (WIP)
│   └── hr_contract_document_wizard_views.xml   # Wizard form for PDF generation
│
├── report/
│   └── hr_contract_document_qweb_template.xml  # QWeb template for PDF rendering
│
├── security/
│   ├── hr_contract_document_groups.xml         # User group definitions
│   ├── ir.model.access.csv                     # Model access permissions
│   └── ir_rule.hr_contract_document.xml        # Record rules (company, archival)
│
├── static/
│   ├── description/
│   │   ├── icon.png                            # Module icon
│   │   ├── banner.png                          # Module banner (store listing)
│   │   └── index.html                          # Module description HTML
│   └── src/
│       ├── js/
│       │   └── editor_placeholder_dropdown.js  # Placeholder insertion helper JS
│       └── css/
│           └── contract_report.css             # PDF report styling
│
├── docs/
│   └── architecture.md                         # Detailed technical architecture
│
└── controllers/
    └── __init__.py                             # Controllers (currently minimal)
```

---

## 🔌 Key Methods & APIs

### Template Model Methods

#### `action_activate()`
```python
def action_activate(self):
    """Activate template and auto-increment version."""
```
- Sets state to "active"
- Increments version counter
- Called from template form actions

#### `action_archive()`
```python
def action_archive(self):
    """Archive template and mark inactive."""
```
- Sets state to "archived"
- Sets active = False
- Hidden from UI by default

#### `validate_placeholders()`
```python
def validate_placeholders(self):
    """Ensure all snippet placeholders exist in whitelist."""
```
- Iterates all child snippets
- Extracts placeholders via regex
- Raises `ValidationError` if unknown keys found
- Called before PDF generation

#### `_get_allowed_placeholder_keys()` (Static)
```python
@api.model
def _get_allowed_placeholder_keys(self):
    """Return list of whitelisted placeholder keys."""
    return ["employee_name", "employee_job_title", "contract_date_start", ...]
```
- Defines what placeholders are valid
- **Extend this method to add new placeholders**

#### `_render_template_content(contract)`
```python
def _render_template_content(self, contract):
    """Render all snippets with placeholder substitution."""
```
- Builds context dict from `contract` & `contract.employee_id`
- Iterates snippets sorted by sequence
- Returns concatenated HTML for QWeb

### Snippet Model Methods

#### `action_send_to_review()`
```python
def action_send_to_review(self):
    """Move snippet from Draft to Review state."""
```
- Transitions snippet: **Draft → Review**
- Increments version counter
- Called via form button

#### `action_activate()`
```python
def action_activate(self):
    """Move snippet from Review to Active state."""
```
- Transitions snippet: **Review → Active**
- Increments version counter
- Only available if state is "review"

#### `action_archive()`
```python
def action_archive(self):
    """Archive the snippet (mark as archived)."""
```
- Transitions snippet to: **Archived**
- Available from draft, review, or active states
- Marks snippet as "inactive" (hidden by default)

#### `action_reset_to_draft()`
```python
def action_reset_to_draft(self):
    """Reset snippet from Review/Active back to Draft state."""
```
- Transitions snippet back to: **Draft**
- Useful for making edits after review
- Available from review or active states
```python
@api.depends("content_html")
def _compute_placeholders(self):
    """Auto-extract and store placeholder field list."""
```
- Called whenever `content_html` changes
- Updates `placeholder_fields` display

#### `_extract_placeholders()`
```python
def _extract_placeholders(self):
    """Return list of placeholder keys via regex."""
```
- Uses regex: `r'\$\{([\w_]+)\}'`
- Returns list of placeholder names
- **Do NOT override** – core extraction logic

#### `_render_placeholder_content(context: dict)`
```python
def _render_placeholder_content(self, context: dict):
    """Replace all placeholders in HTML with resolved values."""
```
- Takes dict with keys: `employee`, `contract`
- Returns HTML with substituted values
- Calls `_resolve_placeholder_value()` internally

#### `_resolve_placeholder_value(ph: str, ctx: dict)`
```python
def _resolve_placeholder_value(self, ph: str, ctx: dict):
    """Map placeholder key to actual value from contract/employee."""
```
- Implements mapping logic for all supported placeholders
- **Extend this mapping to add new placeholders**
- Returns `None` if value not found (renders as empty string)

### Wizard Model Methods

#### `action_generate_contract_pdf()`
```python
def action_generate_contract_pdf(self):
    """Main wizard action: validate, render, and attach PDF to contract."""
```
- Validates template is in "active" state
- Calls `validate_placeholders()`
- Renders HTML via `_render_template_content()`
- Converts to PDF via `ir.actions.report._render_qweb_pdf()`
- Creates `ir.attachment` record with timestamped filename
- Returns close action

### HR Contract Extension Methods

#### `action_generate_contract_document()` (on hr.contract)
```python
def action_generate_contract_document(self):
    """Generate and attach PDF document from selected template."""
```
- Available on `hr.contract` model via extension
- Requires template to be selected in `document_template_id` field
- Template must be in "Active" state
- Validates all placeholders before rendering
- Generates PDF using template content + contract data
- Automatically attaches PDF to contract with descriptive filename
- Shows success notification after completion

---

## 🔗 HR Contract Integration

### New Field: `document_template_id`

Added to `hr.contract` model via inheritance:

```python
document_template_id = fields.Many2one(
    "hr.contract.document.template",
    string="Contract Document Template",
)
```

**Visibility**:
- Visible to HR Admins and Specialists only
- Field constraints: `state == 'active'` and same `company_id`
- Optional field (contracts can exist without template selection)

**Location in Form**:
- Placed below `contract_type_id` field
- Shows only active templates from same company
- Click to select or create new template

### New Button: "Generate Contract Document"

**Location**: HR Contract form header (next to employee link)

**Visibility**:
- Only visible when `document_template_id` is selected
- Only available to HR Admins
- Highlighted in green (important action)

**Functionality**:
- Generates PDF from selected template
- Resolves all placeholders with contract/employee data
- Creates attachment with version-numbered filename
- Example: `Contract_John_Doe_v2.pdf`
- Shows success notification

**Workflow**:
```
1. Open HR Contract form
2. Select "Contract Document Template" (active templates only)
3. Click "Generate Contract Document" button
4. PDF generated automatically
5. Success message appears
6. PDF visible in Attachments tab
```

---

## 🎯 Common Development Tasks

### ✏️ Task: Add a New Placeholder

**Steps**:

1. **Update whitelist** in `hr_contract_document_template.py`:
   ```python
   @api.model
   def _get_allowed_placeholder_keys(self):
       return [
           # ... existing placeholders ...
           "my_new_placeholder",  # ADD HERE
       ]
   ```

2. **Update resolver** in `hr_contract_document_snippet.py`:
   ```python
   def _resolve_placeholder_value(self, ph: str, ctx: dict):
       employee = ctx.get("employee")
       contract = ctx.get("contract")
       mapping = {
           # ... existing mappings ...
           "my_new_placeholder": contract.field_name if contract else "",  # ADD HERE
       }
       return mapping.get(ph)
   ```

3. **Test**: Create snippet with `${my_new_placeholder}` and generate PDF

### 📝 Task: Extend the Placeholder Mapping Context

Sometimes you need to pass additional data to placeholders. Modify `_render_template_content()` in the template model:

```python
def _render_template_content(self, contract):
    ctx = {
        "employee": contract.employee_id,
        "contract": contract,
        "company": contract.company_id,  # NEW
        "department": contract.employee_id.department_id,  # NEW
    }
    # ... rest of method
```

Then update the mapping in the snippet model accordingly.

### 🎨 Task: Customize QWeb Report Styling

1. Edit `report/hr_contract_document_qweb_template.xml` for structure
2. Edit `static/src/css/contract_report.css` for styling
3. Use template's `css_style` field for dynamic CSS per template

### 🔐 Task: Restrict Access by Company

Record rules are already implemented. Verify in `security/ir_rule.hr_contract_document.xml`:
- Templates filtered by `company_id`
- Snippets filtered by parent template's company

### 🔄 Task: Integrate with E-Signature (Future)

1. The `hr.contract.document.signer.rule` model is designed for this
2. `relation_rule` field stores Python path to determine signers
3. Example: `"employee.parent_id.user_id"` → resolves to manager
4. Future addon: Parse rules, extract signers, send to Odoo Sign / DocuSign

---

## 🧪 Testing & Debugging

### Enable Debug Logging

In `__init__.py`, uncomment the patching block to trace field setup errors:
```python
from odoo import fields
original_setup_related = fields.Field.setup_related

def patched_setup_related(self, model):
    _logger.info(f"Setting up related field: {self.name} on model {model._name}")
    try:
        return original_setup_related(self, model)
    except Exception as e:
        _logger.exception(f"Error setting up field {self.name}: {e}")
        raise

fields.Field.setup_related = patched_setup_related
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Placeholder not resolving | Key not in whitelist | Add to `_get_allowed_placeholder_keys()` + resolver |
| ValidationError on snippet save | Invalid placeholder name | Check spelling; must match whitelist |
| PDF renders with empty values | Mapping returns None | Verify contract/employee has required field data |
| Wizard closed without action | Template not "active" | Activate template in form view |
| Access denied to template | User not in right group | Check user group assignment & ACL rows |

---

## 📦 Dependencies

### Base Odoo Modules
- `base` – Core Odoo models
- `hr` – HR module (employee model)
- `hr_contract` – Contract management
- `mail` – Mail thread integration (tracking, notifications)
- `web` – Odoo web interface

### No External Dependencies
- Pure Python + XML (no npm, pip packages required)
- Compatible with Community Edition

---

## 🚀 Hooks & Initialization

The module defines three lifecycle hooks in `__init__.py`:

```python
def _pre_init_hook(env):
    """Called before module installation."""
    # Setup placeholder validation rules, etc.

def _post_init_hook(env):
    """Called after module installation."""
    # Create demo templates if needed

def _uninstall_hook(env):
    """Called during module uninstallation."""
    # Cleanup: archive templates, clear logs, etc.
```

Currently, these are placeholders. Implement as needed for:
- Data migration
- Demo data setup
- Custom initialization

---

## 🎓 Key Design Patterns

### 1. **Versioning Strategy**
- Auto-increment version on state transition (draft → active)
- Immutable once contract is created (pin version)
- Allows safe template evolution

### 2. **Placeholder Validation**
- Whitelist approach (security + maintainability)
- Regex extraction for robustness
- Clear error messages for invalid keys

### 3. **Separation of Concerns**
- Template: orchestration + versioning
- Snippet: content + rendering
- Attachment: document reference + metadata
- Signer Rule: configuration (not yet execution)
- Wizard: user workflow + PDF generation

### 4. **Multi-Company, Multi-Language**
- `company_id` on every model → ACL + isolation
- `language` on attachments → version by language
- `country_id` on templates → localization hook

### 5. **Audit & Traceability**
- `mail.thread` + `mail.activity.mixin` on template/snippet
- `tracking=True` on key fields
- Immutable version snapshots
- PDF filename includes version: `Contract_{name}_v{version}.pdf`

---

## 📋 Development Checklist

When extending or maintaining this module:

- [ ] Follow LGPL-3 licensing
- [ ] Update `__manifest__.py` version after changes
- [ ] Add new placeholders to BOTH whitelist AND resolver
- [ ] Include docstrings in all methods
- [ ] Test placeholder resolution with sample contracts
- [ ] Verify ACL rules grant correct permissions
- [ ] Document new models/fields in `docs/architecture.md`
- [ ] Use `tracking=True` on important fields for audit
- [ ] Inherit `mail.thread` for notification support
- [ ] Sanitize HTML inputs (default behavior in Odoo)
- [ ] Test with multi-company setup
- [ ] Validate with e-signature flow in mind

---

## 🔗 Related Modules & Future Integrations

### Current Dependencies
- `hr_contract` – Source of contract/employee data
- `mail` – Notifications & thread tracking
- `web` – UI rendering

### Planned Extensions
- `sign` (Odoo digital signature) – e-signature integration
- `docusign_connector` (3rd party) – DocuSign support
- `l10n_xx` modules – Country-specific templates

---

## 📞 Support & Notes

- **Author**: Michael Blickenstorfer
- **Website**: https://www.blicki.ch
- **License**: LGPL-3.0-or-later
- **Odoo Version**: 18.0
- **Edition**: Community
- **Status**: In Development (v18.0.0.1.0)

For detailed architecture and design rationale, see `docs/architecture.md`.

---

## Quick Reference Commands (Development)

### Common grep patterns to understand code:
```bash
# Find all placeholder-related logic
grep -r "placeholder" --include="*.py"

# Find all state transitions
grep -r "state.*=" --include="*.py"

# Find all field definitions
grep -r "fields\." --include="*.py" | head -20

# Find all @api.depends decorators
grep -r "@api.depends" --include="*.py"
```

### Restart Odoo after changes:
```bash
# In Odoo container/environment:
./odoo-bin --update=hr_contract_document --stop-after-init
```

---

**Last Updated**: February 5, 2026  
**Version**: 1.0 (Initial Documentation)
