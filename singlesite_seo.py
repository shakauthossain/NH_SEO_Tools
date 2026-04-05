"""
RankMath SEO Analyzer — Single Site + Slide-Based HTML Report
-------------------------------------------------------------
Generates a beautiful slide-deck style HTML report for non-tech users.

Requirements:
    pip install playwright
    playwright install chromium
"""

import time
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright


# ─── CONFIG ────────────────────────────────────────────────────────────────────
TARGET_URL  = "https://notionhive.com"
HEADLESS    = True
OUTPUT_HTML = "seo_report.html"
# ───────────────────────────────────────────────────────────────────────────────


def scrape_rankmath(url):
    data = {
        "url": url,
        "seo_score": "N/A",
        "passed": "N/A",
        "warnings": "N/A",
        "failed": "N/A",
        "categories": [],
        "timestamp": datetime.now().strftime("%B %d, %Y at %H:%M"),
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        page = context.new_page()

        print(f"\n🔍 Analyzing: {url}")
        print("   Opening RankMath SEO Analyzer...")

        page.goto("https://rankmath.com/tools/seo-analyzer/", timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)

        # Debug inputs
        inputs = page.locator("input").all()
        print(f"   Found {len(inputs)} input(s):")
        for inp in inputs:
            try:
                print(f"     id='{inp.get_attribute('id')}' "
                      f"placeholder='{inp.get_attribute('placeholder')}' "
                      f"type='{inp.get_attribute('type')}'")
            except Exception:
                pass

        # Find input
        input_box = None
        for sel in [
            "input#url", "input[name='url']", "input[type='url']",
            "input[placeholder*='http']", "input[placeholder*='URL']",
            "input[placeholder*='url']", "input[placeholder*='Enter']",
            "input[placeholder*='website']", "form input[type='text']",
            "input[type='text']",
        ]:
            try:
                el = page.locator(sel).first
                el.wait_for(timeout=3000, state="visible")
                input_box = el
                print(f"   ✅ Input found: {sel}")
                break
            except Exception:
                continue

        if input_box is None:
            try:
                input_box = page.locator("input").first
                input_box.wait_for(timeout=5000, state="visible")
                print("   ⚠ Using first input as fallback")
            except Exception:
                with open("debug_page.html", "w") as f:
                    f.write(page.content())
                print("   ✗ No input found. Saved debug_page.html")
                browser.close()
                return data

        input_box.click()
        input_box.fill("")
        input_box.type(url, delay=50)

        # Find button
        btn = None
        for sel in [
            "button#analyze", "button[type='submit']", "input[type='submit']",
            "button:has-text('Analyze')", "button:has-text('Check')",
            ".analyzer button", "form button",
        ]:
            try:
                el = page.locator(sel).first
                el.wait_for(timeout=3000, state="visible")
                btn = el
                print(f"   ✅ Button found: {sel}")
                break
            except Exception:
                continue

        if btn:
            btn.click()
        else:
            print("   ⚠ No button, pressing Enter")
            input_box.press("Enter")

        print("   ⏳ Waiting for results...")

        result_found = False
        for sel in [
            "div.container.analysis-result.clear", "div.analysis-result",
            ".rank-math-result-graphs", "#analysis", "[class*='result']",
        ]:
            try:
                page.wait_for_selector(sel, timeout=90000)
                print(f"   ✅ Results loaded: {sel}")
                result_found = True
                break
            except Exception:
                continue

        if not result_found:
            with open("debug_page.html", "w") as f:
                f.write(page.content())
            print("   ✗ Results not found. Saved debug_page.html")
            browser.close()
            return data

        time.sleep(3)

        # Scrape score
        try:
            graphs = page.locator("div.rank-math-result-graphs")
            lines = [l.strip() for l in graphs.inner_text().splitlines() if l.strip()]
            print(f"   Score lines: {lines}")
            for i, line in enumerate(lines):
                if "Passed Tests" in line and i > 0:
                    data["passed"] = lines[i - 1]
                if "Warnings" in line and i > 0:
                    data["warnings"] = lines[i - 1]
                if "Failed Tests" in line and i > 0:
                    data["failed"] = lines[i - 1]
            for line in lines:
                if "/" in line and "Tests" not in line and "Warnings" not in line:
                    data["seo_score"] = line.split("/")[0].strip()
                    break
        except Exception as e:
            print(f"   ⚠ Score error: {e}")

        # Scrape categories
        try:
            tables = page.locator("div.rank-math-result-table").all()
            print(f"   Found {len(tables)} tables")
            for table in tables:
                try:
                    cat_name = table.locator("div.category-title").inner_text().strip()
                    rows = table.locator("div.table-row").all()
                    items = []
                    for row in rows:
                        try:
                            title   = row.locator("div.row-title").inner_text().strip()
                            content = row.locator("div.row-content").inner_text().strip()
                            status  = "info"
                            try:
                                ic = row.locator("div.status-icon").get_attribute("class") or ""
                                if any(x in ic for x in ["check", "good", "success"]): status = "pass"
                                elif any(x in ic for x in ["warning", "warn"]):         status = "warning"
                                elif any(x in ic for x in ["times", "bad", "error", "fail"]): status = "fail"
                                elif "attention" in ic:                                  status = "info"
                            except Exception:
                                pass
                            items.append({"title": title, "content": content, "status": status})
                        except Exception:
                            continue
                    if items:
                        data["categories"].append({"name": cat_name, "items": items})
                except Exception:
                    continue
        except Exception as e:
            print(f"   ⚠ Category error: {e}")

        browser.close()

    print(f"\n   Score: {data['seo_score']}/100 | Passed: {data['passed']} | Warnings: {data['warnings']} | Failed: {data['failed']}")
    print(f"   Categories scraped: {len(data['categories'])}")
    return data


def score_color(score):
    try:
        s = int(score)
        if s >= 80: return "#16a34a"
        if s >= 60: return "#d97706"
        return "#dc2626"
    except:
        return "#6b7280"

def score_label(score):
    try:
        s = int(score)
        if s >= 80: return ("Excellent", "Your website is well-optimized! A few tweaks and you could be perfect.")
        if s >= 60: return ("Needs Work", "Your site has a decent foundation but several things need attention.")
        return ("Critical Issues", "Your website has serious SEO problems that are likely hurting your visibility.")
    except:
        return ("Unknown", "We couldn't determine your score.")

def grade(score):
    try:
        s = int(score)
        if s >= 90: return "A"
        if s >= 80: return "B"
        if s >= 70: return "C"
        if s >= 60: return "D"
        return "F"
    except:
        return "?"

def status_meta(status):
    if status == "pass":    return ("✅", "All Good",   "#16a34a", "#f0fdf4", "#bbf7d0")
    if status == "warning": return ("⚠️",  "Needs Fix",  "#d97706", "#fffbeb", "#fde68a")
    if status == "fail":    return ("❌", "Problem",    "#dc2626", "#fef2f2", "#fecaca")
    return                          ("ℹ️",  "Info",       "#2563eb", "#eff6ff", "#bfdbfe")

def friendly_name(name):
    mapping = {
        "Basic SEO":    ("🔍", "Basic SEO Checks",         "The fundamental building blocks of your site's visibility on Google."),
        "Advanced SEO": ("🚀", "Advanced SEO",             "Deeper technical signals that help Google better understand your site."),
        "Performance":  ("⚡", "Page Speed & Performance", "How fast your website loads — slow sites lose visitors and rankings."),
        "Security":     ("🔒", "Security",                 "Whether your site is safe and trusted by browsers."),
        "Mobile SEO":   ("📱", "Mobile Friendliness",      "How well your site works on phones — most people browse on mobile!"),
        "Social":       ("📣", "Social Media Sharing",     "How your site looks when shared on Facebook, Twitter, etc."),
        "Local SEO":    ("📍", "Local SEO",                "How well your site appears in local searches like 'near me'."),
    }
    for key, val in mapping.items():
        if key.lower() in name.lower():
            return val
    return ("📋", name, "Analysis results for this category.")


def generate_report(data):
    color        = score_color(data["seo_score"])
    s_label, s_desc = score_label(data["seo_score"])
    g            = grade(data["seo_score"])
    score_pct    = data["seo_score"] if data["seo_score"] != "N/A" else "0"
    try:
        dash_val = round(3.14159 * 2 * 54 * int(score_pct) / 100, 1)
    except:
        dash_val = 0

    domain = data["url"].replace("https://", "").replace("http://", "").rstrip("/")

    def parse_num(val):
        try: return int(val.split("/")[0])
        except: return 0
    def parse_total(val):
        try: return int(val.split("/")[1])
        except: return 28

    passed_n   = parse_num(data["passed"])
    warnings_n = parse_num(data["warnings"])
    failed_n   = parse_num(data["failed"])
    total_n    = parse_total(data["passed"])

    p_pct = round(passed_n   / total_n * 100) if total_n else 0
    w_pct = round(warnings_n / total_n * 100) if total_n else 0
    f_pct = round(failed_n   / total_n * 100) if total_n else 0

    total_slides    = 2 + len(data["categories"]) + 1
    category_slides = ""
    slide_nav_dots  = ""

    for idx, cat in enumerate(data["categories"]):
        icon, friendly, tagline = friendly_name(cat["name"])
        slide_num = idx + 3

        pass_c = sum(1 for i in cat["items"] if i["status"] == "pass")
        warn_c = sum(1 for i in cat["items"] if i["status"] == "warning")
        fail_c = sum(1 for i in cat["items"] if i["status"] == "fail")
        info_c = sum(1 for i in cat["items"] if i["status"] == "info")

        items_html = ""
        for item in cat["items"]:
            emoji, label, clr, bg, border = status_meta(item["status"])
            safe_content = item["content"].replace("<", "&lt;").replace(">", "&gt;")
            display = safe_content[:200] + "…" if len(safe_content) > 200 else safe_content
            items_html += f"""
            <div class="check-card" style="background:{bg}; border-color:{border};">
              <div class="check-card-top">
                <span class="check-emoji">{emoji}</span>
                <div class="check-info">
                  <div class="check-title">{item['title']}</div>
                  <div class="check-desc">{display}</div>
                </div>
                <span class="check-badge" style="background:{clr};">{label}</span>
              </div>
            </div>"""

        category_slides += f"""
        <div class="slide" data-slide="{slide_num}">
          <div class="slide-inner">
            <div class="cat-header">
              <div class="cat-icon">{icon}</div>
              <div>
                <div class="cat-title">{friendly}</div>
                <div class="cat-tagline">{tagline}</div>
              </div>
            </div>
            <div class="cat-summary-bar">
              <span class="mini-pill green">✓ {pass_c} Good</span>
              <span class="mini-pill amber">⚠ {warn_c} Warning</span>
              <span class="mini-pill red">✗ {fail_c} Problem</span>
              <span class="mini-pill blue">ℹ {info_c} Info</span>
            </div>
            <div class="checks-grid">{items_html}</div>
          </div>
        </div>"""

    for i in range(1, total_slides + 1):
        slide_nav_dots += f'<span class="dot" data-goto="{i}"></span>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEO Report — {domain}</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --cream:#faf8f5; --white:#ffffff; --ink:#1a1a2e; --muted:#6b7280; --border:#e5e7eb;
  --green:#16a34a; --green-bg:#f0fdf4; --amber:#d97706; --amber-bg:#fffbeb;
  --red:#dc2626; --red-bg:#fef2f2; --blue:#2563eb; --blue-bg:#eff6ff; --accent:#4f46e5;
}}
html, body {{ height:100%; width:100%; background:#1a1a2e; font-family:'Plus Jakarta Sans',sans-serif; overflow:hidden; }}

.deck {{ width:100vw; height:100vh; position:relative; overflow:hidden; }}

.slide {{
  position:absolute; inset:0; opacity:0; pointer-events:none;
  transform:translateX(60px);
  transition:opacity 0.45s ease, transform 0.45s ease;
  overflow-y:auto; background:var(--cream);
}}
.slide.active {{ opacity:1; pointer-events:all; transform:translateX(0); }}
.slide.exit   {{ opacity:0; transform:translateX(-60px); }}
.slide-inner  {{ max-width:880px; margin:0 auto; padding:52px 48px 110px; min-height:100vh; }}

/* Nav */
.nav {{
  position:fixed; bottom:0; left:0; right:0;
  background:rgba(255,255,255,0.96); backdrop-filter:blur(12px);
  border-top:1px solid var(--border);
  display:flex; align-items:center; justify-content:space-between;
  padding:14px 40px; z-index:100; gap:16px;
}}
.nav-btn {{
  display:flex; align-items:center; gap:8px;
  padding:10px 22px; border-radius:50px;
  border:2px solid var(--border); background:var(--white);
  color:var(--ink); font-family:'Plus Jakarta Sans',sans-serif;
  font-weight:600; font-size:0.875rem; cursor:pointer; transition:all 0.2s;
}}
.nav-btn:hover {{ background:var(--ink); color:white; border-color:var(--ink); }}
.nav-btn:disabled {{ opacity:0.3; cursor:not-allowed; }}
.nav-btn:disabled:hover {{ background:var(--white); color:var(--ink); border-color:var(--border); }}
.dots {{ display:flex; gap:6px; align-items:center; flex-wrap:wrap; justify-content:center; flex:1; }}
.dot {{ width:8px; height:8px; border-radius:50%; background:var(--border); cursor:pointer; transition:all 0.2s; }}
.dot.active {{ background:var(--accent); width:24px; border-radius:4px; }}
.slide-counter {{ font-size:0.75rem; color:var(--muted); font-weight:600; white-space:nowrap; min-width:60px; text-align:right; }}

/* Cover */
.cover {{ background:linear-gradient(145deg,#f8f7ff 0%,#eef2ff 40%,#faf8f5 100%); display:flex; align-items:center; }}
.cover .slide-inner {{ display:flex; flex-direction:column; justify-content:center; min-height:100vh; }}
.cover-eyebrow {{
  display:inline-flex; align-items:center; gap:8px;
  background:white; border:1px solid var(--border); border-radius:50px;
  padding:6px 16px; font-size:0.75rem; font-weight:700; color:var(--accent);
  letter-spacing:0.08em; text-transform:uppercase; margin-bottom:28px; width:fit-content;
}}
.cover-title {{ font-family:'Playfair Display',serif; font-size:clamp(2.2rem,5vw,3.6rem); font-weight:900; color:var(--ink); line-height:1.12; margin-bottom:12px; }}
.cover-domain {{ font-family:'Playfair Display',serif; font-size:clamp(1.2rem,2.5vw,1.8rem); color:var(--accent); margin-bottom:10px; }}
.cover-meta {{ font-size:0.85rem; color:var(--muted); margin-bottom:40px; }}

.score-showcase {{
  display:flex; align-items:center; gap:40px;
  background:white; border:1px solid var(--border); border-radius:24px;
  padding:32px 40px; box-shadow:0 4px 24px rgba(0,0,0,0.06); flex-wrap:wrap;
}}
.score-ring-wrap {{ position:relative; flex-shrink:0; }}
.score-ring-wrap svg {{ transform:rotate(-90deg); }}
.score-ring-label {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
.score-num {{ font-family:'Playfair Display',serif; font-size:2.5rem; font-weight:900; color:{color}; line-height:1; }}
.score-of {{ font-size:0.78rem; color:var(--muted); }}
.score-grade-badge {{ background:{color}; color:white; font-weight:800; font-size:0.68rem; letter-spacing:0.1em; padding:3px 10px; border-radius:20px; margin-top:6px; }}
.score-words {{ flex:1; min-width:180px; }}
.score-verdict {{ font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:700; color:{color}; margin-bottom:8px; }}
.score-verdict-desc {{ font-size:0.88rem; color:var(--muted); line-height:1.6; margin-bottom:20px; }}
.stat-row {{ display:flex; gap:10px; flex-wrap:wrap; }}
.stat-chip {{ display:flex; align-items:center; gap:6px; padding:6px 14px; border-radius:50px; font-size:0.78rem; font-weight:700; }}
.stat-chip.g {{ background:var(--green-bg); color:var(--green); }}
.stat-chip.a {{ background:var(--amber-bg); color:var(--amber); }}
.stat-chip.r {{ background:var(--red-bg);   color:var(--red);   }}

/* Summary slide */
.summary-title {{ font-family:'Playfair Display',serif; font-size:2rem; font-weight:900; color:var(--ink); margin-bottom:6px; }}
.summary-sub {{ color:var(--muted); font-size:0.92rem; margin-bottom:32px; line-height:1.6; }}
.donut-row {{ display:flex; gap:14px; flex-wrap:wrap; margin-bottom:28px; }}
.donut-card {{ flex:1; min-width:110px; background:white; border:1px solid var(--border); border-radius:16px; padding:20px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.04); }}
.donut-num {{ font-family:'Playfair Display',serif; font-size:2rem; font-weight:900; line-height:1; margin-bottom:4px; }}
.donut-lbl {{ font-size:0.75rem; color:var(--muted); font-weight:600; }}
.donut-card.g .donut-num {{ color:var(--green); }}
.donut-card.a .donut-num {{ color:var(--amber); }}
.donut-card.r .donut-num {{ color:var(--red);   }}
.summary-bars {{ display:flex; flex-direction:column; gap:14px; margin-bottom:28px; }}
.bar-row {{ display:flex; flex-direction:column; gap:6px; }}
.bar-label {{ display:flex; justify-content:space-between; font-size:0.85rem; font-weight:600; color:var(--ink); }}
.bar-track {{ height:12px; background:var(--border); border-radius:99px; overflow:hidden; }}
.bar-fill  {{ height:100%; border-radius:99px; }}
.meaning-grid {{ display:flex; gap:12px; flex-wrap:wrap; }}
.meaning-card {{ flex:1; min-width:150px; border-radius:14px; padding:16px; border:1.5px solid; }}
.meaning-card.g {{ background:var(--green-bg); border-color:#bbf7d0; }}
.meaning-card.a {{ background:var(--amber-bg); border-color:#fde68a; }}
.meaning-card.r {{ background:var(--red-bg);   border-color:#fecaca; }}
.meaning-icon {{ font-size:1.3rem; margin-bottom:6px; }}
.meaning-head {{ font-size:0.8rem; font-weight:700; margin-bottom:4px; }}
.meaning-card.g .meaning-head {{ color:var(--green); }}
.meaning-card.a .meaning-head {{ color:var(--amber); }}
.meaning-card.r .meaning-head {{ color:var(--red);   }}
.meaning-body {{ font-size:0.75rem; color:var(--muted); line-height:1.5; }}

/* Category slides */
.cat-header {{ display:flex; align-items:flex-start; gap:18px; margin-bottom:18px; }}
.cat-icon {{ font-size:2.4rem; line-height:1; flex-shrink:0; }}
.cat-title {{ font-family:'Playfair Display',serif; font-size:1.7rem; font-weight:900; color:var(--ink); line-height:1.2; margin-bottom:5px; }}
.cat-tagline {{ font-size:0.88rem; color:var(--muted); line-height:1.5; }}
.cat-summary-bar {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:20px; }}
.mini-pill {{ padding:4px 12px; border-radius:50px; font-size:0.75rem; font-weight:700; }}
.mini-pill.green {{ background:var(--green-bg); color:var(--green); }}
.mini-pill.amber {{ background:var(--amber-bg); color:var(--amber); }}
.mini-pill.red   {{ background:var(--red-bg);   color:var(--red);   }}
.mini-pill.blue  {{ background:var(--blue-bg);  color:var(--blue);  }}
.checks-grid {{ display:flex; flex-direction:column; gap:10px; }}
.check-card {{ border-radius:12px; border:1.5px solid; padding:14px 16px; transition:transform 0.15s; }}
.check-card:hover {{ transform:translateY(-1px); }}
.check-card-top {{ display:flex; align-items:flex-start; gap:12px; }}
.check-emoji {{ font-size:1.3rem; flex-shrink:0; line-height:1.3; }}
.check-info {{ flex:1; }}
.check-title {{ font-size:0.88rem; font-weight:700; color:var(--ink); margin-bottom:3px; }}
.check-desc  {{ font-size:0.76rem; color:var(--muted); line-height:1.5; }}
.check-badge {{ flex-shrink:0; color:white; font-size:0.68rem; font-weight:700; padding:4px 10px; border-radius:50px; white-space:nowrap; align-self:flex-start; }}

/* End slide */
.end-slide {{ background:linear-gradient(145deg,#1a1a2e 0%,#2d2561 100%); }}
.end-slide .slide-inner {{ display:flex; flex-direction:column; justify-content:center; min-height:100vh; }}
.end-title {{ font-family:'Playfair Display',serif; font-size:clamp(1.8rem,4vw,3rem); font-weight:900; color:white; line-height:1.15; margin-bottom:16px; }}
.end-sub {{ font-size:0.95rem; color:rgba(255,255,255,0.6); line-height:1.7; margin-bottom:36px; }}
.end-score-badge {{ display:inline-flex; align-items:center; gap:16px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); border-radius:16px; padding:20px 28px; margin-bottom:36px; }}
.end-score-num {{ font-family:'Playfair Display',serif; font-size:2.6rem; font-weight:900; color:{color}; }}
.end-score-text {{ color:rgba(255,255,255,0.6); font-size:0.85rem; margin-top:2px; }}
.end-footer {{ font-size:0.72rem; color:rgba(255,255,255,0.3); }}

.key-hint {{ position:fixed; top:18px; right:18px; background:rgba(0,0,0,0.55); color:white; font-size:0.68rem; padding:5px 14px; border-radius:50px; opacity:0.65; pointer-events:none; z-index:200; }}

@media(max-width:640px) {{
  .slide-inner {{ padding:28px 18px 100px; }}
  .score-showcase {{ padding:20px; gap:20px; }}
  .nav {{ padding:10px 16px; }}
}}
</style>
</head>
<body>
<div class="key-hint">← → Arrow keys to navigate</div>
<div class="deck" id="deck">

  <!-- SLIDE 1: Cover -->
  <div class="slide cover active" data-slide="1">
    <div class="slide-inner">
      <div class="cover-eyebrow"><span>📊</span> SEO HEALTH REPORT</div>
      <div class="cover-title">How is your website<br>performing on Google?</div>
      <div class="cover-domain">{domain}</div>
      <div class="cover-meta">Report generated on {data["timestamp"]}</div>
      <div class="score-showcase">
        <div class="score-ring-wrap">
          <svg width="130" height="130" viewBox="0 0 130 130">
            <circle cx="65" cy="65" r="54" fill="none" stroke="#e5e7eb" stroke-width="10"/>
            <circle cx="65" cy="65" r="54" fill="none" stroke="{color}" stroke-width="10"
              stroke-linecap="round" stroke-dasharray="{dash_val} 999"/>
          </svg>
          <div class="score-ring-label">
            <div class="score-num">{data["seo_score"]}</div>
            <div class="score-of">out of 100</div>
            <div class="score-grade-badge">GRADE {g}</div>
          </div>
        </div>
        <div class="score-words">
          <div class="score-verdict">{s_label}</div>
          <div class="score-verdict-desc">{s_desc}</div>
          <div class="stat-row">
            <div class="stat-chip g">✓ {data["passed"]} Passed</div>
            <div class="stat-chip a">⚠ {data["warnings"]} Warnings</div>
            <div class="stat-chip r">✗ {data["failed"]} Failed</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- SLIDE 2: Summary -->
  <div class="slide" data-slide="2">
    <div class="slide-inner">
      <div class="summary-title">Here's the big picture</div>
      <div class="summary-sub">Out of <strong>{total_n} total checks</strong> we ran on your website, here's how things broke down. We'll walk you through each one in the next slides.</div>
      <div class="donut-row">
        <div class="donut-card g"><div class="donut-num">{passed_n}</div><div class="donut-lbl">✅ Things working well</div></div>
        <div class="donut-card a"><div class="donut-num">{warnings_n}</div><div class="donut-lbl">⚠️ Could be improved</div></div>
        <div class="donut-card r"><div class="donut-num">{failed_n}</div><div class="donut-lbl">❌ Need fixing now</div></div>
      </div>
      <div class="summary-bars">
        <div class="bar-row">
          <div class="bar-label"><span>✅ Working well</span><span>{p_pct}%</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:{p_pct}%;background:#16a34a;"></div></div>
        </div>
        <div class="bar-row">
          <div class="bar-label"><span>⚠️ Could be improved</span><span>{w_pct}%</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:{w_pct}%;background:#d97706;"></div></div>
        </div>
        <div class="bar-row">
          <div class="bar-label"><span>❌ Need fixing</span><span>{f_pct}%</span></div>
          <div class="bar-track"><div class="bar-fill" style="width:{f_pct}%;background:#dc2626;"></div></div>
        </div>
      </div>
      <div class="meaning-grid">
        <div class="meaning-card g"><div class="meaning-icon">✅</div><div class="meaning-head">Working Well</div><div class="meaning-body">These are set up correctly and actively helping your Google rankings.</div></div>
        <div class="meaning-card a"><div class="meaning-icon">⚠️</div><div class="meaning-head">Could Be Better</div><div class="meaning-body">Not broken, but fixing these could noticeably improve your visibility.</div></div>
        <div class="meaning-card r"><div class="meaning-icon">❌</div><div class="meaning-head">Needs Fixing</div><div class="meaning-body">These issues are actively hurting your chances of ranking on Google.</div></div>
      </div>
    </div>
  </div>

  <!-- CATEGORY SLIDES -->
  {category_slides}

  <!-- END SLIDE -->
  <div class="slide end-slide" data-slide="{total_slides}">
    <div class="slide-inner">
      <div class="cover-eyebrow" style="background:rgba(255,255,255,0.08);border-color:rgba(255,255,255,0.15);color:rgba(255,255,255,0.65);">
        <span>🎯</span> REPORT COMPLETE
      </div>
      <div class="end-title">That's your full<br>SEO health check.</div>
      <div class="end-sub">You've reviewed all {total_n} checks across {len(data["categories"])} categories. Start with the ❌ red items first — they have the biggest impact on your Google rankings. Then work through the ⚠️ warnings.</div>
      <div class="end-score-badge">
        <div class="end-score-num">{data["seo_score"]}/100</div>
        <div>
          <div style="color:white;font-weight:700;font-size:1rem;">{s_label}</div>
          <div class="end-score-text">Overall SEO Score for {domain}</div>
        </div>
      </div>
      <div class="end-footer">Generated using RankMath SEO Analyzer · {data["timestamp"]}</div>
    </div>
  </div>

</div>

<nav class="nav">
  <button class="nav-btn" id="prevBtn" onclick="changeSlide(-1)" disabled>← Back</button>
  <div class="dots" id="dots">{slide_nav_dots}</div>
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
  dots.forEach((d,i) => d.classList.toggle('active', i === cur));
  ctr.textContent = (cur+1) + ' / ' + total;
  prev.disabled = cur === 0;
  next.disabled = cur === total - 1;
  slides[cur].scrollTop = 0;
}}

function changeSlide(dir) {{
  const n = cur + dir;
  if (n >= 0 && n < total) goTo(n);
}}

dots.forEach((d,i) => d.addEventListener('click', () => goTo(i)));
document.querySelectorAll('[data-goto]').forEach(el =>
  el.addEventListener('click', () => goTo(parseInt(el.dataset.goto)-1))
);
document.addEventListener('keydown', e => {{
  if (e.key==='ArrowRight'||e.key==='ArrowDown') changeSlide(1);
  if (e.key==='ArrowLeft' ||e.key==='ArrowUp')   changeSlide(-1);
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

    data = scrape_rankmath(url)

    print("\n📄 Generating slide report...")
    html = generate_report(data)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Report saved → {OUTPUT_HTML}")
    print("   Open in browser. Use ← → arrow keys or buttons to navigate.\n")


if __name__ == "__main__":
    main()