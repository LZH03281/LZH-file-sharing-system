# 共享文件服务器架构设计

## 1. 文档目的与项目边界

本文档把课程需求转换成可直接开发、测试和验收的技术方案。课程需求文档用于确定产品范围；若其内容与用户当前指令冲突，以用户指令为准。

项目采用“按模块参考、统一实现”的方式：

| 参考项目 | 只参考的内容 |
| --- | --- |
| QShare | PyQt6 界面、文件选择、传输交互和进度反馈 |
| File-Upload-and-Download-API | FastAPI 上传、下载、删除接口的基本实现方式 |
| Upload-files-fastapi | SQLAlchemy 文件元数据和本地文件存储方式 |
| file-storage-api | UUID 标识、MIME 类型、路径安全和文件管理 |
| fastapi-auth-template | 用户模型、JWT、登录和权限依赖 |

不完整阅读或复制参考仓库，不保留无关代码，也不提前加入课程需求之外的大型功能。

## 2. 架构目标

- Windows 客户端通过局域网访问 Ubuntu Server。
- API、业务逻辑、数据库访问和磁盘存储职责分离。
- SQLite 只保存元数据，大文件保存在服务器本地目录。
- 所有受保护接口统一使用 JWT Bearer Token。
- 文件访问同时经过数据库查询、权限判断和安全路径校验。
- 各阶段可独立启动、测试和演示，后续阶段不推翻前一阶段的核心结构。

暂不设计分布式存储、断点续传、秒传、在线预览、多节点部署等超出课程范围的功能。

## 3. 总体架构

```text
┌──────────────────────── Windows ────────────────────────┐
│ PyQt6 Client                                            │
│ UI → ApiClient → TransferWorker                         │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/JSON + multipart/file stream
┌───────────────────────▼ Ubuntu Server ──────────────────┐
│ FastAPI                                                 │
│ Router → Auth/Permission → Service → Repository/Storage │
│                                  ├→ SQLite metadata     │
│                                  └→ local file storage  │
└─────────────────────────────────────────────────────────┘
```

客户端负责登录、文件展示与搜索、文件选择、传输进度、错误提示和删除确认。服务端负责认证授权、参数验证、流式传输、元数据、磁盘文件、日志和统一异常响应。

## 4. 统一项目结构

```text
.
├── README.md
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── test-plan.md
│   └── ubuntu-deploy.md
├── server/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── deps.py
│   │   │   ├── files.py
│   │   │   └── logs.py        # 后续增强
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── errors.py
│   │   │   └── security.py
│   │   ├── db/database.py
│   │   ├── models/models.py
│   │   ├── repositories/
│   │   │   ├── memory.py
│   │   │   └── sqlalchemy.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   └── files.py
│   │   └── services/
│   │       ├── audit.py
│   │       └── storage.py
│   └── tests/test_api.py
└── client/
    ├── requirements.txt
    ├── main.py
    ├── api_client/client.py
    ├── ui/
    │   ├── login_window.py
    │   └── main_window.py
    └── workers/transfer_worker.py
```

服务端依赖保持单向：`api → services → repositories/storage`，仓库层负责接入 `db`。UI 只调用 `ApiClient`；传输线程不直接修改控件，只通过 Qt signal 回传结果。

## 5. 服务端接口设计

### 5.1 API 清单

| 方法 | 路径 | 用途 | 权限 |
| --- | --- | --- | --- |
| GET | `/health` | 健康检查 | 公开 |
| POST | `/auth/login` | 用户登录 | 公开 |
| GET | `/auth/me` | 当前用户信息 | 登录用户 |
| POST | `/auth/users` | 创建用户 | 管理员 |
| GET | `/files` | 可见文件列表 | 登录用户 |
| GET | `/files/search?q=` | 按原始文件名搜索 | 登录用户 |
| POST | `/files/upload` | 上传文件 | 登录用户 |
| GET | `/files/{file_id}/download` | 下载文件 | 有查看权限的用户 |
| DELETE | `/files/{file_id}` | 删除文件 | 所有者或管理员 |
| GET | `/logs` | 查询操作日志 | 管理员，后续增强 |

