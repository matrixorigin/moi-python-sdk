# MOI Product Python SDK

[简体中文](https://github.com/matrixorigin/moi-python-sdk/blob/v5.2.3/README_zh-CN.md)

Use the MatrixOne Intelligence (MOI) 5.x AI Studio product API from Python to manage workspaces, Catalog resources and files, workflows, knowledge bases, SQL, and agents. The server enforces workspace and role permissions.

## Requirements and installation

Use Python 3.11 or newer. The distribution name is `moi-product-sdk` and the import name is `moi_product_sdk`.

### Install from PyPI

In an activated Python virtual environment, install the latest stable version available on PyPI and verify the import:

```sh
python -m pip install moi-product-sdk
python -c "from importlib.metadata import version; import moi_product_sdk; print(version('moi-product-sdk'))"
```

To pin a version, choose it from the [PyPI release history](https://pypi.org/project/moi-product-sdk/#history). The [GitHub v5.2.3 release](https://github.com/matrixorigin/moi-python-sdk/releases/tag/v5.2.3) provides the source snapshot and its manifest. Package availability is listed separately on PyPI.

### Older offline package

The [official SDK downloads page](https://docs.matrixorigin.cn/moi/en/5.0/developer/quickstart/downloads/ai-studio.html) offers the `0.1.0-r2` offline archive, which contains a `0.1.0` wheel. If your deployment requires this older build, verify the archive and install the wheel included in it.

## Authentication and quickstart

Create an AI Studio personal access token (PAT) in the MOI console. The example reads the endpoint and token from the environment and passes them explicitly to the client. The SDK sends the raw token as `X-API-Key`, without a `Bearer` prefix. Use the hosted endpoint below or the full API endpoint and path prefix supplied by your deployment administrator. Send the token only to a trusted AI Studio product endpoint. Inject it through a protected environment and keep it out of source, shell history, and logs.

```sh
export PRODUCT_API_BASE_URL='https://api.moi.matrixorigin.cn/v5'
export PRODUCT_API_KEY='YOUR_PERSONAL_ACCESS_TOKEN'
```

Save the following as `bind_workspace.py` and run `python bind_workspace.py`. The example binds a workspace by name and prints its ID, using the promoted `ensure_workspace` user-story entry. Once you have a workspace, continue with `WorkspaceHandle` for workspace-scoped tasks. Use `client.workspace(workspace_id)` only when you already sourced the workspace id.

```python
import os

import moi_product_sdk as sdk

client = sdk.new_with_personal_access_token(
    os.environ["PRODUCT_API_BASE_URL"],
    os.environ["PRODUCT_API_KEY"],
)
workspace = client.ensure_workspace("my-first-workspace")
print(workspace.id, workspace.name)
```

Low-level route-aligned services stay available for explicit control:

```python
for workspace in client.workspaces().list().workspaces:
    print(workspace.id, workspace.name)
```

The PAT identifies your account. Workspace requests use the server's Default Role unless you select a role for that workspace with `with_workspace_current_role_id` when constructing the client. Use an assigned role ID. The server validates the role and rejects invalid explicit selections.

## Compatibility and license

Python SDK 5.2.3 targets the AI Studio API (`/v5`) on MOI 5.2.3. For other MOI versions, use the build specified by your deployment documentation. Older offline packages may cover different capabilities.

The [legacy Catalog SDK](https://github.com/matrixorigin/moi-python-sdk/tree/legacy) targets MOI 4.0 and uses `moi-python-sdk`, `moi`, and `RawClient` / `SDKClient`. To migrate to MOI 5.x, switch to the Product SDK's package, import, API endpoint, and client methods, then verify each business operation.

This Product SDK is licensed under the [Apache License 2.0](LICENSE). Third-party dependencies retain their own licenses and copyright notices.

## Documentation

- [AI Studio SDK quickstart](https://docs.matrixorigin.cn/moi/en/5.0/developer/quickstart/ai-studio/sdk.html) and [API setup](https://docs.matrixorigin.cn/moi/en/5.0/developer/quickstart/ai-studio/http-api.html)
- [Tasks and API notes](#tasks-and-api-notes) for files, workflows, knowledge bases, and Agent A2A.

## Tasks and API notes

| Task | Entry point |
| --- | --- |
| Bind a workspace and select resources | `WorkspaceHandle` |
| Manage volumes and files | `VolumeHandle` / `FileHandle` |
| Deploy, run, and inspect workflows | `WorkflowHandle` / `WorkflowRunHandle` |
| Manage knowledge bases and semantic entries | `SemanticModelHandle` |
| Invoke agents and follow A2A tasks | `AgentHandle` / `send_text` |

- The SDK returns typed product results. `Error.details` retains structured diagnostics from the server.
- Pass capability IDs to `current_principal_capabilities` to check specific permissions. The server reports unrecognized IDs separately.
- `SQLService.download_query_result` streams the saved CSV result for a statement ID. Close the response stream after reading. [Run SQL queries](https://docs.matrixorigin.cn/moi/en/5.0/developer/sdk/ai-studio/%E6%95%B0%E6%8D%AE%E5%A4%84%E7%90%86/%E6%89%A7%E8%A1%8CSQL%E6%9F%A5%E8%AF%A2.html)
- A2A `message/send` responds at admission and may return a task in `submitted` or `working`. The server rejects `configuration.blocking: true` with HTTP 400, JSON-RPC `-32602`, and `BLOCKING_UNSUPPORTED`.
- `AgentHandle.send_text` and `AgentService.a2a` follow pending tasks with `tasks/resubscribe` and poll `tasks/get` every 2 seconds if streaming is unavailable. Handle the returned terminal state or `input-required` or `auth-required` status. `with_a2a_wait_timeout` defaults to 10 minutes for the whole follow, independent of per-request `with_timeout`. After `ErrTimeout`, use `task_id` in `Error.details` to query the same task.
- Set `no_wait=True` on an explicit A2A request to return at admission. The setting controls client-side following. Keep the returned task ID. [Invoke agents and track tasks](https://docs.matrixorigin.cn/moi/en/5.0/developer/sdk/ai-studio/%E6%99%BA%E8%83%BD%E4%BD%93/%E8%B0%83%E7%94%A8%E6%99%BA%E8%83%BD%E4%BD%93%E5%B9%B6%E8%B7%9F%E8%B8%AA%E4%BB%BB%E5%8A%A1.html)
- `MemoryService` and `ConsumerMemoryHandle` refer to the legacy Consumer Memory/Profile API. Current MOI product deployments do not expose those endpoints.
