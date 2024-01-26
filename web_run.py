import asyncio
import glob


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import time
import subprocess


async def process_with_selenium(url, options, resolution, session_id, current_time):
    # Configure Selenium WebDriver options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Enable headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-cache")

    # Set browser window size based on the selected resolution
    width, height = map(int, resolution.split("x"))
    chrome_options.add_argument(f"--window-size={width},{height}")

    # Options processing
    if "disableJavascript" in options:
        print("Disabling javascript.......", session_id)
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.javascript": 2}
        )

    if "disableImages" in options:
        print("Disabling images.......", session_id)
        chrome_options.add_argument("--disable-images")
        chrome_options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )

    # Set up capabilities to capture browser logs
    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"browser": "ALL"}
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    # Load strategy to 'none' to return immediately after the initial page content is received
    chrome_options.page_load_strategy = "none"

    # Initialize WebDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    if "disableCSS" in options:
        print("Disabling css.......", session_id)
        chrome_options.add_argument("--disable-css")
        disable_css_script = """
        for (let i = 0; i < document.styleSheets.length; i++) {
            document.styleSheets[i].disabled = true;
        }
        """
        driver.execute_script(disable_css_script)

    if "slowNetwork" in options:
        print("Slow network.......", session_id)
        driver.set_network_conditions(
            offline=False,
            latency=250,  # 250ms of latency
            download_throughput=100 * 1024,  # 100 kb/s
            upload_throughput=100 * 1024,
        )
    if "offlineMode" in options:
        print("Offline mode.......", session_id)
        driver.set_network_conditions(
            offline=True,
            latency=0,
            download_throughput=0,
            upload_throughput=0,
        )

    if "highLatency" in options:
        print("High latency.......", session_id)
        driver.set_network_conditions(
            latency=1000,  # 1000ms of latency
            download_throughput=500 * 1024,  # 500 kb/s
            upload_throughput=500 * 1024,
        )

    # Test run option name
    options_str = "_".join(options).lower() if options else "default"

    # Create directories for screenshots and logs
    screenshots_dir = f"static/{session_id}/screenshots"
    logs_dir = f"static/{session_id}/logs"
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    # Start taking screenshots before we get the webpage
    # in an attempt to capture the loading process
    screenshot_task = asyncio.create_task(
        capture_load_screenshots(
            driver,
            interval=0.001,
            duration=20,
            screenshots_dir=screenshots_dir,
            options_str=options_str,
        )
    )

    driver.get(url)

    await screenshot_task
    print("Finished capturing screenshots", options_str)

    # Create a video using the options_str
    video_filename = create_filename(url, options_str, "video.mp4")
    create_video_from_screenshots(
        screenshots_dir,
        os.path.join(f"static/{session_id}", video_filename),
        options_str,
    )

    # Extract console logs
    logs = driver.get_log("browser")
    log_filename = create_filename(url, options_str, "console.log")

    with open(os.path.join(logs_dir, log_filename), "w") as file:
        for entry in logs:
            file.write(f"{entry['level']} - {entry['message']}\n")

    driver.quit()

    return (
        session_id,
        log_filename,
        options,
        video_filename,
    )


# C
def create_filename(url, options_str, file_type):
    sanitized_url = url.replace("http://", "").replace("https://", "").replace("/", "_")
    filename = f"{sanitized_url}_{options_str}_{file_type}"
    return filename


async def capture_load_screenshots(
    driver, interval, duration, screenshots_dir, options_str
):
    start_time = time.time()
    while time.time() - start_time < duration:
        screenshot_filename = (
            f"{screenshots_dir}/{int(time.time() - start_time)}-{options_str}.png"
        )
        driver.save_screenshot(screenshot_filename)
        await asyncio.sleep(interval)


def create_video_from_screenshots(screenshots_dir, output_file, options_str):
    absolute_screenshots_dir = os.path.abspath(screenshots_dir)
    absolute_output_file = os.path.abspath(output_file)

    pattern = f"{absolute_screenshots_dir}/*-{options_str}.png"

    # Check if there are any files matching the pattern
    if not glob.glob(pattern):
        print(f"No images found for pattern: {pattern}")
        return

    ffmpeg_command = [
        "ffmpeg",
        "-framerate",
        "24",
        "-pattern_type",
        "glob",
        "-i",
        pattern,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        absolute_output_file,
    ]
    print("Processing video for", options_str, "......")
    subprocess.run(ffmpeg_command)
