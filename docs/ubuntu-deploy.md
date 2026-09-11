# Ubuntu Server 部署说明

> 文件安全功能默认启用。请优先按 [文件安全与部署](file-security.md) 安装 ClamAV、更新病毒库，并使用 `deploy/` 中的低权限 systemd 配置。下文基础部署步骤不包含完整安全配置；未安装扫描器时上传和下载会被拒绝。

本文档用于小组成员在统一虚拟机环境中部署服务端。推荐环境：

- VMware Workstation Pro
- `ubuntu-24.04.4-live-server-amd64.iso`
- 2 CPU、2 GB 内存、20 GB 磁盘
- 演示时推荐桥接网络，方便 Windows 客户端访问虚拟机 IP

## 1. 安装系统依赖

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

## 2. 克隆项目

```bash
git clone https://github.com/LZH03281/LZH-file-sharing-system.git
cd LZH-file-sharing-system/server
```

## 3. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. 配置环境变量

开发演示可先使用默认账号 `admin / admin123`。正式演示前建议至少设置 JWT 密钥和管理员密码：

```bash
export CFS_SECRET_KEY="change-this-secret-key-at-least-32-characters"
export CFS_DEFAULT_ADMIN_USERNAME="admin"
export CFS_DEFAULT_ADMIN_PASSWORD="change-admin-password"
export CFS_DATA_DIR="$PWD/data"
export CFS_MAX_UPLOAD_SIZE="52428800"
```

## 5. 前台启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

在虚拟机中查看 IP：

```bash
ip addr
```

Windows 客户端登录窗口中填写：

```text
http://<Ubuntu虚拟机IP>:8000
```

## 6. 健康检查

在 Windows 或 Ubuntu 中访问：

```bash
curl http://<Ubuntu虚拟机IP>:8000/health
```

返回 `{"status":"ok"}` 即表示服务端可访问。

## 7. systemd 常驻运行（可选）

创建环境变量文件：

```bash
sudo mkdir -p /etc/shared-file-server
sudo nano /etc/shared-file-server/server.env
```

示例内容：

```text
CFS_SECRET_KEY=change-this-secret-key-at-least-32-characters
CFS_DEFAULT_ADMIN_USERNAME=admin
CFS_DEFAULT_ADMIN_PASSWORD=change-admin-password
CFS_DATA_DIR=/opt/shared-file-server/data
CFS_MAX_UPLOAD_SIZE=52428800
```

创建服务目录并复制项目：

```bash
sudo mkdir -p /opt/shared-file-server
sudo cp -r . /opt/shared-file-server/server
sudo mkdir -p /opt/shared-file-server/data
```

创建 systemd 服务：

```bash
sudo nano /etc/systemd/system/shared-file-server.service
```

示例内容：

```ini
[Unit]
Description=Shared File Server
After=network.target

[Service]
WorkingDirectory=/opt/shared-file-server/server
EnvironmentFile=/etc/shared-file-server/server.env
ExecStart=/opt/shared-file-server/server/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now shared-file-server
sudo systemctl status shared-file-server
```

## 8. 常见问题

- 客户端连不上：确认 Uvicorn 监听 `0.0.0.0:8000`，并检查 VMware 网络模式。
- NAT 访问异常：优先改用桥接网络，或配置 VMware NAT 端口映射。
- 登录失败：确认默认管理员密码是否被环境变量修改。
- 文件没有持久保存：确认 `CFS_DATA_DIR` 指向的目录有写权限。
