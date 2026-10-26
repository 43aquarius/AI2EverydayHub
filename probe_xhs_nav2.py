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
    time.sleep(4)
    # 打印全部链接(shadow已open, 也扫shadow内)
    links = page.evaluate("""
    (() => {
      const out = [];
      const walk = (root) => {
        root.querySelectorAll('a[href]').forEach(a => {
          const t = (a.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 16);
          out.push({t: t, h: (a.getAttribute('href') || '').slice(0, 90)});
        });
      };
      walk(document);
      return out;
    })()""")
    seen = set()
    for l in links:
        if l["h"] and l["h"] not in seen:
            seen.add(l["h"])
            print(l["t"], "|", l["h"])
    c._shot("nav_home")
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
