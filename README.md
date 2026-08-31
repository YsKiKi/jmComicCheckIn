# jmComicCheckIn —— 禁漫天堂自动签到服务

每天自动登录禁漫天堂并完成打卡签到，支持多账号、定时执行、失败重试与结果推送。

## 实现原理

- 登录与接口调用基于 [JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)（`jmcomic`）的移动端 API 客户端：
  - 自动处理 APP 接口的 `token` / `tokenparam` 加解密；
  - 自动更新最新 API 域名、自动携带 cookies，无需对抗 Cloudflare。
- 签到接口路径参考 [JMComic-qt](https://github.com/tonquer/JMComic-qt) 客户端实现：

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/login` | POST | 登录，返回 `uid` 与 `s`（即 AVS cookie） |
| `/daily?user_id={uid}` | GET | 查询当月签到记录，返回 `daily_id` |
| `/daily_chk` | POST | 提交签到，参数 `user_id`、`daily_id` |

工作流程：登录 → 查询今日是否已签到 → 未签到则调用 `/daily_chk` 打卡 → 输出/推送结果。

## 安装

```bash
pip install -r requirements.txt
```

## 配置

复制示例配置并填写账号：

```bash
copy config.example.yml config.yml     # Windows
cp config.example.yml config.yml       # Linux / macOS
```

配置项说明见 `config.example.yml` 内注释。密码支持 `${ENV_VAR}` 环境变量占位，例如：

```bash
set JM_PASSWORD=你的密码        # Windows PowerShell: $env:JM_PASSWORD="你的密码"
python run.py --once
```

## 使用

```bash
python run.py --once           # 立即签到一次后退出（适合计划任务 / GitHub Actions）
python run.py                  # 常驻运行，每天按 schedule.time 自动签到
python run.py --test-notify    # 测试通知配置
python run.py --once -v        # 调试模式，输出详细日志
```

签到失败时（`--once` 模式）进程退出码为 1，方便配合任务系统做失败告警。

## 部署方式

### 1. Windows 任务计划程序

```powershell
schtasks /Create /TN "JMCheckIn" /TR "python D:\路径\run.py --once --config D:\路径\config.yml" /SC DAILY /ST 08:00
```

### 2. Docker / Docker Compose

```bash
docker compose up -d          # 常驻模式，每天自动签到
```

### 3. Linux systemd（可选）

```ini
[Unit]
Description=JM Comic check-in service
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/jmComicCheckIn
ExecStart=/usr/bin/python3 run.py --config /opt/jmComicCheckIn/config.yml
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. GitHub Actions

推送到 GitHub 后，在仓库 `Settings → Secrets and variables → Actions` 中配置以下 Secrets：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `JM_USERNAME` | ✅ | 禁漫天堂用户名 |
| `JM_PASSWORD` | ✅ | 禁漫天堂密码 |
| `PUSHPLUS_TOKEN` | 可选 | PushPlus 通知 token |

工作流 `.github/workflows/jm-checkin.yml` 会每天北京时间 08:00（UTC 0:00）自动执行签到，也可在 Actions 页面手动触发。

## 项目结构

```
jmComicCheckIn/
├── run.py                     # 入口脚本
├── config.example.yml         # 配置示例（复制为 config.yml 使用）
├── requirements.txt
├── Dockerfile / docker-compose.yml
├── .github/workflows/jm-checkin.yml   # GitHub Actions 定时任务
└── jm_checkin/
    ├── cli.py                 # 命令行参数与入口
    ├── config.py              # 配置加载（支持环境变量占位）
    ├── client.py              # 登录 + 签到接口封装（基于 jmcomic）
    ├── service.py             # 一次性执行 / 常驻定时守护
    └── notify.py              # PushPlus / Server酱 / Webhook 通知
```

## 免责声明

本项目仅供学习交流使用，请勿用于任何违反平台服务条款的行为；使用本项目产生的一切后果由使用者自行承担。
