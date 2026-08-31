"""加载与校验 config.yml 配置"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import yaml

_ENV_PATTERN = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')


class ConfigError(Exception):
    """配置错误"""


def _substitute_env(value: Any) -> Any:
    """递归地把字符串中的 ${ENV_VAR} 替换为环境变量值"""
    if isinstance(value, str):
        return _ENV_PATTERN.sub(
            lambda m: os.environ.get(m.group(1), m.group(0)), value
        )
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(v) for v in value]
    return value


@dataclass
class Account:
    username: str
    password: str
    name: str = ''

    @property
    def label(self) -> str:
        return self.name or self.username


@dataclass
class Schedule:
    time: str = '08:00'
    timezone: str = 'Asia/Shanghai'
    jitter_seconds: int = 300
    run_on_start: bool = True
    retry_interval_minutes: int = 30
    max_retries: int = 2

    def hour_minute(self):
        try:
            hh, mm = (int(part.strip()) for part in self.time.split(':'))
        except (ValueError, AttributeError):
            raise ConfigError(f'无效的签到时间: {self.time!r}，应为 HH:MM')
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ConfigError(f'无效的签到时间: {self.time!r}，应为 HH:MM')
        return hh, mm


@dataclass
class Notifier:
    type: str
    token: str = ''
    sendkey: str = ''
    url: str = ''


@dataclass
class Config:
    accounts: List[Account] = field(default_factory=list)
    schedule: Schedule = field(default_factory=Schedule)
    notifiers: List[Notifier] = field(default_factory=list)
    option_file: Optional[str] = None


def load_config(path) -> Config:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f'配置文件不存在: {path}（可参考 config.example.yml 创建）')

    try:
        raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as e:
        raise ConfigError(f'配置文件解析失败: {e}') from e

    if not raw or not isinstance(raw, dict):
        raise ConfigError('配置文件为空或格式错误')

    raw = _substitute_env(raw)

    accounts_raw = raw.get('accounts') or []
    if not accounts_raw:
        raise ConfigError('配置中缺少 accounts，请至少填写一个账号')

    cfg = Config()
    for item in accounts_raw:
        if not isinstance(item, dict):
            raise ConfigError('accounts 项必须为字典（包含 username/password）')
        username = str(item.get('username', '')).strip()
        password = str(item.get('password', '')).strip()
        if not username or not password:
            raise ConfigError('账号缺少 username 或 password')
        cfg.accounts.append(
            Account(username, password, str(item.get('name', '')).strip())
        )

    schedule_raw = raw.get('schedule') or {}
    sch = cfg.schedule
    for key in ('time', 'timezone'):
        if key in schedule_raw:
            setattr(sch, key, str(schedule_raw[key]))
    for key in ('jitter_seconds', 'retry_interval_minutes', 'max_retries'):
        if key in schedule_raw:
            setattr(sch, key, int(schedule_raw[key]))
    if 'run_on_start' in schedule_raw:
        sch.run_on_start = bool(schedule_raw['run_on_start'])
    sch.hour_minute()  # 校验时间格式

    for item in raw.get('notify') or []:
        if not isinstance(item, dict):
            raise ConfigError('notify 项必须为字典')
        ntype = str(item.get('type', '')).strip().lower()
        if not ntype:
            raise ConfigError('notify 项缺少 type')
        cfg.notifiers.append(Notifier(
            type=ntype,
            token=str(item.get('token', '')),
            sendkey=str(item.get('sendkey', '')),
            url=str(item.get('url', '')),
        ))

    if raw.get('option_file'):
        cfg.option_file = str(raw['option_file'])

    return cfg
