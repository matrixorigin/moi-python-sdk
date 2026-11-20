# MOI IAM 公开 API、前端与 SDK 合同

本文记录 Backend 对外 IAM API、Frontend 和 Product SDK 必须共同遵守的稳定语义。它不复制完整 JSON/protobuf schema；字段和生成类型以 Backend handler、`sdk/proto/product/iam.proto` 及生成器为准，资源/action 语义以 Core Registry 和[业务功能权限模型目录](08-business-permission-model-catalog.md)为准。

## 1. 边界与权威来源

- Product SDK 只包装 `/newmoi` Backend 产品 API，不直连 Core。
- Backend 负责账号认证、workspace/Explicit Role Candidate 解析、公开错误映射和 Core client 调用，不本地计算 allow。
- Frontend 只消费 Backend 返回的 Current Principal、Permission Schema、permission view 和 mutation result，不读取 Core proto 或拼接 allow。
- 生成的 Go/Python 类型、route manifest 和 API matrix 必须与 Backend route 同步；当前分支未发布的错误入口直接删除或修改全部调用点，不保留必然失败的 wrapper。

除 `POST /newmoi/user/info` bootstrap 外，当前公开 IAM 管理与资源 API 都以 `/newmoi/workspaces/{workspace_id}/iam` 为根路径。Frontend 内部 client 可以统一处理 `/newmoi` base prefix，但不能省略 workspace 和 `iam` path segment。

### 1.1 保存与重试的统一原则

