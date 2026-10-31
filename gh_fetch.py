#!/usr/bin/env python3
import base64, json, os, sys, urllib.request
def fetch(repo, path, dst):
    req = urllib.request.Request("https://api.github.com/repos/%s/contents/%s" % (repo, path), headers={"Authorization": "token " + open("/home/z/.secrets/gh_pat.txt").read().strip(), "Accept": "application/vnd.github.v3+json", "User-Agent": "heal-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        c = base64.b64decode(json.load(r)["content"])
    d_ = os.path.dirname(dst)
    if d_:
        os.makedirs(d_, exist_ok=True)
    open(dst, "wb").write(c)
    print("OK %s/%s -> %s (%dB)" % (repo, path, dst, len(c)))
if __name__ == "__main__":
    for spec in sys.argv[2:]:
        p, _, d = spec.partition(":")
        fetch(sys.argv[1], p, d or "/tmp/" + os.path.basename(p))
