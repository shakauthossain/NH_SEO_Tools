import asyncio
import time
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from jinja2 import Environment, FileSystemLoader

# Initialize Jinja2 environment
# Assuming this file is in backend/app/services/seo_service.py
# Templates are in backend/app/templates/
base_dir = os.path.dirname(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "templates")
jinja_env = Environment(loader=FileSystemLoader(template_dir))

async def scrape_rankmath_async(url: str):
    from playwright.async_api import async_playwright
    data = {
        "url": url,
        "seo_score": "N/A",
        "passed": "0",
        "warnings": "0",
        "failed": "0",
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
                    data["passed"] = lines[i - 1].strip()
                if "Warnings" in line and i > 0:
                    data["warnings"] = lines[i - 1].strip()
                if "Failed Tests" in line and i > 0:
                    data["failed"] = lines[i - 1].strip()
            
            for line in lines:
                if "/" in line and "Tests" not in line and "Warnings" not in line:
                    data["seo_score"] = line.split("/")[0].strip()
                    break

            # Scrape categories
            tables = await page.locator("div.rank-math-result-table").all()
            for table in tables:
                cat_name_el = table.locator("div.category-title")
                cat_name = await cat_name_el.inner_text() if await cat_name_el.count() > 0 else "Analysis"
                
                rows = await table.locator("div.table-row").all()
                items = []
                for row in rows:
                    title_el = row.locator("div.row-title")
                    content_el = row.locator("div.row-content")
                    
                    if await title_el.count() == 0: continue
                    
                    title = await title_el.inner_text()
                    content = await content_el.inner_text() if await content_el.count() > 0 else ""
                    
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
    """Generates the premium Slide-Deck HTML report for SEO."""
    try:
        # 1. Parse numeric values
        # Handle cases where value might be 'N/A' or have strings
        def to_int(v):
            if not v: return 0
            if isinstance(v, int): return v
            s = "".join(filter(str.isdigit, str(v)))
            return int(s) if s else 0

        score = to_int(data.get("seo_score"))
        p = to_int(data.get("passed"))
        w = to_int(data.get("warnings"))
        f = to_int(data.get("failed"))
        
        total = p + w + f
        if total == 0: total = p + w + f # Defensive
        if total == 0: total = 1 
        
        # 2. Derived metrics
        domain = data["url"].replace("https://", "").replace("http://", "").split("/")[0]
        grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
        verdict = "Excellent" if score >= 90 else "Good" if score >= 80 else "Needs Work" if score >= 60 else "Critical"
        
        # 3. Gauge Dash Offsets (Circumference 377 for r=60)
        circ = 377
        dash_working = round(circ * (1 - p / total), 2)
        dash_warnings = round(circ * (1 - w / total), 2)
        dash_failed = round(circ * (1 - f / total), 2)
        
        # 4. Percentages for gauges
        pct_working = round((p / total) * 100)
        pct_warnings = round((w / total) * 100)
        pct_failed = round((f / total) * 100)
        
        # 5. Total Slides tracking
        num_categories = len(data.get("categories", []))
        total_slides = num_categories + 3 # Cover + Summary + Marketing
        
        template_data = {
            **data,
            "seo_score": score,
            "passed": p,
            "warnings": w,
            "failed": f,
            "domain": domain,
            "grade": grade,
            "verdict": verdict,
            "total_checks": total,
            "total_slides": total_slides,
            "dash_working": dash_working,
            "dash_warnings": dash_warnings,
            "dash_failed": dash_failed,
            "pct_working": pct_working,
            "pct_warnings": pct_warnings,
            "pct_failed": pct_failed,
            "timestamp": data.get("timestamp", datetime.now().strftime("%B %d, %Y"))
        }

        template = jinja_env.get_template("seo_report.html")
        return template.render(**template_data)
        
    except Exception as e:
        print(f"--- ERROR rendering template: {e} ---")
        import traceback
        traceback.print_exc()
        return f"<h1>Error generating report: {e}</h1>"
