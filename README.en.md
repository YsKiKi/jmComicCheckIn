<div align="center">

**JMComic Auto Check-in Service**

Automatically logs in to JMComic (禁漫天堂) and completes the daily check-in. Supports multiple accounts, scheduled execution, retry on failure, and multi-channel notifications.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat)
[![GitHub Repo stars](https://img.shields.io/github/stars/YsKiKi/jmComicCheckIn?style=flat&color=yellow)](https://github.com/YsKiKi/jmComicCheckIn)
[![GitHub forks](https://img.shields.io/github/forks/YsKiKi/jmComicCheckIn?style=flat&color=blue)](https://github.com/YsKiKi/jmComicCheckIn)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

</div>

**Languages:** [简体中文](./README.md) | [繁體中文](./README.zh-TW.md) | [English](./README.en.md)

## ✨ Features

- ✅ Daily automatic login and check-in, with automatic retry on failure in resident mode
- ✅ Multiple account support with independent configuration and unified result summary
- ✅ Scheduled execution + random delay to avoid regular patterns
- ✅ Multi-channel result notifications: PushPlus / ServerChan / Generic Webhook
- ✅ Password supports `${ENV_VAR}` environment variable placeholders to avoid storing plaintext
- ✅ Two run modes — one-shot / resident — suitable for scheduled tasks and CI

## 🚀 Quick Start

> [!NOTE]
> Self-hosting (local / Docker) may fail due to network conditions.  
> If you cannot reliably reach the JMComic API, we recommend **GitHub Actions cloud check-in** for stable scheduled execution with zero maintenance.

**Fork this repository**: click **Fork** in the top-right corner to copy it to your own GitHub account, then choose any of the options below.

### ① GitHub Actions Cloud Check-in (Recommended)

No local environment required — runs automatically on a daily schedule, ideal for production use:

1. Go to `Settings → Secrets and variables → Actions` in your forked repository.
2. Add the following **Actions secrets**:

   | Secret           | Required | Description               |
   | ---------------- | -------- | ------------------------- |
   | `JM_USERNAME`    | ✅        | JMComic username          |
   | `JM_PASSWORD`    | ✅        | JMComic password          |
   | `PUSHPLUS_TOKEN` | Optional | PushPlus notification token |

3. Done. The workflow `.github/workflows/jm-checkin.yml` runs automatically at 08:00 Beijing Time (UTC 0:00) every day; you can also trigger it manually from the Actions page.

### ② Local / Docker Self-hosting

Clone the repository and prepare the config file (choose the command for your platform):

```bash
git clone https://github.com/YsKiKi/jmComicCheckIn
cd jmComicCheckIn
```

#### Windows
```pwsh
copy config.example.yml config.yml
```

#### Linux / MacOS
```bash
cp config.example.yml config.yml
```

Edit `config.yml` and fill in your account and password.  
> See the in-file comments for each config option, or the collapsible "Usage & Configuration" section below.

#### Run with Python
```bash
pip install -r requirements.txt
python run.py --once     # Check in once and exit, for verification
python run.py            # Resident mode, checks in daily at schedule.time
```

#### Docker Compose

> [!IMPORTANT]
> `docker-compose.yml` mounts the root-level `config.yml` into the container.  
> Make sure a `config.yml` exists in the repository root, otherwise the container will fail to start.

```bash
docker compose up -d     # Resident mode, checks in daily
```

#### Scheduled Task (Optional)

Besides resident mode, you can let the system scheduler run `python run.py --once` periodically:

**Windows Task Scheduler**

```powershell
schtasks /Create /TN "JMCheckIn" /TR "python D:\<path>\run.py --once --config D:\<path>\config.yml" /SC DAILY /ST 08:00
```

**Linux systemd**

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

<details>
<summary>⚙️ Usage & Configuration</summary>

### Command-line Usage

| Command                      | Description                                   |
| ---------------------------- | --------------------------------------------- |
| `python run.py --once`       | Run once and exit                             |
| `python run.py`              | Resident mode, checks in daily at `schedule.time` |
| `python run.py --test-notify`| Send a test notification to verify config     |
| `python run.py --once -v`    | Debug mode with verbose logging               |

Command-line arguments:

| Argument        | Alias | Description                             |
| --------------- | ----- | --------------------------------------- |
| `--config`      | `-c`  | Config file path, default `./config.yml` |
| `--once`        | —     | Check in only once and exit              |
| `--test-notify` | —     | Send a test notification and exit        |
| `--verbose`     | `-v`  | Output debug logs                        |

> In `--once` mode the process exits with code `1` on failure, making it easy to alert via your task system.

### Configuration File

Copy `config.example.yml` to `config.yml` and fill in your account; see the in-file comments for all options:

```yaml
accounts:
  - username: your_username
    password: "${JM_PASSWORD}"   # Password supports ${ENV_VAR} placeholders

schedule:
  time: "08:00"                  # Daily check-in time (24-hour format)
  timezone: "Asia/Shanghai"

notify:                          # Optional: check-in result notifications
  - type: pushplus
    token: "your_token"
```

#### Password Environment Variables

Passwords support `${ENV_VAR}` environment variable placeholders to avoid storing them in plaintext:

```bash
# Windows PowerShell
$env:JM_PASSWORD="your_password"
python run.py --once

# Linux / macOS
export JM_PASSWORD="your_password"
python run.py --once
```

If a placeholder cannot be resolved, the service errors out and exits rather than sending the literal value to the server.

#### Notification Channels

| Channel       | `type`       | Field    | Get token                     |
| ------------- | ------------ | -------- | ----------------------------- |
| PushPlus      | `pushplus`   | `token`  | <https://www.pushplus.plus>   |
| ServerChan    | `serverchan` | `sendkey`| <https://sct.ftqq.com>        |
| Generic Webhook | `webhook`  | `url`    | POST JSON `{title, content}`  |

</details>

## ⭐ Support This Project

If this project helps you, feel free to give it a **Star** at the top-right of [this repository](https://github.com/YsKiKi/jmComicCheckIn).

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

Based on [hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)  
Thanks to [tonquer/JMComic-qt](https://github.com/tonquer/JMComic-qt) for the check-in API approach.

## ⚠️ Disclaimer

This project is for learning and communication purposes only. Do not use it in any way that violates platform terms of service; all consequences arising from its use are the sole responsibility of the user.
