"""
Google PageSpeed Insights — Website Speed Report
-------------------------------------------------
Fetches speed data via Google API and generates a slide-based
HTML report focused purely on page speed for non-tech users.

Requirements:
    pip install requests

Usage:
    python pagespeed_report.py
    python pagespeed_report.py https://yoursite.com
"""

import sys
import requests
from datetime import datetime


# ─── CONFIG ────────────────────────────────────────────────────────────────────
TARGET_URL  = "https://notionhive.com"   # ← Change this
API_KEY     = "AIzaSyCItGGWJ4uWXr2EzRwgscKD81N9cislDIw"        # ← Paste your Google API key here
OUTPUT_HTML = "pagespeed_report.html"
STRATEGY    = "mobile"                   # "mobile" or "desktop"
# ───────────────────────────────────────────────────────────────────────────────


def fetch_pagespeed(url, api_key, strategy="mobile"):
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url":      url,
        "key":      api_key,
        "strategy": strategy,
        "category": ["performance"],   # Speed only — no SEO, no accessibility
    }

    print(f"\n⚡ Fetching speed data for: {url}")
    print(f"   Strategy: {strategy.upper()}")
    print("   Calling Google PageSpeed Insights API...")

    resp = requests.get(endpoint, params=params, timeout=60)

    if resp.status_code != 200:
        print(f"   ✗ API error {resp.status_code}: {resp.text[:300]}")
        return None

    print("   ✅ Data received!")
    return resp.json()


