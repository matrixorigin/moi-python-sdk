# MOI Python SDK —— 接口文档（中文）

本文档基于 `moi-go-sdk` 的源码与注释，逐项说明 Python 版本 SDK 中的
`RawClient` 与 `SDKClient` 方法。除特殊说明外，调用成功时返回服务端
Envelope 的 `data` 字段，失败时抛出 `APIError`（业务错误）或
`HTTPError`（HTTP 层错误）。

在不同场景中：

- **RawClient**：一一对应 HTTP API，便于自定义请求。
- **SDKClient**：封装角色/表等多步骤业务逻辑，使用更便捷。

```python
from moi import RawClient, SDKClient, TablePrivInfo

raw = RawClient("https://api.example.com", "your-api-key")
sdk = SDKClient(raw)
```

---

## 目录（Catalog）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_catalog` | POST `/catalog/create`，新增目录，参数包含 `name`/`description`。 | `raw.create_catalog({"name": "analytics", "description": "Prod catalog"})` |
| `delete_catalog` | 删除目录及其全部子资源。 | `raw.delete_catalog({"id": 101})` |
| `update_catalog` | 更新目录名称或描述。 | `raw.update_catalog({"id": 101, "name": "analytics_v2"})` |
| `get_catalog` | 查看目录详情、计数、时间戳等。 | `raw.get_catalog({"id": 101})` |
| `list_catalogs` | 列出所有目录。 | `raw.list_catalogs()` |
| `get_catalog_tree` | 获取目录→数据库→表的树状结构。 | `raw.get_catalog_tree()` |
| `get_catalog_ref_list` | 查看指向该目录的卷引用。 | `raw.get_catalog_ref_list({"id": 101})` |

## 数据库（Database）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_database` | POST `/catalog/database/create`，在目录下创建数据库。 | `raw.create_database({"catalog_id": 101, "name": "sales", "description": "Sales mart"})` |
| `delete_database` | 删除数据库及其下属资源。 | `raw.delete_database({"id": 201})` |
| `update_database` | 更新数据库描述。 | `raw.update_database({"id": 201, "description": "Archive"})` |
| `get_database` | 查询数据库信息。 | `raw.get_database({"id": 201})` |
| `list_databases` | 列出目录下所有数据库。 | `raw.list_databases({"id": 101})` |
| `get_database_children` | 列出数据库下的表和数据卷。 | `raw.get_database_children({"id": 201})` |
| `get_database_ref_list` | 查看与数据库关联的卷引用。 | `raw.get_database_ref_list({"id": 201})` |

## 表（Table）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_table` | 创建表结构，指定列信息与注释。 | `raw.create_table({"database_id": 201, "name": "orders", "columns": [{"name": "id", "type": "int", "is_pk": True}]})` |
| `get_table` | 获取表结构、统计信息、元数据。 | `raw.get_table({"id": 301})` |
| `get_table_overview` | 获取所有表的概览信息。 | `raw.get_table_overview()` |
| `check_table_exists` | 判断某数据库下表名是否存在。 | `raw.check_table_exists({"database_id": 201, "name": "orders"})` |
| `preview_table` | 预览表数据，限制返回行数。 | `raw.preview_table({"id": 301, "lines": 10})` |
| `load_table` | 触发数据载入任务，需指定文件/表参数。 | `raw.load_table({"id": 301, "file_option": {...}, "table_option": {...}})` |
| `get_table_download_link` | 获取表数据的下载链接。 | `raw.get_table_download_link({"id": 301})` |
| `truncate_table` | 清空表数据但保留表结构。 | `raw.truncate_table({"id": 301})` |
| `delete_table` | 删除表及其数据。 | `raw.delete_table({"id": 301})` |
| `get_table_full_path` | 获取表对应的目录/数据库路径。 | `raw.get_table_full_path({"table_id_list": [301]})` |
| `get_table_ref_list` | 查看引用该表的对象列表。 | `raw.get_table_ref_list({"id": 301})` |

## 数据卷（Volume）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_volume` | 在数据库下创建数据卷，用于存放文件。 | `raw.create_volume({"database_id": 201, "name": "sales_files", "description": "Landing"})` |
| `delete_volume` | 删除数据卷。 | `raw.delete_volume({"id": "vol-1"})` |
| `update_volume` | 更新数据卷名称或描述。 | `raw.update_volume({"id": "vol-1", "name": "sales_filesv2"})` |
| `get_volume` | 获取数据卷信息。 | `raw.get_volume({"id": "vol-1"})` |
| `get_volume_ref_list` | 查看引用该卷的对象。 | `raw.get_volume_ref_list({"id": "vol-1"})` |
| `get_volume_full_path` | 获取卷/文件夹的完整路径。 | `raw.get_volume_full_path({"volume_id_list": ["vol-1"]})` |
| `add_volume_workflow_ref` / `remove_volume_workflow_ref` | 与工作流建立/移除关联。 | `raw.add_volume_workflow_ref({"id": "vol-1"})` |

