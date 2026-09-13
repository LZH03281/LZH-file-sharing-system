# 共享文件服务器

一个面向课程大作业的 C/S 文件共享系统：服务端部署在 Ubuntu Server，Windows 客户端通过 HTTP API 完成登录、文件浏览、上传、下载、搜索和权限控制。

## 技术栈

- 客户端：Python + PyQt6 + requests + websocket-client
- 服务端：Python + FastAPI HTTP/WebSocket + SQLAlchemy
- 数据层：SQLite（保存用户、文件元数据、操作日志和聊天消息）
- 文件存储：服务器本地目录，使用 UUID 文件名
- 部署：Ubuntu Server + Uvicorn + systemd

## 统一测试环境

为方便 6 人小组统一复现和分工，服务端测试虚拟机统一使用：

- 虚拟机软件：VMware Workstation Pro
- 系统镜像：`ubuntu-24.04.4-live-server-amd64.iso`
- 虚拟机用途：运行 FastAPI 服务端、SQLite 数据库和本地文件存储
- 推荐配置：2 CPU、2 GB 内存、20 GB 磁盘
- 网络建议：开发调试可用 NAT；需要让 Windows 客户端直接访问时使用桥接网络或确认 NAT 端口映射

组员自行下载 VMware Workstation Pro 和上述 Ubuntu Server ISO 后，按相同版本创建虚拟机，减少系统差异导致的部署问题。

## 功能范围

主干功能：登录与 JWT 认证，文件列表、搜索、上传、下载和删除，普通用户/管理员权限，shared/private 可见性，WebSocket 实时单聊，以及基本异常处理和路径安全。

安全增强已实现：基于 ClamAV 的上传与下载扫描、危险文件防护和 Ubuntu 低权限部署模板。后续可继续完善传输进度和密码哈希方案。

## 当前进度

当前已完成项目基础版、文件安全增强和实时单聊：FastAPI 服务端、SQLite/JWT 权限、PyQt6 客户端主界面、操作日志、ClamAV 扫描、WebSocket 聊天和 Ubuntu 部署模板。本次服务端测试结果为 `37 passed`（扫描器使用模拟结果）；服务端与客户端均通过语法检查。真实 ClamAV 引擎需在目标 Ubuntu 上验收。

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| 1 | FastAPI 骨架与文件上传、列表、下载、删除 | 已完成 |
| 2 | SQLite、用户、JWT、权限与搜索 | 已完成 |
| 3 | PyQt6 登录和文件管理客户端、基础传输进度 | 已完成 |
| 4 | 日志、管理员功能、安全加固与 Ubuntu 部署 | 基础版已完成 |
| 5 | WebSocket 文本单聊、在线状态与历史消息 | 已完成 |

## 实时聊天功能

本版在不改变现有服务端和客户端启动方式的前提下，复用登录认证、用户模型和 SQLite 数据库，实现局域网内实时单聊：

- 服务端新增 WebSocket 单聊通道，客户端登录后使用 JWT 建立长连接；
- 服务端维护在线连接表，在线用户之间实时推送消息；
- 聊天消息落库到 SQLite，保存发送者、接收者、内容、发送时间和已读状态等基础字段；
- 客户端主界面新增“聊天”入口，打开独立聊天窗口；
- 聊天窗口支持选择用户、加载历史记录、发送文本消息、接收实时消息和基础异常提示；
- 离线用户重新登录后，可以通过历史记录看到此前收到的消息；
- 当前只实现文本单聊，暂不包含群聊、文件消息、撤回、已读回执和复杂通知系统。

后续可扩展方向：群聊、管理员公告、文件消息、未读数量聚合、消息撤回、已读状态和更完整的在线状态展示。

每个阶段完成后必须先运行测试并记录结果，再开始下一阶段。

服务端测试命令：

```powershell
cd server
& 'C:\Users\lenovo\miniconda3\python.exe' -m pytest
```

开发启动命令：

```powershell
cd server
& 'C:\Users\lenovo\miniconda3\python.exe' -m uvicorn app.main:app --reload
```

默认开发管理员为 `admin / admin123`，部署或演示前可通过环境变量修改。

客户端首次运行或拉取新功能后，需要先安装客户端依赖。实时聊天功能新增 `websocket-client`，如果不安装会导致聊天窗口无法启动：

```powershell
cd client
& 'C:\Users\lenovo\miniconda3\python.exe' -m pip install -r requirements.txt
```

客户端启动命令：

```powershell
cd client
& 'C:\Users\lenovo\miniconda3\python.exe' .\main.py
```

客户端默认连接 `http://127.0.0.1:8000`，先启动服务端后再登录。

## 计划目录

```text
.
├── client/             # PyQt6 客户端
├── server/             # FastAPI 服务端和测试
├── deploy/             # Ubuntu 环境变量和 systemd 模板
├── docs/               # 架构、API、测试和部署文档
└── README.md
```

详细模块边界、接口、数据模型、权限矩阵和阶段验收标准见 [架构设计](docs/architecture.md)。

Ubuntu Server 部署步骤见 [部署说明](docs/ubuntu-deploy.md)。

## 文件病毒筛查与风险防护

已接入可选启用的 **ClamAV** 本地扫描。服务端调用 `clamscan`，在文件写入临时目录后、正式入库前完成扫描：

- 扫描通过：继续保存文件元数据并允许下载；
- 扫描失败或发现病毒：删除临时文件，返回明确错误提示，并写入操作日志；
- 服务不可用：优先采用保守策略，拒绝本次上传或提示管理员检查杀毒服务。

同时增加危险后缀、可执行文件头检查、扫描超时和并发限制。下载前再次扫描，包括历史文件，并添加安全响应头。

本地开发和课程演示默认不强制启用 ClamAV，以免未安装杀毒引擎的虚拟机无法上传文件。正式部署到 Ubuntu 时建议安装 ClamAV、更新病毒库，并在环境变量中设置 `CFS_ANTIVIRUS_ENABLED=true`；如果扫描器不可用，上传和下载会被保守拒绝。

完整配置、GitHub 参考、限制和验收步骤见 [文件安全说明](docs/file-security.md)。部署模板位于 `deploy/server.env.example` 和 `deploy/shared-file-server.service`。

## 参考原则

项目只按当前模块选择性参考 QShare、File-Upload-and-Download-API、Upload-files-fastapi、file-storage-api 和 fastapi-auth-template 的成熟实现思路，不整库照搬，不引入与需求无关的功能，最终统一到本项目自己的目录和编码风格中。