登录接口接收 JSON 用户名和密码，成功后返回 `access_token`、`token_type` 和用户摘要。上传使用 `multipart/form-data`，包含 `file` 和 `visibility`。下载返回文件流，并通过 `Content-Disposition` 提供原始文件名。

列表与搜索返回相同的文件摘要，至少包含：

```text
id, original_name, size, content_type, visibility,
owner_id, owner_name, created_at, can_delete
```

`can_delete` 由服务端计算，用于客户端按钮状态；真正删除时服务端仍重新校验权限。

### 5.2 错误响应

除文件流外，错误统一为：

```json
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "文件不存在",
    "details": null
  }
}
```

状态码约定：`400` 参数错误，`401` 令牌无效或过期，`403` 权限不足，`404` 资源不存在，`409` 唯一资源冲突，`413` 文件超限，`500` 服务端异常。服务端日志保留内部细节，客户端只显示安全、可理解的 `message`。

## 6. 核心业务流程

### 6.1 上传

```text
验证 JWT 和 visibility
        ↓
流式写入 storage/.tmp，同时统计大小和 SHA-256
        ↓
超过限制则删除临时文件并返回 413
        ↓
生成 UUID，将临时文件原子移动为最终文件名
        ↓
写入文件元数据，后续增强再补操作日志
        ↓
返回文件摘要
```

原始文件名只用于展示和下载，磁盘文件名由 UUID 生成。同名上传创建独立记录，不覆盖旧文件。若数据库写入失败，服务层删除本次生成的文件，避免孤立文件。

### 6.2 下载

```text
验证 JWT → 查询元数据 → 校验可见性/所有权
          → 安全解析 storage 内路径 → 返回文件流
```

元数据存在但实际文件丢失时返回受控错误并写失败日志，不暴露真实路径。

### 6.3 删除

```text
验证 JWT → 查询元数据 → 校验所有者/管理员
          → 数据库事务删除记录并写日志 → 删除实际文件
```

记录提交成功但磁盘删除失败时写入告警；该文件已不可通过 API 访问，可由管理员后续清理。不存在的文件 ID 返回 `404`。

## 7. 数据模型

### 7.1 users

| 字段 | 类型/约束 | 说明 |
| --- | --- | --- |
| id | integer, PK | 用户标识 |
| username | string, unique, index | 登录名 |
| password_hash | string | 当前使用 PBKDF2 哈希，后续可升级 bcrypt/argon2 |
| role | string | `user` / `admin` |
| enabled | boolean | 是否允许登录 |
| created_at | datetime | UTC 创建时间 |

### 7.2 files

| 字段 | 类型/约束 | 说明 |
| --- | --- | --- |
| id | string UUID, PK | API 文件标识 |
| stored_name | string, unique | UUID 磁盘文件名 |
| original_name | string | 原始展示名 |
| owner_id | FK users.id, index | 上传者 |
| size | integer | 字节数 |
| content_type | string | MIME 类型 |
| visibility | string, index | `private` / `shared` |
| sha256 | string | 完整性摘要 |
| created_at | datetime, index | UTC 上传时间 |

### 7.3 operation_logs（后续增强）

| 字段 | 类型/约束 | 说明 |
| --- | --- | --- |
| id | integer, PK | 日志标识 |
| user_id | integer, nullable | 操作用户 |
| action | string, index | login/upload/download/delete 等 |
| file_id | string, nullable | 关联文件 |
| file_name | string, nullable | 展示名快照 |
| result | string | `success` / `failed` |
| client_ip | string, nullable | 客户端地址 |
| detail | string, nullable | 受控的错误摘要 |
| created_at | datetime, index | UTC 操作时间 |

