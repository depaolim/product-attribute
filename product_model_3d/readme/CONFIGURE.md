## `odoo.conf` — required parameters

Asynchronous conversion relies on `queue_job` workers. The following
settings are **mandatory**:

``` ini
[options]
# queue_job must be listed in server_wide_modules so the job runner
# process starts alongside Odoo.
server_wide_modules = base,web,queue_job

# At least 2 workers are required: one serves HTTP requests while the
# other processes background jobs.  With workers=1 the job runner never
# gets CPU time and conversions will queue indefinitely.
workers = 2
```

### Dedicated conversion channel

The module creates the `root.model_3d_conversion` queue channel
automatically on install (`data/queue_job_channel_data.xml`). No manual
channel configuration is needed; the default `root` channel worker count
set by `queue_job` applies.

## System parameters (`ir.config_parameter`)

| Key | Default | Description |
|----|----|----|
| `model_3d_convert.max.size.kb` | `51200` (50 MB) | Maximum allowed source file size in KB. Uploads exceeding this limit are rejected before a job is queued. |

Set the parameter from *Settings → Technical → System Parameters* or via
`xmlrpc`:

``` python
models.execute_kw(db, uid, password,
    'ir.config_parameter', 'set_param',
    ['model_3d_convert.max.size.kb', '10240'])  # 10 MB
```
