/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useEffect, useRef } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Summernote WYSIWYG Editor Widget for Odoo 18
 * 
 * A lightweight custom field widget that replaces the default HTML editor
 * with Summernote for better WYSIWYG editing experience.
 * 
 * Supports:
 * - Rich text formatting
 * - Table insertion
 * - Image/link insertion
 * - Code view
 * - Placeholder insertion
 */
class SummernoteEditorField extends Component {
    static template = "hr_contract_document.SummernoteEditorField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.contentRef = useRef("content");
        this.state = useState({
            initialized: false,
            resourcesLoaded: false,
            editorId: `summernote_${Math.random().toString(36).substr(2, 9)}`,
        });

        useEffect(() => {
            // Cannot use async directly in useEffect callback
            // Wrap async logic in a separate function
            const initializeAsync = async () => {
                try {
                    await this._loadResources();
                    this._initializeEditor();
                } catch (error) {
                    console.error('Error initializing Summernote:', error);
                }
            };
            initializeAsync();
        });
    }

    async _loadResources() {
        if (this.state.resourcesLoaded) {
            return;
        }

        // Load Summernote CSS
        if (!document.querySelector('link[href*="summernote"]')) {
            const linkCSS = document.createElement('link');
            linkCSS.rel = 'stylesheet';
            linkCSS.href = 'https://cdn.jsdelivr.net/npm/summernote@0.8.20/dist/summernote-lite.min.css';
            linkCSS.crossOrigin = 'anonymous';
            document.head.appendChild(linkCSS);
        }

        // Load jQuery
        if (!window.jQuery) {
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }

        // Load Summernote JS
        if (!window.jQuery?.summernote) {
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/summernote@0.8.20/dist/summernote-lite.min.js';
                script.crossOrigin = 'anonymous';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }

        this.state.resourcesLoaded = true;
    }

    _initializeEditor() {
        if (!this.contentRef.el || this.state.initialized) {
            return;
        }

        // Small delay to ensure DOM is ready
        setTimeout(() => {
            if (!window.jQuery) {
                console.error('jQuery not loaded, cannot initialize Summernote');
                return;
            }

            const $editor = window.jQuery(this.contentRef.el);
            
            // Check if already initialized
            if ($editor.data('summernote')) {
                return;
            }

            try {
                $editor.summernote({
                    height: 400,
                    minHeight: 300,
                    maxHeight: null,
                    placeholder: 'Enter contract content here. Use expressions like {{ contract.employee_id.name }} or {{ contract.wage }}.',
                    focus: false,
                    disableDragAndDrop: false,
                    toolbar: [
                        ['style', ['style']],
                        ['font', ['bold', 'underline', 'italic', 'strikethrough', 'clear']],
                        ['fontname', ['fontname']],
                        ['fontsize', ['fontsize']],
                        ['color', ['forecolor', 'backcolor']],
                        ['para', ['ul', 'ol', 'paragraph', 'height']],
                        ['table', ['table', 'hr']],
                        ['insert', ['link', 'picture', 'video']],
                        ['view', ['fullscreen', 'codeview', 'help']],
                    ],
                    fontNames: [
                        'Segoe UI',
                        'Arial',
                        'Arial Black',
                        'Courier New',
                        'Georgia',
                        'Helvetica Neue',
                        'Times New Roman',
                        'Verdana',
                    ],
                    fontNamesIgnoreCheck: [
                        'Segoe UI',
                        'Courier New',
                        'Helvetica Neue',
                        'Times New Roman',
                    ],
                    fontSizes: ['8', '9', '10', '11', '12', '14', '16', '18', '20'],
                    colors: [
                        ["#000000", "#555555", "#999999", "#CCCCCC", "#FFFFFF", "#3A0066", "#9900FF", "#FFC0CB"],
                        ["#004D1A", '#39A641', "#00FF00", "#3DFF17", "#002060", "#0000FF", "#3399FF", "#00F0FF"],
                        ["#990000", "#FF0000", "#FF007F", "#FF8080", "#FF6600", "#FFAA00", "#FFD700", "#FFFF00"],
                    ],
                    colorsName: [
                        ["Reines Schwarz", "Dunkelgrau",    "Silbergrau",  "Hellgrau",     "Weiss",         "Dunkelviolett", "Leuchtviolett",  "Soft-Rosa"],
                        ["Tannengrün",     "FCT Titelgrün", "Reines Grün", "FCT Hellgrün", "Tiefsee",       "Reines Blau",   "Jeansblau",      "Cyan-Leuchtblau"],
                        ["Weinrot",        "Reines Rot",    "Neon-Rosa",   "Hellrot",      "System Orange", "System Gelb",   "Vibrantes Gelb", "Hellgelb"],
                    ],
                    callbacks: {
                        onChange: (contents) => {
                            this._onEditorChange(contents);
                        },
                        onBlur: () => {
                            const contents = $editor.summernote('code');
                            this._onEditorChange(contents);
                        },
                    },
                });

                this.state.initialized = true;
            } catch (error) {
                console.error('Error initializing Summernote:', error);
            }
        }, 50);
    }

    _onEditorChange(htmlContent) {
        // Update the field value
        this.props.record.update({
            [this.props.name]: htmlContent,
        });
    }

    get value() {
        return this.props.record.data[this.props.name] || '';
    }
}

// Register the widget for the 'summernote' widget name
registry.category('fields').add('summernote', {
    component: SummernoteEditorField,
    displayName: 'Summernote Editor',
    supportedTypes: ['html', 'text'],
});

export default SummernoteEditorField;
