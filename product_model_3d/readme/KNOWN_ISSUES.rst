* ``max_retries=0`` is hard-coded on the queue job: a failed conversion will
  not be retried automatically.  Upload a corrected file to restart the
  pipeline.
* The model-viewer library is loaded dynamically at widget mount time;
  ensure the file is accessible under
  ``/product_model_3d/static/lib/model-viewer.min.js``.
* Conversion quality and supported input formats depend on the installed
  version of ``trimesh`` and its optional dependencies (``cascadio`` for
  STEP/STP support).
