import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_rankmath_async(url: str):
    data = {
        "url": url,
        "seo_score": "N/A",
        "passed": "N/A",
        "warnings": "N/A",
        "failed": "N/A",
        "categories": [],
        "timestamp": datetime.now().strftime("%B %d, %Y at %H:%M"),
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        try:
            await page.goto("https://rankmath.com/tools/seo-analyzer/", timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

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
                    await el.wait_for(timeout=3000, state="visible")
                    input_box = el
                    break
                except Exception:
                    continue

            if input_box is None:
                try:
                    input_box = page.locator("input").first
                    await input_box.wait_for(timeout=5000, state="visible")
                except Exception:
                    await browser.close()
                    return data

            await input_box.click()
            await input_box.fill("")
            await input_box.type(url, delay=50)

            # Find button
            btn = None
            for sel in [
                "button#analyze", "button[type='submit']", "input[type='submit']",
                "button:has-text('Analyze')", "button:has-text('Check')",
                ".analyzer button", "form button",
            ]:
                try:
                    el = page.locator(sel).first
                    await el.wait_for(timeout=3000, state="visible")
                    btn = el
                    break
                except Exception:
                    continue

            if btn:
                await btn.click()
            else:
                await input_box.press("Enter")

            # Wait for results
            result_found = False
            for sel in [
                "div.container.analysis-result.clear", "div.analysis-result",
                ".rank-math-result-graphs", "#analysis", "[class*='result']",
            ]:
                try:
                    await page.wait_for_selector(sel, timeout=60000)
                    result_found = True
                    break
                except Exception:
                    continue

            if not result_found:
                await browser.close()
                return data

            await asyncio.sleep(3)

            # Scrape score
            graphs = page.locator("div.rank-math-result-graphs")
            text = await graphs.inner_text()
            lines = [l.strip() for l in text.splitlines() if l.strip()]

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

            # Scrape categories
            tables = await page.locator("div.rank-math-result-table").all()
            for table in tables:
                cat_name = await table.locator("div.category-title").inner_text()
                rows = await table.locator("div.table-row").all()
                items = []
                for row in rows:
                    title = await row.locator("div.row-title").inner_text()
                    content = await row.locator("div.row-content").inner_text()
                    status = "info"
                    try:
                        ic = await row.locator("div.status-icon").get_attribute("class") or ""
                        if any(x in ic for x in ["check", "good", "success"]): status = "pass"
                        elif any(x in ic for x in ["warning", "warn"]): status = "warning"
                        elif any(x in ic for x in ["times", "error", "fail"]): status = "fail"
                    except: pass
                    items.append({"title": title.strip(), "content": content.strip(), "status": status})
                if items:
                    data["categories"].append({"name": cat_name.strip(), "items": items})

        except Exception as e:
            print(f"Error scraping SEO: {e}")
        finally:
            await browser.close()
            return data

def generate_html(data: dict):
    """Generates a premium HTML report for SEO data."""
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
            <h3 class="text-2xl font-bold text-gray-900 border-l-4 border-indigo-600 pl-4 mb-6">{cat['name']}</h3>
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
        <title>SEO Audit: {data['url']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #f9fafb; color: #111827; }}
            .glass {{ background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); }}
        </style>
    </head>
    <body class="py-12">
        <div class="max-w-4xl mx-auto px-6">
            <header class="mb-16">
                <div class="flex items-center justify-between mb-8">
                    <div>
                        <h1 class="text-4xl font-extrabold tracking-tight mb-2">SEO Audit Report</h1>
                        <p class="text-gray-500 flex items-center gap-2">
                             Analysis for <span class="font-semibold text-indigo-600">{data['url']}</span>
                        </p>
                    </div>
                    <div class="bg-indigo-600 text-white w-24 h-24 rounded-3xl flex flex-col items-center justify-center shadow-xl shadow-indigo-200">
                        <span class="text-xs font-bold uppercase opacity-80 mb-1">Score</span>
                        <span class="text-3xl font-black">{data['seo_score']}</span>
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-6">
                    <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                        <span class="text-xs font-bold text-green-600 uppercase tracking-widest block mb-1">Passed</span>
                        <span class="text-2xl font-bold">{data['passed']}</span>
                    </div>
                    <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                        <span class="text-xs font-bold text-yellow-600 uppercase tracking-widest block mb-1">Warnings</span>
                        <span class="text-2xl font-bold">{data['warnings']}</span>
                    </div>
                    <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                        <span class="text-xs font-bold text-red-600 uppercase tracking-widest block mb-1">Errors</span>
                        <span class="text-2xl font-bold">{data['failed']}</span>
                    </div>
                </div>
            </header>
            
            {categories_html}

            <footer class="mt-20 pt-8 border-t border-gray-200 text-center text-gray-400 text-sm italic">
                Report generated on {data['timestamp']} &bull; Antigravity SEO Engine
            </footer>
        </div>
    </body>
    </html>
    '''