数据库保存 UTC 时间，API 返回 ISO 8601 字符串，客户端转换为本地时间显示。

## 8. 权限模型

| 操作 | 普通用户 | 文件所有者 | 管理员 |
| --- | --- | --- | --- |
| 上传文件 | 允许 | 允许 | 允许 |
| 查看/下载 shared 文件 | 允许 | 允许 | 允许 |
| 查看/下载他人 private 文件 | 拒绝 | 不适用 | 允许 |
| 查看/下载自己的 private 文件 | 不适用 | 允许 | 允许 |
| 删除文件 | 拒绝 | 允许 | 允许 |
| 创建用户、查看日志 | 拒绝 | 拒绝 | 允许 |

列表与搜索必须在数据库查询阶段过滤不可见记录，不能先返回全部数据再由客户端隐藏。为降低私有文件枚举风险，“不存在”和“无查看权限”可以统一返回 `404`。

## 9. 安全与配置

### 9.1 安全基线

- 密码仅保存哈希，当前主干使用标准库 PBKDF2；JWT 密钥从环境变量读取。
- 除健康检查和登录外，接口全部要求有效令牌。
- 不信任文件名、MIME、文件大小和客户端权限标记。
- 上传按块读取并由服务端累计大小，不只依赖请求头。
- 存储路径经 `resolve` 后必须仍位于 storage 根目录内。
- 日志不得记录密码、JWT 或文件正文。
- 默认管理员密码仅用于首次开发启动，部署前必须更改。

### 9.2 环境变量

```text
CFS_SECRET_KEY
CFS_DATA_DIR
CFS_DATABASE_URL
CFS_MAX_UPLOAD_SIZE
CFS_ACCESS_TOKEN_EXPIRE_MINUTES
CFS_DEFAULT_ADMIN_USERNAME
CFS_DEFAULT_ADMIN_PASSWORD
```

密钥和密码不得硬编码到仓库。服务监听地址由启动命令控制，Ubuntu 部署使用 `0.0.0.0:8000`。

## 10. PyQt6 客户端设计

```text
LoginWindow
├── 服务器地址、用户名、密码
└── 登录按钮和错误提示

MainWindow
├── 搜索框、刷新和退出
├── 文件表格：名称、大小、上传者、可见性、时间、MIME
├── 上传、下载、删除按钮
└── 当前任务状态和进度条
```

- 登录成功后令牌只保存在内存；退出或收到 `401` 时清除令牌并返回登录窗口。
- `ApiClient` 统一管理服务器地址、Authorization 头、超时和错误转换。
- 上传和下载在 `QThread` 工作对象中执行，通过 signal 报告进度、成功和失败。
- 下载先写临时文件，成功后再重命名，失败时删除临时文件。
- 任务期间禁用冲突按钮，结束后恢复界面状态。

## 11. 部署设计

Ubuntu Server 使用独立系统用户、Python 虚拟环境和数据目录。基础启动命令：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

开发验证通过后再配置 systemd。服务文件引用环境变量文件，不在启动命令中放置密钥。SQLite、storage 和日志目录授予服务用户读写权限；防火墙只开放实际端口。

### 11.1 小组统一测试虚拟机

为保证组内开发、测试和答辩演示环境一致，服务端虚拟机统一采用以下配置：

| 项目 | 统一要求 |
| --- | --- |
| 虚拟机软件 | VMware Workstation Pro |
| Ubuntu 镜像 | `ubuntu-24.04.4-live-server-amd64.iso` |
| 虚拟机角色 | FastAPI 服务端、SQLite 数据库、本地文件存储 |
| CPU | 建议 2 核 |
| 内存 | 建议 2 GB，机器资源充足可给 4 GB |
| 磁盘 | 建议 20 GB 或以上 |
| 网络 | NAT 适合本机开发；桥接网络适合让同一局域网内其他 Windows 客户端访问 |

