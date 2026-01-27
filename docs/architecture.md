# Architecture Documentation – hr_contract_document

## 📦 Module Overview

`hr_contract_document` extends Odoo’s `hr_contract` module by providing a complete **Contract Document Management Framework**.

It enables **structured**, **versioned**, and **translatable contract templates** which can be composed of reusable text blocks and document references, equipped with **placeholders** that dynamically resolve values from Odoo models (e.g. `hr.employee`, `hr.contract`).

---

## 🧭 Functional Scope

| Area | Description |
|------|-------------|
| **Templates** | Define structured, versioned, and styleable contract documents |
| **Text Snippets** | Reusable HTML text blocks with placeholders |
| **Attachments** | Multi-language, versioned reference documents |
| **Signatures** | Rules to define signers dynamically (HR, manager, team lead, etc.) |
| **Wizard** | User interface for HR to create printable contract instances |
| **Rendering** | Automated QWeb report generation with placeholder substitution |
| **Version Control** | Auto-versioning and freeze for existing contracts |

---

## 🧱 Data Model (ORM Layer)

Below are the technical entities of the module and their key relations.

### 1️⃣ Model: `hr.contract.document.template`

**Purpose:**  
Represents a complete, versioned contract template which links snippets, attachments, and signer rules.

**Table name:** `hr_contract_document_template`

**Key Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Display name |
| `version` | Char / Int | Auto‑incremented version number |
| `state` | Selection | `draft`, `review`, `active`, `archived` |
| `snippet_ids` | One2many (`hr.contract.document.snippet`) | Included text blocks |
| `attachment_ids` | One2many (`hr.contract.document.attachment`) | Referenced documents |
| `signer_rule_ids` | One2many (`hr.contract.document.signer.rule`) | Dynamic signer definitions |
| `css_style` | Text | Optional custom CSS for the QWeb report |
| `company_id` | Many2one (`res.company`) | Restrict templates by company |
| `country_id` | Many2one (`res.country`) | Optional localization binding |
| `active` | Boolean | Archive support |

**Relations Diagram:**
hr.contract.document.template
|----- 1:N  hr.contract.document.snippet
|----- 1:N  hr.contract.document.attachment
|----- 1:N  hr.contract.doucment.signer.rule

### 2️⃣ Model: `hr.contract.document.snippet`

**Purpose:**  
Contains the content blocks that form a contract. Supports dynamic placeholders.

**Table name:** `hr_contract_document_snippet`

**Key Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Title of the snippet |
| `content_html` | Html | Editable content with placeholders |
| `sequence` | Integer | Display order within template |
| `is_mandatory` | Boolean | Marks block as mandatory; cannot be excluded |
| `placeholder_fields` | Text (computed) | Automatically detected placeholder list |
| `state` | Selection | `draft`, `review`, `active`, `archived` |
| `version` | Integer | Incremented upon change |
| `template_id` | Many2one (`hr.contract.document.template`) | Parent template |
| `company_id` | Many2one (`res.company`) | Multicompany support |

**Validation Rules:**
- Mandatory snippets must exist in every generated contract.
- Placeholders are validated against a known mapping schema (`contract_ctx` mapping).

---

### 3️⃣ Model: `hr.contract.document.attachment`

**Purpose:**  
Represents reference attachments that can be included with the contract (e.g. policies, agreements).

**Table name:** `hr_contract_document_attachment`

**Key Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Document name |
| `document_ref_id` | Many2one (`ir.attachment`) | Reference to actual Odoo file |
| `version` | Char | Version ID or tag |
| `is_mandatory` | Boolean | Required document for the template |
| `language` | Selection | Language of the document |
| `state` | Selection | `active`, `archived` |
| `template_id` | Many2one (`hr.contract.document.template`) | Parent template |

**Behavior:**
- Mandatory attachments are automatically appended to printed contract PDF.
- Attachment versions are referenced, not copied per contract.

---

### 4️⃣ Model: `hr.contract.document.signer.rule`

**Purpose:**  
Defines who must sign a contract template instance and how to determine that person dynamically.

**Table name:** `hr_contract_document_signer_rule`

**Key Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Role title (e.g. “HR Manager”) |
| `sequence` | Integer | Processing order |
| `relation_rule` | Char | Python-like path, e.g. `"employee.parent_id.user_id"` |
| `is_mandatory` | Boolean | Must this signer approve or optional? |
| `template_id` | Many2one (`hr.contract.document.template`) | Parent template |

**Future Usage:**  
These rules act as configuration for later integration with `sign` or `docusign` modules.

---

### 5️⃣ Model: `hr.contract.create.wizard`

**Purpose:**  
User-facing wizard for HR Admins to generate a printable `hr.contract` from a selected template.

**Key Steps:**
1. Template selection
2. Optional snippet/attachment choice
3. Validation of all placeholders
4. Contract creation + PDF rendering