## 文件（File）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_file` | 在卷/文件夹下注册文件（元数据）。 | `raw.create_file({"name": "report.pdf", "volume_id": "vol-1", "parent_id": "", "size": 2048, "show_type": "pdf"})` |
| `update_file` | 修改文件名称等信息。 | `raw.update_file({"id": "file-7", "name": "report_v2.pdf"})` |
| `delete_file` | 根据 ID 删除文件。 | `raw.delete_file({"id": "file-7"})` |
| `delete_file_ref` | 通过引用 ID 删除文件。 | `raw.delete_file_ref({"id": "ref-1"})` |
| `get_file` | 查看文件详细信息。 | `raw.get_file({"id": "file-7"})` |
| `list_files` | 分页列出文件。 | `raw.list_files({"keyword": "", "common_condition": {"page": 1, "page_size": 20}})` |
| `upload_file` | 直接上传文件到 `/catalog/file/upload`。 | `raw.upload_file({"name": "blob.parquet", "volume_id": "vol-1", "parent_id": ""})` |
| `get_file_download_link` | 获取文件下载链接。 | `raw.get_file_download_link({"file_id": "file-7", "volume_id": "vol-1"})` |
| `get_file_preview_link` | 浏览器预览链接。 | `raw.get_file_preview_link({"file_id": "file-7", "volume_id": "vol-1"})` |
| `get_file_preview_stream` | 以流形式预览文件。 | `raw.get_file_preview_stream({"file_id": "file-7"})` |

## 文件夹（Folder）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_folder` | 创建文件夹。 | `raw.create_folder({"name": "2024", "volume_id": "vol-1", "parent_id": ""})` |
| `update_folder` | 修改文件夹名称。 | `raw.update_folder({"id": "fold-1", "name": "2024_Q1"})` |
| `delete_folder` | 删除文件夹及其内容。 | `raw.delete_folder({"id": "fold-1"})` |
| `clean_folder` | 清空文件夹内容但保留文件夹。 | `raw.clean_folder({"id": "fold-1"})` |
| `get_folder_ref_list` | 查看引用该文件夹的对象。 | `raw.get_folder_ref_list({"id": "fold-1"})` |

## 连接器与上传相关接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `upload_local_files` | 将多个本地文件上传至连接器临时存储。 | `raw.upload_local_files([(open("data.csv","rb"), "data.csv")], [{"filename": "data.csv", "path": "/"}])` |
| `upload_local_file` | 单文件上传封装。 | `raw.upload_local_file(open("data.csv","rb"), "data.csv", [{"filename": "data.csv", "path": "/"}])` |
| `upload_local_file_from_path` | 通过路径打开并上传。 | `raw.upload_local_file_from_path("data.csv", [{"filename": "data.csv", "path": "/"}])` |
| `preview_connector_file` | 预览连接器/本地上传文件的结构。 | `raw.preview_connector_file({"conn_file_id": conn_file_id})` |
| `upload_connector_file` | 上传（或引用 `table_config.conn_file_ids`）来触发表导入。 | `raw.upload_connector_file("123456", meta=[{"filename": "data.csv", "path": "/"}], table_config={"new_table": True, "database_id": 201, "conn_file_ids": [conn_file_id]})` |
| `download_connector_file` | 生成 connector 文件的下载链接。 | `raw.download_connector_file({"conn_file_id": conn_file_id})` |
| `delete_connector_file` | 通过 `conn_file_id` 删除 connector 文件。 | `raw.delete_connector_file({"conn_file_id": conn_file_id})` |

## 任务（Task）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `get_task` | 根据任务 ID 获取任务的详细信息，包括状态、配置和结果。 | `raw.get_task({"task_id": 123})` |

