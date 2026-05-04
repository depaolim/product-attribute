/** @odoo-module **/

import {describe, expect, test} from "@odoo/hoot";
import {manuallyDispatchProgrammaticEvent, queryFirst} from "@odoo/hoot-dom";
import {animationFrame} from "@odoo/hoot-mock";
import {defineMailModels} from "@mail/../tests/mail_test_helpers";
import {defineModels, fields, models, mountView} from "@web/../tests/web_test_helpers";

const HINT_KEY = "model_3d_convert.viewer_hint_dismissed";

// Pre-register a stub <model-viewer> element so the widget's onWillStart skips
// loading model-viewer.min.js and the element never issues HTTP requests.
// The data-URL satisfies the script[src*="model-viewer"] guard without fetching
// anything, while the custom-element stub prevents any fetch on src assignment.
{
    if (!document.querySelector('script[src*="model-viewer"]')) {
        const stub = document.createElement("script");
        // Data: URL matches the selector and executes harmlessly as plain JS
        stub.src = "data:text/javascript,// model-viewer-stub";
        document.head.appendChild(stub);
    }
    if (!customElements.get("model-viewer")) {
        customElements.define("model-viewer", class extends HTMLElement {});
    }
}

class ProductTemplate extends models.Model {
    _name = "product.template";

    model_3d = fields.Binary();
    model_3d_filename = fields.Char();
    model_3d_conversion_state = fields.Selection({
        selection: [
            ["draft", "Draft"],
            ["queued", "Queued"],
            ["processing", "Processing"],
            ["done", "Done"],
            ["failed", "Failed"],
        ],
    });

    _records = [
        {
            id: 1,
            model_3d: false,
            model_3d_filename: false,
            model_3d_conversion_state: "draft",
        },
    ];
}

defineMailModels();
defineModels([ProductTemplate]);

// Common patch used by tests that need the model-viewer element to be rendered.
const WITH_MODEL = {model_3d: "ZmFrZQ==", model_3d_conversion_state: "done"};

async function mountViewerWidget(recordPatch = {}, widgetOptions = null) {
    Object.assign(ProductTemplate._records[0], recordPatch);
    const optionsStr = widgetOptions ? ` options="${widgetOptions}"` : "";
    return mountView({
        type: "form",
        resModel: "product.template",
        resId: 1,
        arch: `
            <form>
                <field name="model_3d" widget="model_viewer_3d"${optionsStr}/>
                <field name="model_3d_filename" invisible="1"/>
                <field name="model_3d_conversion_state" invisible="1"/>
            </form>
        `,
    });
}