组员自行下载 VMware Workstation Pro 和指定 ISO，创建虚拟机时尽量保持上述参数一致。安装 Ubuntu Server 后，记录虚拟机 IP，并在 Windows 客户端登录窗口中把服务器地址改为：

```text
http://<Ubuntu虚拟机IP>:8000
```

若使用 NAT 网络但 Windows 客户端无法访问虚拟机服务，需要检查 VMware NAT 网络、端口映射、防火墙和 Ubuntu 侧 Uvicorn 是否监听 `0.0.0.0:8000`。课程演示建议优先使用桥接网络，便于其他组员机器直接访问。

## 12. 分阶段实现与验收

### 第一阶段：FastAPI 文件服务闭环

实现应用骨架、配置、`/health` 以及上传、列表、下载、删除。此阶段使用与最终模型一致的文件摘要和存储服务，元数据仓库先采用进程内实现，文件接口暂不要求令牌；第二阶段只替换为 SQLAlchemy 仓库并挂接认证依赖，避免重写路由和存储逻辑。

验收：服务可启动；文件落盘；列表正确；下载字节与原文件一致；删除后不可查询或下载；非法 ID 和路径输入得到受控错误。

### 第二阶段：SQLite、认证、搜索和权限

加入 SQLAlchemy/SQLite、用户与文件模型、登录、JWT、搜索、角色和 shared/private 权限。初始化默认管理员，管理员可以创建普通用户。

验收：登录和令牌过期行为正确；普通用户只能删除自己的文件；其他用户不能发现或下载 private 文件；shared 文件对所有登录用户可见；测试使用临时数据库和目录。

### 第三阶段：PyQt6 客户端主干

实现登录、文件列表、上传、下载、删除、刷新和搜索。传输进度先做基础进度条或忙碌状态，后续再细化真实字节级进度。

验收：客户端完成文件全生命周期；上传/下载在后台线程执行；删除前确认；服务断开、权限不足和文件超限有明确提示。

### 第四阶段：日志、管理、安全加固和部署（后续增强）

在主干可演示后再完善操作日志与管理员界面，执行更完整的安全测试，编写 Ubuntu/systemd 部署文档。

验收：管理员可查询日志；越权、超限和路径穿越测试通过；按文档可在 Ubuntu Server 从干净环境启动，并由 Windows 客户端连接。

每阶段完成时提交：新增/修改文件清单、启动命令、测试命令、通过情况和下一阶段计划。未通过当前阶段测试时不进入下一阶段。

## 13. 测试策略

服务端使用 `pytest` 和 FastAPI `TestClient`，至少覆盖健康检查、登录、上传、列表、搜索、下载字节一致性、删除、无令牌、令牌失效、越权访问、超大文件、非法 visibility 和路径安全。测试数据库与 storage 使用临时目录。

客户端以手动验收为主，覆盖登录、刷新、搜索、文件选择、保存路径、删除确认、进度变化和网络异常；对 `ApiClient` 的响应解析与错误转换补充单元测试。

部署阶段验证虚拟环境安装、环境变量、前台 Uvicorn、systemd 重启和 Windows 客户端连接。

## 14. 下一步

第一阶段已完成：`server/` 骨架、配置、统一错误、进程内元数据仓库、安全存储服务，以及上传、列表、下载、删除接口测试已经通过。

第二阶段已完成：进程内仓库已替换为 SQLite/SQLAlchemy，已加入用户模型、默认管理员、登录、JWT、搜索、shared/private 权限和管理员创建用户接口。

第三阶段已完成：已实现 PyQt6 登录窗口、文件列表主窗口、上传、下载、删除、刷新、搜索、shared/private 选择和基础传输进度。

项目第一版主干到此完成。后续小组成员可以围绕客户端美化、真实上传进度、操作日志、管理员功能、部署文档和答辩材料继续分工。
