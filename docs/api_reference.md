# MOI Python SDK – Detailed API Reference

Every method mirrors the behavior of the Go counterpart. Examples below are
Python snippets that can be copy‑pasted into an interactive session.

```python
from moi import RawClient, SDKClient, TablePrivInfo

raw = RawClient("https://api.example.com", "your-api-key")
sdk = SDKClient(raw)
```

---

## Catalog APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_catalog` | POST `/catalog/create` – add a new catalog. | `raw.create_catalog({"name": "analytics", "description": "Prod catalog"})` |
| `delete_catalog` | Delete catalog and everything beneath it. | `raw.delete_catalog({"id": 101})` |
| `update_catalog` | Rename/update description. | `raw.update_catalog({"id": 101, "name": "analytics_v2"})` |
| `get_catalog` | Fetch metadata for one catalog. | `raw.get_catalog({"id": 101})` |
| `list_catalogs` | List all catalogs. | `raw.list_catalogs()` |
| `get_catalog_tree` | Retrieve nested tree (catalog→db→tables). | `raw.get_catalog_tree()` |
| `get_catalog_ref_list` | List volumes referencing catalog. | `raw.get_catalog_ref_list({"id": 101})` |

## Database APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_database` | POST `/catalog/database/create`. | `raw.create_database({"catalog_id": 101, "name": "sales", "description": "Sales mart"})` |
| `delete_database` | Remove entire database. | `raw.delete_database({"id": 201})` |
| `update_database` | Update description. | `raw.update_database({"id": 201, "description": "Archive"})` |
| `get_database` | Fetch DB metadata. | `raw.get_database({"id": 201})` |
| `list_databases` | List DBs in catalog. | `raw.list_databases({"id": 101})` |
| `get_database_children` | Tables + volumes under DB. | `raw.get_database_children({"id": 201})` |
| `get_database_ref_list` | Volume references for DB. | `raw.get_database_ref_list({"id": 201})` |

## Table APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_table` | Create schema. | `raw.create_table({"database_id": 201, "name": "orders", "columns": [{"name": "id", "type": "int", "is_pk": True}]})` |
| `get_table` | Full schema + stats. | `raw.get_table({"id": 301})` |
| `get_table_overview` | Lightweight table list. | `raw.get_table_overview()` |
| `check_table_exists` | Boolean check by DB/name. | `raw.check_table_exists({"database_id": 201, "name": "orders"})` |
| `preview_table` | Sample rows. | `raw.preview_table({"id": 301, "lines": 10})` |
| `load_table` | Trigger load task. | `raw.load_table({"id": 301, "file_option": {...}, "table_option": {...}})` |
| `get_table_download_link` | Signed download URL. | `raw.get_table_download_link({"id": 301})` |
| `truncate_table` | Delete all rows. | `raw.truncate_table({"id": 301})` |
| `delete_table` | Drop table. | `raw.delete_table({"id": 301})` |
| `get_table_full_path` | Resolve catalog/DB path. | `raw.get_table_full_path({"table_id_list": [301]})` |
| `get_table_ref_list` | See referencing objects. | `raw.get_table_ref_list({"id": 301})` |

## Volume APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_volume` | Create file volume under DB. | `raw.create_volume({"database_id": 201, "name": "sales_files", "description": "Landing"})` |
| `delete_volume` | Remove volume. | `raw.delete_volume({"id": "vol-1"})` |
| `update_volume` | Rename/describe. | `raw.update_volume({"id": "vol-1", "name": "sales_filesv2"})` |
| `get_volume` | Inspect metadata. | `raw.get_volume({"id": "vol-1"})` |
| `get_volume_ref_list` | References to volume. | `raw.get_volume_ref_list({"id": "vol-1"})` |
| `get_volume_full_path` | Resolve folder paths. | `raw.get_volume_full_path({"volume_id_list": ["vol-1"]})` |
| `add_volume_workflow_ref` / `remove_volume_workflow_ref` | Link/unlink workflows. | `raw.add_volume_workflow_ref({"id": "vol-1"})` |

## File APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_file` | Register file metadata. | `raw.create_file({"name": "report.pdf", "volume_id": "vol-1", "parent_id": "", "size": 2048, "show_type": "pdf"})` |
| `update_file` | Rename file. | `raw.update_file({"id": "file-7", "name": "report_v2.pdf"})` |
| `delete_file` | Remove file by ID. | `raw.delete_file({"id": "file-7"})` |
| `delete_file_ref` | Delete via reference ID. | `raw.delete_file_ref({"id": "ref-1"})` |
| `get_file` | Inspect metadata. | `raw.get_file({"id": "file-7"})` |
| `list_files` | Paginated listing. | `raw.list_files({"keyword": "", "common_condition": {"page": 1, "page_size": 20}})` |
| `upload_file` | Simple upload workflow. | `raw.upload_file({"name": "blob.parquet", "volume_id": "vol-1", "parent_id": ""})` |
| `get_file_download_link` | Signed download URL. | `raw.get_file_download_link({"file_id": "file-7", "volume_id": "vol-1"})` |
| `get_file_preview_link` | Browser preview link. | `raw.get_file_preview_link({"file_id": "file-7", "volume_id": "vol-1"})` |
| `get_file_preview_stream` | Streaming preview. | `raw.get_file_preview_stream({"file_id": "file-7"})` |

