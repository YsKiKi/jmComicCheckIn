"""加载与校验 config.yml 配置"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import yaml

logger = logging.getLogger('jmcheckin.config')

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


def _collect_unresolved(value: Any, path: str, out: List[str]):
    """收集替换后仍未解析的 ${VAR} 占位符，避免把字面量当作真实值使用"""
    if isinstance(value, str):
        for m in _ENV_PATTERN.finditer(value):
            out.append(f'{path}: {m.group(0)}' if path else m.group(0))
    elif isinstance(value, dict):
        for k, v in value.items():
            _collect_unresolved(v, f'{path}.{k}' if path else str(k), out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _collect_unresolved(v, f'{path}[{i}]', out)


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

    # 快速失败：环境变量缺失时直接报错，而不是把 ${VAR} 字面量发给服务器
    unresolved: List[str] = []
    _collect_unresolved(raw, '', unresolved)
    if unresolved:
        raise ConfigError(
            '以下环境变量占位符未解析，请设置对应环境变量'
            '（GitHub Actions 中请检查仓库 Secrets 配置）: '
            + ', '.join(unresolved)
        )

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
        notifier = Notifier(
            type=ntype,
            token=str(item.get('token', '')).strip(),
            sendkey=str(item.get('sendkey', '')).strip(),
            url=str(item.get('url', '')).strip(),
        )
        # 缺少凭证的渠道直接跳过，避免空 token 造成的无效请求
        if ntype == 'pushplus' and not notifier.token:
            logger.warning('pushplus 未配置 token，已跳过该通知渠道')
            continue
        if ntype == 'serverchan' and not notifier.sendkey:
            logger.warning('serverchan 未配置 sendkey，已跳过该通知渠道')
            continue
        if ntype == 'webhook' and not notifier.url:
            logger.warning('webhook 未配置 url，已跳过该通知渠道')
            continue
        cfg.notifiers.append(notifier)

    if raw.get('option_file'):
        cfg.option_file = str(raw['option_file'])

    return cfg