## 用户（User）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_user` | 创建用户并绑定角色。 | `raw.create_user({"name": "alice", "password": "Secret!", "role_id_list": [401]})` |
| `delete_user` | 删除用户。 | `raw.delete_user({"id": 501})` |
| `get_user_detail` | 获取用户详细信息。 | `raw.get_user_detail({"id": 501})` |
| `list_users` | 分页查询用户列表。 | `raw.list_users({"keyword": "", "common_condition": {"page": 1, "page_size": 20}})` |
| `update_user_password` | 管理员重置密码。 | `raw.update_user_password({"id": 501, "password": "NewPass!"})` |
| `update_user_info` | 更新用户联系方式等信息。 | `raw.update_user_info({"id": 501, "email": "alice@example.com"})` |
| `update_user_roles` | 替换用户角色列表。 | `raw.update_user_roles({"id": 501, "role_id_list": [401, 402]})` |
| `update_user_status` | 启用/禁用用户。 | `raw.update_user_status({"id": 501, "action": "enable"})` |
| `get_my_api_key` | 获取当前登录者的 API Key。 | `raw.get_my_api_key()` |
| `refresh_my_api_key` | 刷新 API Key。 | `raw.refresh_my_api_key()` |
| `get_my_info` | 查看当前登录者信息。 | `raw.get_my_info()` |
| `update_my_info` / `update_my_password` | 自助更新个人信息或密码。 | `raw.update_my_info({"email": "me@company.com"})` |

## 角色（Role）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_role` | 创建角色并设置权限。 | `raw.create_role({"name": "analyst", "authority_code_list": ["DT8"]})` |
| `delete_role` | 删除角色。 | `raw.delete_role({"id": 401})` |
| `get_role` | 获取角色详细信息。 | `raw.get_role({"id": 401})` |
| `list_roles` | 分页列出角色。 | `raw.list_roles({"keyword": "", "common_condition": {"page": 1, "page_size": 20}})` |
| `list_roles_by_category_and_object` | 查询绑定到某对象的角色。 | `raw.list_roles_by_category_and_object({"category": "table", "id": "301"})` |
| `update_role_code_list` | 更新角色的全局权限码列表。 | `raw.update_role_code_list({"role_id": 401, "code_list": ["DT8", "DT9"]})` |
| `update_role_info` | 同时更新全局/对象级权限。 | `raw.update_role_info({...})` |
| `update_roles_by_object` | 批量为对象绑定角色。 | `raw.update_roles_by_object({"id": "301", "code": "DT8", "role_id_list": [401]})` |
| `update_role_status` | 启用或禁用角色。 | `raw.update_role_status({"id": 401, "action": "enable"})` |

## 权限（Privilege）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `list_objects_by_category` | 列出某权限类别下可绑定的对象。 | `raw.list_objects_by_category({"category": "table"})` |

## GenAI 接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_genai_pipeline` | 创建 GenAI 流水线，可附带文件上传。 | `raw.create_genai_pipeline({"steps": [{"node": "ingest"}]})` |
| `get_genai_job` | 查看任务状态及输出文件。 | `raw.get_genai_job("job-123")` |
| `download_genai_result` | 下载任务产出，返回 `FileStream`。 | `stream = raw.download_genai_result("file-xyz"); data = stream.read(); stream.close()` |

## NL2SQL 与知识库接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `run_nl2sql` | 将自然语言转换为 SQL 并执行。 | `raw.run_nl2sql({"operation": "run_sql", "statement": "select * from sales limit 10"})` |
| `create_knowledge` / `update_knowledge` | 新增/更新 NL2SQL 知识项。 | `raw.create_knowledge({...})` |
| `delete_knowledge` | 删除知识项。 | `raw.delete_knowledge({"id": 1})` |
| `get_knowledge` | 查看知识项详情。 | `raw.get_knowledge({"id": 1})` |

## 数据分析（Data Asking）接口

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `analyze_data_stream` | 执行数据分析并返回流式响应（SSE）。 | `stream = raw.analyze_data_stream({"question": "平均薪资是多少？", "config": {"data_category": "admin", "data_source": {"type": "all"}}}); event = stream.read_event(); stream.close()` |
| `cancel_analyze` | 取消正在进行的数据分析请求。 | `raw.cancel_analyze({"request_id": "request-123"})` |
| `list_knowledge` / `search_knowledge` | 分页或按条件列出知识项。 | `raw.list_knowledge({"page_number": 1, "page_size": 20})` |

## 健康检查与审计日志

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `health_check` | GET `/healthz`，返回服务健康状态。 | `raw.health_check()` |
| `list_user_logs` | 查询用户操作日志。 | `raw.list_user_logs({"common_condition": {"page": 1, "page_size": 20}})` |
| `list_role_logs` | 查询角色操作日志。 | `raw.list_role_logs({"common_condition": {"page": 1, "page_size": 20}})` |

## LLM Proxy API

LLM Proxy API 使用 `/llm-proxy` 前缀，响应格式为直接返回数据（无 envelope 包装）。

