"""可选的通知渠道：PushPlus / Server酱 / 通用 Webhook"""
from __future__ import annotations

import logging
from typing import List

import requests

from .config import Notifier

logger = logging.getLogger('jmcheckin.notify')

_TIMEOUT = 15


def _send_pushplus(n: Notifier, title: str, content: str):
    resp = requests.post(
        'https://www.pushplus.plus/send',
        json={
            'token': n.token,
            'title': title,
            'content': content,
            'template': 'markdown',
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 200:
        raise RuntimeError(f"pushplus 返回错误: {data.get('msg', data)}")


def _send_serverchan(n: Notifier, title: str, content: str):
    resp = requests.post(
        f'https://sctapi.ftqq.com/{n.sendkey}.send',
        data={'title': title, 'desp': content},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get('code') != 0:
        raise RuntimeError(f"server酱 返回错误: {data.get('message', data)}")


def _send_webhook(n: Notifier, title: str, content: str):
    resp = requests.post(
        n.url,
        json={'title': title, 'content': content},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()


def send_notifications(notifiers: List[Notifier], title: str, content: str):
    """逐条发送通知，单条失败不影响其它渠道"""
    for n in notifiers:
        try:
            if n.type == 'pushplus':
                _send_pushplus(n, title, content)
            elif n.type == 'serverchan':
                _send_serverchan(n, title, content)
            elif n.type == 'webhook':
                _send_webhook(n, title, content)
            else:
                logger.warning('未知通知类型: %s，已跳过', n.type)
                continue
            logger.info('通知已发送: %s', n.type)
        except Exception as e:
            logger.warning('通知发送失败 [%s]: %s', n.type, e)
