<div align="center">

# [jmComicCheckIn](https://github.com/YsKiKi/jmComicCheckIn)

**JMComic 自动签到服务**

每天自动登录禁漫天堂并完成打卡签到，支持多账号、定时执行、失败重试与多渠道通知。

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat)]()
[![GitHub Repo stars](https://img.shields.io/github/stars/YsKiKi/jmComicCheckIn?style=flat&color=yellow)](https://github.com/YsKiKi/jmComicCheckIn)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

</div>

## ✨ 功能特性

- ✅ 每日自动登录并完成打卡签到，失败自动重试
- ✅ 多账号支持，独立配置、统一汇总结果
- ✅ 定时执行 + 随机延迟，避免规律化
- ✅ 多渠道结果通知：PushPlus / Server酱 / 通用 Webhook
- ✅ 密码支持 `${ENV_VAR}` 环境变量占位，避免明文入库
- ✅ 一次性 / 常驻两种运行模式，适配计划任务与 CI

## 🚀 快速开始

```bash
git clone https://github.com/YsKiKi/jmComicCheckIn
cd jmComicCheckIn
pip install -r requirements.txt        # 需要 Python 3.12+
copy config.example.yml config.yml     # 复制配置并填写配置项
python run.py --once                   # 单次执行
```

## 🎮 使用

| 命令 | 说明 |
| --- | --- |
| `python run.py --once` | 单次执行后退出 |
| `python run.py` | 常驻运行，每天按 `schedule.time` 自动签到 |
| `python run.py --test-notify` | 发送测试通知，验证通知配置 |
| `python run.py --once -v` | 调试模式，输出详细日志 |

命令行参数：

| 参数 | 简写 | 说明 |
| --- | --- | --- |
| `--config` | `-c` | 配置文件路径，默认 `./config.yml` |
| `--once` | — | 只签到一次后退出 |
| `--test-notify` | — | 发送一条测试通知并退出 |
| `--verbose` | `-v` | 输出调试日志 |

> `--once` 模式下签到失败时进程退出码为 `1`，方便配合任务系统做失败告警。

## ⚙️ 配置

复制 `config.example.yml` 为 `config.yml` 并填写账号，所有配置项说明见文件内注释：

```yaml
accounts:
  - username: your_username
    password: "${JM_PASSWORD}"   # 密码支持 ${环境变量} 占位

schedule:
  time: "08:00"                  # 每天签到时间（24 小时制）
  timezone: "Asia/Shanghai"

notify:                          # 可选：签到结果通知
  - type: pushplus
    token: "你的token"
```

### 密码环境变量

密码支持 `${ENV_VAR}` 环境变量占位，避免明文保存：

```bash
# Windows PowerShell
$env:JM_PASSWORD="你的密码"
python run.py --once

# Linux / macOS
export JM_PASSWORD="你的密码"
python run.py --once
```

若占位符未能解析，服务会直接报错并退出，不会把字面量发给服务器。

### 通知渠道

| 渠道 | `type` | 字段 | 获取 token |
| --- | --- | --- | --- |
| PushPlus | `pushplus` | `token` | <https://www.pushplus.plus> |
| Server酱 | `serverchan` | `sendkey` | <https://sct.ftqq.com> |
| 通用 Webhook | `webhook` | `url` | POST JSON `{title, content}` |

## 🐳 部署

### Docker / Docker Compose

拉取项目后，先复制示例配置并填写账号（`docker-compose.yml` 会把根目录的 `config.yml` 挂载进容器，缺少该文件无法启动）：

```bash
copy config.example.yml config.yml   # Windows
# cp config.example.yml config.yml   # Linux / macOS
# 编辑 config.yml，填写 username / password
```

然后在项目根目录执行：

```bash
docker compose up -d    # 常驻模式，每天自动签到
```

### Windows 任务计划程序

```powershell
schtasks /Create /TN "JMCheckIn" /TR "python D:\<路径>\run.py --once --config D:\路径\config.yml" /SC DAILY /ST 08:00
```

### Linux systemd

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

### GitHub Actions

Fork 本仓库，在仓库 `Settings → Secrets and variables → Actions` 中配置 **项目** Secrets：

| Secret | 必填 | 说明 |
| --- | --- | --- |
| `JM_USERNAME` | ✅ | 禁漫天堂用户名 |
| `JM_PASSWORD` | ✅ | 禁漫天堂密码 |
| `PUSHPLUS_TOKEN` | 可选 | PushPlus 通知 token |

工作流程 `.github/workflows/jm-checkin.yml` 每天北京时间 08:00（UTC 0:00）自动签到，也可在 Actions 页面手动触发。

## 📄 许可证

本项目采用 [MIT License](./LICENSE)

基于 [hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)  
签到接口参考 [tonquer/JMComic-qt](https://github.com/tonquer/JMComic-qt)

## ⚠️ 免责声明

本项目仅供学习交流使用，请勿用于任何违反平台服务条款的行为；使用本项目产生的一切后果由使用者自行承担。