**Outputs:**
- Generated QWeb PDF
- Attachment stored on `hr.contract` with timestamped version name

---

## 🔄 Placeholder Resolving Engine

### **Syntax**
Placholders follow a simple readable syntax: ${placeholder_name}

### **Example**
Snippet content:
"Der Mitarbeiter ${employee_name} tritt am ${contract_date_start} seine Tätigkeit an.

**Resolved via Mapping Dictionary:**
```python
placeholders = {
  'employee_name': contract.employee_id.name,
  'contract_date_start': contract.date_start,
  'contract_job_title': contract.job_id.name,
  'contract_wage': contract.wage,
}
```

### **Validation**
- Upon snipped save, each placeholder token is parsed via regex ( r'\$\{([\w_]+)\}' ).
- System ensures, that every placeholder key exists in placeholders mapping.
- Invalid keys raise a clear ValidationError

### **Injection in Editor
A small JS plugin ( editor_placeholder_dropdown.js ) displays an "Inser Placeholder" dropdown.

### **Rendering & Report Flow
1. User selects Template via hr.contract.create.wizard.
2. System collects all mandatory snippets/attachments.
3. Optional blocks are loaded per user selection.
4. Placeholders are dynamically replaced by real contract/employee data.
5. Combined HTML is passed to QWeb to render PDF.
6. Final PDF gets attached to the contract.

**Report Example**
```xml
<t t-name="hr_contract_document.report_contract_document">
  <t t-foreach="docs" t-as="contract">
    <t t-foreach="contract.snippet_ids" t-as="snippet">
      <div t-raw="snippet.rendered_html"/>
    </t>
  </t>
</t>
```

### ***States and Version Management***
| Model | States | Versioning Rule |
|-------|--------|-----------------|
| Template | Draft → Review → Active → Archived | New version auto-created when saved during non-frozen state |
| Snipped | Draft → Review → Active → Archived | Each edit increases version |
| Attachment | Active / Archived | Reference to immutable **ir.attachment** version |

**Version Freeze**: Once a contract instance uses a template version, that version is pinned (no retroactive changes).

### **Security Model**
| Role | Description | Technical Group |
|------|-------------|-----------------|
| HR Document Specialist | Full template editing, versioning, activation | group_hr_contract_document_specialist |
| HR Administration | Create contracts from active templates | group_hr_contract_document_admin |
| Signer/Manager | Read-only access for signable documents | group_hr_contract_document_signer |

**Access Rights** (ir.model.access.csv)
- Specialists: *create*, *read*, *write*, *unlink* on templates/snippets/attachments
- Admins: *read*, *create* on wizard and generated contracts
- Signers: *read* only

## 🧩 File and Directory Structure
hr_contract_document/
├── __manifest__.py
├── models/
│   ├── hr_contract_document_template.py
│   ├── hr_contract_document_snippet.py
│   ├── hr_contract_document_attachment.py
│   ├── hr_contract_document_signer_rule.py
│   └── hr_contract_document_wizard.py
├── views/
│   ├── contract_document_menu.xml
│   ├── hr_contract_document_template_views.xml
│   ├── hr_contract_document_snippet_views.xml
│   ├── hr_contract_document_attachment_views.xml
│   ├── hr_contract_document_signer_rule_views.xml
│   └── hr_contract_document_wizard_views.xml
├── report/
│   ├── hr_contract_document_report.xml
│   └── templates/
│       └── hr_contract_document_qweb_template.xml
├── security/
│   ├── ir.model.access.csv
│   └── security_groups.xml
└── static/
    ├── description/
    │   ├── icon.png
    │   ├── banner.png
    │   └── index.html
    └── src/js/
        └── editor_placeholder_dropdown.js

## 🧱 Integration Points
- Base Module Dependency: hr_contract
- Optional Extensions:
  - sign (digital signature)
  - mail (document sharing & notification)
  - website (public link to sign documents)
- Future Adapter: hr_contract_document_enterprise → integrates with Enterprise’s hr_contract_salary.

## 🧩 Key Design Decisions
1. Modular Separation:
   Template logic independent from salary configuration (no conflict with Odoo Enterprise).

2. Readability for HR Users:
   Simple ${placeholder} syntax + intuitive WYSIWYG editor.

3. Maintainability:
   Version control for all text-based components to ensure audit compliance.

4. Legal Traceability:
   Each generated contract holds references to template version, attached docs, and render date.

## 🔒 Security & Compliance
- Full audit trail for template and snippet edits.
- Version immutability ensures legal integrity.
- Access limited via HR roles (Odoo ACL + Record Rules).
- Stored PDFs automatically attached to contracts in ir.attachment.

## ☑️ Conclusion
The hr_contract_document module builds a solid and extensible foundation for professional HR contract management within Odoo, going far beyond the built-in “Contract Templates” of the Enterprise Core.

It is production-ready for enterprises, compliant with multi-language and versioning needs, and extendable for future digital signature or country-specific legal templates.