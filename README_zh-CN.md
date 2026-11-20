# MOI Product Python SDK

[English](https://github.com/matrixorigin/moi-python-sdk/blob/v5.2.3/README.md)

在 Python 应用中通过 MatrixOne Intelligence（MOI）5.x AI Studio 产品 API 管理工作区、Catalog 和文件、工作流、知识库、SQL 及智能体。请求沿用服务端的工作区与角色权限。

## 环境要求与安装

需要 Python 3.11 或更高版本。发行包名为 `moi-product-sdk`，导入名为 `moi_product_sdk`。

### 从 PyPI 安装

在已激活的 Python 虚拟环境中安装 PyPI 上最新的稳定版，并检查导入和版本：

```sh
python -m pip install moi-product-sdk
python -c "from importlib.metadata import version; import moi_product_sdk; print(version('moi-product-sdk'))"
```

如需固定版本，请从 [PyPI 发布历史](https://pypi.org/project/moi-product-sdk/#history)选择。[GitHub v5.2.3 Release](https://github.com/matrixorigin/moi-python-sdk/releases/tag/v5.2.3)提供源码快照和校验清单，安装包的可用版本以 PyPI 为准。

### 旧版离线包

[官方 SDK 下载页](https://docs.matrixorigin.cn/moi/zh/5.0/developer/quickstart/downloads/ai-studio.html)提供 `0.1.0-r2` 离线归档，其中的 wheel 版本是 `0.1.0`。如果部署需要该旧版，请按下载页校验归档，并安装其中实际提供的 wheel。

## 认证与最小示例

在 MOI 控制台创建 AI Studio 的个人访问令牌（PAT）。示例从环境变量读取地址和令牌并显式传入客户端。SDK 将原始令牌放入 `X-API-Key`，无需添加 `Bearer` 前缀。公有云使用以下地址，私有部署请使用管理员提供的完整 API 地址及其路径前缀。令牌仅用于可信的 AI Studio 产品端点。请通过受保护的环境注入令牌，避免写入源码、终端历史或日志。

```sh
export PRODUCT_API_BASE_URL='https://api.moi.matrixorigin.cn/v5'
export PRODUCT_API_KEY='YOUR_PERSONAL_ACCESS_TOKEN'
```

将以下代码保存为 `bind_workspace.py`，执行 `python bind_workspace.py`。示例按名称绑定工作区并输出其 ID，使用受推荐的 `ensure_workspace` 用户故事入口。绑定工作区后，后续操作请继续使用 `WorkspaceHandle`。只有在已经拿到工作区 ID 时才使用 `client.workspace(workspace_id)`。

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

也可以直接调用与 API 路由对应的底层服务：

```python
for workspace in client.workspaces().list().workspaces:
    print(workspace.id, workspace.name)
```

PAT 标识账号。工作区请求默认使用服务端的 Default Role，也可以在创建客户端时使用 `with_workspace_current_role_id` 为指定工作区选择角色。 请使用已绑定的角色 ID。服务端会验证角色，显式选择无效时请求会失败。

## 版本兼容性与许可证

Python SDK 5.2.3 面向 MOI 5.2.3 的 AI Studio API（`/v5`）。使用其他 MOI 版本时，请按部署说明选择匹配的制品。旧离线包的能力覆盖可能不同。

[旧版 Catalog SDK](https://github.com/matrixorigin/moi-python-sdk/tree/legacy) 面向 MOI 4.0，使用 `moi-python-sdk`、`moi` 和 `RawClient` / `SDKClient`。迁移到 MOI 5.x 时，请改用 Product SDK 的安装包、导入名、API 地址与客户端方法，并重新验证各业务调用。

本 Product SDK 采用 [Apache License 2.0](LICENSE)。第三方依赖保留各自的许可证与版权声明。

## 文档

- [AI Studio SDK 快速开始](https://docs.matrixorigin.cn/moi/zh/5.0/developer/quickstart/ai-studio/sdk.html)和[调用准备](https://docs.matrixorigin.cn/moi/zh/5.0/developer/quickstart/ai-studio/http-api.html)
- [任务与接口说明](#任务与接口说明)，涵盖文件、工作流、知识库和 Agent A2A。

## 任务与接口说明

| 任务 | 入口 |
| --- | --- |
| 绑定工作区并选择资源 | `WorkspaceHandle` |
| 管理卷和文件 | `VolumeHandle` / `FileHandle` |
| 部署、运行和查看工作流 | `WorkflowHandle` / `WorkflowRunHandle` |
| 管理知识库与语义条目 | `SemanticModelHandle` |
| 调用智能体并跟踪 A2A 任务 | `AgentHandle` / `send_text` |

- SDK 返回类型化的产品结果。`Error.details` 保留服务端的结构化诊断数据。
- 可向 `current_principal_capabilities` 传入能力 ID，只检查指定权限。服务端会单独报告无法识别的 ID。
- `SQLService.download_query_result` 使用已保存结果的 statement ID 流式下载 CSV。读取后关闭响应流。[执行 SQL 查询](https://docs.matrixorigin.cn/moi/zh/5.0/developer/sdk/ai-studio/%E6%95%B0%E6%8D%AE%E5%A4%84%E7%90%86/%E6%89%A7%E8%A1%8CSQL%E6%9F%A5%E8%AF%A2.html)
- A2A `message/send` 在受理时响应，可能返回处于 `submitted` 或 `working` 的任务。服务端以 HTTP 400、JSON-RPC `-32602` 和 `BLOCKING_UNSUPPORTED` 拒绝 `configuration.blocking: true`。
- `AgentHandle.send_text` 和 `AgentService.a2a` 默认通过 `tasks/resubscribe` 跟踪尚未完成的任务，流不可用时每 2 秒轮询 `tasks/get`。处理返回的终态或 `input-required`、`auth-required` 状态。`with_a2a_wait_timeout` 默认将整个跟踪过程限制为 10 分钟，独立于单次请求的 `with_timeout`。等待超时后，可用 `ErrTimeout` 的 `Error.details` 中的 `task_id` 查询同一任务。
- 要在受理时返回，在显式 A2A 请求上设置 `no_wait=True`。该选项只控制客户端跟踪，请保留返回的任务 ID。[调用智能体与跟踪任务](https://docs.matrixorigin.cn/moi/zh/5.0/developer/sdk/ai-studio/%E6%99%BA%E8%83%BD%E4%BD%93/%E8%B0%83%E7%94%A8%E6%99%BA%E8%83%BD%E4%BD%93%E5%B9%B6%E8%B7%9F%E8%B8%AA%E4%BB%BB%E5%8A%A1.html)
- `MemoryService` 和 `ConsumerMemoryHandle` 对应旧 Consumer Memory/Profile 接口，当前 MOI 产品部署未开放这些端点。
