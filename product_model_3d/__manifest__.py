{
    "name": "Product 3D Model Viewer",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "category": "Product",
    "summary": "Attach 3D models to products (GLB/GLTF direct; converts STL/OBJ/STEP)",
    "author": "Depaolim, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/product-attribute",
    "images": ["static/description/banner.png"],
    "depends": ["product", "queue_job"],
    "assets": {
        "web.assets_backend": [
            "product_model_3d/static/src/js/model_viewer_widget.esm.js",
            "product_model_3d/static/src/xml/model_viewer_widget.xml",
            "product_model_3d/static/src/css/model_viewer.css",
            "product_model_3d/static/src/js/model_3d_source_upload_widget.esm.js",
            "product_model_3d/static/src/xml/model_3d_source_upload_widget.xml",
        ],
        "web.assets_unit_tests": [
            "product_model_3d/static/src/js/tests/model_3d_source_upload_widget.test.js",
            "product_model_3d/static/src/js/tests/model_viewer_widget.test.js",
        ],
    },
    "data": [
        "data/queue_job_channel_data.xml",
        "views/product_template_views.xml",
    ],
    "demo": [
        "demo/product_demo.xml",
    ],
    "installable": True,
    "application": False,
    "external_dependencies": {"python": ["trimesh", "cascadio"]},
}
