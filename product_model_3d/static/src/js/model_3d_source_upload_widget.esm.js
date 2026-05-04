/** @odoo-module **/
import {Component, onMounted, onPatched, onWillUnmount, useRef} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

const POLL_INTERVAL_MS = 3000;

export class Model3dSourceUploadWidget extends Component {
    static template = "product_model_3d.Model3dSourceUploadWidget";
    static props = {...standardFieldProps};

    setup() {
        this.fileInputRef = useRef("fileInput");
        this._pollTimer = null;
        onMounted(() => this._syncPolling());
        onPatched(() => this._syncPolling());
        onWillUnmount(() => this._stopPolling());
    }

    _resetFileInput() {
        if (this.fileInputRef.el) {
            this.fileInputRef.el.value = "";
        }
    }

    _syncPolling() {
        if (this.isConverting) {
            if (!this._pollTimer) {
                this._pollTimer = setInterval(() => this._poll(), POLL_INTERVAL_MS);
            }
        } else {
            this._stopPolling();
        }
    }

    async _poll() {
        await this.props.record.load();
    }

    _stopPolling() {
        if (this._pollTimer) {
            clearInterval(this._pollTimer);
            this._pollTimer = null;
        }
    }

    get hasFile() {
        return Boolean(this.props.record.data[this.props.name]);
    }

    get filename() {
        return this.props.record.data.model_3d_source_filename || "";
    }

    get sizeKb() {
        return this.props.record.data.model_3d_source_size_kb || 0;
    }

    get formattedSize() {
        const kb = this.sizeKb;
        if (kb >= 1024) {
            return (kb / 1024).toFixed(1) + " MB";
        }
        return kb + " KB";
    }

    get conversionState() {
        return this.props.record.data.model_3d_conversion_state || "draft";
    }

    get conversionError() {
        return this.props.record.data.model_3d_conversion_error || "";
    }

    get isConverting() {
        return ["queued", "processing"].includes(this.conversionState);
    }

    get canConvert() {
        return ["draft", "failed", "done"].includes(this.conversionState);
    }

    get isGlbOrGltf() {
        const name = this.filename.toLowerCase();
        return name.endsWith(".glb") || name.endsWith(".gltf");
    }

    get actionButtonLabel() {
        return this.isGlbOrGltf ? "Use as 3D Model" : "Convert to GLB";
    }

    async onFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        if (this.isConverting && this.props.record.resId) {
            await this.env.services.action.doActionButton({
                name: "action_model_3d_abort",
                type: "object",
                resModel: this.props.record.resModel,
                resId: this.props.record.resId,
            });
            await this.props.record.load();
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            const base64 = e.target.result.split(",")[1];
            this.props.record.update({
                [this.props.name]: base64,
                model_3d_source_filename: file.name,
            });
        };
        reader.readAsDataURL(file);
    }

    async onClearClick() {
        this._resetFileInput();
        if (!this.props.record.resId) {
            this.props.record.update({
                [this.props.name]: false,
                model_3d_source_filename: false,
            });
            return;
        }
        await this.env.services.action.doActionButton({
            name: "action_model_3d_clear",
            type: "object",
            resModel: this.props.record.resModel,
            resId: this.props.record.resId,
        });
        await this.props.record.load();
    }

    async onActionClick() {
        await this.props.record.save();
        await this.env.services.action.doActionButton({
            name: "action_model_3d_convert",
            type: "object",
            resModel: this.props.record.resModel,
            resId: this.props.record.resId,
        });
        await this.props.record.load();
    }
}

registry.category("fields").add("model_3d_source_upload", {
    component: Model3dSourceUploadWidget,
    supportedTypes: ["binary"],
});