describe("ModelViewer3dField", () => {
    test("test_widget_renders_model_viewer_when_glb_present", async () => {
        await mountViewerWidget(WITH_MODEL);
        expect(queryFirst("model-viewer")).not.toBe(null);
    });

    test("test_widget_renders_nothing_in_draft_without_file", async () => {
        await mountViewerWidget({model_3d: false, model_3d_conversion_state: "draft"});
        expect(queryFirst("model-viewer")).toBe(null);
        expect(queryFirst(".o_model_viewer_placeholder")).toBe(null);
    });

    test("test_widget_placeholder_queued_shows_human_copy", async () => {
        await mountViewerWidget({model_3d: false, model_3d_conversion_state: "queued"});
        const placeholder = queryFirst(".o_model_viewer_placeholder");
        expect(placeholder).not.toBe(null);
        const text = placeholder.textContent;
        expect(text.trim()).not.toBe("queued");
        expect(text.toLowerCase().includes("queue")).toBe(true);
    });

    test("test_widget_placeholder_processing_shows_human_copy", async () => {
        await mountViewerWidget({
            model_3d: false,
            model_3d_conversion_state: "processing",
        });
        const placeholder = queryFirst(".o_model_viewer_placeholder");
        expect(placeholder).not.toBe(null);
        const text = placeholder.textContent.toLowerCase();
        expect(text.includes("converting") || text.includes("please wait")).toBe(true);
    });

    test("test_widget_placeholder_failed_shows_human_copy", async () => {
        await mountViewerWidget({model_3d: false, model_3d_conversion_state: "failed"});
        const placeholder = queryFirst(".o_model_viewer_placeholder");
        expect(placeholder).not.toBe(null);
        expect(placeholder.textContent.toLowerCase().includes("failed")).toBe(true);
    });

    test("test_widget_src_url_correct_format", async () => {
        await mountViewerWidget({
            model_3d: "ZmFrZQ==",
            model_3d_filename: "part.glb",
            model_3d_conversion_state: "done",
        });
        const src = queryFirst("model-viewer").getAttribute("src");
        expect(src.includes("id=1")).toBe(true);
        expect(src.includes("filename=part.glb")).toBe(true);
    });

    test("test_widget_download_link_present_when_model_3d_set", async () => {
        await mountViewerWidget(WITH_MODEL);
        const link = queryFirst("a.o_model_viewer_download");
        expect(link).not.toBe(null);
        expect(link.getAttribute("href").includes("download=1")).toBe(true);
    });

    test("test_widget_auto_rotate_off_by_default", async () => {
        await mountViewerWidget(WITH_MODEL);
        expect(queryFirst("model-viewer").hasAttribute("auto-rotate")).toBe(false);
    });

    test("test_widget_auto_rotate_on_when_option_set", async () => {
        await mountViewerWidget(WITH_MODEL, "{'auto_rotate': true}");
        expect(queryFirst("model-viewer").hasAttribute("auto-rotate")).toBe(true);
    });

    test("test_widget_camera_controls_attribute_set", async () => {
        await mountViewerWidget(WITH_MODEL);
        expect(queryFirst("model-viewer").hasAttribute("camera-controls")).toBe(true);
    });

    test("test_widget_loading_spinner_shown_before_load_event", async () => {
        await mountViewerWidget(WITH_MODEL);
        expect(queryFirst(".o_model_viewer_loading")).not.toBe(null);
    });

    test("test_widget_loading_spinner_hidden_after_load_event", async () => {
        await mountViewerWidget(WITH_MODEL);
        manuallyDispatchProgrammaticEvent(queryFirst("model-viewer"), "load");
        await animationFrame();
        expect(queryFirst(".o_model_viewer_loading")).toBe(null);
    });

    test("test_widget_error_state_on_model_viewer_error_event", async () => {
        await mountViewerWidget(WITH_MODEL);
        manuallyDispatchProgrammaticEvent(queryFirst("model-viewer"), "error");
        await animationFrame();
        expect(queryFirst("model-viewer")).toBe(null);
        expect(queryFirst(".o_model_viewer_error")).not.toBe(null);
    });

    test("test_widget_error_message_mentions_corrupt_or_load", async () => {
        await mountViewerWidget(WITH_MODEL);
        manuallyDispatchProgrammaticEvent(queryFirst("model-viewer"), "error");
        await animationFrame();
        const text = queryFirst(".o_model_viewer_error").textContent.toLowerCase();
        expect(text.includes("corrupt") || text.includes("load")).toBe(true);
    });

    test("test_widget_loading_spinner_absent_after_error_event", async () => {
        await mountViewerWidget(WITH_MODEL);
        manuallyDispatchProgrammaticEvent(queryFirst("model-viewer"), "error");
        await animationFrame();
        expect(queryFirst(".o_model_viewer_loading")).toBe(null);
    });

    test("test_widget_hint_overlay_shown_on_first_load", async () => {
        localStorage.removeItem(HINT_KEY);
        await mountViewerWidget(WITH_MODEL);
        expect(queryFirst(".o_model_viewer_hint")).not.toBe(null);
    });

    test("test_widget_hint_overlay_dismissed_on_mousedown", async () => {
        localStorage.removeItem(HINT_KEY);
        await mountViewerWidget(WITH_MODEL);
        manuallyDispatchProgrammaticEvent(
            queryFirst(".o_model_viewer_hint"),
            "mousedown"
        );
        await animationFrame();
        expect(queryFirst(".o_model_viewer_hint")).toBe(null);
    });

    test("test_widget_hint_dismissed_stores_key_in_localStorage", async () => {
        localStorage.removeItem(HINT_KEY);
        await mountViewerWidget(WITH_MODEL);
        manuallyDispatchProgrammaticEvent(
            queryFirst(".o_model_viewer_hint"),
            "mousedown"
        );
        await animationFrame();
        expect(localStorage.getItem(HINT_KEY)).toBe("1");
    });

    test("test_widget_hint_dismissed_on_touchstart", async () => {
        localStorage.removeItem(HINT_KEY);
        await mountViewerWidget(WITH_MODEL);
        manuallyDispatchProgrammaticEvent(
            queryFirst(".o_model_viewer_hint"),
            "touchstart"
        );
        await animationFrame();
        expect(queryFirst(".o_model_viewer_hint")).toBe(null);
    });

    test("test_widget_hint_suppressed_when_localStorage_set", async () => {
        localStorage.setItem(HINT_KEY, "1");
        await mountViewerWidget(WITH_MODEL);
        expect(queryFirst(".o_model_viewer_hint")).toBe(null);
    });

    test("test_widget_model_viewer_script_injected_once", async () => {
        await mountViewerWidget(WITH_MODEL);
        // MountView clears _records after processing; restore before the second mount
        ProductTemplate._records[0] = {
            id: 1,
            model_3d: "ZmFrZQ==",
            model_3d_filename: false,
            model_3d_conversion_state: "done",
        };
        await mountViewerWidget();
        const scripts = document.querySelectorAll('script[src*="model-viewer"]');
        expect(scripts.length).toBe(1);
    });

    test("test_widget_min_camera_orbit_attribute_set", async () => {
        await mountViewerWidget(WITH_MODEL);
        expect(queryFirst("model-viewer").hasAttribute("min-camera-orbit")).toBe(true);
    });

    test("test_fullscreen_button_present_when_model_loaded", async () => {
        await mountViewerWidget(WITH_MODEL);
        expect(queryFirst(".o_model_viewer_fullscreen")).not.toBe(null);
    });

    test("test_fullscreen_button_absent_when_no_model", async () => {
        await mountViewerWidget({model_3d: false, model_3d_conversion_state: "draft"});
        expect(queryFirst(".o_model_viewer_fullscreen")).toBe(null);
    });

    test("test_fullscreen_button_calls_requestFullscreen_on_click", async () => {
        await mountViewerWidget(WITH_MODEL);
        const mv = queryFirst("model-viewer");
        let called = false;
        mv.requestFullscreen = () => {
            called = true;
            return Promise.resolve();
        };
        manuallyDispatchProgrammaticEvent(
            queryFirst(".o_model_viewer_fullscreen"),
            "click"
        );
        await animationFrame();
        expect(called).toBe(true);
    });
});
