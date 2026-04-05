import requests
from datetime import datetime
from typing import Optional

def fetch_pagespeed_data_sync(url: str, api_key: str, strategy: str = "mobile"):
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url":      url,
        "key":      api_key,
        "strategy": strategy,
        "category": ["performance"],
    }

    resp = requests.get(endpoint, params=params, timeout=60)
    if resp.status_code != 200:
        print(f"--- ERROR: PageSpeed API {resp.status_code} for {url} ---")
        print(f"--- DETAIL: {resp.text[:200]} ---")
        return None
    return resp.json()

def parse_pagespeed_data(raw: dict, url: str, strategy: str):
    lhr = raw.get("lighthouseResult", {})
    cats = lhr.get("categories", {})
    audits = lhr.get("audits", {})

    def score(cat_key):
        s = cats.get(cat_key, {}).get("score")
        return round(s * 100) if s is not None else "N/A"

    def ms_val(key):
        val = audits.get(key, {}).get("numericValue")
        return val

    def ms_str(key):
        val = ms_val(key)
        if val is None: return "N/A"
        if val >= 1000: return f"{val/1000:.1f}s"
        return f"{round(val)}ms"

    lcp_raw = ms_val("largest-contentful-paint")
    tbt_raw = ms_val("total-blocking-time")
    cls_raw = ms_val("cumulative-layout-shift")
    fcp_raw = ms_val("first-contentful-paint")
    si_raw  = ms_val("speed-index")
    tti_raw = ms_val("interactive")

    def get_perf_items(group_ids):
        items = []
        for audit_id in group_ids:
            audit = audits.get(audit_id, {})
            title = audit.get("title", "")
            description = audit.get("description", "")
            s = audit.get("score")
            display_val = audit.get("displayValue", "")
            if not title: continue

            if s is None: status = "info"
            elif s >= 0.9: status = "pass"
            elif s >= 0.5: status = "warning"
            else: status = "fail"

            detail = display_val if display_val else (description[:150] + "…" if len(description) > 150 else description)
            items.append({"title": title, "content": detail, "status": status})
        return items

    speed_groups = [
        {"icon": "🖼️", "name": "Images & Media", "tagline": "Unoptimized images are a main cause of slowness.", "ids": ["uses-optimized-images", "uses-webp-images", "uses-responsive-images", "uses-lazy-loading", "offscreen-images"]},
        {"icon": "📦", "name": "Code & Scripts", "tagline": "Heavy JS ruins interactivity.", "ids": ["unused-javascript", "unused-css-rules", "unminified-javascript", "unminified-css", "render-blocking-resources", "bootup-time"]},
        {"icon": "🌐", "name": "Server & Network", "tagline": "Fast hosting is critical.", "ids": ["uses-text-compression", "server-response-time", "redirects", "efficient-cache-policy"]},
    ]

    categories = []
    for grp in speed_groups:
        items = get_perf_items(grp["ids"])
        if items:
            categories.append({"icon": grp["icon"], "name": grp["name"], "tagline": grp["tagline"], "items": items})

    return {
        "url": url,
        "strategy": strategy,
        "timestamp": datetime.now().strftime("%B %d, %Y at %H:%M"),
        "perf_score": score("performance"),
        "lcp": ms_str("largest-contentful-paint"),
        "tbt": ms_str("total-blocking-time"),
        "cls": f"{cls_raw:.3f}" if cls_raw is not None else "N/A",
        "fcp": ms_str("first-contentful-paint"),
        "si": ms_str("speed-index"),
        "tti": ms_str("interactive"),
        "categories": categories,
    }

def generate_html(data: dict):
    """Generates a premium HTML report for Speed data."""
    categories_html = ""
    for cat in data.get("categories", []):
        items_html = ""
        for item in cat.get("items", []):
            status_color = "text-green-500" if item['status'] == 'pass' else "text-yellow-500" if item['status'] == 'warning' else "text-red-500"
            items_html += f'''
            <div class="border-b border-gray-100 py-4">
                <div class="flex items-center gap-2 mb-1">
                    <span class="font-bold {status_color} uppercase text-xs tracking-widest">{item['status']}</span>
                    <h4 class="font-semibold text-gray-800">{item['title']}</h4>
                </div>
                <p class="text-gray-600 text-sm leading-relaxed">{item['content']}</p>
            </div>
            '''
        categories_html += f'''
        <div class="mb-12">
            <h3 class="text-2xl font-bold text-gray-900 border-l-4 border-yellow-500 pl-4 mb-2">{cat['icon']} {cat['name']}</h3>
            <p class="text-gray-500 mb-6 italic pl-5">{cat['tagline']}</p>
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
                {items_html}
            </div>
        </div>
        '''

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Speed Audit: {data['url']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #fffbeb; color: #111827; }}
        </style>
    </head>
    <body class="py-12">
        <div class="max-w-4xl mx-auto px-6">
            <header class="mb-16">
                <div class="flex items-center justify-between mb-8">
                    <div>
                        <h1 class="text-4xl font-extrabold tracking-tight mb-2">Page Experience Report</h1>
                        <p class="text-gray-500 flex items-center gap-2">
                             Performance for <span class="font-semibold text-yellow-600">{data['url']}</span>
                        </p>
                    </div>
                    <div class="bg-yellow-500 text-white w-24 h-24 rounded-3xl flex flex-col items-center justify-center shadow-xl shadow-yellow-200">
                        <span class="text-xs font-bold uppercase opacity-80 mb-1">Score</span>
                        <span class="text-3xl font-black">{data['perf_score']}</span>
                    </div>
                </div>
                <div class="grid grid-cols-4 gap-4">
                    <div class="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm text-center">
                        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest block mb-1">LCP</span>
                        <span class="text-xl font-bold">{data['lcp']}</span>
                    </div>
                    <div class="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm text-center">
                        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest block mb-1">FCP</span>
                        <span class="text-xl font-bold">{data['fcp']}</span>
                    </div>
                    <div class="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm text-center">
                        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest block mb-1">CLS</span>
                        <span class="text-xl font-bold">{data['cls']}</span>
                    </div>
                    <div class="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm text-center">
                        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest block mb-1">TBT</span>
                        <span class="text-xl font-bold">{data['tbt']}</span>
                    </div>
                </div>
            </header>
            
            {categories_html}

            <footer class="mt-20 pt-8 border-t border-gray-200 text-center text-gray-400 text-sm italic">
                Report generated on {data['timestamp']} &bull; Antigravity Speed Engine
            </footer>
        </div>
    </body>
    </html>
    '''
