from playwright.async_api import async_playwright
import os

async def generate_pdf(html_content: str, output_path: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Set content from HTML string
        await page.set_content(html_content, wait_until="networkidle")
        # Ensure we wait long enough for graphs or animations to settle (if any)
        # For PDFs, we usually wait a bit extra
        import asyncio
        await asyncio.sleep(2)
        
        # Print to PDF
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "0cm", "bottom": "0cm", "left": "0cm", "right": "0cm"},
            prefer_css_page_size=True,
            landscape=True
        )
        await browser.close()
