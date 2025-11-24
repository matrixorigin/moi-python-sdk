# MOI Python SDK

Python client for the MatrixOrigin MOI Catalog Service, mirroring the feature
set provided by the Go SDK (`moi-go-sdk`). It offers both a low-level
`RawClient` (1:1 HTTP bindings) and a high-level `SDKClient` with productivity
helpers for role/table workflows.

## Installation

```bash
pip install -r requirements.txt
python setup.py install  # or pip install .
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