### 会话管理

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_llm_session` | 创建新会话。 | `raw.create_llm_session({"title": "我的会话", "source": "my-app", "user_id": "user123", "tags": ["alpha"]})` |
| `list_llm_sessions` | 列出会话（支持过滤和分页）。 | `raw.list_llm_sessions({"user_id": "user123", "source": "my-app", "page": 1, "page_size": 20})` |
| `get_llm_session` | 根据 ID 获取会话。 | `raw.get_llm_session(1)` |
| `update_llm_session` | 更新会话（支持部分更新）。 | `raw.update_llm_session(1, {"title": "更新标题", "tags": ["release"]})` |
| `delete_llm_session` | 删除会话。 | `raw.delete_llm_session(1)` |
| `list_llm_session_messages` | 列出会话中的消息。注意：不返回 content 字段，使用 `get_llm_chat_message` 获取完整内容。 | `raw.list_llm_session_messages(1, {"role": "user", "status": "success", "after": 5, "limit": 50})` |
| `get_llm_session_latest_completed_message` | 获取会话中最新已完成的消息 ID（仅成功状态）。 | `raw.get_llm_session_latest_completed_message(1)` |
| `get_llm_session_latest_message` | 获取会话中最新消息 ID（无论状态）。 | `raw.get_llm_session_latest_message(1)` |
| `modify_llm_session_message_response` | 修改会话中消息的 modified_response 字段。 | `raw.modify_llm_session_message_response(1, 10, "修改后的回复内容")` |
| `append_llm_session_message_modified_response` | 追加内容到会话中消息的 modified_response 字段。 | `raw.append_llm_session_message_modified_response(1, 10, "追加的内容")` |

### 聊天消息管理

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_llm_chat_message` | 创建聊天消息记录。 | `raw.create_llm_chat_message({"user_id": "user123", "source": "my-app", "role": "user", "content": "你好", "model": "gpt-4", "status": "success"})` |
| `get_llm_chat_message` | 根据 ID 获取消息。 | `raw.get_llm_chat_message(1)` |
| `update_llm_chat_message` | 更新消息。 | `raw.update_llm_chat_message(1, {"status": "success", "response": "回复内容", "modified_response": "修改后的回复"})` |
| `delete_llm_chat_message` | 删除消息。 | `raw.delete_llm_chat_message(1)` |
| `update_llm_chat_message_tags` | 替换消息标签（完全替换）。 | `raw.update_llm_chat_message_tags(1, {"tags": ["tag1", "tag2"]})` |
| `delete_llm_chat_message_tag` | 删除消息中的单个标签。 | `raw.delete_llm_chat_message_tag(1, "my-app", "tag1")` |

---

# SDKClient 高级封装

| 方法 | 描述 | 示例 |
| --- | --- | --- |
| `create_table_role` | 新建或复用仅包含表权限的角色，返回 `(role_id, created)`。 | `sdk.create_table_role("analytics_reader", "表级读权限", [TablePrivInfo(table_id=301, priv_codes=["DT8"])])` |
| `update_table_role` | 更新表权限/全局权限，可自动保留未指定字段。 | `sdk.update_table_role(role_id, "", [TablePrivInfo(table_id=301, priv_codes=["DT8","DT9"])], global_privs=None)` |
| `import_local_file_to_table` | 将已上传的本地文件导入目标表，自动拼好 MOI 所需参数（VolumeID、Meta 等）。 | `sdk.import_local_file_to_table({"new_table": False, "table_id": 301, "database_id": 201, "conn_file_ids": [conn_file_id], "existed_table": []})` |
| `import_local_file_to_volume` | 将本地非结构化文件上传到目标数据卷，支持元数据和去重配置。 | `sdk.import_local_file_to_volume("/path/to/file.docx", "vol-1", {"filename": "file.docx", "path": "file.docx"}, {"by": ["name", "md5"], "strategy": "skip"})` |
| `import_local_files_to_volume` | 将多个本地非结构化文件上传到目标数据卷，支持批量上传和自动生成元数据。 | `sdk.import_local_files_to_volume(["/path/to/file1.docx", "/path/to/file2.docx"], "vol-1", [{"filename": "file1.docx", "path": "file1.docx"}, {"filename": "file2.docx", "path": "file2.docx"}], {"by": ["name", "md5"], "strategy": "skip"})` |
| `run_sql` | 通过 NL2SQL RunSQL 执行 SQL 语句。 | `sdk.run_sql("select * from sales.orders limit 10")` |

这些高级方法复用了 Go SDK 中的业务逻辑，确保 Python 开发者可以以同样的方式完成角色管理与文件导入等场景。