## Folder APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_folder` | New folder. | `raw.create_folder({"name": "2024", "volume_id": "vol-1", "parent_id": ""})` |
| `update_folder` | Rename folder. | `raw.update_folder({"id": "fold-1", "name": "2024_Q1"})` |
| `delete_folder` | Remove folder tree. | `raw.delete_folder({"id": "fold-1"})` |
| `clean_folder` | Remove contents but keep folder. | `raw.clean_folder({"id": "fold-1"})` |
| `get_folder_ref_list` | References to folder. | `raw.get_folder_ref_list({"id": "fold-1"})` |

## Connector & Upload APIs

| Method | Description | Example |
| --- | --- | --- |
| `upload_local_files` | Multipart upload of local files. | `raw.upload_local_files([(open("data.csv","rb"), "data.csv")], [{"filename": "data.csv", "path": "/"}])` |
| `upload_local_file` | Single-file helper. | `raw.upload_local_file(open("data.csv","rb"), "data.csv", [{"filename": "data.csv", "path": "/"}])` |
| `upload_local_file_from_path` | Open + upload by path. | `raw.upload_local_file_from_path("data.csv", [{"filename": "data.csv", "path": "/"}])` |
| `preview_connector_file` | Inspect uploaded/connector file. | `raw.preview_connector_file({"conn_file_id": conn_file_id})` |
| `upload_connector_file` | Upload or reference files for ingestion. | `raw.upload_connector_file("123456", meta=[{"filename": "data.csv", "path": "/"}], table_config={"new_table": True, "database_id": 201, "conn_file_ids": [conn_file_id]})` |
| `download_connector_file` | Generate a signed download URL for connector files. | `raw.download_connector_file({"conn_file_id": conn_file_id})` |
| `delete_connector_file` | Delete connector file by `conn_file_id`. | `raw.delete_connector_file({"conn_file_id": conn_file_id})` |

## User APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_user` | Add user with roles. | `raw.create_user({"name": "alice", "password": "Secret!", "role_id_list": [401]})` |
| `delete_user` | Remove user. | `raw.delete_user({"id": 501})` |
| `get_user_detail` | Fetch profile. | `raw.get_user_detail({"id": 501})` |
| `list_users` | Paginated listing. | `raw.list_users({"keyword": "", "common_condition": {"page": 1, "page_size": 20}})` |
| `update_user_password` | Admin password reset. | `raw.update_user_password({"id": 501, "password": "NewPass!"})` |
| `update_user_info` | Update contact info. | `raw.update_user_info({"id": 501, "email": "alice@example.com"})` |
| `update_user_roles` | Replace role list. | `raw.update_user_roles({"id": 501, "role_id_list": [401, 402]})` |
| `update_user_status` | Activate/deactivate. | `raw.update_user_status({"id": 501, "action": "enable"})` |
| `get_my_api_key` | View own API key. | `raw.get_my_api_key()` |
| `refresh_my_api_key` | Rotate API key. | `raw.refresh_my_api_key()` |
| `get_my_info` | Fetch caller profile. | `raw.get_my_info()` |
| `update_my_info` / `update_my_password` | Self-service updates. | `raw.update_my_info({"email": "me@company.com"})` |

## Role APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_role` | Create role with privileges. | `raw.create_role({"name": "analyst", "authority_code_list": ["DT8"]})` |
| `delete_role` | Remove role. | `raw.delete_role({"id": 401})` |
| `get_role` | Inspect role details. | `raw.get_role({"id": 401})` |
| `list_roles` | Paginated listing. | `raw.list_roles({"keyword": "", "common_condition": {"page": 1, "page_size": 20}})` |
| `list_roles_by_category_and_object` | Roles attached to specific object. | `raw.list_roles_by_category_and_object({"category": "table", "id": "301"})` |
| `update_role_code_list` | Update global privileges. | `raw.update_role_code_list({"role_id": 401, "code_list": ["DT8", "DT9"]})` |
| `update_role_info` | Update both global/object privs. | `raw.update_role_info({...})` |
| `update_roles_by_object` | Assign roles to object in bulk. | `raw.update_roles_by_object({"id": "301", "code": "DT8", "role_id_list": [401]})` |
| `update_role_status` | Enable/disable role. | `raw.update_role_status({"id": 401, "action": "enable"})` |

## Privilege APIs

| Method | Description | Example |
| --- | --- | --- |
| `list_objects_by_category` | List objects eligible for privilege binding. | `raw.list_objects_by_category({"category": "table"})` |

## GenAI APIs

