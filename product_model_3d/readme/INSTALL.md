## Python dependencies

The following Python packages must be available in the Odoo virtualenv:

``` text
trimesh>=4.11.5
cascadio>=0.0.17
```

Install them with:

``` bash
pip install trimesh>=4.11.5 cascadio>=0.0.17
```

or add them to your project's `requirements.txt` and run
`pip install -r requirements.txt`.

## JavaScript library

The module uses the [Google model-viewer](https://modelviewer.dev/)
library. A stub file is committed at `static/lib/model-viewer.min.js`;
replace it with the real build before deploying:

``` bash
MODEL_VIEWER_CDN=https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js
curl -fsSL $MODEL_VIEWER_CDN -o addons/product_model_3d/static/lib/model-viewer.min.js
```

## Odoo modules

This module depends on:

- `product` (Odoo core)
- `queue_job` (OCA/queue)
