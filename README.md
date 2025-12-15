# MOI Python SDK

Python client for the MatrixOrigin MOI Catalog Service, mirroring the feature
set provided by the Go SDK (`moi-go-sdk`). It offers both a low-level
`RawClient` (1:1 HTTP bindings) and a high-level `SDKClient` with productivity
helpers for role/table workflows.

## Installation

### 方式一：从 PyPI 安装（推荐）

如果包已发布到 PyPI，可以直接安装：

```bash
pip install moi-python-sdk
```

### 方式二：从 GitHub 直接安装

无需下载源码，直接从 GitHub 仓库安装：

```bash
pip install git+https://github.com/matrixorigin/moi-python-sdk.git
```

或者安装特定版本/分支：

```bash
# 安装特定分支
pip install git+https://github.com/matrixorigin/moi-python-sdk.git@main

# 安装特定标签版本
pip install git+https://github.com/matrixorigin/moi-python-sdk.git@v0.1.0
```

### 方式三：本地开发安装

如果需要修改源码或进行开发：

```bash
# 克隆仓库
git clone https://github.com/matrixorigin/moi-python-sdk.git
cd moi-python-sdk

# 安装依赖和包
pip install -r requirements.txt
pip install -e .  # 可编辑模式安装，修改代码后无需重新安装
```

## Quick Start

```python
from moi import RawClient, SDKClient, TablePrivInfo

raw = RawClient(
    base_url="https://api.example.com",
    api_key="your-api-key",
)

# Low-level call
catalog = raw.create_catalog({"name": "analytics", "description": "Prod catalog"})

# High-level helpers
sdk = SDKClient(raw)
role_id, created = sdk.create_table_role(
    role_name="analytics_reader",
    comment="Read-only access",
    table_privs=[
        TablePrivInfo(
            table_id=123,
            priv_codes=["DT8"],  # SELECT
        ),
    ],
)
```

## Features

- Full coverage of Catalog/Database/Table/Volume/File/Folder APIs
- Detailed per-method references in `docs/api_reference.md` (EN) and `docs/api_reference_zh.md` (中文)
- Connector workflows: local uploads, connector imports, preview
- User/Role/Privilege management
- GenAI, NL2SQL, Health, and Log endpoints
- Streaming downloads via `FileStream`
- High-level helpers for table role management and file-to-table import

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Code style follows standard `pyproject`-less tooling (feel free to add linters
or tests). Contributions are welcome—please align new APIs with the Go SDK
behavior to keep parity between implementations.
