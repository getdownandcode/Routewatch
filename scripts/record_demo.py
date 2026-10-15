"""Record high-definition automated browser walkthrough video for Routewatch."""

import os
import subprocess
import time
from pathlib import Path
import urllib.request
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUTPUT_DIR = Path("outputs")
TEMP_VIDEO_DIR = OUTPUT_DIR / "temp_video"
FINAL_MP4 = OUTPUT_DIR / "routewatch_demo.mp4"


def wait_for_server(url: str, timeout: float = 30.0):
    """Wait until the web server is responding."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def inject_mouse_cursor(page):
    """Inject a visual cursor to follow clicks and moves on screen."""
    page.evaluate("""
    () => {
        if (document.getElementById('demo-cursor')) return;
        const cursor = document.createElement('div');
        cursor.id = 'demo-cursor';
        cursor.style.width = '24px';
        cursor.style.height = '24px';
        cursor.style.border = '2.5px solid #FFFFFF';
        cursor.style.backgroundColor = '#F2A900';
        cursor.style.borderRadius = '50%';
        cursor.style.position = 'fixed';
        cursor.style.pointerEvents = 'none';
        cursor.style.zIndex = '999999';
        cursor.style.transition = 'left 0.4s cubic-bezier(0.25, 1, 0.5, 1), top 0.4s cubic-bezier(0.25, 1, 0.5, 1), transform 0.15s ease, background-color 0.15s ease';
        cursor.style.transform = 'translate(-50%, -50%)';
        cursor.style.boxShadow = '0 3px 12px rgba(0,0,0,0.45)';
        cursor.style.top = '120px';
        cursor.style.left = '120px';
        document.body.appendChild(cursor);

        window.moveCursorTo = (x, y) => {
            cursor.style.left = x + 'px';
            cursor.style.top = y + 'px';
        };

        window.clickCursor = () => {
            cursor.style.transform = 'translate(-50%, -50%) scale(0.65)';
            cursor.style.backgroundColor = '#0B5D3B';
            setTimeout(() => {
                cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                cursor.style.backgroundColor = '#F2A900';
            }, 250);
        };
    }
    """)


def animate_mouse_to(page, selector_or_coords, click=True, delay=0.8):
    """Smoothly animate the visual cursor to an element or coordinate."""
    try:
        if isinstance(selector_or_coords, str):
            box = page.locator(selector_or_coords).first.bounding_box()
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
            else:
                return
        else:
            x, y = selector_or_coords

        page.evaluate(f"window.moveCursorTo && window.moveCursorTo({x}, {y})")
        time.sleep(0.45)
        if click:
            page.evaluate("window.clickCursor && window.clickCursor()")
            time.sleep(0.25)
        time.sleep(delay)
    except Exception as e:
        print(f"Cursor animation note: {e}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Start Streamlit server on clean port
    port = 8507
    app_url = f"http://127.0.0.1:{port}"
    print(f"Starting Streamlit app on {app_url}...")
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    server_process = subprocess.Popen(
        [".venv/bin/streamlit", "run", "app/app.py", "--server.port", str(port), "--server.headless", "true"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        print(f"Waiting for {app_url} to be ready...")
        if not wait_for_server(app_url):
            raise RuntimeError("Streamlit server failed to start within timeout.")
        print("Streamlit app is ready!")

        # 2. Launch Playwright with video recording
        with sync_playwright() as p:
            print("Launching Chrome and setting up recording context...")
            browser = p.chromium.launch(
                executable_path=CHROME_PATH,
                headless=True,
            )

            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                record_video_dir=str(TEMP_VIDEO_DIR),
                record_video_size={"width": 1280, "height": 720},
            )

            page = context.new_page()
            page.goto(app_url)
            page.wait_for_selector(".brand-header", timeout=15000)
            time.sleep(1.0)
            inject_mouse_cursor(page)

            print("Scene 1: App Overview & Metric Strip")
            time.sleep(3.5)

            print("Scene 2: Filter by Status")
            # Selectbox 1 is Status (index 1)
            status_selectbox = page.locator("div[data-testid='stSelectbox']").nth(1)
            status_box = status_selectbox.bounding_box()
            if status_box:
                animate_mouse_to(page, (status_box['x'] + 80, status_box['y'] + 25))
                status_selectbox.click()
                time.sleep(0.8)

                # Select "Needs Review (Unexplained)"
                needs_review_opt = page.locator("li[role='option']:has-text('Needs Review')")
                if needs_review_opt.count() > 0:
                    opt_box = needs_review_opt.first.bounding_box()
                    if opt_box:
                        animate_mouse_to(page, (opt_box['x'] + 80, opt_box['y'] + 15))
                    needs_review_opt.first.click()
                    time.sleep(2.5)

                # Select "Explained (Justified)"
                status_selectbox.click()
                time.sleep(0.8)
                justified_opt = page.locator("li[role='option']:has-text('Explained')")
                if justified_opt.count() > 0:
                    opt_box = justified_opt.first.bounding_box()
                    if opt_box:
                        animate_mouse_to(page, (opt_box['x'] + 80, opt_box['y'] + 15))
                    justified_opt.first.click()
                    time.sleep(2.5)

                # Reset to "All Statuses"
                status_selectbox.click()
                time.sleep(0.8)
                all_opt = page.locator("li[role='option']:has-text('All Statuses')")
                if all_opt.count() > 0:
                    opt_box = all_opt.first.bounding_box()
                    if opt_box:
                        animate_mouse_to(page, (opt_box['x'] + 80, opt_box['y'] + 15))
                    all_opt.first.click()
                    time.sleep(1.5)

            print("Scene 3: Inspect Justified Corridor Details (Chennai-Bangalore)")
            corridor_select = page.locator("div[data-testid='stSelectbox']").nth(2)
            corridor_box = corridor_select.bounding_box()
            if corridor_box:
                animate_mouse_to(page, (corridor_box['x'] + 100, corridor_box['y'] + 25))
                corridor_select.click()
                time.sleep(0.8)
                cb_opt = page.locator("li[role='option']:has-text('Chennai-Bangalore')")
                if cb_opt.count() > 0:
                    opt_box = cb_opt.first.bounding_box()
                    if opt_box:
                        animate_mouse_to(page, (opt_box['x'] + 120, opt_box['y'] + 15))
                    cb_opt.first.click()
                    time.sleep(1.0)

            # Smoothly scroll down to inspect evidence card & plotly chart
            page.evaluate("window.scrollBy({top: 300, behavior: 'smooth'});")
            time.sleep(4.0)

            print("Scene 4: Inspect Unexplained Corridor Details")
            page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'});")
            time.sleep(1.0)
            corridor_select.click()
            time.sleep(0.8)
            unexp_opt = page.locator("li[role='option']:has-text('Needs Review')")
            if unexp_opt.count() > 0:
                opt_box = unexp_opt.first.bounding_box()
                if opt_box:
                    animate_mouse_to(page, (opt_box['x'] + 120, opt_box['y'] + 15))
                unexp_opt.first.click()
                time.sleep(1.0)

            page.evaluate("window.scrollBy({top: 300, behavior: 'smooth'});")
            time.sleep(4.0)

            print("Scene 5: Grounded Q&A Assistant")
            page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'});")
            time.sleep(1.0)

            # Click Tab 2: Grounded Q&A
            tab2 = page.get_by_text("Ask Routewatch (Grounded Q&A)").first
            tab_box = tab2.bounding_box()
            if tab_box:
                animate_mouse_to(page, (tab_box['x'] + tab_box['width'] / 2, tab_box['y'] + tab_box['height'] / 2))
            tab2.click()
            time.sleep(1.5)
            inject_mouse_cursor(page)

            # Click preset chip question 1: Chennai-Bangalore
            chip1 = page.locator("button:has-text('Why did Chennai-Bangalore get pricier')").first
            chip_box = chip1.bounding_box()
            if chip_box:
                animate_mouse_to(page, (chip_box['x'] + chip_box['width'] / 2, chip_box['y'] + chip_box['height'] / 2))
            chip1.click()
            time.sleep(1.5)
            inject_mouse_cursor(page)

            # Click "Ask Assistant"
            ask_btn = page.locator("button:has-text('Ask Assistant')").first
            btn_box = ask_btn.bounding_box()
            if btn_box:
                animate_mouse_to(page, (btn_box['x'] + btn_box['width'] / 2, btn_box['y'] + btn_box['height'] / 2))
            ask_btn.click()

            time.sleep(2.0)
            page.evaluate("window.scrollBy({top: 150, behavior: 'smooth'});")
            time.sleep(4.0)

            # Click preset chip question 2: Which flags have no explanation?
            page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'});")
            time.sleep(1.0)
            chip2 = page.locator("button:has-text('Which flags have no explanation?')").first
            chip_box = chip2.bounding_box()
            if chip_box:
                animate_mouse_to(page, (chip_box['x'] + chip_box['width'] / 2, chip_box['y'] + chip_box['height'] / 2))
            chip2.click()
            time.sleep(1.5)
            inject_mouse_cursor(page)

            ask_btn = page.locator("button:has-text('Ask Assistant')").first
            btn_box = ask_btn.bounding_box()
            if btn_box:
                animate_mouse_to(page, (btn_box['x'] + btn_box['width'] / 2, btn_box['y'] + btn_box['height'] / 2))
            ask_btn.click()

            time.sleep(2.0)
            page.evaluate("window.scrollBy({top: 150, behavior: 'smooth'});")
            time.sleep(4.0)

            # Final wrap up pause
            page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'});")
            time.sleep(2.5)

            print("Closing browser and finalizing video...")
            page.close()
            context.close()
            browser.close()

    finally:
        print("Terminating Streamlit server...")
        server_process.terminate()
        server_process.wait()

    # 3. Transcode with FFmpeg to MP4
    webm_files = list(TEMP_VIDEO_DIR.glob("*.webm"))
    if not webm_files:
        raise RuntimeError("No recorded video file found in temp directory.")

    input_webm = webm_files[0]
    print(f"Transcoding {input_webm} to {FINAL_MP4} via FFmpeg...")

    cmd = [
        "/opt/homebrew/bin/ffmpeg",
        "-y",
        "-i", str(input_webm),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(FINAL_MP4),
    ]

    subprocess.run(cmd, check=True)

    # Clean up temp webm
    for f in TEMP_VIDEO_DIR.glob("*"):
        f.unlink()
    TEMP_VIDEO_DIR.rmdir()

    print(f"SUCCESS: Video saved to {FINAL_MP4}")


if __name__ == "__main__":
    main()
