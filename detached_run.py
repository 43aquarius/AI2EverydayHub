#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性任务守护启动器(双 fork 脱离会话, 沙箱实测可常驻)

用法: python3 scripts/detached_run.py <工作目录> <日志文件> <命令...>
示例: python3 scripts/detached_run.py /home/z/my-project/github-hot-heybox \
        /tmp/heybox_agi_run.log python3 agi_news.py
"""
import os
import subprocess
import sys
import time


def daemonize(log_path: str) -> bool:
    pid = os.fork()
    if pid > 0:
        return False
    os.setsid()
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)
    sys.stdout.flush()
    sys.stderr.flush()
    log = open(log_path, "a")
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    return True


def main():
    workdir, log_path, *cmd = sys.argv[1:]
    if not daemonize(log_path):
        print(f"detached 已 fork 到后台 → {log_path}")
        return
    os.chdir(workdir)
    with open(log_path + ".pid", "w") as f:
        f.write(str(os.getpid()))
    r = subprocess.run(cmd, cwd=workdir)
    with open(log_path + ".rc", "w") as f:
        f.write(str(r.returncode))
    # rc 文件保留 2 小时后自杀(防止占位)
    time.sleep(0)


if __name__ == "__main__":
    main()
