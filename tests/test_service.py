"""service.py 的单元测试"""
import datetime as dt

import pytest
from zoneinfo import ZoneInfoNotFoundError

from jm_checkin import service as service_mod
from jm_checkin.config import Account, Config, ConfigError, Notifier, Schedule
from jm_checkin.service import (
    AccountResult,
    _next_run_delay,
    format_report,
    run_account,
    run_once,
)


def test_run_account_ok(monkeypatch):
    class _FakeClient:
        def __init__(self, option_file):
            self.option_file = option_file

        def login(self, username, password):
            pass

        def check_in(self):
            return {'status': 'ok', 'msg': '签到成功'}

    monkeypatch.setattr(service_mod, 'JMCheckinClient', _FakeClient)
    cfg = Config(accounts=[Account('alice', 'p')])
    result = run_account(cfg, cfg.accounts[0])
    assert result.account == 'alice'
    assert result.status == 'ok'
    assert result.message == '签到成功'


def test_run_account_already(monkeypatch):
    class _FakeClient:
        def __init__(self, option_file):
            pass

        def login(self, username, password):
            pass

        def check_in(self):
            return {'status': 'already'}

    monkeypatch.setattr(service_mod, 'JMCheckinClient', _FakeClient)
    cfg = Config(accounts=[Account('alice', 'p')])
    result = run_account(cfg, cfg.accounts[0])
    assert result.status == 'already'


def test_run_account_failed(monkeypatch):
    class _FakeClient:
        def __init__(self, option_file):
            pass

        def login(self, username, password):
            raise service_mod.JMCheckinError('登录失败')

    monkeypatch.setattr(service_mod, 'JMCheckinClient', _FakeClient)
    cfg = Config(accounts=[Account('alice', 'p')])
    result = run_account(cfg, cfg.accounts[0])
    assert result.status == 'failed'
    assert '登录失败' in result.message


def test_run_account_unexpected_exception(monkeypatch):
    class _FakeClient:
        def __init__(self, option_file):
            pass

        def login(self, username, password):
            raise ValueError('未知错误')

    monkeypatch.setattr(service_mod, 'JMCheckinClient', _FakeClient)
    cfg = Config(accounts=[Account('alice', 'p')])
    result = run_account(cfg, cfg.accounts[0])
    assert result.status == 'failed'
    assert '未知异常' in result.message


def test_format_report():
    report = format_report([
        AccountResult('a', 'ok', '签到成功'),
        AccountResult('b', 'already', '今日已签到'),
        AccountResult('c', 'failed', '登录失败'),
    ])
    assert '✅ a' in report
    assert '⏭️ b' in report
    assert '❌ c' in report


def test_run_once_sends_notifications(monkeypatch):
    monkeypatch.setattr(
        service_mod, 'run_account',
        lambda cfg, acc: AccountResult(acc.label, 'ok', 'ok'),
    )
    sent = []
    monkeypatch.setattr(
        service_mod, 'send_notifications',
        lambda notifiers, title, content: sent.append((notifiers, title, content)),
    )
    cfg = Config(
        accounts=[Account('alice', 'p')],
        notifiers=[Notifier(type='webhook', url='https://example.com/h')],
    )
    results = run_once(cfg)
    assert [r.status for r in results] == ['ok']
    assert len(sent) == 1


def test_next_run_delay_invalid_timezone():
    with pytest.raises(ZoneInfoNotFoundError):
        _next_run_delay(Schedule(timezone='Not/AZone'))


def test_next_run_delay_invalid_time():
    with pytest.raises(ConfigError, match='无效的签到时间'):
        _next_run_delay(Schedule(time='25:00'))


def test_next_run_delay_within_a_day():
    delay = _next_run_delay(Schedule(time='08:00', timezone='Asia/Shanghai', jitter_seconds=0))
    assert dt.timedelta(0) < delay <= dt.timedelta(days=1)
