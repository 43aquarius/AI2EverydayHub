import json, os, subprocess, sys, time
sys.path.insert(0, "/home/z/my-project/xhs-draft-poster")
xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1440x900x24"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
os.environ["DISPLAY"] = ":99"
from xhs_client import XhsDraftClient
cfg = json.load(open("/home/z/my-project/xhs-draft-poster/config.json"))
c = XhsDraftClient(cfg["cookie"], headless=False)
try:
    page = c._launch()
    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=45000)
    time.sleep(2)
    page.goto("https://creator.xiaohongshu.com/new/home", wait_until="domcontentloaded", timeout=45000)
    time.sleep(3.5)
    links = page.evaluate("""
    (() => {
      const out = [];
      document.querySelectorAll('a[href]').forEach(a => {
        const t = (a.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 20);
        if (t) out.push({t: t, h: a.getAttribute('href').slice(0, 80)});
      });
      return out;
    })()""")
    seen = set()
    for l in links:
        k = l["h"]
        if k not in seen and ("manage" in k or "note" in k or "publish" in k or "content" in k):
            seen.add(k)
            print(json.dumps(l, ensure_ascii=False))
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
