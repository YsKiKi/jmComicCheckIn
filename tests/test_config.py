"""config.py 的单元测试"""
import textwrap
from pathlib import Path

import pytest

from jm_checkin.config import (
    Account,
    ConfigError,
    Schedule,
    _substitute_env,
    load_config,
)


def _write(tmp_path, text, name='config.yml'):
    path = tmp_path / name
    path.write_text(textwrap.dedent(text), encoding='utf-8')
    return path


def test_substitute_env(monkeypatch):
    monkeypatch.setenv('JM_PASSWORD', 's3cret')
    out = _substitute_env({
        'a': '${JM_PASSWORD}',
        'b': ['${JM_PASSWORD}', 'x'],
        'c': {'d': '${MISSING_KEEP}'},
        'e': 1,
    })
    assert out['a'] == 's3cret'
    assert out['b'] == ['s3cret', 'x']
    assert out['c']['d'] == '${MISSING_KEEP}'
    assert out['e'] == 1


def test_load_config_minimal(tmp_path, monkeypatch):
    monkeypatch.setenv('JM_PASSWORD', 'p@ss')
    path = _write(tmp_path, '''
        accounts:
          - username: alice
            password: "${JM_PASSWORD}"
    ''')
    cfg = load_config(path)
    assert len(cfg.accounts) == 1
    assert cfg.accounts[0].username == 'alice'
    assert cfg.accounts[0].password == 'p@ss'
    assert cfg.schedule.hour_minute() == (8, 0)
    assert cfg.notifiers == []


def test_load_config_missing_env_var(tmp_path, monkeypatch):
    monkeypatch.delenv('JM_PASSWORD', raising=False)
    path = _write(tmp_path, '''
        accounts:
          - username: alice
            password: "${JM_PASSWORD}"
    ''')
    with pytest.raises(ConfigError, match='JM_PASSWORD'):
        load_config(path)


def test_load_config_file_not_found(tmp_path):
    with pytest.raises(ConfigError, match='不存在'):
        load_config(tmp_path / 'no_such_file.yml')


def test_load_config_invalid_yaml(tmp_path):
    path = _write(tmp_path, 'accounts: [unclosed\n')
    with pytest.raises(ConfigError, match='解析失败'):
        load_config(path)


def test_load_config_empty(tmp_path):
    path = _write(tmp_path, '')
    with pytest.raises(ConfigError, match='为空或格式错误'):
        load_config(path)


def test_load_config_missing_accounts(tmp_path):
    path = _write(tmp_path, 'schedule:\n  time: "08:00"\n')
    with pytest.raises(ConfigError, match='accounts'):
        load_config(path)


def test_load_config_account_missing_password(tmp_path):
    path = _write(tmp_path, 'accounts:\n  - username: alice\n')
    with pytest.raises(ConfigError, match='password'):
        load_config(path)


def test_load_config_invalid_time(tmp_path, monkeypatch):
    monkeypatch.setenv('JM_PASSWORD', 'p')
    path = _write(tmp_path, '''
        accounts:
          - username: alice
            password: "${JM_PASSWORD}"
        schedule:
          time: "25:00"
    ''')
    with pytest.raises(ConfigError, match='无效的签到时间'):
        load_config(path)


def test_load_config_skips_notifier_without_credential(tmp_path, monkeypatch):
    monkeypatch.setenv('JM_PASSWORD', 'p')
    path = _write(tmp_path, '''
        accounts:
          - username: alice
            password: "${JM_PASSWORD}"
        notify:
          - type: pushplus
          - type: serverchan
            sendkey: "SCT123"
          - type: webhook
            url: "https://example.com/hook"
    ''')
    cfg = load_config(path)
    assert [n.type for n in cfg.notifiers] == ['serverchan', 'webhook']


def test_config_example_yml_loads(monkeypatch):
    """config.example.yml 能正常解析"""
    monkeypatch.setenv('JM_PASSWORD', 'example-password')
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / 'config.example.yml')
    assert cfg.accounts[0].username == 'your_username'
    assert cfg.accounts[0].password == 'example-password'


def test_account_label():
    assert Account('alice', 'p').label == 'alice'
    assert Account('alice', 'p', name='主账号').label == '主账号'


def test_schedule_invalid_time_direct():
    with pytest.raises(ConfigError, match='无效的签到时间'):
        Schedule(time='8点').hour_minute()
    with pytest.raises(ConfigError, match='无效的签到时间'):
        Schedule(time='24:00').hour_minute()
