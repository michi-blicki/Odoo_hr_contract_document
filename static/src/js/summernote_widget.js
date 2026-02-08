/** @odoo-module **/

import { HtmlField, htmlField } from "@html_editor/fields/html_field";
import { registry } from "@web/core/registry";
import { useState } from "@odoo/owl";

/**
 * Summernote HTML Editor Widget for Odoo 18
 * 
 * Integrates Summernote WYSIWYG editor for contract snippet content editing
 * with support for placeholders and rich text formatting.
 */
class SummernoteWidget extends HtmlField {
    setup() {
        super.setup();
        this.state = useState({
            initialized: false,
        });
    }

    async willStart() {
        await super.willStart();
        // Load Summernote CSS and JS from CDN
        await this._loadSummernoteResources();
    }

    async _loadSummernoteResources() {
        // Load Summernote CSS
        if (!document.querySelector('link[href*="summernote"]')) {
            const linkCSS = document.createElement('link');
            linkCSS.rel = 'stylesheet';
            linkCSS.href = 'https://cdn.jsdelivr.net/npm/summernote@0.8.20/dist/summernote-lite.min.css';
            document.head.appendChild(linkCSS);
        }

        // Load Summernote JS
        if (!window.$.summernote) {
            await new Promise((resolve) => {
                // Ensure jQuery is loaded first
                if (!window.$) {
                    const scriptJQuery = document.createElement('script');
                    scriptJQuery.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
                    scriptJQuery.onload = () => {
                        const scriptSummernote = document.createElement('script');
                        scriptSummernote.src = 'https://cdn.jsdelivr.net/npm/summernote@0.8.20/dist/summernote-lite.min.js';
                        scriptSummernote.onload = resolve;
                        document.head.appendChild(scriptSummernote);
                    };
                    document.head.appendChild(scriptJQuery);
                } else {
                    const scriptSummernote = document.createElement('script');
                    scriptSummernote.src = 'https://cdn.jsdelivr.net/npm/summernote@0.8.20/dist/summernote-lite.min.js';
                    scriptSummernote.onload = resolve;
                    document.head.appendChild(scriptSummernote);
                }
            });
        }
    }

    async onLoadTemplate() {
        await super.onLoadTemplate();
        // Initialize Summernote after DOM is ready
        setTimeout(() => this._initializeSummernote(), 100);
    }

    _initializeSummernote() {
        const textareaElement = this.element?.querySelector('textarea[name="content_html"]');
        
        if (!textareaElement || window.$.summernote === undefined) {
            console.warn('Summernote: textarea element or jQuery not found');
            return;
        }

        // Convert textarea to Summernote editor
        const $element = window.$(textareaElement);
        
        if ($element.data('summernote')) {
            return; // Already initialized
        }

        try {
            $element.summernote({
                height: 400,
                minHeight: 300,
                maxHeight: 600,
                placeholder: 'Start typing your contract content here...',
                focus: true,
                toolbar: [
                    ['style', ['style']],
                    ['font', ['bold', 'underline', 'italic', 'clear']],
                    ['fontname', ['fontname']],
                    ['fontsize', ['fontsize']],
                    ['color', ['color']],
                    ['para', ['ul', 'ol', 'paragraph']],
                    ['table', ['table']],
                    ['insert', ['link', 'picture', 'hr']],
                    ['view', ['fullscreen', 'codeview', 'help']],
                    ['custom', ['placeholder']],
                ],
                buttons: {
                    placeholder: this._getPlaceholderButton(),
                },
                onImageUpload: (files) => {
                    this._uploadImage(files[0]);
                },
                callbacks: {
                    onChange: () => {
                        // Update Odoo field value
                        const htmlContent = $element.summernote('code');
                        textareaElement.value = htmlContent;
                        
                        // Trigger field change
                        const event = new Event('change', { bubbles: true });
                        textareaElement.dispatchEvent(event);
                    },
                    onBlur: () => {
                        const htmlContent = $element.summernote('code');
                        textareaElement.value = htmlContent;
                    },
                },
                popover: {
                    image: [
                        ['imagesize', ['imageSize100', 'imageSize50', 'imageSize25']],
                        ['float', ['floatLeft', 'floatRight', 'floatNone']],
                        ['remove', ['removeMedia']],
                    ],
                    link: [
                        ['link', ['linkDialogShow', 'unlink']],
                    ],
                    air: [
                        ['color', ['color']],
                        ['font', ['bold', 'underline', 'clear']],
                        ['para', ['ul', 'paragraph']],
                        ['table', ['table']],
                        ['insert', ['link', 'picture']],
                    ],
                },
            });

            this.state.initialized = true;
        } catch (e) {
            console.error('Failed to initialize Summernote:', e);
        }
    }

    _getPlaceholderButton() {
        const PLACEHOLDERS = [
            { key: 'employee_name', label: 'Employee Name' },
            { key: 'employee_job_title', label: 'Employee Job Title' },
            { key: 'contract_date_start', label: 'Contract Start Date' },
            { key: 'contract_date_end', label: 'Contract End Date' },
            { key: 'contract_wage', label: 'Contract Wage' },
            { key: 'contract_company', label: 'Company Name' },
        ];

        return {
            action: () => {
                // Create dropdown menu for placeholders
                const dropdown = this._createPlaceholderDropdown(PLACEHOLDERS);
                document.body.appendChild(dropdown);
            },
            className: 'note-icon-action',
            title: 'Insert Placeholder',
            innerHTML: '<i class="note-icon-code"></i>',
        };
    }

    _createPlaceholderDropdown(placeholders) {
        const menu = document.createElement('div');
        menu.className = 'placeholder-dropdown-menu';
        menu.style.cssText = `
            position: fixed;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            min-width: 280px;
        `;

        placeholders.forEach((ph) => {
            const item = document.createElement('div');
            item.style.cssText = `
                padding: 10px 15px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
                font-size: 13px;
                transition: background 0.15s;
            `;
            item.innerHTML = `
                <div style="font-weight: 500; color: #333;">${ph.label}</div>
                <div style="font-family: monospace; color: #999; font-size: 11px; margin-top: 3px;">
                    $\{${ph.key}\}
                </div>
            `;

            item.onmouseover = () => {
                item.style.backgroundColor = '#f9f9f9';
            };

            item.onmouseout = () => {
                item.style.backgroundColor = 'white';
            };

            item.onclick = () => {
                const $element = window.$(this.element?.querySelector('textarea[name="content_html"]'));
                if ($element.data('summernote')) {
                    $element.summernote('insertText', `\${${ph.key}}`);
                }
                menu.remove();
            };

            menu.appendChild(item);
        });

        return menu;
    }

    _uploadImage(file) {
        // For now, just a placeholder for image upload functionality
        const reader = new FileReader();
        reader.onload = (e) => {
            const $element = window.$(this.element?.querySelector('textarea[name="content_html"]'));
            if ($element.data('summernote')) {
                $element.summernote('insertImage', e.target.result);
            }
        };
        reader.readAsDataURL(file);
    }
}

registry.category('fields').add('summernote', {
    ...htmlField,
    component: SummernoteWidget,
});

export default SummernoteWidget;