事务方案遵循[存储合同 §4.1](04-storage-lifecycle-audit.md#41-事务与持久恢复边界)。同事务与跨事务操作都应由一个产品接口表达用户的一次业务动作，由后端 owner 完成内部提交；Frontend、Product SDK 和 CLI 不编排 MO、MOI 的提交或补偿步骤。

普通设置保存默认不要求调用方生成业务幂等键。角色编辑与独立 Data Privilege apply 可省略请求体 `request_id`，后端在需要持久化关联时生成编号；用户再次保存代表使用当前输入发起新操作。创建、删除等已明确要求请求标识的接口继续遵循各自合同，不能据此推断所有接口都接受空编号。响应头 `X-Request-ID`／trace 用于诊断，请求体 `request_id` 用于业务操作关联，expected version 用于防止过期写入；三者不能互相替代。

Frontend 在保存期间禁用提交并防止重复点击；调用方重复提交普通设置时，后端仍按正常保存处理，无须承诺“只执行一次”，也不额外读取旧值比较是否变化。按钮节流不替代后端鉴权、CAS 或跨事务冲突隔离。

owner 必须分别表达操作结果与失败原因，客户端按稳定 code 和结果控制交互，展示安全、本地化的 `msg`：

| 操作结果 | 调用方交互 |
| --- | --- |
| 已确认成功 | 更新界面并结束本次保存；不得把提交后的辅助记录失败误报成需要重新写入 |
| 校验拒绝、确认未写入或已完整回滚 | 保留草稿，允许修正；下一次用户点击提交当前输入 |
| Schema／版本冲突 | 刷新当前 Schema 和业务版本，保留草稿；由用户确认后再次保存，不静默采用新版本覆盖 |
| 无响应或结果未知 | 保留草稿并说明尚未确认，不能宣称“未保存”或“已回滚”；普通设置允许显式重新提交，是否可写仍由后端根据当前版本和未完成操作判断 |
| 整角色编辑已确认失败并停止 | 保留可编辑草稿和保存入口，核对当前设置后允许新保存；新请求使用当前输入，旧失败请求不能重新执行 |
| 已确认部分完成或停止且需人工处理 | 展示已知结果和后端提示；按既有业务入口核验或修复，不能把普通“重试”变成重复执行旧副作用 |

角色编辑不缓存原 payload 或让用户管理 Saga；失败终态不能永久阻塞新编辑。确认原执行已停止后释放占用；新保存只处理当前请求，旧操作由共享 Saga 入口在剩余预算内恢复。预算耗尽保留失败记录，交由 owner 管理员处理，不阻止新保存。未知结果后再次保存提交当前草稿，后端仍可因原操作尚在执行或终态未确认而返回冲突。创建等已有原请求确认合同的接口，继续使用原编号和原 payload 确认，不自动转换为新的创建。已确认成功或确认未生效之前，HTTP 超时、关闭抽屉、页面刷新和后续 `403` 都不能证明先前操作被撤销。

用户重试、内部有限重试、原请求结果确认是不同动作。Frontend/SDK 不自动重发写请求或轮询 Saga；内部重试只由业务 owner 使用原操作的剩余预算执行。只有业务确实允许关闭后继续执行时，才按已有合同提供重新定位结果的入口，不向所有保存接口添加任务、撤销、轮询或客户端幂等框架。

### 1.2 角色继承修改

添加、移除父角色只提交 `parent_role_id`、父子角色各自的 `expected_*_lifecycle_version` 和必填 `request_id`。不再提交 `expected_role_graph_version`。成功响应为父子角色 ID 和 `idempotent_replay`，不再返回变更后的全图版本；图版本仍属于读取接口的快照元数据，不用作继承写入前置条件。

重复编号不会重新执行 MO。成功返回历史成功，失败返回原失败，未确认返回 `409 ErrIAMInheritancePending`。MO 明确拒绝一般返回 `422 ErrIAMInheritanceFailed`；MO 明确报告环时保持 `409 ErrIAMInheritanceConflict` 与 `IAM_ERROR_CODE_INHERITANCE_CYCLE`。角色 lifecycle 或请求输入冲突仍返回 409，准入失败保持 403，初始记录无法写入返回 503。

Frontend、Go/Python SDK、CLI 与 MCP 展示 owner 提供的安全本地化消息，不暴露原始 SQL。继承写请求不自动重试；前端刷新当前关系，用户明确再次操作时创建新编号。不同角色图读取结果可来自不同时刻，不因图版本不同禁止继承修改。确认成功后刷新失败不得误报保存失败。无响应与响应损坏按客户端传输/合同错误提示，不推断业务失败。

## 2. Current Principal Bootstrap

`POST /newmoi/user/info` 是 App Shell 的当前用户与 IAM context bootstrap。它通过一次 Core projection 返回展示用户、可选 Role、Default Role、Explicit Role Candidate、唯一 Effective Role、Role context status、capability 和 snapshot version。

- `X-MOI-Role-ID` 在 Frontend 只能由 principal context store 统一注入，页面不得自行伪造。Go Product SDK 通过 `WithWorkspaceCurrentRoleID(workspaceID, roleID)` 、Python Product SDK 通过 `with_workspace_current_role_id(workspace_id, role_id)` 提供 workspace-scoped Explicit Role Candidate，`moi-cli` 复用该入口；这些入口只接受规范正十进制 `int64` Role ID。Product SDK 在 HTTP request modifier 之后大小写不敏感地清除 `X-Workspace-ID` 与 `X-MOI-Role-ID`，重新绑定请求 workspace，并且只从匹配的 typed mapping 注入候选 Role；没有 typed mapping 时同样清除通用扩展写入的 Role header。候选 Role 仍必须由 Backend/Core 校验 direct binding 与 lifecycle 后才能成为唯一 Effective Role。WebSocket 在 custom headers 之后执行相同的保留字段绑定，不经过 HTTP request modifier。
- `moi-cli` 只允许通过配置文件中的 workspace→Role mapping 选择 Role：`config set-role` 写入 mapping，`config unset-role` 删除 mapping，启动后的一个 CLI 进程使用不可变快照；不存在全局一次性 Role override。发现任意非法持久化 mapping 时，所有非 `config` 命令在发请求前 fail closed，错误必须列出 workspace、原因、修复命令并明确 `No request was sent.`；`config show/set-role/unset-role` 保持可用以完成修复。
- Explicit Role SDK 能力覆盖 Go/Python Product SDK 和使用人类 PAT 的 `moi-cli`；Python 的 workspace mapping、规范正十进制 int64 校验、冲突拒绝、HTTP/WebSocket 保留 header 最终绑定与 Go 一致。浏览器 CORS 尚未开放稳定入口。通用 custom-header/request-modifier 只支持非保留 header，不是 Role 选择合同。Core SDK 不承载这项产品 API 能力。
- Bootstrap 使用 `sdk/proto/product/workspace.proto` 中的精简投影：capability item 不返回 `action_id`、`resource_type`；Role option 不返回 `lifecycle_state`、`system_role`；`iam_context` 不返回 `schema_version`、`capability_version`、`request_id`、`trace_id`；`iam_capabilities` 不返回 `capability_version`。诊断标识统一读取 `iam_capabilities.request_id/trace_id`。`lifecycle_version`、`default_role_version` 和 `iam_snapshot_version` 继续用于上下文刷新与快照识别。独立的 `/iam/me/roles`、`/iam/me/capabilities` 仍返回完整元数据；内部 Core projection、版本一致性校验和授权计算不因响应精简而改变。
- Role context 非 `ready` 时清除旧 Role 的业务 capability 和相关数据，不发出依赖该 context 的受保护请求。可控拒绝显示当前工作区无权限，真实加载故障显示局部错误与适用的只读刷新入口；App Shell 的账号导航、切换工作区和退出保持可用。单项 capability 的可控异常在共同身份仍有效时仅影响该项，不能使整个 bootstrap 失败；分类由后端完成，Frontend 不自行将未知错误转换成空权限。
- workspace 级 capability 使用 `allowed`；对象写操作 capability 还必须保留 Core `RESOURCE_ACTION_SCOPE` 返回的 `all_resources` 和 `resource_ids`。Frontend 只有在 `allowed=true` 且 `all_resources=true` 或 canonical resource ID 精确命中时才显示对应对象操作，不能把“至少一个对象可操作”折叠成页面级 allow，也不能自行扩展资源 scope。
- 切换 Explicit Role Candidate 后先清空旧 context、capability 和依赖该 Role 的 query cache，再重新 bootstrap。
- `permissionCodes`、`objPermissions`、菜单可见性和本地角色名只用于展示或已退休，不是公开 allow contract。

### 2.1 按 ID 查询当前主体 Capability

`GET /newmoi/workspaces/{workspace_id}/iam/me/capabilities` 支持可重复的 `capability_id` query 参数，例如 `?capability_id=action.role.create&capability_id=navigation.roles`。省略参数时计算并返回现有完整清单；传入时从生成的 capability manifest 选择支持的请求项，仅对这些项执行原有授权计算，结果按 capability ID 排序。未登记的 ID（包括空值）原样返回在 `unsupported_capability_ids` 字符串数组中，不触发请求错误；有效项正常返回，HTTP 状态为 200。全部 ID 都不支持时 `items` 为空数组，仍返回不支持列表；省略筛选或全部支持时 `unsupported_capability_ids` 为空数组。两个列表均去重、按 ID 排序，不自动修剪或拆分参数。无法解析的 query 编码仍沿用 `400 INVALID_ARGUMENT`。

筛选沿用当前账号、workspace membership、Explicit Role Candidate、Effective Role 和 lifecycle 校验，以及授权快照一致性检查，包括全部 ID 都不支持的请求；鉴权失败或有效项计算失败仍返回既有错误。`effective_role_id`、`capability_version`、`request_id`、`trace_id` 和每项的 action、resource、reason、allow、scope 字段保持原合同；`capability_version` 仍标识完整 capability 定义，不随筛选集合改变。`allowed=false` 的请求项仍返回其原有拒绝原因，未请求项不出现在结果中。

Go Product SDK 使用 `CurrentPrincipalCapabilities(ctx, "action.role.create", "navigation.roles")`；Python 使用 `current_principal_capabilities("action.role.create", "navigation.roles")`；CLI 使用 `moi-cli iam current-principal-capabilities --capability-id action.role.create --capability-id navigation.roles`。三者省略 ID 时保持全量行为，原样传递 ID，由服务端验证。该筛选只绑定到独立 capabilities 接口，`/user/info`、App Shell bootstrap 和页面调用保持原行为。

## 3. Permission Schema 与 Role Permission View

`GET /newmoi/workspaces/{workspace_id}/iam/permissions/schema` 返回当前 Registry 的资源/action/operation schema 和 capability gates。普通 Role 的权限预览及权限编辑只能使用 `enabled=true` 且相应 capability 已验证的 scope/action；未知字段、未知 action 或 capability false 不能本地补全。`admin`/`superadmin` 的只读预览按第 3.3 节展示系统 Role 的全权限合同，不使用普通 Role 的可配置 scope 判断其权限范围。

Schema 是部署级元数据，不包含用户、Role 或工作区授权结果。Core 在创建 Schema service 时，根据不可变 Registry 和启动时确定的 capability 构建、验证并计算一次指纹；服务重建时重新生成，对调用方返回独立副本。Registry 无效或读取失败时 service 初始化失败，不发布部分快照；正常读取只深拷贝快照中的嵌套 slice/map，不重新扫描 Registry 或计算指纹。DTO 转换或调用方修改返回值不能污染服务快照。Backend 每次真实请求仍走成员准入并透传到 Core，不缓存含 request/trace ID 的响应。

Frontend 在同一应用 QueryClient 中跨工作区、Role 共用 Schema，30 分钟内复用，过期后下次查询重新加载；没有定时刷新。未使用的缓存 30 分钟后回收，页面重载或应用清空 QueryClient 后重新获取。切换工作区只保留这一全局元数据查询，其余权限及资源缓存仍清除。缓存不持久化、不在不同应用实例或后端环境间共享，也不参与服务端 allow/deny。

共享入口 `permissionSchemaQuery` 使用不含 workspace/Role 的 `['iam', 'schema']` key；真实请求仍使用当前调用者的 workspace 路径和认证上下文。同一 QueryClient 的并发查询合并为一次请求，`staleTime` 与 `gcTime` 都为 30 分钟。缓存只保存成功的原始 wire response，各 observer 在 `select` 中校验自己的读写合同，包括缓存命中时；只读页面可接受的响应不必然满足编辑器保存所需的完整字段。预览转换只修改 observer 的独立投影，不能改写共享响应，HTTP 错误 envelope 也不能作为成功数据缓存。实现入口：[共享 Schema query](../../moi-frontend/modules/moi-permission/src/permission-schema-query.ts)、[Core Schema service](../../moi-core/catalog/pkg/iamcore/permission_schema.go)。

`GET /newmoi/workspaces/{workspace_id}/iam/roles` 返回 canonical RoleSummary 列表。系统 Role 的 `role_name` 与稳定的 `system_role_name` 使用同一个英文名称（例如 `admin`），切换界面语言时都不变化；只有 `description` 按当前 locale 投影。Frontend/SDK 使用 `system_role_name` 判断系统角色语义，不能用描述文案或本地翻译反向推断授权事实。

`GET /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/permission-view` 返回目标 Role 的 direct policy view、版本、Role kind 和可编辑能力。通过此接口读取继承、MatrixOne data privilege、Ownership 或其它来源时，只有 capability 明确表示 included 才可展示为完整事实；展示层不能把未返回的数据推断为空集合。系统 Role 的只读预览不依赖此接口。 响应 `lifecycle_state` 明确为 `active` 或 `disabled`。具备 workspace `role.read` 的调用者可查看停用目标角色的已保存 direct policy；停用目标返回 `policy_mutation_allowed=false`，不改变实际鉴权的 active 要求。

Permission Schema 的 `schema_version` 是当前 Registry 快照指纹；Permission View 的同名字段记录该 Policy 写入请求携带的指纹，仅用于缓存和诊断。两者不同不代表历史 Policy 无效，Frontend 不得仅据此禁止查看或编辑。服务端先验证持久化 document 与 Grant Index 的完整性、归属和版本，再从视图中排除当前 Registry 未注册的 action 及已不支持的 scope；有效条目保留原范围、审计身份和策略版本。Frontend 使用 Schema 编辑有效条目，读取或取消编辑不写回历史策略。

创建角色、保存策略和对象授权/撤权时，服务端使用当前 Registry、现有别名映射和规范化逻辑校验操作意图；意图仍有效时正常完成，不因请求或持久化策略的 Schema 指纹与当前值不同而拒绝。兼容处理保持资源、scope、condition 和授权能力，不把对象范围扩大为全局，也不顺带丢弃无关授权。请求携带的指纹保留在文档和原操作事实中；仅服务端指纹变化不改写同一请求的幂等身份。

并发覆盖保护继续使用 lifecycle、`policy_version` 和 data-privilege 各自的 CAS；权限校验、数据完整性和同 request ID 不同操作内容的冲突检查继续保留。确实改变权限语义的升级由内部发布流程处理受影响数据，不能把系统 Schema 演进转化为要求用户重新保存、反复重试或找管理员修复。真实并发修改时，编辑器保留草稿并重新读取角色状态，不能绕过 CAS 覆盖他人的修改。

### 3.1 Role 创建

数据库权限树的目录导航复用 `GET /newmoi/workspaces/{workspace_id}/iam/permissions/resources`，固定传入 `resource_type=catalog`、`purpose=database_tree_catalogs`。编辑传入 `action_id=role.update`，创建传入 `action_id=role.create`；两个入口分别由 Core 校验当前 Verified Effective Role 的对应 workspace action，不能通过请求参数替代授权。该 purpose 的其它资源/action 组合，以及 BatchDescribe 请求均返回 `400 ErrIAMResourcePickerInvalid`。目录只返回身份和展示元数据，按 `limit`、`cursor` 分页，不查询后代、不授予 Catalog/Database 查看或使用权限；目录项固定 `selectable=false`、`disabled_reason=CATALOG_NAVIGATION_ONLY`。展开后的数据库列表仍使用原数据库 action 的 IAM picker 和 `parent_id` 过滤，目录 ID 不作为数据库权限提交。

创建入口及创建事务中的初始权限校验要求 workspace `role.create`，不叠加其它角色管理权限。该授权覆盖本次新 Role 的初始 Application Policy 和 Data Privilege；恢复执行仍以原冻结 Effective Role 重新校验 `role.create`，该创建事务不能修改其它已有 Role；具有 `role.create` 的 Role 仍可通过独立授权接口配置已有 Role 的权限。已有 Role 的统一编辑要求 `role.update`。

Role 创建使用 `POST /newmoi/workspaces/{workspace_id}/iam/roles`。请求一次性携带 `name`、可选 `description`、`schema_version`、`request_id`、初始 Application Policy `statements` 和初始 `data_privilege_mutations`；过滤历史遗留的 `model_runtime.invoke` 后仍须至少存在一项 Application Policy 或 Data Privilege。否则 Core 返回 `IAM_ERROR_CODE_ROLE_PERMISSION_REQUIRED`，Backend 映射为 `422 ErrIAMRolePermissionRequired`，Frontend 提示用户选择至少一项有效权限。Frontend 保存时只调用该写接口，不再对新 Role 追加调用 permission view、policy validate/apply 或 data-privilege apply。

创建请求只兼容已确认存在于历史 Role 数据中的 `model_runtime.invoke`：它以 `resource_type=workspace` 或旧 `resource_type=model_runtime` 出现时被忽略，初始策略只保存其余 canonical statement。其他未知 action、resource/action 不匹配、非法 scope、condition 或 grant-action 结构仍然失败，Registry unavailable/invalid 也保持 fail closed。

它是一个产品事务：只有本地 Role、完整初始 Application Policy（含系统必需 baseline）、MatrixOne Role/GRANT、由策略派生的 account privilege 与初始 Data Privilege 全部完成并持久化为 `ready` 后才返回成功；任一步失败都返回非 2xx，且不返回 `role_id`。

`moi` 在单个租户事务中准备本地 Role 和初始 Application Policy，MatrixOne Role/DCL 在事务外执行。失败时先确认 MatrixOne Role 及其 DCL 已删除，再在单个租户事务中删除本地暂存的 Role、Policy、Grant Index 和 Data Privilege 操作事实。创建使用现有租户操作回执承接重放，不写入 system Saga；确认补偿后，`.empty-policy` 回执的 `error_code` 保存安全的失败原因。`pending/failed` 仅是内部执行事实，不属于公开产品状态；Frontend 和 Product SDK 不提供 provisioning 查询、列表或人工重试入口。

`ready` 是唯一产品提交点。若最终提交的确认丢失，必须读取持久化事实确认结果；已为 `ready` 时仍返回成功，读取失败时返回结果未知，不能补偿可能已提交的 Role。

角色名称重复由 `moi` IAM owner 分类，HTTP 层返回 `409 ErrIAMRoleNameExists`；调用方保留草稿，允许用户修改名称后使用新 `request_id` 提交。成功删除的普通角色释放名称，随后创建或编辑可使用该名称；重建使用新 Role ID，不继承旧角色的权限、绑定或 Ownership。尚未删除、disabled 或未完成创建/回滚的同名角色继续占用名称。删除完成后硬删除角色主表，原名称和旧身份保留在独立回执与审计中；收尾与历史记录清理见[生命周期合同 §4.2](04-storage-lifecycle-audit.md#42-role-删除)。

角色创建和编辑共用下列后端结果分类；参数、授权、Schema/CAS 冲突和进入持久化写入前的依赖不可用继续保留原有分类。明确的角色写入结果优先于其错误链中的超时、审计或依赖错误。下表的原请求确认动作适用于角色创建；角色编辑的重新提交遵循第 3.2 节，不要求前端保存业务请求编号。

| HTTP / public code | 已确认事实 | 调用方动作 |
| --- | --- | --- |
| `409 ErrIAMRoleWriteRolledBack` | 创建的临时 Role 已删除，或本地编辑事务已确认整体回滚 | 保留草稿，允许修改；用户明确再次提交时生成新 `request_id` |
| `500 ErrIAMRoleWriteFailed` | 操作已经停止，不能宣称原有设置已恢复 | 创建保留并锁定原请求表单；编辑刷新当前设置和版本、保留可编辑草稿，允许按第 3.2 节重新保存 |
| `409 ErrIAMRoleWriteResultUnknown` | 已存在的操作仍可能在执行、曾被中断，或其结果尚未确认 | 保留原 `request_id` 与原 payload；只允许用户手动确认该请求结果，同请求调用只读结果，不启动或恢复操作 |

角色保存失败的结果和原因分别传递：公开 `code` 始终按上表决定交互；只有确认原有状态已恢复的 `ErrIAMRoleWriteRolledBack` 才可在 `data.cause_code` 携带具体数据权限原因。`moi` IAM owner 保留类型化原因，HTTP 层映射为下表中的公开分类并从统一 i18n catalog 提供对应中英文 `msg`，同时说明原有设置已保留。`ErrIAMRoleWriteFailed` 和 `ErrIAMRoleWriteResultUnknown` 不携带可修正原因，也不会被底层超时、无权限或表达式错误改写成已回滚；它们是否允许新保存仍按创建和编辑各自的合同处理。原始诊断只保留在受控日志；相同请求重放保留原结果与原因。

| `data.cause_code` | 具体原因 |
| --- | --- |
| `ErrIAMDataPrivilegeInvalid` | 行过滤表达式或列配置无效 |
| `ErrIAMDataPrivilegeResourceChanged` | 所选资源已变化 |
| `ErrIAMDataPrivilegeDenied` | 已无法修改这些数据权限 |
| `ErrIAMDataPrivilegeUnavailable` | 数据权限暂时无法保存 |
| `ErrIAMDataPrivilegeTimeout` | 数据权限保存超时，但原有设置已确认保留 |
| `ErrIAMDataPrivilegeDrifted` | 数据权限写入校验未通过，原有设置已恢复 |
| `ErrIAMDataPrivilegeApplyFailed` | 数据权限保存失败 |

角色创建前端使用抽屉并保留草稿：本地必填、空白、长度等错误由 Form 在字段附近提示并定位；首次名称重复由后端判定后就地展示在名称字段。已确认恢复原状时允许编辑并重新提交；结果未确认时锁定原请求，名称和备注可只读复制，提供手动“确认结果”或原请求重交；后续前置拒绝不能解锁请求。已停止时保留内容供核对，只提供关闭入口。所有状态展示后端安全提示，前端不自动重试或轮询。

确认角色编辑已恢复原状后，前端刷新当前角色和权限版本，保留用户填写的元数据、应用权限和行列权限草稿；使用最新版本发起下一次显式提交。刷新失败时保留草稿并提供刷新入口，不自动重复写入。


角色编辑只有在纯本地事务已确认回滚时才使用 `ErrIAMRoleWriteRolledBack`。提交响应丢失且未读到成功回执时返回 `ErrIAMRoleWriteResultUnknown`；跨 MO 边界的操作失败不恢复旧权限，按第 3.2 节确认停止后允许新保存。上述创建表单的原请求锁定规则不适用于角色编辑。

角色创建 Frontend 直接显示 Backend 返回的安全、本地化 `msg`，只按稳定 `code` 控制交互。无响应、响应合同损坏或其它 `5xx` 同样保留原 `request_id` 与原 payload，但用户点击“重新提交”时，请求若此前尚未到达 owner，可能首次启动操作；因此不能把这类未知结果解释为只读查询。首次提交收到其它明确的 `4xx` 时允许修正后以新 ID 提交；`ErrIAMRoleWriteResultUnknown` 是明确例外。已有未确认请求后，手动确认或原请求重交遇到权限 `403` 或其它前置 `4xx`，只能说明当前调用被拒绝，不能证明原操作已结束；Frontend 继续保留原 ID、原 payload 与原按钮动作，展示新的 Backend 提示。只有完整成功响应、`ErrIAMRoleWriteRolledBack` 或 `ErrIAMRoleWriteFailed` 明确原操作结果后，才能退出未确认状态。同请求查询/重放不刷新服务器重试预算；Frontend 不自动重试或轮询。不同 payload 复用同一 ID 返回幂等冲突。

### 3.2 Role 编辑

Role 编辑使用 `PATCH /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}`，沿用 Role 写入响应和公开错误模型；同事务编辑直接提交，跨 MatrixOne 副作用时由唯一持久化 Saga 向前收尾。请求一次性携带完整 `name`、`description`、`schema_version`、`statements`、`data_privilege_mutations`、`expected_lifecycle_version`、`expected_policy_version` 和 `expected_data_privilege_version`。`request_id` 可省略，由后端为本次保存生成并在成功响应中返回。成功响应同时返回 `session_invalidation_status`；`ready` 表示产品事务已提交，该字段单独说明权限对既有 MatrixOne session 的可见性。Backend 要求调用者具备 `role.update`；Frontend 的统一编辑器保存时只发这一个 PATCH，不串行调用元数据、Application Policy 或 Data Privilege mutation。CAS 冲突刷新 server baseline 时保留用户尚未提交的元数据、Policy 和 Data Privilege 草稿，由用户确认后再次提交当前草稿。保存期间禁用提交按钮，失败后保留输入；前端不生成业务请求编号、不缓存或重放旧请求。

名称、备注和 Application Policy 在一个本地事务内保存。需要执行本次数据权限 DCL 或同步本次策略变更派生的 account `CREATE DATABASE` 时，使用一个聚合 Saga；先校验三个版本并占用 Role，再执行当前请求的 mutation、确认 MO，最后原子提交全部 MOI 事实、审计和成功回执。编辑期间的 `pending` 只作为内部事实，不进入 Role 列表。执行仍在进行或终态未确认时保留并发保护；确认失败终态后释放占用，保留失败记录并允许新保存，不恢复编辑前权限。详见[存储合同 §4.3](04-storage-lifecycle-audit.md#43-role-创建与编辑)。

后端生成的 `request_id` 关联本次保存，每次省略编号的调用都是新请求；三个 expected version 继续防止过期草稿覆盖新设置。显式提供同一 `request_id` 和 payload 时，已有成功回执返回原结果，即使之后角色又被编辑；改变 payload 返回幂等冲突。跨事务请求尚未完成时，同请求调用返回结果未知，不恢复旧操作；恢复由共享 Saga 入口在原执行锁和剩余预算内读回 MO、补做未完成的 MOI 提交。活跃执行者不可抢占，已失败操作不重新执行。业务已提交但 Saga 未完成时，普通调用返回成功回执，共享入口只补 Saga 记账。普通新请求的旧版本仍稳定返回 `409`。

角色编辑遇到无响应、损坏响应、临时错误或 `ErrIAMRoleWriteResultUnknown` 时保留可编辑草稿，下一次点击提交当前输入；这不承诺原操作已经结束。收到 `ErrIAMRoleWriteFailed` 时展示已停止的事实，刷新 Schema、角色及权限版本，保留可编辑草稿和保存入口；明确版本冲突或已恢复原状时同样刷新，刷新失败不得继续发送旧版本。每次新保存都由后端检查当前授权、执行状态和 CAS；旧失败请求不会重新执行，客户端不自动修复或重放原操作。

旧编辑因进程中断而未完成时，由共享恢复入口接管过期租约并只读回收尾，普通保存不接管。执行尚未停止时新保存返回冲突；确认失败后，只释放旧执行占用并允许按当前版本保存，不合并旧 intent 或替旧操作修复权限。恢复已推进版本时，新草稿仍按原预期版本返回 CAS 冲突，刷新后再次保存。原请求的确定性失败分类保持一致；旧操作的失败记录留待 owner 管理员处理。

独立的 Application Policy 与 Data Privilege validate/apply API 继续作为其它产品流程的 owner API；Role 统一编辑器不再调用它们，因此不存在 `partialSaveFailed` 产品状态。

### 3.3 Role 权限预览

`admin`/`superadmin` 的全权限语义来自[产品与授权模型](01-product-authorization-model.md#3-role-模型)。Frontend 以待查看 RoleSummary 的稳定 `system_role_name` 精确识别这两个角色；不能用 `role_name`、本地化名称、角色 ID、`system_role` 或 `protected_role` 单独推断全权限，也不能把当前查看者的系统 Role 身份套用到普通目标 Role。

| 目标 Role | 预览读取 | 展示范围 |
| --- | --- | --- |
| `system_role_name=admin/superadmin` | 只读取 Permission Schema，可复用同一应用 QueryClient 的有效 Schema 缓存 | Schema 中全部可展示的 Application Policy 与 MatrixOne 数据权限，scope 统一为 `all` |
| 普通 Role | Permission Schema、Role Permission View，以及能力就绪时的 Data Privilege | 按实际返回的授权与 Schema 展示；未返回或读取失败不能推断为全权限或空权限 |

普通目标 Role 停用时，预览继续展示返回的已保存权限，并根据 permission view 的 `lifecycle_state` 显示“已停用”提示。该页面只读，不提供编辑入口；列表缓存中的旧 active 状态不能覆盖权限视图返回的 disabled。缺失或未知状态视为响应合同不完整，不能推断为 active。

权限项继续由 Core Schema 提供，Frontend 只负责编码、分组与名称映射，不维护另一份 action 清单。沿用现有预览展示规则：覆盖 `application_policy` 和 `matrixone_adapter` 的普通 action，`grant_action=true` 的委派定义不重复显示为独立权限项。新增 Schema action 必须自动进入系统 Role 预览；普通 Role 的 `scope_options`、Data Privilege 编辑能力和配套 grant action 是否可用，不限制系统 Role 的只读全权限展示。

系统 Role 预览不调用 `permission-view`、`data-privileges`、资源列表或单表行列详情，也不按对象逐项判权。旧权限明细缓存中的 error、损坏响应或进行中的请求均不参与其加载状态和展示结果；重试只刷新 Schema。Schema 自身仍须通过响应和结构校验：加载中显示 loading，读取失败显示错误，可恢复错误只重试 Schema，权限拒绝保持拒绝态。该路径不提供编辑入口，也不写入权限。

切换目标 Role 时重新按目标的稳定身份选择读取路径。返回普通 Role 后必须恢复实际授权读取与原有失败语义，不能沿用先前系统 Role 的 `all` 展示。这项优化只用于角色权限说明，不替代 Backend/Core 的请求鉴权、系统 Role 写保护或 MatrixOne 的运行期 DCL 校验。

## 4. Role Binding 与 Default Role

用户 Role binding 使用：

- `GET /newmoi/workspaces/{workspace_id}/iam/users/{user_id}/role-bindings`；
- `PUT /newmoi/workspaces/{workspace_id}/iam/users/{user_id}/role-bindings`。

mutation 显式携带 assigned Role 集合、binding/default-role CAS version 和 request ID。存在 Default Role 时必须显式提供 `default_role_id`，且它属于 assigned set；清理 Default Role 时必须显式提供 `clear_default_role=true`。Backend 和 Core 都拒绝两者均未提供的模糊请求，不按 assigned Role 数组第一项推断。

绑定变更使用[存储合同第 4.5 节](04-storage-lifecycle-audit.md#45-用户角色绑定)的标准 Saga。相同 request ID 与 payload 重放原操作；成功回执返回原绑定版本和结果，即使后续请求已经修改当前绑定。进行中或已失败的旧请求不创建第二次执行、不重开重试预算；用户主动重新操作使用新 request ID 和当前 CAS 版本。

`POST /newmoi/user/list` 为尚未清理完成的当前删除记录返回 `status=deletion_incomplete` 与可选 `deletion`：`state`（`pending` 或 `failed`）、`phase`、稳定 `code`、安全本地化 `message`、`request_id`、`trace_id` 和 RFC 3339 `updated_at`。普通成员不返回 `deletion`；系统已收尾且仅 tenant 孤儿清理待处理的 deleted 记录也不返回，不将运维清理任务暴露为用户的继续删除操作。Go/Python Product SDK 保留同一份公开字段。

Frontend 在同一用户列表中保留“删除未完成”记录，有删除权限时提供“继续删除”，向原删除接口提交 `deletion.request_id` 接续同一操作；编辑、角色修改与启停保持禁用。失败仅展示 Backend 的安全本地化消息，技术错误保留在日志和受控诊断中。`pending` 表示尚未确认完成，重启恢复只接续未结束操作；`failed` 等待显式点击，不进行周期性失败重试。结果未知或传输异常时保留原请求编号，不另建删除请求。关闭弹窗或刷新页面不会丢失记录。System membership 在删除收尾提交前保持原 `active`/`disabled` 状态；删除依次执行 MO 账号清理、tenant 角色绑定和默认角色等清理、System 删除收尾。tenant 清理失败仍尝试 System 删除，并保留内部失败回执；System 收尾成功后立即拒绝准入，成员删除接口返回成功，该行从列表消失，孤儿数据留给运维处理；失败则保留原成员关系并允许显式继续，不恢复已经删除的 MO 账号或 tenant 绑定。成功移除后的同请求重放不重试孤儿清理。

继续删除使用当前请求的 principal 与 Verified Effective Role 重新鉴权，可以由另一位有权限的管理员接手，或由原管理员切换到另一个有权限的 Role 执行。原请求的目标、版本和审计身份保持不变；无权限的当前调用不能触发重试，也不能读取原操作成功结果。启停重放与重启恢复的原身份规则不变。

Issue #15015 的成员 Role 更新已完成 breaking clean-break：Backend 只公开 canonical workspace IAM Role Binding API，Go/Python Product SDK 与 CLI 均使用 typed binding request/result 和显式 CAS 字段。typed GET 保留 Core 的 canonical `binding-v0` 或无前导零的 `binding-v[1-9][0-9]*` 诊断值；`binding-v01` 等非 canonical 值必须被拒绝。Go `IAMBindingVersionNumber`、Python `iam_binding_version_number` 与 CLI 的 `--use-current-versions` 负责将其校验后带入 PUT，格式异常明确返回 `ErrIAMBindingVersionInvalid`。旧成员角色兼容 surface、DTO、route mapping、API matrix 与测试 fixture 已移除；后续 M8 仅跟踪其他 legacy 物理资产和真实环境验收。

### 4.1 工作区成员展示

成员列表的 canonical membership 枚举与 tenant 展示事实批量读取遵循[存储合同第 1.4 节](04-storage-lifecycle-audit.md#14-工作区成员展示事实批量读取)。Backend 保持现有展示补充、过滤与分页语义，不能用资料缺失推断成员不存在或角色不可用；列表返回的 binding/default-role version 继续用于独立 mutation 的 CAS。

`GET /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/members` 继续要求 `role.read`，按 canonical `user_id` 游标分页返回直接绑定用户。每项包含 `user_id`、`display_name`、`email`、`default_role`、`default_role_version` 与 `binding_created_at`，同步 Product SDK 与 MCP 输出合同。姓名和邮箱由身份目录按当前页用户批量补充，不改变绑定事实、排序或分页；已确认缺少资料时保留该用户及空展示字段，未绑定邮箱不影响成员展示，目录读取失败返回既有依赖不可用错误，不能当作空成员列表。角色删除弹窗第一行显示用户名称，第二行显示 canonical `user_id`，区分可能重名的显示名；名称缺失时只显示 ID。弹窗不显示邮箱或默认角色标记，也不将邮箱作为名称回退。绑定用户均阻止删除，管理角色表单继续校验至少一个角色与默认角色替换。

角色删除弹窗的绑定用户行提供“管理用户角色”，复用成员角色与 Default Role 配置表单，以 canonical `user_id` 定位用户。入口只在 IAM context ready 且具备 `navigation.users`、`navigation.roles` 和 `action.workspace_member.role_binding.mutate` 时开放；缺少权限时说明需联系有权限的管理员。配置表单与删除确认分步展示，保留待删除角色的转移选择；返回时重新读取删除影响和绑定用户，不在前端假定绑定已经解除，也不自动发起删除。移除当前默认角色后须明确重选，且至少保留一个角色，继续使用现有 binding/default-role CAS 与后端鉴权。

## 5. Application Policy 与对象授权

Role policy 使用：

- `POST /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/application-policy:validate`；
- `PUT /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/application-policy`。

请求显式携带 schema version、expected policy version、expected Role lifecycle version、request ID 和 statements。validate 只做 canonical 校验与编译，不写 policy；apply 使用 CAS 和幂等写入 policy/Grant Index。一次请求只修改 path 中的一个目标 Role，不存在 `policy_version_by_role` 批量原子合同。grant-action statement 的 `grant_resource_id` 明确指定转授目标，Role/Object permission view 原样返回；精确 statement 只能覆盖同一精确对象，不能扩大为 all 或另一对象。MatrixOne data action 只能作为其 Registry 登记的 grant action 的目标，不能写成普通 Application Policy allow。

这两个接口只接受普通 Role 作为可写策略目标。合法策略请求通过 workspace 身份与 Effective Role 校验后，受保护的 `admin`/`superadmin` 目标在策略变更证明之前返回 `409 ErrIAMPolicyConflict`，空策略和 validate 请求同样拒绝；不写入系统 Role 的策略、版本、DCL 投影或成功回执。操作普通目标 Role 时，当前 Verified Effective Role 必须为 `admin` 或 `superadmin`，或具备 workspace `role.create` 或 `role.update`。缺少这类管理权限时，validate、apply 和同请求重放均返回 `403 ErrIAMPolicyDenied`。对象 Ownership 用于下述单对象授权。

编辑已有 Role 时，Frontend 和 Core 都会从输入及历史策略中删除已确认废弃的 `model_runtime.invoke`；apply 使用过滤后的 canonical policy 重建 Grant Index，因此该历史权限不会阻断保存，并会随下一次成功编辑自然清理。历史策略还按当前 Registry 排除未注册 action 和不支持的旧 scope。成功保存以当前合法配置完整替换旧 document 与 Grant Index，失败恢复原始历史快照。新输入中的未知 action、resource/action 不匹配或结构错误仍由当前 Registry 严格拒绝，Registry 故障也保持 fail closed。

对象授权使用：

- `GET /newmoi/workspaces/{workspace_id}/iam/permissions/objects/{resource_type}/{resource_id}/permission-view`；
- `POST /newmoi/workspaces/{workspace_id}/iam/permissions/objects/{resource_type}/{resource_id}/roles/{role_id}/grants:validate`；
- `PUT /newmoi/workspaces/{workspace_id}/iam/permissions/objects/{resource_type}/{resource_id}/roles/{role_id}/grants`。

permission view 展示 canonical owner、direct specific grants、all-scope grants 和 capability；owner 与每条 grant 的 `role_lifecycle_state` 明确返回 `active` 或 `disabled`，停用来源的记录仍可查看。该状态是管理元数据，不是运行期 allow 证明。缺少某个 included capability 不能推断该来源为空。grant mutation 每次只针对 path 中一个 Role，携带 expected policy/Role lifecycle version；validate 不写入，apply 复用 Application Policy CAS，不写入 retired object ACL。

对象授权/撤权是局部修改，不把权限视图过滤后的结果当作完整替换策略。服务端转换已确认等价的别名，保留本次操作以外的历史条目及原范围；当前 Registry 不认识或暂不支持的条目仍不参与运行期放行，其语义升级由内部发布流程处理。已明确批准移除的废弃权限按既有清理规则删除。

来源角色的批量校验和请求内图版本复用遵循[存储合同第 1.5 节](04-storage-lifecycle-audit.md#15-对象权限来源角色批量读取)。该优化只减少 view 的事实读取，不扩大 inherited/system/MatrixOne 等 included capability，也不把页面结果变成 grant mutation 的授权依据。

独立对象 Owner 管理转移使用 `PUT /newmoi/workspaces/{workspace_id}/iam/permissions/objects/{resource_type}/{resource_id}/owner`。当前入口面向角色管理流程，生成边界要求 workspace `role.update`，读取表单沿用 permission view 的 `role.read`；未在此入口新增普通 Owner 身份的准入分支，也不恢复已退休的独立 transfer action。请求为 `target_role_id`、正整数 `expected_ownership_version` 和 `request_id`。服务端从当前工作区的 canonical Ownership exact key 解析当前归属，在同一事务内锁定相关 Role、验证接收角色 active/ready、执行 active Ownership CAS 并保存审计回执；不删除原角色，不复制 MatrixOne DCL。响应包含对象身份、`previous_owner_role_id`、`owner_role_id`、新 `ownership_version`、`request_id` 和 `idempotent_replay`。同请求同载荷重放返回原回执，版本或载荷冲突返回 `409 ErrIAMObjectGrantConflict`；无效请求、无权限、不存在和依赖不可用复用现有对象权限错误 envelope。对象页通过现有共享入口打开该 Owner 表单。

## 6. Ownership Impact 与 Role 删除

`GET /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/ownership-impact` 是 owner provenance 与清理观测接口，返回 active direct Ownership 总数、按类型统计、有限样本以及 ownership/Role graph/lifecycle version。它不是 Role 删除前置 gate，也不能把业务对象或 Role 置为不可用。

该只读接口使用生命周期管理的目标 Role 读取合同，允许查询 active 和 disabled Role（包括生命周期恢复允许读取的 disabled/failed 状态）；deleted、非法版本和不满足该合同的 provisioning 状态仍拒绝。查询范围不改变调用者的 Effective Role 校验，也不放宽 Application Policy 等写入操作对目标 Role 的 active 要求。

旧 `ownership-impact` 的有限样本及 `transfer_supported=false` 只描述该观测接口，不承载删除转移。删除弹窗从不携带 `include_ownership` 的 `GET .../roles/{role_id}/delete-impact` 读取用户、对象总数和阻断原因，再按每页 10 条独立读取对象和绑定用户。标题展示该次检查的总量；翻页不重新执行删除影响检查，外部并发变更的总量在显式刷新或本界面修改完成后更新。删除影响响应新增 `transfer_blocked`，表示提供转移方案后仍存在的业务阻断（包括不单独公开计数的阻断），不代表转移授权。

独立的 `GET .../roles/{role_id}/delete-ownerships?cursor=...&limit=10` 按资源键进行数据库分页，只返回当前页 `items`、`ownership_version` 与 `next_cursor`，不统计总量或其它删除影响。每项返回 canonical 类型、ID、可用的业务名称和 Ownership 版本；名称不参与授权。普通读取需要 `role.delete`；携带 `transfer_requested=true` 时，生成边界同时校验 `role.update`。每次独立 Owner 转移由 Backend 重新校验 `role.update`，最终普通删除重新校验 `role.delete`，不采用页面保存的总量或版本作为授权。

列表按当前数据查询，不要求翻页期间集合保持不变。游标绑定工作区、角色和最后读取的资源键；首屏计算一次完整集合 `ownership_version`，后续页沿用它以保持已有列表合同，不再读取完整集合或因集合变化立即拒绝翻页。翻页替换当前页，列表内部限高滚动，翻页按钮位于滚动区域之外。游标耗尽表示末页，不能用累计项数等于首屏数量作为完成条件；末页被清空时返回上一页。显式刷新保留当前页并重新读取，首屏完整集合指纹仍随总对象数增长，分页只限制响应和渲染规模，不能据此宣称首屏查询恒定开销。读取失败不能当作没有对象。

旧 `delete-impact?include_ownership=true` 组合合同保留，继续支持 `ownership_cursor`、`ownership_limit`；嵌套列表的 `owned_count` 复用影响检查的 `active_ownership_count`，不再重复计数。


有对象时，DELETE 必须携带 `ownership_transfer.expected_ownership_version` 以及一个批量 `target_role_id`，或完整逐项 `targets`；每项包含 `resource_type`、`resource_id`、`target_role_id`。转给当前操作者表示接收者为当前 Verified Effective Role，而非用户 ID、默认角色或角色并集。转移删除同时要求工作区 `role.delete` 与 `role.update`；无转移的普通删除只要求 `role.delete`。`transfer_requested=true` 可用于删除影响预检的同等权限校验。

弹窗提供“全部转移给我”“全部转移给指定角色”“逐个手动转移”三种选项。前两项使用统一的接收角色，按每页 10 条读取并逐对象调用独立 Owner 转移接口，每次调用独立提交。弹窗显示遮罩和已确认的进度，期间禁止重复提交；中途异常停止后续转移，已成功部分不回退，角色保留。明确拒绝后须显式刷新并确认剩余对象；结果未知时锁定接收角色并按原请求 ID 与参数显式确认当前对象，然后继续该页和后续页。所有分页完成后单独发起不含 `ownership_transfer` 的 DELETE，不再要求用户返回再次点击删除。原 DELETE 携带完整转移方案的原子合同保留；第三项在当前页每个对象行提供“前往转移”，直接打开该对象的独立 Owner 表单；“去手动处理”打开当前页首个对象。单对象“转移并返回”确认后立即执行独立转移，成功则刷新并自动返回删除清单；刷新失败明确区分转移已成功，只重试读取，不重复写入。原角色保留，所有绑定与对象处理完后仍需另行确认删除。此路径无需先加载全部对象，也不在删除清单中执行转移删除。没有转移请求且仍有 Ownership 时，删除预检的 `blocked=true`；显式转移预检只解除 Ownership 阻断，系统角色、绑定、默认角色及未完成操作仍阻止删除。继承关系不阻止删除；删除预检和最终删除校验不再统计继承数量，公开响应删除 `parent_inheritance_count`、`child_inheritance_count`，Frontend 与 Product SDK 同步使用不含这两个字段的合同。Frontend 不展示继承计数或继承提示，也不额外请求 Role graph。删除后相关角色失去经该角色继承的权限。用户确认删除时由 Backend 清理目标参与的全部继承边，调用方无需先解除关系；其它角色已创建的对象及其 Ownership 保留。转移成功后对象及其接收角色 Ownership 保留，原角色的 MatrixOne 数据权限不复制给接收角色。

缺少转移方案、集合版本变化或 Ownership 状态异常返回 `409 ErrIAMRoleDeleteOwnershipConflict`；接收角色不存在、不可用或与源角色相同返回 `400 ErrIAMRoleDeleteTransferTargetInvalid`。前端保留选择并提供显式刷新，不自动采用新版本重交。未知结果的确认复用原请求 ID 和冻结方案，不能用修改接收角色的请求冒充重放。

Role 删除扩展上述转移字段并复用现有错误 envelope，不公开 Saga 状态或恢复轮询接口。请求无效为 `422 ErrIAMRoleDeleteInvalid`，受保护 Role 等删除业务拒绝为 `403 ErrIAMRoleDeleteDenied`，不存在为 `404 ErrIAMResourceNotFound`，版本、幂等和依赖冲突为 `409 ErrIAMRoleDeleteConflict`，并保留对应的机器可读原因。已确定失败的删除操作返回 `500 ErrIAMRoleDeleteFailed`；尚不能确认终态返回 `409 ErrIAMRoleDeleteResultUnknown`。读取依赖不可用保持 `503 ErrIAMRoleAdministrationUnavailable`；Frontend 展示 owner 的安全、本地化消息，不从错误码推断外部 DCL 已回滚。

权限不足的 `403 ErrIAMRoleDeleteDenied` 使用 `IAM_ERROR_CODE_PERMISSION_DENIED`，只有真实系统角色保护使用 `IAM_ERROR_CODE_PROTECTED_SYSTEM_ROLE`。已经确认 MatrixOne 角色不存在，但因原操作者权限撤销而不能完成 Ownership 转移或本地清理时，返回 `500 ErrIAMRoleDeleteFailed` 与 `IAM_ERROR_CODE_ROLE_DELETE_FINALIZATION_DENIED`，本地化消息明确说明外部删除已完成、收尾尚未完成。失败终态按原请求重放同一分类；有权操作者可以使用新请求继续完成删除，不能将恢复授权后的旧失败请求改为成功。

成功响应与成功重放中的 Role 使用删除回执保存的旧 ID、原名称及逻辑 `deleted` 状态，不依赖角色主表存在。相同请求不影响后来创建的同名新角色；使用新请求访问已不存在的旧角色保持既有不存在分类。审计查询继续按旧 Role ID 读取历史记录，不因主表删除失效。

删除失败同 `request_id` 重放原分类，新的 `request_id` 表示显式重试。未完成操作由既有 Saga 的后台恢复继续收尾，成功后同请求读取原回执；失败终态不被后台扫描重新执行。内部重试预算、每次转移的重新鉴权与部分完成语义见[生命周期合同 §4.2](04-storage-lifecycle-audit.md#42-role-删除)。Frontend 展示 Backend 的 `msg`；结果未知时锁定原方案，由用户通过原 `request_id` 显式确认结果，不生成新请求。确认终止后再次删除才建立新请求；版本冲突时保留选择并由用户刷新、复核后重新提交。DELETE 不自动重发，前端不读取 Saga 状态或轮询恢复。

## 7. Data Privilege

公开链路为：

- `GET /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/data-privileges`；
- `POST /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/data-privileges:validate`；
- `PUT /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/data-privileges`；
- `GET /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/data-privilege-operations/{request_id}`；
- `POST /newmoi/workspaces/{workspace_id}/iam/roles/{role_id}/data-privilege-operations/{repair_operation}`。

GET 默认返回权限概览和可回显的行列规则，不查询表结构（`columns=[]`、`table_schema_version=""`）。打开单表行列权限弹窗时传入可选 query `table_id`（canonical table ID），返回该表的权限项并仅查询一次列结构。鉴权仍为 workspace `role.read`；表必须在当前 workspace 的目标 Role 权限/规则事实中解析成功，否则返回 404。详情依赖失败返回错误，Frontend 保留表列表并在详情弹窗中重试，不将失败解释为无限制权限。Validate/Apply 继续基于实时表结构校验。

概览中的 MatrixOne 授权或孤立行列规则无法关联到当前资源时，保留 `resource_unresolved` 只读诊断项：`resource_type`、`display_name`、`action_id` 和 `privilege` 来自已读取的原生事实及 Registry，`resource_id=""`、`editable=false`、`disabled_reason=RESOURCE_UNRESOLVED`，不生成行列草稿或表结构。名称仅用于核对，不是 canonical ID。角色编辑与预览应明确展示这些记录，不将它们计入对象选择或生成 GRANT/REVOKE，也不因该诊断阻断其他合法权限的展示和保存。读取不清理、重绑定或修复记录；存储/解析依赖故障仍返回错误，不能伪装成资源不存在。

`admin`/`superadmin` 的产品权限预览按第 3.3 节直接展示全权限，不通过此 GET 枚举数据库/表授权。该预览约定不改变本节接口的服务端读取、mutation 或错误合同。

目标 Role 固定在 path 中，可以是当前 Verified Effective Role 自身，也可以是同一 workspace 的其他可修改普通 Role。mutation 使用 `expected_data_privilege_version` CAS，并只接受 canonical database/table resource ID；调用方不能提交 SQL 名称或可信 Role facts。

- validate 返回 canonical mutations、字段错误、warning 和 payload fingerprint，不执行 DCL。
- apply 的 `request_id` 可省略，后端为本次保存生成编号，响应中的 `request_id` 可用于查询；再次省略编号提交会作为新保存处理，过期版本仍返回冲突。显式提供编号的既有调用方保留同请求幂等合同。正常保存直接执行 DCL，不预读整套权限判断是否需要写入；仅在 `clear` 时检查规则存在性，避免 MatrixOne 对不存在的 `DROP RULE` 报错。保留写后读回、活跃操作隔离和可选的当前事实同步。
- apply/operation/repair 返回 operation ID、`applying|succeeded|failed|drifted|unknown`、data privilege version、MatrixOne fact version、session invalidation status 和逐资源结果。
- 非成功终态仍是可诊断的业务结果，Frontend/SDK 不得丢弃逐资源 state/error；transport/依赖失败仍按错误 envelope 返回非 2xx。
- row/column `keep|set|clear` 只有 Permission Schema 的相关 capability gates 全部满足时可用；`expression` 接受完整 SQL 条件，支持 `@标签名` 用户标签引用；Core 仅为 Unicode 裸变量名补充 MO 标识符引号，保存时同步带变量的规则，执行时绑定当前用户的字符串标签值。其他 SQL 语法、函数、变量及引用权限由 MatrixOne 校验。普通比较值仍按字面量解释，标签缺失时不注入默认值。
- SELECT 授权 mutation 的 `row_column` 配置作用于 path 指定的目标 Role 在该表上的规则，与 SELECT 转授使用同一次数据委派准入；不额外叠加角色管理权限，也不以操作者当前的行列限制约束目标配置。`keep` 保留目标现有规则，`set` 设置或替换规则，`clear` 删除规则；向自身授权和清除自身限制同样遵循 [Table 与 MatrixOne](08-business-permission-model-catalog.md#54-table-与-matrixone) 的规则。
- 独立 Data Privilege apply 使用 `iam-data-privilege` Saga，先执行并读回 MO，再提交 MOI 权限投影、版本、回执和审计。MO 的每条 GRANT、REVOKE、ADD/DROP RULE 独立提交，整个 MO 阶段可能部分完成。Saga 有限重试 MOI 提交；预算耗尽保留失败记录，停止自动执行。
- 同一 Role 仅 `applying` 执行保留冲突隔离；`unknown|drifted|failed` 历史结果不阻止新的保存、整角色编辑或删除。若 Saga 已持久化为 `failed` 而回执仍是 `applying`，原 owner 在失败返回或下一次编辑时原子记录未知结果及审计并释放占用，不改动权限投影和版本。旧请求保留原结果，延迟恢复不能覆盖后续保存。过期版本或仍在执行的操作返回 `409 ErrIAMDataPrivilegeConflict`。
- repair 是显式的 MO → MOI 同步命令，只读回原操作影响资源的当前 MO 授权、WGO 与规则，并原子提交本地投影、修复回执、审计和原操作处置。它不执行原 GRANT/REVOKE，不重建不存在的权限，也不改变无关资源；同一修复 request ID 重放返回同一回执。当前规则无法还原成已验证 UI 草稿时保留原生观测，不编造草稿。
- MOI 提交预算耗尽留下的 `applying` 回执，只有其 Saga 已确认 `failed` 才可释放或手动同步；手动同步不再是后续保存的前置条件。仍活跃或进程中断的 Saga 继续遵循原执行锁和共享恢复流程；没有成功记录不能解释为没有执行。普通 apply 的同请求调用只返回终态回执或进行中冲突，不触发旧操作恢复；普通 GET/readback/drift 查询不执行修复。
- 旧格式、无 Saga 的独立 `applying` 回执继续支持显式 repair。新保存由原 owner 将已停止的历史占用记为 `unknown`，只保存本次输入；升级范围及校验条件见[存储合同 §6](04-storage-lifecycle-audit.md#6-data-privilege-durable-operation)。

## 8. Role 与成员审计

Role audit 和 workspace member audit 均读取 Core `iam_audit_events`，按时间倒序、cursor 分页，默认 limit 20，最大 100。Role audit 支持 operation、actor、status 过滤并返回结构化 `diff`、各 IAM version、status/error 和 actor display projection；成员 audit 返回结构化 summary，并在每条事件返回同一 `actor_display_name` 展示字段。

actor display name 是本地化展示投影，不是授权或审计主体事实。Backend 对当前页 user actor ID 去重后批量解析；解析失败、历史账号已删除、目录不可用或 actor 不是用户时 `actor_display_name` 为空字符串，不把 canonical ID 回填为展示名，也不隐藏或改变审计事件。Frontend 对空展示名显示本地化的“用户已不存在”，并仅在 Tooltip 中保留 canonical `actor_principal_id`。Frontend 不得把结构化 diff 压缩成无法恢复字段语义的单一 summary，Product SDK 也不得丢弃 cursor、version、request/trace ID。

## 8.1 Workspace Member Invite

`POST /newmoi/user/create` 仍是 Product SDK `Invite` / `invite` 与 Frontend CreateUser 的唯一写入口，不新增 route 或 IAM resource/action。

- 联系方式三选一：`email`、`mobile_number`、`github_login`。Go `WithUserGithubLogin` / Python `with_user_github_login` 与邮箱、手机互斥。
- 三种定向邀请都要求 UC 中已存在且可用的账号；未命中返回 `USER_NOT_FOUND`，不创建邀请或占位用户。UC 依赖失败仍返回目录不可用错误。面向外部用户的链接邀请是独立渠道，不适用这一前置条件。
- 邮箱/手机创建 Core pending invitation，结果 `id` 是 canonical target user id，但还不是 active member handle。
- GitHub 目录命中立即入组，结果 `id` 按已是成员返回，可立即绑定 `WorkspaceMemberHandle`。不支持挂起或后续绑定登录时自动认领。
- 三种邀请都要求非空 `role_id_list`，并显式指定属于该列表的 `default_role_id`。邀请及初始角色分配只要求 `workspace_member.invite`；已有成员改绑角色使用 `workspace_member.role_binding.mutate`。
- 角色下拉通过 `role.read` 过滤列表；无可读角色时返回空列表，前端不额外显示权限提示。该读取不成为邀请 API 的复合准入条件。

显式接受 `POST /newmoi/workspaces/invitations/{invitation_id}/accept` 与自动接受链路 `POST /newmoi/user/create` 使用相同错误合同，由业务 owner 区分已知原因并提供安全、本地化的 `msg`：

| 已确认原因 | HTTP | `code` | 中文提示 |
| --- | --- | --- | --- |
| 邀请已取消 | 410 | `ErrWorkspaceInvitationCancelled` | 此邀请已取消，请联系工作区管理员重新邀请。 |
| 邀请或成员状态/版本发生变化 | 409 | `ErrWorkspaceInvitationStateChanged` | 邀请或成员状态已发生变化，请刷新工作区列表后重试。 |
| 旧成员删除清理未完成 | 409 | `ErrWorkspaceInvitationCleanupPending` | 您之前的成员信息尚未清理完成，请稍后重试；如持续出现，请联系工作区管理员。 |
| 分配的角色已删除、停用或尚不可用 | 409 | `ErrWorkspaceInvitationRoleUnavailable` | 邀请分配的角色已不可用，请联系工作区管理员处理。 |
| 接受意图或账号/授权记录校验不一致 | 409 | `ErrWorkspaceInvitationFactsConflict` | 邀请信息校验未通过，暂时无法接受。请联系工作区管理员处理。 |
| 同一用户已有未删除成员关系（active/disabled） | 409 | `ErrWorkspaceInvitationAlreadyMember` | 您已是该工作区成员，无需重复接受邀请。请刷新工作区列表。 |

角色查询失败与已确认角色不可用分开，读取故障保留原始系统/依赖错误。Frontend 和 Product SDK 直接消费 owner 的消息；不从已有成员记录推断本次接受已成功或当前可进入工作区。错误分类保留原成员、邀请和失败恢复语义，不新增异常数据自动修复或取消行为；普通重复邀请继续返回 `USER_ALREADY_EXISTS`，同一已接受邀请的幂等重放仍返回成功。

成员事实冲突的服务日志记录接受阶段、workspace/invitation/user、预期与实际 membership ID、实际成员状态及当前 request/trace ID；凭据和底层存储诊断不进入公开错误消息，密码和加密凭据不进入日志。

## 9. 错误 envelope

权限拒绝、可控授权异常与不可控故障按[失败语义](01-product-authorization-model.md#9-失败语义)分类。该原则约束 owner 的返回值与客户端交互，不授予客户端将所有错误转成无权限的权限。

Backend IAM 错误保持：

```json
{
  "code": "stable_backend_code",
  "msg": "localized_safe_message",
  "data": null
}
```

需要返回 IAM 操作诊断字段的端点可以在既有 `data` 中附带：

```json
{
  "data": {
    "request_id": "...",
    "trace_id": "...",
    "core_error_code": "..."
  }
}
```

`data` 是端点既有 envelope 的可选字段，不得为了错误分类新建平行响应格式。存在时，`data.request_id` 和 `data.trace_id` 是最终 Backend 公共响应头
`X-Request-ID` / `X-Trace-ID` 的镜像，便于兼容既有 IAM DTO；其中只有
`X-Request-ID` 是产品关联查询的权威来源。请求体中的幂等 `request_id`、Core
返回的 request/trace ID 只写入结构化日志，不得覆盖公共关联 ID。Frontend 和
Product SDK 只从最终响应头读取 request ID，不从响应体回退。`core_error_code`
仍是可选的稳定 IAM 分类字段，不包含未结构化的上游错误文本。

正常拒绝和可控授权异常为 `403`，CAS/幂等冲突为 `409`，可公开的不存在为 `404`，结构或 schema 错误为 `400/422`，Core/PDP/storage/transport 确实不可用为 `503`。PAT 无效、inactive、缺少必需 audience/scope 或断言结构非法返回 `401 ErrApiKeyInvalid`；PAT 已通过 introspection 但 canonical Product/Core principal 缺失、歧义或投影不完整返回 `403 ErrUserNotSynced`，调用方据此发现同步前置条件，不能把它重试为凭据错误。Frontend 在受影响区域展示 owner 的安全、本地化 `msg`，code 与 request ID 作为辅助诊断，不为正常无权限重复弹出错误；SDK 保留 status、code、message 和 diagnostic IDs，不能只返回机器码或统一改成 500。

已知 IAM 暂时不可用错误虽然都返回 `503`，Backend 仍逐项映射：

| Core code | Backend code | 用户语义 |
| --- | --- | --- |
| `IAM_ERROR_CODE_CORE_AUTHORIZE_UNAVAILABLE` | `ErrCoreAuthorizeUnavailable` | IAM 服务暂时不可用 |
| `IAM_ERROR_CODE_RESOURCE_METADATA_UNAVAILABLE` | `ErrIAMResourceMetadataUnavailable` | 资源权限信息暂时不可用 |
| `IAM_ERROR_CODE_POLICY_STORE_UNAVAILABLE` | `ErrIAMPolicyStoreUnavailable` | 权限策略服务暂时不可用 |
| `IAM_ERROR_CODE_TARGET_ROLE_UNAVAILABLE` | `ErrIAMTargetRoleUnavailable` | 角色信息暂时不可用 |
| `IAM_ERROR_CODE_AUDIT_UNAVAILABLE` | `ErrIAMAuditUnavailable` | 必须事务落审计的 IAM mutation 或审计查询不可用，本次操作未执行 |

成功读取后确认的授权快照变化不属于依赖不可用。既有有限重读后仍变化时，`IAM_ERROR_CODE_AUTHORIZATION_STATE_CHANGED` / `ErrIAMAuthorizationStateChanged` 返回 `403`，消息说明当前权限状态变化、暂不能执行该操作；客户端仅更新相关无权限状态，后续请求重新裁决，不自动重发原写请求。native 的错误类型由现有 IAM owner 分类并通过既有 envelope 映射，不因此恢复旧进程或新增平行错误格式。

Role 创建过滤历史 `model_runtime.invoke` 后若没有剩余 Application Policy 或 Data Privilege，Core 返回 `IAM_ERROR_CODE_ROLE_PERMISSION_REQUIRED`，Backend 返回 `422 ErrIAMRolePermissionRequired` 和按 locale 本地化的选择权限提示。该错误只描述用户可修正的输入场景；原始内部错误、Core request/trace ID 和幂等 request ID 仅进入结构化日志。

普通 `Authorize`/filter 的 decision audit 是 best-effort：写失败只记录结构化错误，不改变已经计算完成的 allow/deny，也不返回 `IAM_ERROR_CODE_AUDIT_UNAVAILABLE`。Backend 只依据 Core 稳定 code 选择本地化 `msg`，不得把 Core `safe_message` 或 raw cause 原样暴露给 Frontend。未命中已知分类的 `DECISION_INTERNAL_ERROR` / `DECISION_UNKNOWN` 保持 `500`，不能伪装成可重试的 `503`。

### 9.1 页面与能力隔离

- detail/list 的读取已独立获权且返回合同完整时，附带动作投影的局部可控异常只使相应动作不可用；不清空其它有效动作，也不把整页替换为错误。读取自身无权时不保留该对象的受保护内容。
- 权限清单只能按接口已声明的 included/完整性合同展示。诊断项与不可用状态必须可辨识，不能以丢弃记录后的“空权限”冒充完整已保存策略，更不能用这种投影覆盖保存。
- 共同身份未就绪时，依赖它的 workspace 内容均不可用，但仍保留第 2 节的账号级入口；单个子请求无权或失败不能清空其它独立请求的权限上下文。
- 用户切换 Role、workspace 或对象后，旧请求不能恢复旧能力或覆盖新页面。权限展示不能替代 mutation 的实时服务端鉴权。
- 系统故障只在受影响区域提示；允许恢复时提供显式只读刷新，不重放写入。写入的部分完成或结果未知继续按第 1.1 节处理，之后的 `403` 不能证明原写入未发生。

## 10. 变更与验证

公开字段、route、Default Role 输入、Role Candidate transport 或错误分类变化会同时影响 Backend、Frontend、Go/Python Product SDK、route manifest、API matrix 和文档。实施前按根 `AGENTS.md` 的确认门禁列出影响；确认后一次更新全部调用点和契约测试。

最低验证包括 Backend handler contract tests、Product SDK route/body/response tests、Frontend principal bootstrap/cache/error tests，以及 [验证与漂移控制](06-verification-drift-control.md) 规定的 Core/Backend route 和真实环境分层验证。
