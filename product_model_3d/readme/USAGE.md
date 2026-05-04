## Uploading a 3D model

1.  Open a product form and navigate to the **3D Model** tab.
2.  Click **Choose File** and select a 3D file (GLB, GLTF, STL, OBJ,
    STP, …).
3.  Click the action button:
    - **Use as 3D Model** — for GLB/GLTF files (no conversion needed;
      the file is stored directly).
    - **Convert to GLB** — for all other formats; a `queue_job` worker
      converts the file asynchronously via `trimesh`.
4.  While conversion is in progress the upload widget displays a
    **Converting…** spinner and polls the server every 3 seconds. Once
    done the 3D viewer renders automatically.

## Viewing and downloading

- The **3D Model** tab renders an interactive `<model-viewer>` element.
  Use the mouse or touch to rotate, zoom, and pan.
- A **Download** link below the viewer retrieves the converted GLB file.
- The first time the viewer loads, a hint overlay ("Drag to rotate ·
  Scroll to zoom") is shown; dismissing it stores the preference in
  `localStorage` so it does not reappear.

## Conversion states

| State | Meaning |
|----|----|
| `draft` | No source file uploaded, or fields have been cleared. |
| `queued` | Conversion job is waiting in the queue. |
| `processing` \| Worker has picked up the job and is running. |  |
| `done` | GLB available; viewer is rendered. |
| `failed` | Conversion error; message displayed in the widget. |

If the conversion fails, the error message from `trimesh` is displayed
directly in the upload widget. Uploading a new file or clicking
**Clear** resets the state to `draft`.

## Error handling

Failed conversions write their state and error message in a **separate
database cursor**, isolated from the `queue_job` transaction rollback.
This guarantees that the `failed` state and error text are always
visible to the user even if the worker transaction is rolled back.
