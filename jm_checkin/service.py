"""签到服务：一次性执行与常驻定时守护"""
from __future__ import annotations

import datetime as dt
import logging
import random
import time
from dataclasses import dataclass
from typing import List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .client import JMCheckinClient, JMCheckinError
from .config import Account, Config, Schedule
from .notify import send_notifications

logger = logging.getLogger('jmcheckin')


@dataclass
class AccountResult:
    account: str
    status: str  # ok / already / failed
    message: str


def run_account(cfg: Config, account: Account) -> AccountResult:
    try:
        client = JMCheckinClient(cfg.option_file)
        client.login(account.username, account.password)
        result = client.check_in()
    except JMCheckinError as e:
        logger.error('账号 %s 签到失败: %s', account.label, e)
        return AccountResult(account.label, 'failed', str(e))
    except Exception as e:
        logger.exception('账号 %s 签到出现未知异常', account.label)
        return AccountResult(account.label, 'failed', f'未知异常: {e}')

    if result['status'] == 'already':
        return AccountResult(account.label, 'already', '今日已签到')
    msg = str(result.get('msg') or '签到成功')
    return AccountResult(account.label, 'ok', msg)


def format_report(results: List[AccountResult]) -> str:
    emoji = {'ok': '✅', 'already': '⏭️', 'failed': '❌'}
    return '\n'.join(f"{emoji[r.status]} {r.account}：{r.message}" for r in results)


def run_once(cfg: Config) -> List[AccountResult]:
    results = [run_account(cfg, account) for account in cfg.accounts]
    title = f'{dt.date.today().isoformat()} 禁漫签到结果'
    report = format_report(results)
    logger.info('%s\n%s', title, report)
    if cfg.notifiers:
        try:
            send_notifications(cfg.notifiers, title, report)
        except Exception as e:
            logger.warning('通知发送异常: %s', e)
    return results


def _next_run_delay(schedule: Schedule) -> dt.timedelta:
    try:
        tz = ZoneInfo(schedule.timezone)
    except ZoneInfoNotFoundError:
        raise
    hh, mm = schedule.hour_minute()
    now = dt.datetime.now(tz)
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)
    jitter = random.uniform(0, schedule.jitter_seconds) if schedule.jitter_seconds > 0 else 0.0
    return (target - now) + dt.timedelta(seconds=jitter)


def _sleep_interruptible(seconds: float):
    """分段睡眠，便于 Ctrl+C 及时退出"""
    while seconds > 0:
        time.sleep(min(seconds, 600))
        seconds -= 600


def run_daemon(cfg: Config):
    if cfg.schedule.run_on_start:
        run_once(cfg)

    while True:
        delay = _next_run_delay(cfg.schedule)
        logger.info('下一次签到: 约 %s 后', str(delay).split('.')[0])
        _sleep_interruptible(delay.total_seconds())

        for attempt in range(cfg.schedule.max_retries + 1):
            results = run_once(cfg)
            if all(r.status != 'failed' for r in results):
                break
            if attempt < cfg.schedule.max_retries:
                wait = cfg.schedule.retry_interval_minutes * 60
                logger.warning(
                    '存在失败账号，%d 分钟后重试 (%d/%d)',
                    cfg.schedule.retry_interval_minutes,
                    attempt + 1,
                    cfg.schedule.max_retries,
                )
                _sleep_interruptible(wait)
