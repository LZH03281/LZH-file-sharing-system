# 共享文件服务器

一个面向课程大作业的 C/S 文件共享系统：服务端部署在 Ubuntu Server，Windows 客户端通过 HTTP API 完成登录、文件浏览、上传、下载、搜索和权限控制。

## 技术栈

- 客户端：Python + PyQt6 + requests
- 服务端：Python + FastAPI + SQLAlchemy
- 数据层：SQLite（仅保存用户、文件元数据和操作日志）
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

主干功能：登录与 JWT 认证，文件列表、搜索、上传、下载和删除，普通用户/管理员权限，shared/private 可见性，以及基本异常处理和路径安全。

后续增强：操作日志与管理员界面、传输进度细化、Ubuntu Server 常驻部署，以及密码哈希方案升级。

## 当前进度

当前已完成项目第一版主干：FastAPI 服务端、SQLite/JWT 权限、PyQt6 客户端主界面。服务端测试结果为 `9 passed`，客户端已通过语法检查和窗口构造检查。

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| 1 | FastAPI 骨架与文件上传、列表、下载、删除 | 已完成 |
| 2 | SQLite、用户、JWT、权限与搜索 | 已完成 |
| 3 | PyQt6 登录和文件管理客户端、基础传输进度 | 已完成 |
| 4 | 日志、管理员功能、安全加固与 Ubuntu 部署 | 后续增强 |

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
├── docs/               # 架构、API、测试和部署文档
└── README.md
```

详细模块边界、接口、数据模型、权限矩阵和阶段验收标准见 [架构设计](docs/architecture.md)。

## 参考原则

项目只按当前模块选择性参考 QShare、File-Upload-and-Download-API、Upload-files-fastapi、file-storage-api 和 fastapi-auth-template 的成熟实现思路，不整库照搬，不引入与需求无关的功能，最终统一到本项目自己的目录和编码风格中。
