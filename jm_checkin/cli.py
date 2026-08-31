"""命令行入口"""
from __future__ import annotations

import argparse
import logging
import sys

from .config import ConfigError, load_config
from .notify import send_notifications
from .service import run_daemon, run_once

logger = logging.getLogger('jmcheckin')

DEFAULT_CONFIG = 'config.yml'


def setup_logging(verbose: bool):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def build_parser():
    parser = argparse.ArgumentParser(description='禁漫天堂自动签到服务')
    parser.add_argument(
        '--config', '-c',
        default=DEFAULT_CONFIG,
        help='配置文件路径，默认 ./config.yml',
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='只签到一次后退出（适合计划任务 / GitHub Actions）',
    )
    parser.add_argument(
        '--test-notify',
        action='store_true',
        help='发送一条测试通知并退出',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='输出调试日志',
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging(args.verbose)

    try:
        cfg = load_config(args.config)
    except ConfigError as e:
        print(f'[配置错误] {e}', file=sys.stderr)
        return 2

    if args.test_notify:
        if not cfg.notifiers:
            print('未配置 notify，无需测试', file=sys.stderr)
            return 1
        send_notifications(
            cfg.notifiers,
            '禁漫签到测试通知',
            '这是一条测试消息，收到即代表通知配置正确 ✅',
        )
        return 0

    if args.once:
        results = run_once(cfg)
        return 0 if all(r.status != 'failed' for r in results) else 1

    run_daemon(cfg)
    return 0