def parse_data(raw, url, strategy):
    lhr    = raw.get("lighthouseResult", {})
    cats   = lhr.get("categories", {})
    audits = lhr.get("audits", {})

    def score(cat_key):
        s = cats.get(cat_key, {}).get("score")
        return round(s * 100) if s is not None else "N/A"

    def ms_val(key):
        val = audits.get(key, {}).get("numericValue")
        if val is None: return None
        return val

    def ms_str(key):
        val = ms_val(key)
        if val is None: return "N/A"
        if val >= 1000: return f"{val/1000:.1f}s"
        return f"{round(val)}ms"

    def cls_str(key):
        val = ms_val(key)
        if val is None: return "N/A"
        return f"{val:.3f}"

    # Metric statuses
    def lcp_status(v):
        if v is None: return "info"
        return "pass" if v <= 2500 else ("warning" if v <= 4000 else "fail")

    def tbt_status(v):
        if v is None: return "info"
        return "pass" if v <= 200 else ("warning" if v <= 600 else "fail")

    def cls_status(v):
        if v is None: return "info"
        return "pass" if v <= 0.1 else ("warning" if v <= 0.25 else "fail")

    def fcp_status(v):
        if v is None: return "info"
        return "pass" if v <= 1800 else ("warning" if v <= 3000 else "fail")

    def si_status(v):
        if v is None: return "info"
        return "pass" if v <= 3400 else ("warning" if v <= 5800 else "fail")

    def tti_status(v):
        if v is None: return "info"
        return "pass" if v <= 3800 else ("warning" if v <= 7300 else "fail")

    lcp_raw = ms_val("largest-contentful-paint")
    tbt_raw = ms_val("total-blocking-time")
    cls_raw = ms_val("cumulative-layout-shift")
    fcp_raw = ms_val("first-contentful-paint")
    si_raw  = ms_val("speed-index")
    tti_raw = ms_val("interactive")

    # Performance audit items grouped into friendly buckets
    def get_perf_items(group_ids):
        items = []
        for audit_id in group_ids:
            audit = audits.get(audit_id, {})
            title       = audit.get("title", "")
            description = audit.get("description", "")
            s           = audit.get("score")
            display_val = audit.get("displayValue", "")
            if not title: continue

            if s is None:
                status = "info"
            elif s >= 0.9:
                status = "pass"
            elif s >= 0.5:
                status = "warning"
            else:
                status = "fail"

            detail = display_val if display_val else (description[:200] + "…" if len(description) > 200 else description)
            items.append({"title": title, "content": detail, "status": status})
        return items

    # Group audits into non-tech friendly categories
    speed_groups = [
        {
            "icon":    "🖼️",
            "name":    "Images & Media",
            "tagline": "Unoptimized images are the #1 cause of slow websites. Here's how yours look.",
            "ids": [
                "uses-optimized-images", "uses-webp-images", "uses-responsive-images",
                "efficient-animated-content", "uses-lazy-loading", "offscreen-images",
                "modern-image-formats",
            ],
        },
        {
            "icon":    "📦",
            "name":    "JavaScript & Code",
            "tagline": "Heavy or unused code makes your pages slow to become interactive.",
            "ids": [
                "unused-javascript", "unused-css-rules", "unminified-javascript",
                "unminified-css", "render-blocking-resources", "bootup-time",
                "mainthread-work-breakdown", "third-party-summary",
            ],
        },
        {
            "icon":    "🌐",
            "name":    "Network & Server",
            "tagline": "How your server delivers content affects every visitor's experience.",
            "ids": [
                "uses-text-compression", "uses-rel-preconnect", "server-response-time",
                "redirects", "uses-http2", "efficient-cache-policy",
                "preload-lcp-image", "uses-rel-preload",
            ],
        },
        {
            "icon":    "🎨",
            "name":    "Page Layout & Fonts",
            "tagline": "Visual stability and font loading affect how smooth your site feels.",
            "ids": [
                "cumulative-layout-shift", "layout-shift-elements",
                "font-display", "uses-passive-event-listeners",
                "non-composited-animations", "unsized-images",
            ],
        },
    ]

    categories = []
    for grp in speed_groups:
        items = get_perf_items(grp["ids"])
        # Only include items that were actually returned by API
        items = [i for i in items if i["title"]]
        if items:
            categories.append({
                "icon":    grp["icon"],
                "name":    grp["name"],
                "tagline": grp["tagline"],
                "items":   items,
            })

    return {
        "url":        url,
        "strategy":   strategy,
        "timestamp":  datetime.now().strftime("%B %d, %Y at %H:%M"),
        "perf_score": score("performance"),
        # Core Web Vitals
        "lcp":        ms_str("largest-contentful-paint"),
        "lcp_raw":    lcp_raw,
        "lcp_status": lcp_status(lcp_raw),
        "tbt":        ms_str("total-blocking-time"),
        "tbt_raw":    tbt_raw,
        "tbt_status": tbt_status(tbt_raw),
        "cls":        cls_str("cumulative-layout-shift"),
        "cls_raw":    cls_raw,
        "cls_status": cls_status(cls_raw),
        "fcp":        ms_str("first-contentful-paint"),
        "fcp_raw":    fcp_raw,
        "fcp_status": fcp_status(fcp_raw),
        "si":         ms_str("speed-index"),
        "si_raw":     si_raw,
        "si_status":  si_status(si_raw),
        "tti":        ms_str("interactive"),
        "tti_raw":    tti_raw,
        "tti_status": tti_status(tti_raw),
        "categories": categories,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def score_color(s):
    try:
        v = int(s)
        if v >= 90: return "#16a34a"
        if v >= 50: return "#d97706"
        return "#dc2626"
    except:
        return "#6b7280"

def score_verdict(s):
    try:
        v = int(s)
        if v >= 90: return ("Fast", "Your website loads quickly. Visitors get a smooth, snappy experience.")
        if v >= 50: return ("Needs Improvement", "Your site is average speed. Some visitors may leave before it loads fully.")
        return ("Slow", "Your website is slow. This is likely costing you visitors and Google rankings.")
    except:
        return ("Unknown", "We couldn't determine your speed score.")

def grade(s):
    try:
        v = int(s)
        if v >= 90: return "A"
        if v >= 80: return "B"
        if v >= 70: return "C"
        if v >= 50: return "D"
        return "F"
    except:
        return "?"

def metric_color(status):
    return {"pass": "#16a34a", "warning": "#d97706", "fail": "#dc2626"}.get(status, "#6b7280")

def metric_bg(status):
    return {"pass": "#f0fdf4", "warning": "#fffbeb", "fail": "#fef2f2"}.get(status, "#f9fafb")

def metric_border(status):
    return {"pass": "#bbf7d0", "warning": "#fde68a", "fail": "#fecaca"}.get(status, "#e5e7eb")

def metric_label(status):
    return {"pass": "✅ Good", "warning": "⚠️ Needs Work", "fail": "❌ Slow"}.get(status, "ℹ️ Info")

def status_meta(status):
    if status == "pass":    return ("✅", "Good",     "#16a34a", "#f0fdf4", "#bbf7d0")
    if status == "warning": return ("⚠️",  "Improve",  "#d97706", "#fffbeb", "#fde68a")
    if status == "fail":    return ("❌", "Fix This", "#dc2626", "#fef2f2", "#fecaca")
    return                          ("ℹ️",  "Info",     "#2563eb", "#eff6ff", "#bfdbfe")

def ring_dash(score, r=54):
    try:
        return round(3.14159 * 2 * r * int(score) / 100, 1)
    except:
        return 0


def generate_report(data):
    domain   = data["url"].replace("https://","").replace("http://","").rstrip("/")
    pc       = score_color(data["perf_score"])
    verdict, verdict_desc = score_verdict(data["perf_score"])
    pg       = grade(data["perf_score"])
    total_slides = 2 + len(data["categories"]) + 1  # cover + cwv + groups + end

    # ── Core Web Vitals cards ─────────────────────────────────────────────────
    cwv_items = [
        {
            "abbr":   "LCP",
            "name":   "Largest Contentful Paint",
            "val":    data["lcp"],
            "status": data["lcp_status"],
            "desc":   "How long until the main content (hero image or big text) appears on screen.",
            "scale":  "✅ Under 2.5s  ·  ⚠️ Under 4s  ·  ❌ Over 4s",
            "why":    "Visitors decide to stay or leave within seconds of arriving.",
        },
        {
            "abbr":   "TBT",
            "name":   "Total Blocking Time",
            "val":    data["tbt"],
            "status": data["tbt_status"],
            "desc":   "How long your page freezes and ignores clicks while it loads.",
            "scale":  "✅ Under 200ms  ·  ⚠️ Under 600ms  ·  ❌ Over 600ms",
            "why":    "A frozen page feels broken to visitors — they'll click away.",
        },
        {
            "abbr":   "CLS",
            "name":   "Cumulative Layout Shift",
            "val":    data["cls"],
            "status": data["cls_status"],
            "desc":   "How much the page content jumps around while it loads.",
            "scale":  "✅ Under 0.1  ·  ⚠️ Under 0.25  ·  ❌ Over 0.25",
            "why":    "Layout jumps cause accidental clicks and a frustrating experience.",
        },
        {
            "abbr":   "FCP",
            "name":   "First Contentful Paint",
            "val":    data["fcp"],
            "status": data["fcp_status"],
            "desc":   "When the very first thing appears on screen — text, image, or logo.",
            "scale":  "✅ Under 1.8s  ·  ⚠️ Under 3s  ·  ❌ Over 3s",
            "why":    "A blank white screen for too long signals a slow or broken site.",
        },
        {
            "abbr":   "SI",
            "name":   "Speed Index",
            "val":    data["si"],
            "status": data["si_status"],
            "desc":   "How quickly the visible parts of the page fill in as it loads.",
            "scale":  "✅ Under 3.4s  ·  ⚠️ Under 5.8s  ·  ❌ Over 5.8s",
            "why":    "A page that fills in gradually feels faster than one that appears all at once late.",
        },
        {
            "abbr":   "TTI",
            "name":   "Time to Interactive",
            "val":    data["tti"],
            "status": data["tti_status"],
            "desc":   "How long until visitors can fully click, scroll, and use the page.",
            "scale":  "✅ Under 3.8s  ·  ⚠️ Under 7.3s  ·  ❌ Over 7.3s",
            "why":    "Even if the page looks loaded, it may still be unresponsive.",
        },
    ]

    cwv_cards_html = ""
    for m in cwv_items:
        clr = metric_color(m["status"])
        bg  = metric_bg(m["status"])
        brd = metric_border(m["status"])
        lbl = metric_label(m["status"])
        cwv_cards_html += f"""
        <div class="cwv-card" style="background:{bg};border-color:{brd};">
          <div class="cwv-top">
            <div>
              <div class="cwv-abbr" style="color:{clr};">{m['abbr']}</div>
              <div class="cwv-name">{m['name']}</div>
            </div>
            <div class="cwv-val" style="color:{clr};">{m['val']}</div>
          </div>
          <div class="cwv-desc">{m['desc']}</div>
          <div class="cwv-why">💡 {m['why']}</div>
          <div class="cwv-footer">
            <span class="cwv-badge" style="background:{clr};">{lbl}</span>
            <span class="cwv-scale">{m['scale']}</span>
          </div>
        </div>"""

    # ── Category slides ───────────────────────────────────────────────────────
    category_slides = ""
    for idx, cat in enumerate(data["categories"]):
        slide_num = idx + 3
        pass_c = sum(1 for i in cat["items"] if i["status"] == "pass")
        warn_c = sum(1 for i in cat["items"] if i["status"] == "warning")
        fail_c = sum(1 for i in cat["items"] if i["status"] == "fail")
        info_c = sum(1 for i in cat["items"] if i["status"] == "info")

        items_html = ""
        for item in cat["items"]:
            emoji, label, clr, bg, border = status_meta(item["status"])
            safe = item["content"].replace("<","&lt;").replace(">","&gt;")
            items_html += f"""
            <div class="check-card" style="background:{bg};border-color:{border};">
              <div class="check-card-top">
                <span class="check-emoji">{emoji}</span>
                <div class="check-info">
                  <div class="check-title">{item['title']}</div>
                  <div class="check-desc">{safe}</div>
                </div>
                <span class="check-badge" style="background:{clr};">{label}</span>
              </div>
            </div>"""

        category_slides += f"""
        <div class="slide" data-slide="{slide_num}">
          <div class="slide-inner">
            <div class="cat-header">
              <div class="cat-icon">{cat['icon']}</div>
              <div>
                <div class="cat-title">{cat['name']}</div>
                <div class="cat-tagline">{cat['tagline']}</div>
              </div>
            </div>
            <div class="cat-summary-bar">
              <span class="mini-pill green">✓ {pass_c} Good</span>
              <span class="mini-pill amber">⚠ {warn_c} Improve</span>
              <span class="mini-pill red">✗ {fail_c} Fix</span>
              {'<span class="mini-pill blue">ℹ ' + str(info_c) + ' Info</span>' if info_c else ''}
            </div>
            <div class="checks-grid">{items_html}</div>
          </div>
        </div>"""

    # ── Nav dots ──────────────────────────────────────────────────────────────
    dots_html = "".join(
        f'<span class="dot" data-goto="{i}"></span>'
        for i in range(1, total_slides + 1)
    )

    # ── Speed bar helper (visual bar for score) ───────────────────────────────
    speed_bar_width = data["perf_score"] if data["perf_score"] != "N/A" else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Speed Report — {domain}</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{ box-sizing:border-box; margin:0; padding:0; }}
