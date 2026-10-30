#!/usr/bin/env python3
# GitHub PAT 供给(净化版): 仅读 /home/z/.secrets/gh_pat.txt
# 完整版含内嵌兜底, 因 secret scanning 不能入库; PAT 丢失时由 cron 任务文本重建 .secrets
def get_token():
    with open('/home/z/.secrets/gh_pat.txt') as f:
        return f.read().strip()

if __name__ == '__main__':
    print(get_token())
