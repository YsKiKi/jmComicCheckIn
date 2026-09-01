"""notify.py 的单元测试"""
from jm_checkin import notify as notify_mod
from jm_checkin.config import Notifier


class _Resp:
    def __init__(self, json_data):
        self._json = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


def test_send_notifications_all_channels(monkeypatch):
    calls = []
    payloads = {}

    def fake_post(url, **kwargs):
        calls.append(url)
        payloads[url] = kwargs
        if url.startswith('https://www.pushplus.plus'):
            return _Resp({'code': 200})
        if url.startswith('https://sctapi.ftqq.com'):
            return _Resp({'code': 0})
        return _Resp({})

    monkeypatch.setattr(notify_mod.requests, 'post', fake_post)

    notifiers = [
        Notifier(type='pushplus', token='TOKEN1'),
        Notifier(type='serverchan', sendkey='SK1'),
        Notifier(type='webhook', url='https://example.com/hook'),
    ]
    notify_mod.send_notifications(notifiers, '标题', '内容')

    assert calls == [
        'https://www.pushplus.plus/send',
        'https://sctapi.ftqq.com/SK1.send',
        'https://example.com/hook',
    ]
    pushplus_payload = payloads['https://www.pushplus.plus/send']['json']
    assert pushplus_payload['token'] == 'TOKEN1'
    assert pushplus_payload['title'] == '标题'


def test_one_channel_failure_does_not_stop_others(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        if 'pushplus' in url:
            raise RuntimeError('网络错误')
        return _Resp({})

    monkeypatch.setattr(notify_mod.requests, 'post', fake_post)

    notify_mod.send_notifications(
        [Notifier(type='pushplus', token='T'), Notifier(type='webhook', url='https://example.com/h')],
        't', 'c',
    )
    assert len(calls) == 2
    assert 'https://example.com/h' in calls


def test_channel_error_is_swallowed(monkeypatch):
    """渠道返回业务错误码时不抛出异常"""
    monkeypatch.setattr(
        notify_mod.requests, 'post',
        lambda url, **kwargs: _Resp({'code': 500, 'msg': 'token 无效'}),
    )
    notify_mod.send_notifications([Notifier(type='pushplus', token='T')], 't', 'c')