:root{{
  --cream:#fafaf7; --white:#ffffff; --ink:#111827; --muted:#6b7280; --border:#e5e7eb;
  --green:#16a34a; --green-bg:#f0fdf4; --amber:#d97706; --amber-bg:#fffbeb;
  --red:#dc2626; --red-bg:#fef2f2; --blue:#2563eb; --blue-bg:#eff6ff;
  --accent:#0284c7;
}}
html,body{{ height:100%; width:100%; background:#0c1a2e; font-family:'Plus Jakarta Sans',sans-serif; overflow:hidden; }}

.deck{{ width:100vw; height:100vh; position:relative; overflow:hidden; }}
.slide{{
  position:absolute; inset:0; opacity:0; pointer-events:none;
  transform:translateX(56px); transition:opacity 0.42s ease, transform 0.42s ease;
  overflow-y:auto; background:var(--cream);
}}
.slide.active{{ opacity:1; pointer-events:all; transform:translateX(0); }}
.slide.exit{{ opacity:0; transform:translateX(-56px); }}
.slide-inner{{ max-width:900px; margin:0 auto; padding:52px 48px 110px; min-height:100vh; }}

/* Nav */
.nav{{
  position:fixed; bottom:0; left:0; right:0;
  background:rgba(255,255,255,0.96); backdrop-filter:blur(14px);
  border-top:1px solid var(--border);
  display:flex; align-items:center; justify-content:space-between;
  padding:14px 40px; z-index:100; gap:16px;
}}
.nav-btn{{
  display:flex; align-items:center; gap:8px; padding:10px 22px;
  border-radius:50px; border:2px solid var(--border); background:var(--white);
  color:var(--ink); font-family:'Plus Jakarta Sans',sans-serif;
  font-weight:600; font-size:0.875rem; cursor:pointer; transition:all 0.2s;
}}
.nav-btn:hover{{ background:var(--ink); color:white; border-color:var(--ink); }}
.nav-btn:disabled{{ opacity:0.3; cursor:not-allowed; }}
.nav-btn:disabled:hover{{ background:var(--white); color:var(--ink); border-color:var(--border); }}
.dots{{ display:flex; gap:6px; align-items:center; flex-wrap:wrap; justify-content:center; flex:1; }}
.dot{{ width:8px; height:8px; border-radius:50%; background:var(--border); cursor:pointer; transition:all 0.2s; }}
.dot.active{{ background:var(--accent); width:24px; border-radius:4px; }}
.slide-counter{{ font-size:0.75rem; color:var(--muted); font-weight:600; white-space:nowrap; min-width:60px; text-align:right; }}

/* Cover */
.cover{{ background:linear-gradient(150deg,#f0f9ff 0%,#e0f2fe 50%,#fafaf7 100%); display:flex; align-items:center; }}
.cover .slide-inner{{ display:flex; flex-direction:column; justify-content:center; min-height:100vh; }}
.eyebrow{{
  display:inline-flex; align-items:center; gap:8px;
  background:white; border:1px solid var(--border); border-radius:50px;
  padding:6px 16px; font-size:0.72rem; font-weight:700; color:var(--accent);
  letter-spacing:0.1em; text-transform:uppercase; margin-bottom:24px; width:fit-content;
}}
.cover-title{{ font-family:'Playfair Display',serif; font-size:clamp(2rem,5vw,3.5rem); font-weight:900; color:var(--ink); line-height:1.1; margin-bottom:10px; }}
.cover-domain{{ font-family:'Playfair Display',serif; font-size:clamp(1.1rem,2.5vw,1.7rem); color:var(--accent); margin-bottom:6px; }}
.cover-meta{{ font-size:0.8rem; color:var(--muted); margin-bottom:8px; }}
.strategy-tag{{ display:inline-flex; align-items:center; gap:6px; background:var(--ink); color:white; font-size:0.72rem; font-weight:700; padding:5px 14px; border-radius:50px; margin-bottom:32px; }}

/* Hero score card */
.hero-card{{
  background:white; border:1px solid var(--border); border-radius:24px;
  padding:32px 36px; box-shadow:0 4px 32px rgba(0,0,0,0.07);
}}
.hero-top{{ display:flex; align-items:center; gap:32px; flex-wrap:wrap; margin-bottom:24px; }}
.hero-ring-wrap{{ position:relative; flex-shrink:0; }}
.hero-ring-wrap svg{{ transform:rotate(-90deg); }}
.ring-center{{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
.ring-num{{ font-family:'Playfair Display',serif; font-size:2.6rem; font-weight:900; color:{pc}; line-height:1; }}
.ring-of{{ font-size:0.72rem; color:var(--muted); }}
.ring-grade{{ background:{pc}; color:white; font-weight:800; font-size:0.65rem; letter-spacing:0.1em; padding:3px 9px; border-radius:20px; margin-top:5px; }}
.hero-words{{ flex:1; min-width:180px; }}
.hero-verdict{{ font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:700; color:{pc}; margin-bottom:8px; }}
.hero-desc{{ font-size:0.86rem; color:var(--muted); line-height:1.6; }}

/* Speed bar */
.speed-bar-wrap{{ margin-top:4px; }}
.speed-bar-label{{ display:flex; justify-content:space-between; font-size:0.78rem; font-weight:600; color:var(--ink); margin-bottom:8px; }}
.speed-bar-track{{ height:16px; background:#f3f4f6; border-radius:99px; overflow:hidden; position:relative; }}
.speed-bar-fill{{ height:100%; border-radius:99px; background:linear-gradient(90deg, #16a34a, {pc}); transition:width 1.2s ease; }}
.speed-bar-zones{{ display:flex; gap:12px; margin-top:8px; }}
.speed-zone{{ font-size:0.68rem; font-weight:600; }}
.speed-zone.g{{ color:var(--green); }}
.speed-zone.a{{ color:var(--amber); }}
.speed-zone.r{{ color:var(--red);   }}

/* CWV slide */
.slide-title{{ font-family:'Playfair Display',serif; font-size:1.9rem; font-weight:900; color:var(--ink); margin-bottom:6px; }}
.slide-sub{{ color:var(--muted); font-size:0.88rem; line-height:1.6; margin-bottom:24px; }}
.cwv-grid{{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }}
.cwv-card{{ border-radius:16px; border:1.5px solid; padding:18px 18px 14px; transition:transform 0.15s; }}
.cwv-card:hover{{ transform:translateY(-2px); }}
.cwv-top{{ display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:8px; }}
.cwv-abbr{{ font-family:'Playfair Display',serif; font-size:1rem; font-weight:900; letter-spacing:0.04em; }}
.cwv-name{{ font-size:0.72rem; color:var(--muted); font-weight:600; margin-top:2px; }}
.cwv-val{{ font-family:'Playfair Display',serif; font-size:1.7rem; font-weight:900; line-height:1; }}
.cwv-desc{{ font-size:0.74rem; color:var(--muted); line-height:1.5; margin-bottom:6px; }}
.cwv-why{{ font-size:0.72rem; color:var(--ink); line-height:1.4; margin-bottom:10px; font-style:italic; }}
.cwv-footer{{ display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:6px; }}
.cwv-badge{{ color:white; font-size:0.66rem; font-weight:700; padding:3px 10px; border-radius:50px; white-space:nowrap; }}
.cwv-scale{{ font-size:0.62rem; color:var(--muted); }}

/* Category slides */
.cat-header{{ display:flex; align-items:flex-start; gap:16px; margin-bottom:16px; }}
.cat-icon{{ font-size:2.2rem; line-height:1; flex-shrink:0; }}
.cat-title{{ font-family:'Playfair Display',serif; font-size:1.7rem; font-weight:900; color:var(--ink); line-height:1.2; margin-bottom:4px; }}
.cat-tagline{{ font-size:0.84rem; color:var(--muted); line-height:1.5; }}
.cat-summary-bar{{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:20px; }}
.mini-pill{{ padding:4px 12px; border-radius:50px; font-size:0.74rem; font-weight:700; }}
.mini-pill.green{{ background:var(--green-bg); color:var(--green); }}
.mini-pill.amber{{ background:var(--amber-bg); color:var(--amber); }}
.mini-pill.red  {{ background:var(--red-bg);   color:var(--red);   }}
.mini-pill.blue {{ background:var(--blue-bg);  color:var(--blue);  }}
.checks-grid{{ display:flex; flex-direction:column; gap:10px; }}
.check-card{{ border-radius:12px; border:1.5px solid; padding:13px 15px; transition:transform 0.15s; }}
.check-card:hover{{ transform:translateY(-1px); }}
.check-card-top{{ display:flex; align-items:flex-start; gap:12px; }}
.check-emoji{{ font-size:1.2rem; flex-shrink:0; line-height:1.4; }}
.check-info{{ flex:1; }}
.check-title{{ font-size:0.86rem; font-weight:700; color:var(--ink); margin-bottom:3px; }}
.check-desc{{ font-size:0.73rem; color:var(--muted); line-height:1.5; }}
.check-badge{{ flex-shrink:0; color:white; font-size:0.64rem; font-weight:700; padding:3px 9px; border-radius:50px; white-space:nowrap; align-self:flex-start; }}

/* End slide */
.end-slide{{ background:linear-gradient(145deg,#0c1a2e 0%,#063555 100%); }}
.end-slide .slide-inner{{ display:flex; flex-direction:column; justify-content:center; min-height:100vh; }}
.end-eyebrow{{ display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); border-radius:50px; padding:6px 16px; font-size:0.7rem; font-weight:700; color:rgba(255,255,255,0.55); letter-spacing:0.1em; text-transform:uppercase; margin-bottom:22px; width:fit-content; }}
.end-title{{ font-family:'Playfair Display',serif; font-size:clamp(1.8rem,4vw,3rem); font-weight:900; color:white; line-height:1.15; margin-bottom:14px; }}
.end-sub{{ font-size:0.9rem; color:rgba(255,255,255,0.55); line-height:1.7; margin-bottom:32px; max-width:580px; }}
.end-metrics{{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:32px; }}
.end-metric{{ background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.12); border-radius:14px; padding:16px 18px; text-align:center; min-width:90px; }}
.end-metric-val{{ font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:900; line-height:1; margin-bottom:4px; }}
.end-metric-lbl{{ font-size:0.65rem; color:rgba(255,255,255,0.45); font-weight:600; }}
.end-footer{{ font-size:0.68rem; color:rgba(255,255,255,0.22); }}

.key-hint{{ position:fixed; top:18px; right:18px; background:rgba(0,0,0,0.45); color:white; font-size:0.66rem; padding:5px 13px; border-radius:50px; opacity:0.55; pointer-events:none; z-index:200; }}

@media(max-width:640px){{
  .slide-inner{{ padding:28px 18px 100px; }}
  .hero-card{{ padding:20px; }}
  .nav{{ padding:10px 16px; }}
}}
</style>
</head>
<body>
<div class="key-hint">← → Arrow keys to navigate</div>
<div class="deck" id="deck">

  <!-- SLIDE 1: Cover -->
  <div class="slide cover active" data-slide="1">
    <div class="slide-inner">
      <div class="eyebrow"><span>⚡</span> WEBSITE SPEED REPORT</div>
      <div class="cover-title">How fast does your<br>website actually load?</div>
      <div class="cover-domain">{domain}</div>
      <div class="cover-meta">Analyzed on {data["timestamp"]}</div>
      <div class="strategy-tag">{("📱 Mobile" if data["strategy"] == "mobile" else "🖥️ Desktop")} Test</div>
      <div class="hero-card">
        <div class="hero-top">
          <div class="hero-ring-wrap">
            <svg width="130" height="130" viewBox="0 0 130 130">
              <circle cx="65" cy="65" r="54" fill="none" stroke="#f3f4f6" stroke-width="10"/>
              <circle cx="65" cy="65" r="54" fill="none" stroke="{pc}" stroke-width="10"
                stroke-linecap="round" stroke-dasharray="{ring_dash(data['perf_score'])} 999"/>
            </svg>
            <div class="ring-center">
              <div class="ring-num">{data["perf_score"]}</div>
              <div class="ring-of">out of 100</div>
              <div class="ring-grade">GRADE {pg}</div>
            </div>
          </div>
          <div class="hero-words">
            <div class="hero-verdict">{verdict}</div>
            <div class="hero-desc">{verdict_desc}</div>
          </div>
        </div>
        <div class="speed-bar-wrap">
          <div class="speed-bar-label"><span>Speed Score</span><span style="color:{pc};">{data["perf_score"]}/100</span></div>
          <div class="speed-bar-track">
            <div class="speed-bar-fill" style="width:{speed_bar_width}%;"></div>
          </div>
          <div class="speed-bar-zones">
            <span class="speed-zone r">0–49 Slow</span>
            <span class="speed-zone a">50–89 Needs Work</span>
            <span class="speed-zone g">90–100 Fast</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 2: Core Web Vitals -->
  <div class="slide" data-slide="2">
    <div class="slide-inner">
      <div class="slide-title">Your Speed Measurements</div>
      <div class="slide-sub">Google measures page speed using 6 specific signals called Core Web Vitals. Each one tells a different story about how your website feels to real visitors. Here's how you scored on each one.</div>
      <div class="cwv-grid">{cwv_cards_html}</div>
    </div>
  </div>

  <!-- CATEGORY SLIDES -->
  {category_slides}

  <!-- END SLIDE -->
  <div class="slide end-slide" data-slide="{total_slides}">
    <div class="slide-inner">
      <div class="end-eyebrow"><span>🏁</span> REPORT COMPLETE</div>
      <div class="end-title">Here's your website<br>speed summary.</div>
      <div class="end-sub">Fix the ❌ red items first — they have the biggest impact on load time. Images and unused JavaScript are usually the quickest wins. Even shaving 1 second off load time can meaningfully increase conversions.</div>
      <div class="end-metrics">
        <div class="end-metric">
          <div class="end-metric-val" style="color:{pc};">{data["perf_score"]}</div>
          <div class="end-metric-lbl">Speed Score</div>
        </div>
        <div class="end-metric">
          <div class="end-metric-val" style="color:{metric_color(data['lcp_status'])};">{data["lcp"]}</div>
          <div class="end-metric-lbl">LCP</div>
        </div>
        <div class="end-metric">
          <div class="end-metric-val" style="color:{metric_color(data['tbt_status'])};">{data["tbt"]}</div>
          <div class="end-metric-lbl">TBT</div>
        </div>
        <div class="end-metric">
          <div class="end-metric-val" style="color:{metric_color(data['cls_status'])};">{data["cls"]}</div>
          <div class="end-metric-lbl">CLS</div>
        </div>
        <div class="end-metric">
          <div class="end-metric-val" style="color:{metric_color(data['fcp_status'])};">{data["fcp"]}</div>
          <div class="end-metric-lbl">FCP</div>
        </div>
      </div>
      <div class="end-footer">Powered by Google PageSpeed Insights API · {data["timestamp"]}</div>
    </div>
  </div>

</div>

<nav class="nav">
  <button class="nav-btn" id="prevBtn" onclick="changeSlide(-1)" disabled>← Back</button>
  <div class="dots" id="dots">{dots_html}</div>
  <span class="slide-counter" id="counter">1 / {total_slides}</span>
  <button class="nav-btn" id="nextBtn" onclick="changeSlide(1)">Next →</button>
</nav>

<script>
const slides = document.querySelectorAll('.slide');
const dots   = document.querySelectorAll('.dot');
const prev   = document.getElementById('prevBtn');
const next   = document.getElementById('nextBtn');
const ctr    = document.getElementById('counter');
const total  = slides.length;
let cur      = 0;

function goTo(n) {{
  slides[cur].classList.remove('active');
  slides[cur].classList.add('exit');
  const old = cur;
  setTimeout(() => slides[old].classList.remove('exit'), 500);
  cur = n;
  slides[cur].classList.add('active');
  dots.forEach((d,i) => d.classList.toggle('active', i===cur));
  ctr.textContent = (cur+1)+' / '+total;
  prev.disabled = cur===0;
  next.disabled = cur===total-1;
  slides[cur].scrollTop = 0;
}}
function changeSlide(dir) {{
  const n = cur+dir;
  if(n>=0 && n<total) goTo(n);
}}
dots.forEach((d,i) => d.addEventListener('click', ()=>goTo(i)));
document.addEventListener('keydown', e=>{{
  if(e.key==='ArrowRight'||e.key==='ArrowDown') changeSlide(1);
  if(e.key==='ArrowLeft' ||e.key==='ArrowUp')   changeSlide(-1);
}});
goTo(0);
</script>
</body>
</html>"""
    return html


def main():
    url = TARGET_URL.strip()
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    if not url.startswith("http"):
        url = "https://" + url

    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n⚠️  Set your API_KEY at the top of the script.")
        print("   Get a free key → https://console.cloud.google.com/")
        print("   Enable 'PageSpeed Insights API' → Credentials → Create API Key\n")
        sys.exit(1)

    raw = fetch_pagespeed(url, API_KEY, STRATEGY)
    if not raw:
        print("✗ Failed to fetch data. Check your API key and URL.")
        sys.exit(1)

    data = parse_data(raw, url, STRATEGY)

    print(f"\n   Speed Score : {data['perf_score']}/100")
    print(f"   LCP: {data['lcp']}  TBT: {data['tbt']}  CLS: {data['cls']}  FCP: {data['fcp']}")
    print(f"   SI:  {data['si']}   TTI: {data['tti']}")

    print("\n📄 Generating speed report...")
    html = generate_report(data)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Report saved → {OUTPUT_HTML}")
    print("   Open in browser. Use ← → arrow keys or buttons to navigate.\n")


if __name__ == "__main__":
    main()