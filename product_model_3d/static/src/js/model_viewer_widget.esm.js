/** @odoo-module **/
import {Component, onWillStart, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

const HINT_KEY = "model_3d_convert.viewer_hint_dismissed";

export class ModelViewer3dField extends Component {
    static template = "product_model_3d.ModelViewer3dField";
    static props = {
        ...standardFieldProps,
        autoRotate: {type: Boolean, optional: true},
    };

    setup() {
        this.modelViewerRef = useRef("modelViewer");
        this.state = useState({
            loading: true,
            loadError: false,
            showHint: !localStorage.getItem(HINT_KEY),
        });

        onWillStart(() => {
            if (document.querySelector('script[src*="model-viewer"]')) {
                return;
            }
            return new Promise((resolve) => {
                const script = document.createElement("script");
                script.type = "module";
                script.src = "/product_model_3d/static/lib/model-viewer.min.js";
                script.onload = resolve;
                script.onerror = resolve;
                document.head.appendChild(script);
            });
        });
    }

    get hasValue() {
        return Boolean(this.props.record.data[this.props.name]);
    }

    get conversionState() {
        return this.props.record.data.model_3d_conversion_state || "draft";
    }

    get src() {
        const {record, name} = this.props;
        if (!record.data[name] || !record.resId) {
            return "";
        }
        const filename = record.data.model_3d_filename || "";
        return `/web/content?model=${record.resModel}&field=${name}&id=${record.resId}&filename=${filename}`;
    }

    get downloadSrc() {
        return this.src ? `${this.src}&download=1` : "";
    }

    get autoRotate() {
        return Boolean(this.props.autoRotate);
    }

    onModelLoad() {
        this.state.loading = false;
    }

    onModelError() {
        this.state.loadError = true;
        this.state.loading = false;
    }

    toggleFullscreen() {
        this.modelViewerRef.el?.requestFullscreen();
    }

    dismissHint() {
        this.state.showHint = false;
        localStorage.setItem(HINT_KEY, "1");
    }
}

registry.category("fields").add("model_viewer_3d", {
    component: ModelViewer3dField,
    supportedTypes: ["binary"],
    extractProps: ({options}) => ({
        autoRotate: Boolean(options?.auto_rotate),
    }),
});
