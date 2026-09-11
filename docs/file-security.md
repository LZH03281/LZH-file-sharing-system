# 文件安全与部署

## 实现与参考

依据 README 的临时目录扫描方案，实现本地 ClamAV 扫描，不向外部服务发送文件。
参考检索的 GitHub 项目：[Cisco-Talos/clamav](https://github.com/Cisco-Talos/clamav)、[nais/clamav-rest](https://github.com/nais/clamav-rest)。前者提供扫描引擎及命令行接口，后者展示上传后扫描的服务边界。本项目独立实现适合课程规模的 `clamscan` 调用，没有复制这些项目的源码，也无需额外 REST 服务。
配置依据：[官方扫描说明](https://docs.clamav.net/manual/Usage/Scanning.html)、[clamscan 参数与退出码](https://github.com/Cisco-Talos/clamav/blob/main/docs/man/clamscan.1.in)。

## 行为

- 默认启用病毒扫描：上传写入 UUID 临时文件，扫描通过才移动至存储目录并入库。失败删除临时文件并记录原因代码。
- 下载前复查，包括历史文件；被拦截的历史文件保留供管理员删除，不提供文件内容。下载使用附件、二进制类型和 `nosniff`，避免浏览器主动解释文件。
- 大小写、全角字符规范化后检查所有后缀，拒绝可执行文件、脚本、快捷方式、磁盘映像和宏文档；检查常见 PE、ELF、Mach-O、Java 和 shebang 文件头，防止简单改名绕过。完整后缀表见 `server/app/services/file_security.py`。
- ClamAV 拒绝病毒、加密文档/压缩包和超过扫描限制的内容。解包扫描总量限制为上传上限的四倍，嵌套最多 16 层、文件最多 1000 个。
- 扫描器缺失、病毒库缺失、异常退出或超时返回 `503 SCAN_UNAVAILABLE`；占用中返回 `503 SCAN_BUSY`，请重试。每个服务进程最多一个扫描任务。
- `400 UNSAFE_FILE` 为类型策略拦截；`400 FILE_INFECTED` 表示病毒或 ClamAV 安全告警，不一定是确认感染。
- 扫描不能保证发现所有恶意内容，后缀规则也不递归检查压缩包成员；压缩包内容交由 ClamAV 检查。请勿执行用户文件，保持病毒库更新。

## Ubuntu 安全部署

以下在项目根目录执行，建议至少 4 GB 内存；实际内存需求取决于病毒库。只部署文件共享程序，不开放 ClamAV 网络端口。

```bash
sudo apt update
sudo apt install -y python3 python3-venv clamav clamav-freshclam
sudo systemctl stop clamav-freshclam
sudo freshclam
sudo systemctl enable --now clamav-freshclam
sudo useradd --system --user-group --home-dir /nonexistent --shell /usr/sbin/nologin cfs
sudo mkdir -p /opt/shared-file-server /etc/shared-file-server
sudo cp -r server /opt/shared-file-server/
sudo python3 -m venv /opt/shared-file-server/server/.venv
sudo /opt/shared-file-server/server/.venv/bin/pip install -r /opt/shared-file-server/server/requirements.txt
sudo cp deploy/server.env.example /etc/shared-file-server/server.env
sudo chmod 600 /etc/shared-file-server/server.env
sudo nano /etc/shared-file-server/server.env
```

将示例密钥、密码替换为随机强值（可用 `openssl rand -hex 32` 生成密钥）。首次创建用户后修改默认密码环境变量不会重置数据库中已有用户密码。

```bash
sudo cp deploy/shared-file-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now shared-file-server
sudo systemctl status shared-file-server
sudo journalctl -u shared-file-server -n 50
```

此配置使用独立低权限账户、只读程序目录和专用可写数据目录。不要将 storage 映射为静态资源目录，否则会绕过权限与下载复查。外网使用需要另行配置 HTTPS 反向代理；反向代理请求体限制至少覆盖上传上限及 multipart 开销，读取超时应大于 120 秒。

已有数据迁移前停止旧服务、备份 SQLite 与 storage，将旧数据目录内容复制到 `/var/lib/shared-file-server` 并设置所有者 `cfs:cfs`；新路径必须包含原来的 `app.db` 与 `storage`。不要同时运行旧新服务。

## 配置与验收

`CFS_ANTIVIRUS_ENABLED` 默认 `true`，只有明确设为 `false` 才关闭病毒扫描（类型防护仍保留）。仅限无 ClamAV 的本地开发，不可用于实际部署。`CFS_CLAMSCAN_PATH` 指定程序路径，不能附带命令参数。`CFS_SCAN_TIMEOUT` 默认 120 秒，客户端默认等待 150 秒，增大前者时也需调整客户端。

`/health` 仅表示 API 可访问，不表示病毒扫描可用。部署后实际上传普通文本应成功；用 [ClamAV 官方测试说明](https://docs.clamav.net/manual/Usage/Scanning.html) 中的无害 EICAR 测试文件验证拒绝响应、空临时目录和失败日志；不要下载真实恶意软件。用不存在的 `CFS_CLAMSCAN_PATH` 重启后应拒绝普通文本上传，验证完恢复配置。

```bash
cd server
python -m pytest -q
```

自动测试模拟 ClamAV 的退出码、程序缺失和超时，覆盖清理、日志、风险类型、下载复查与并发限额；真实引擎及病毒库需要在目标 Ubuntu 上按上述步骤验收。
