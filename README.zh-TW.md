<div align="center">

**JMComic 自動簽到服務**

每天自動登入禁漫天堂並完成打卡簽到，支援多帳號、定時執行、失敗重試與多管道通知。

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat)
[![GitHub Repo stars](https://img.shields.io/github/stars/YsKiKi/jmComicCheckIn?style=flat&color=yellow)](https://github.com/YsKiKi/jmComicCheckIn)
[![GitHub forks](https://img.shields.io/github/forks/YsKiKi/jmComicCheckIn?style=flat&color=blue)](https://github.com/YsKiKi/jmComicCheckIn)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

</div>

**語言 / Language:** [简体中文](./README.md) | [繁體中文](./README.zh-TW.md) | [English](./README.en.md)

## ✨ 功能特點

- ✅ 每日自動登入並完成打卡簽到，常駐模式下失敗自動重試
- ✅ 多帳號支援，獨立配置、統一彙總結果
- ✅ 定時執行 + 隨機延遲，避免規律化
- ✅ 多管道結果通知：PushPlus / Server醬 / 通用 Webhook
- ✅ 密碼支援 `${ENV_VAR}` 環境變數佔位，避免明文入庫
- ✅ 一次性 / 常駐兩種執行模式，適用於排程任務與 CI

## 🚀 快速開始

> [!NOTE]
> 自架部署（本機執行 / Docker）可能因網路環境影響導致簽到失敗。  
> 若無法穩定存取禁漫 API，建議直接使用 **GitHub Actions 雲端自動簽到**，穩定定時執行、省心免維運。

**Fork 本倉庫**：點擊右上角 **Fork**，將倉庫複製到你自己的 GitHub 帳號下，然後依需求選擇下列任一方式。

### ① GitHub Actions 雲端自動簽到（推薦）

無需本機環境，每天定時自動執行，適合正式使用：

1. 進入 Fork 後倉庫的 `Settings → Secrets and variables → Actions`。
2. 新增以下 **Actions secrets**：

   | Secret           | 必填 | 說明                |
   | ---------------- | ---- | ------------------- |
   | `JM_USERNAME`    | ✅    | 禁漫天堂使用者名稱  |
   | `JM_PASSWORD`    | ✅    | 禁漫天堂密碼        |
   | `PUSHPLUS_TOKEN` | 選填 | PushPlus 通知 token |

3. 完成。工作流程 `.github/workflows/jm-checkin.yml` 每天台北時間 08:00（UTC 0:00）自動簽到，也可在 Actions 頁面手動觸發執行。

### ② 本機 / Docker 自架部署

複製倉庫並準備設定檔（指令依平台選用）：

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

編輯 `config.yml` 填寫帳號和密碼。  
> 設定項目說明見檔案內註解，或下方摺疊區「使用與設定」。

#### Python 直接執行
```bash
pip install -r requirements.txt
python run.py --once     # 單次簽到後退出，用於驗證
python run.py            # 常駐執行，每天依 schedule.time 自動簽到
```

#### Docker Compose

> [!IMPORTANT]
> `docker-compose.yml` 會把根目錄的 `config.yml` 掛載進容器  
> 請務必確保根目錄下存在 `config.yml` 檔案，否則容器將無法啟動。

```bash
docker compose up -d     # 常駐模式，每天自動簽到
```

#### 排程任務（選用）

除常駐執行外，也可用 `python run.py --once` 交由系統排程器定時執行：

**Windows 工作排程器**

```powershell
schtasks /Create /TN "JMCheckIn" /TR "python D:\<路徑>\run.py --once --config D:\<路徑>\config.yml" /SC DAILY /ST 08:00
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
<summary>⚙️ 使用與設定</summary>

### 命令列用法

| 命令                          | 說明                                      |
| ----------------------------- | ----------------------------------------- |
| `python run.py --once`        | 單次執行後退出                            |
| `python run.py`               | 常駐執行，每天依 `schedule.time` 自動簽到 |
| `python run.py --test-notify` | 傳送測試通知，驗證通知設定                |
| `python run.py --once -v`     | 除錯模式，輸出詳細日誌                    |

命令列參數：

| 參數            | 簡寫 | 說明                              |
| --------------- | ---- | --------------------------------- |
| `--config`      | `-c` | 設定檔路徑，預設 `./config.yml`   |
| `--once`        | —    | 只簽到一次後退出                  |
| `--test-notify` | —    | 傳送一條測試通知並退出            |
| `--verbose`     | `-v` | 輸出除錯日誌                      |

> `--once` 模式下簽到失敗時程序退出碼為 `1`，方便搭配任務系統做失敗告警。

### 設定檔

複製 `config.example.yml` 為 `config.yml` 並填寫帳號，所有設定項目說明見檔案內註解：

```yaml
accounts:
  - username: your_username
    password: "${JM_PASSWORD}"   # 密碼支援 ${環境變數} 佔位

schedule:
  time: "08:00"                  # 每天簽到時間（24 小時制）
  timezone: "Asia/Shanghai"

notify:                          # 選用：簽到結果通知
  - type: pushplus
    token: "你的token"
```

#### 密碼環境變數

密碼支援 `${ENV_VAR}` 環境變數佔位，避免明文儲存：

```bash
# Windows PowerShell
$env:JM_PASSWORD="你的密碼"
python run.py --once

# Linux / macOS
export JM_PASSWORD="你的密碼"
python run.py --once
```

若佔位符未能解析，服務會直接報錯並退出，不會把字面值送給伺服器。

#### 通知管道

| 管道         | `type`       | 欄位      | 取得 token                  |
| ------------ | ------------ | --------- | --------------------------- |
| PushPlus     | `pushplus`   | `token`   | <https://www.pushplus.plus> |
| Server醬     | `serverchan` | `sendkey` | <https://sct.ftqq.com>      |
| 通用 Webhook | `webhook`    | `url`     | POST JSON `{title, content}` |

</details>

## ⭐ 支援本專案

如果本專案對你有幫助，歡迎點擊 [本倉庫](https://github.com/YsKiKi/jmComicCheckIn) 右上角的 **Star** 支持一下。  

## 📄 授權

本專案採用 [MIT License](./LICENSE)

基於 [hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)  
感謝 [tonquer/JMComic-qt](https://github.com/tonquer/JMComic-qt) 提供的簽到介面思路

## ⚠️ 免責聲明

本專案僅供學習交流使用，請勿用於任何違反平台服務條款的行為；使用本專案產生的一切後果由使用者自行承擔。
