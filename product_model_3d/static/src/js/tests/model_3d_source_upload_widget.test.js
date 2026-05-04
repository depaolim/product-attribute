/** @odoo-module **/

import {describe, expect, test} from "@odoo/hoot";
import {queryFirst} from "@odoo/hoot-dom";
import {defineMailModels} from "@mail/../tests/mail_test_helpers";
import {defineModels, fields, models, mountView} from "@web/../tests/web_test_helpers";

class ProductTemplate extends models.Model {
    _name = "product.template";

    model_3d_source = fields.Binary();
    model_3d_source_filename = fields.Char();
    model_3d_source_size_kb = fields.Integer();
    model_3d_conversion_state = fields.Selection({
        selection: [
            ["draft", "Draft"],
            ["queued", "Queued"],
            ["processing", "Processing"],
            ["done", "Done"],
            ["failed", "Failed"],
        ],
    });
    model_3d_conversion_error = fields.Char();

    _records = [
        {
            id: 1,
            model_3d_source: false,
            model_3d_source_filename: false,
            model_3d_source_size_kb: 0,
            model_3d_conversion_state: "draft",
            model_3d_conversion_error: false,
        },
    ];
}

defineMailModels();
defineModels([ProductTemplate]);

async function mountUploadWidget(recordPatch = {}) {
    Object.assign(ProductTemplate._records[0], recordPatch);
    return mountView({
        type: "form",
        resModel: "product.template",
        resId: 1,
        arch: `
            <form>
                <field name="model_3d_source" widget="model_3d_source_upload"/>
                <field name="model_3d_source_filename" invisible="1"/>
                <field name="model_3d_source_size_kb" invisible="1"/>
                <field name="model_3d_conversion_state" invisible="1"/>
                <field name="model_3d_conversion_error" invisible="1"/>
            </form>
        `,
    });
}

describe("Model3dSourceUploadWidget", () => {
    test("test_widget_shows_filename_and_size_when_file_set", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_source_size_kb: 2400,
        });
        expect(".o_model_3d_filename").toHaveText("part.stl");
        expect(".o_model_3d_size").toHaveText("2.3 MB");
    });

    test("test_widget_clear_button_present_when_file_set", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
        });
        expect(queryFirst(".o_model_3d_clear_btn")).not.toBe(null);
    });

    test("test_widget_clear_button_absent_without_file", async () => {
        await mountUploadWidget({model_3d_source: false});
        expect(queryFirst(".o_model_3d_clear_btn")).toBe(null);
    });

    test("test_widget_file_info_absent_without_file", async () => {
        await mountUploadWidget({model_3d_source: false});
        expect(queryFirst(".o_model_3d_file_info")).toBe(null);
    });

    test("test_widget_shows_convert_button_in_draft", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_conversion_state: "draft",
        });
        const btn = queryFirst(".o_model_3d_action_btn");
        expect(btn).not.toBe(null);
        expect(btn.disabled).toBe(false);
        expect(btn).toHaveText("Convert to GLB");
    });

    test("test_widget_shows_use_as_model_button_for_glb", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.glb",
            model_3d_conversion_state: "draft",
        });
        const btn = queryFirst(".o_model_3d_action_btn");
        expect(btn).not.toBe(null);
        expect(btn).toHaveText("Use as 3D Model");
    });

    test("test_widget_shows_use_as_model_button_for_gltf", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.gltf",
            model_3d_conversion_state: "draft",
        });
        const btn = queryFirst(".o_model_3d_action_btn");
        expect(btn).not.toBe(null);
        expect(btn).toHaveText("Use as 3D Model");
    });

    test("test_widget_shows_convert_button_in_failed", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_conversion_state: "failed",
        });
        const btn = queryFirst(".o_model_3d_action_btn");
        expect(btn).not.toBe(null);
        expect(btn.disabled).toBe(false);
        expect(btn).toHaveText("Convert to GLB");
    });

    test("test_widget_shows_action_button_when_done", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_conversion_state: "done",
        });
        const btn = queryFirst(".o_model_3d_action_btn");
        expect(btn).not.toBe(null);
        expect(btn.disabled).toBe(false);
        expect(btn).toHaveText("Convert to GLB");
    });

    test("test_widget_shows_spinner_when_queued", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_conversion_state: "queued",
        });
        expect(queryFirst(".o_model_3d_converting")).not.toBe(null);
        expect(queryFirst(".o_model_3d_action_btn")).toBe(null);
    });

    test("test_widget_shows_spinner_when_processing", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_conversion_state: "processing",
        });
        expect(queryFirst(".o_model_3d_converting")).not.toBe(null);
        expect(queryFirst(".o_model_3d_action_btn")).toBe(null);
    });

    test("test_widget_shows_error_inline_when_failed", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_conversion_state: "failed",
            model_3d_conversion_error: "Corrupt geometry",
        });
        expect(".o_model_3d_error").toHaveText("Corrupt geometry");
    });

    test("test_widget_error_not_shown_when_failed_without_error_message", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_conversion_state: "failed",
            model_3d_conversion_error: false,
        });
        expect(queryFirst(".o_model_3d_error")).toBe(null);
    });

    test("test_widget_size_formatted_as_mb_above_1024", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_source_size_kb: 5120,
        });
        expect(".o_model_3d_size").toHaveText("5.0 MB");
    });

    test("test_widget_size_formatted_as_kb_below_1024", async () => {
        await mountUploadWidget({
            model_3d_source: "ZmFrZQ==",
            model_3d_source_filename: "part.stl",
            model_3d_source_size_kb: 340,
        });
        expect(".o_model_3d_size").toHaveText("340 KB");
    });
});
