"""禁漫签到客户端

基于 jmcomic 库（hect0x7/JMComic-Crawler-Python）的移动端 API 客户端：
  - 自动处理 APP 接口 token / tokenparam 加解密
  - 自动更新最新 API 域名、自动携带 cookies，无需对抗 Cloudflare

签到接口路径参考 tonquer/JMComic-qt 客户端实现：
  - 登录:     POST /login
  - 查询签到: GET  /daily?user_id={uid}
  - 执行签到: POST /daily_chk  (form: user_id, daily_id)
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, Optional

from jmcomic import JmOption, create_option_by_file

logger = logging.getLogger('jmcheckin.client')


class JMCheckinError(Exception):
    """签到业务错误"""


class JMCheckinClient:
    """封装 jmcomic 的 api client，提供登录与签到能力"""

    def __init__(self, option_file: Optional[str] = None):
        if option_file:
            self.option = create_option_by_file(option_file)
        else:
            # 默认配置 + 关闭 jmcomic 内部日志，保持服务日志干净
            self.option = JmOption.construct({'log': False})
        # 使用移动端 api 实现：兼容性好，自带接口加解密
        self.client = self.option.build_jm_client(impl='api')
        self.uid: Optional[str] = None

    def login(self, username: str, password: str) -> Dict[str, Any]:
        resp = self.client.login(username, password)
        data: Dict[str, Any] = resp.res_data
        uid = data.get('uid')
        if uid is None:
            raise JMCheckinError('登录响应中缺少 uid，登录失败')
        self.uid = str(uid)
        logger.info('账号 %s 登录成功 (uid=%s)', username, self.uid)
        return data

    def get_daily(self) -> Dict[str, Any]:
        resp = self.client.req_api(f'/daily?user_id={self.uid}')
        return resp.res_data

    @staticmethod
    def is_signed_today(data: Dict[str, Any]) -> bool:
        """判断今天是否已签到。

        record 为当月签到日历: [[{date: 日, signed: bool}, ...], ...]
        """
        today = dt.date.today().day
        if data.get('signed') is True:
            return True
        for group in data.get('record') or []:
            for item in group or []:
                if not isinstance(item, dict):
                    continue
                try:
                    day = int(item.get('date'))
                except (TypeError, ValueError):
                    continue
                if day == today:
                    return bool(item.get('signed'))
        return False

    def check_in(self) -> Dict[str, Any]:
        daily = self.get_daily()
        daily_id = daily.get('daily_id')

        if self.is_signed_today(daily):
            logger.info('今日已签到，无需重复签到')
            return {'status': 'already', 'detail': daily}

        if not daily_id:
            raise JMCheckinError('未获取到 daily_id，无法签到')

        resp = self.client.req_api(
            '/daily_chk',
            get=False,
            require_success=False,
            data={'user_id': self.uid, 'daily_id': daily_id},
        )

        if not resp.is_success:
            msg = ''
            try:
                msg = str(resp.res_data.get('msg', ''))
            except Exception:
                pass
            raise JMCheckinError(f'签到接口返回异常: {msg or resp.text[:200]}')

        data: Dict[str, Any] = resp.res_data
        logger.info('签到成功: %s', data.get('msg', ''))
        return {'status': 'ok', 'msg': data.get('msg', ''), 'detail': data}
