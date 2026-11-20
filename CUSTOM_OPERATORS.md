# Runtime SDK in Python custom operators

This guide applies to draft tests and published custom operators.
The worker constructs your client; custom operators do not configure standalone clients.

## Handler and client

```python
def handle(workspace_id, sdk, input):
    info = sdk.catalog(workspace_id).file_info(input["file_id"])
    return {"file_id": info.file_id, "file_name": info.file_name}
```

The parameters are supplied by python-worker:

- `workspace_id`: execution workspace.
- `sdk`: the original Product SDK client (`moi_product_sdk.Client`). The Worker
  configures its endpoint and execution assignment; the operator does not create
  or authenticate a client.
- `input`: the JSON object described by your operator input schema.

Return a JSON object conforming to your output schema. Product SDK results use
their original typed return values: use their documented attributes and build the
business result explicitly;
do not return client handles, streams, or SDK client objects directly.

The example reads metadata of an existing accessible file. Its input schema needs a
string `file_id`; its output schema needs string `file_id` and `file_name` properties.

For a user-supplied Catalog resource, annotate the JSON Schema property with the
stable semantic role used by the workflow form compiler. For example:

```json
{"type":"integer","x-semantic-role":"source_volume_id"}
```

Use `source_volume_id`, `target_volume_id`, `catalog_volume_id`,
`source_file_id`, `source_file_ids`, or the corresponding `catalog_*` role.
The compiled form renders the canonical Catalog selector and submits the
resource identity; a parameter name such as `volume_id` alone is intentionally
not enough to infer a selector.

## Product SDK API

The injected object is the original `moi_product_sdk.Client`, with the same typed
handles, options and protobuf results as a standalone Product SDK client. Use
`sdk.workspace(workspace_id)` for the workspace facade, or the existing
`sdk.catalog(workspace_id)`, `sdk.workflows(workspace_id)`,
`sdk.knowledge(workspace_id)` and other Product SDK services. Do not construct a
second client or supply credentials.

| Call | Result used by the operator |
| --- | --- |
| `sdk.catalog(workspace_id).file_info(file_id)` | typed result: `.file_id`, `.file_name`, `.size` |
| `sdk.catalog(workspace_id).download_workspace_file(file_id)` | stream; use `.read(size)` for chunks and always `.close()` |
| `sdk.catalog(workspace_id).upload_private(name, data)` | typed result: `.file_id`, `.original_name`, `.size`, `.catalog_file.volume_id` |
| `sdk.catalog(workspace_id).create_file(target_volume_id, file_id)` | attaches an uploaded file to the target volume |
| `sdk.catalog(workspace_id).files(*options)` | typed result: `.list`, `.total`; supports Product SDK filter, ordering and pagination options |
| `sdk.workflows(workspace_id).list()` | typed result: `.workflows`, `.total` |
| `sdk.knowledge(workspace_id).list()` | typed result: `.items`, `.total`, `.next_page_token` |

File body download returns a stream; decode its bytes as UTF-8 for text. Uploading
private bytes creates a staging placement. `create_file` attaches the returned
file to the target volume; it does not move or delete the staging placement.

The client carries only the current technical execution assignment. MOI verifies
that assignment is still live, restores the persisted principal and frozen Role,
and applies the ordinary generated Service authorization boundary to every call.
Cross-workspace calls, expired assignments and caller-supplied user/Role headers
are rejected by MOI. SDK method availability does not grant permission to a resource.

## Test channels and SDK availability

- `run_custom_operator_test` (and the frontend "test run" button): executes
  `main.py` on python-worker with the original Product SDK and a live execution
  assignment. SDK calls use the same Product API as standalone clients. Use live
  resource ids or the workflow fixture.
- `test_workflow` (whole-workflow candidate test): executes frozen operator source
  with the same original Product SDK and live technical execution assignment.
  Native MOI persists the candidate execution before Worker dispatch. SDK calls
  keep the ordinary assignment validation and generated Service authorization.
  Use isolated fixture resources for Catalog writes.
- Published workflow runs: same original Product SDK client as
  `run_custom_operator_test`.

A source snapshot selects the code to execute; it does not change SDK availability
or grant access. Missing, mismatched, or expired assignments fail closed. Do not
remove SDK calls or add dummy output to hide an execution-context failure.
A passing direct operator test does not establish whole-workflow acceptance.

## Other SDK capabilities

Use the existing Product SDK services and documented facade operations. The
injected client preserves their original method signatures and result types;
there is no separate reduced operator SDK. Consult the Product SDK documentation
for the required operation and verify its effects with a live operator test.

## Execute and verify

Edit `operators/<identifier>/main.py` and its `operator.json` in the authoring
workspace. Run `run_custom_operator_test` with business input matching the schema.
Python executes on python-worker; the Catalog shell is for reading/writing files,
not running the operator or installing packages.

Use real authorized resource IDs in live tests. MOI platform credentials and Role
are execution context, not business inputs, fixture fields or source constants.
Third-party service parameters belong to the declared business input; follow the
authoring and testing skills to collect missing user-provided values. Missing access,
missing data and SDK failures remain failures: do not replace them with dummy
success output. A passing operator test proves only the exercised calls and
inputs; use workflow tests to verify downstream bindings and requested effects.