| Method | Description | Example |
| --- | --- | --- |
| `create_genai_pipeline` | Create pipeline; optional file upload. | `raw.create_genai_pipeline({"steps": [{"node": "ingest"}]})` |
| `get_genai_job` | Inspect job status/files. | `raw.get_genai_job("job-123")` |
| `download_genai_result` | Stream result file via `FileStream`. | `stream = raw.download_genai_result("file-xyz"); data = stream.read(); stream.close()` |

## NL2SQL & Knowledge APIs

| Method | Description | Example |
| --- | --- | --- |
| `run_nl2sql` | Execute NL→SQL job. | `raw.run_nl2sql({"operation": "run_sql", "statement": "select * from sales limit 10"})` |
| `create_knowledge` | Add NL2SQL knowledge entry. | `raw.create_knowledge({...})` |
| `update_knowledge` | Modify entry. | `raw.update_knowledge({"id": 1, ...})` |
| `delete_knowledge` | Remove entry. | `raw.delete_knowledge({"id": 1})` |
| `get_knowledge` | Fetch entry. | `raw.get_knowledge({"id": 1})` |
| `list_knowledge` | Paginated list. | `raw.list_knowledge({"page_number": 1, "page_size": 20})` |
| `search_knowledge` | Filter by key/type. | `raw.search_knowledge({"knowledge_key": "total sales"})` |

## Health & Log APIs

| Method | Description | Example |
| --- | --- | --- |
| `health_check` | GET `/healthz` status. | `raw.health_check()` |
| `list_user_logs` | Paginated user logs. | `raw.list_user_logs({"common_condition": {"page": 1, "page_size": 20}})` |
| `list_role_logs` | Paginated role logs. | `raw.list_role_logs({"common_condition": {"page": 1, "page_size": 20}})` |

## LLM Proxy APIs

LLM Proxy APIs use `/llm-proxy` prefix and return data directly (no envelope wrapper).

### Session Management

| Method | Description | Example |
| --- | --- | --- |
| `create_llm_session` | Create new session. | `raw.create_llm_session({"title": "My Session", "source": "my-app", "user_id": "user123", "tags": ["alpha"]})` |
| `list_llm_sessions` | List sessions with filters/pagination. | `raw.list_llm_sessions({"user_id": "user123", "source": "my-app", "page": 1, "page_size": 20})` |
| `get_llm_session` | Get session by ID. | `raw.get_llm_session(1)` |
| `update_llm_session` | Update session (partial updates). | `raw.update_llm_session(1, {"title": "Updated", "tags": ["release"]})` |
| `delete_llm_session` | Delete session. | `raw.delete_llm_session(1)` |
| `list_llm_session_messages` | List messages for session. Note: Does not return content fields. Use `get_llm_chat_message` for full content. | `raw.list_llm_session_messages(1, {"role": "user", "status": "success", "after": 5, "limit": 50})` |
| `get_llm_session_latest_completed_message` | Get latest completed message ID (only success status). | `raw.get_llm_session_latest_completed_message(1)` |
| `get_llm_session_latest_message` | Get latest message ID (regardless of status). | `raw.get_llm_session_latest_message(1)` |

### Chat Message Management

| Method | Description | Example |
| --- | --- | --- |
| `create_llm_chat_message` | Create chat message record. | `raw.create_llm_chat_message({"user_id": "user123", "source": "my-app", "role": "user", "content": "Hello", "model": "gpt-4", "status": "success"})` |
| `get_llm_chat_message` | Get message by ID. | `raw.get_llm_chat_message(1)` |
| `update_llm_chat_message` | Update message. | `raw.update_llm_chat_message(1, {"status": "success", "response": "Reply"})` |
| `delete_llm_chat_message` | Delete message. | `raw.delete_llm_chat_message(1)` |
| `update_llm_chat_message_tags` | Replace message tags. | `raw.update_llm_chat_message_tags(1, {"tags": ["tag1", "tag2"]})` |
| `delete_llm_chat_message_tag` | Delete single tag from message. | `raw.delete_llm_chat_message_tag(1, "my-app", "tag1")` |

---

# SDKClient Helpers

| Method | Description | Example |
| --- | --- | --- |
| `create_table_role` | Create/fetch table privilege role. Returns `(role_id, created_bool)`. | `sdk.create_table_role("analytics_reader", "Table read", [TablePrivInfo(table_id=301, priv_codes=["DT8"])])` |
| `update_table_role` | Update table/global privileges while preserving unspecified fields. | `sdk.update_table_role(role_id, "", [TablePrivInfo(table_id=301, priv_codes=["DT8","DT9"])], global_privs=None)` |
| `import_local_file_to_table` | Import already uploaded file(s) into table using connector workflow. | `sdk.import_local_file_to_table({"new_table": False, "table_id": 301, "database_id": 201, "conn_file_ids": [conn_file_id], "existed_table": []})` |
| `run_sql` | Execute fully qualified SQL via NL2SQL RunSQL operation. | `sdk.run_sql("select * from sales.orders limit 10")` |

These high-level helpers encapsulate the multi-step logic showcased in the Go
SDK documentation, ensuring Python developers enjoy the same ergonomic flows.

