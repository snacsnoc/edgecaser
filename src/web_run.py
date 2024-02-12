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
from concurrent.futures import ThreadPoolExecutor

# Initialize a ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)


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
    print(f"Session {session_id} starting with options: {options}")
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

    # Start taking screenshots in intervals before we get the webpage
    # in an attempt to capture the loading process
    # await asyncio.create_task(
    #     capture_load_screenshots(
    #         driver,
    #         interval=0.01,
    #         duration=15,
    #         screenshots_dir=screenshots_dir,
    #         options_str=options_str,
    #     )
    # )

    # Start at a blank page
    driver.get("about:blank")

    # Wait for the page to load
    await asyncio.sleep(1)

    start_time = time.time()  # Time in seconds

    driver.execute_script(f"window.location = '{url}'")

    # Get navigation timing data
    timing_script = """
    return window.performance.timing.toJSON();
    """

    navigation_timing = driver.execute_script(timing_script)

    # print(f"Navigation timing {navigation_timing}")

    # Calculate the timing of when to take screenshots based on navigation events
    # Use this with capture_response_screenshots()
    # timings = calculate_delays(navigation_timing, start_time)

    # Start the screenshot task
    screenshot_task = asyncio.create_task(
        dynamic_interval_screenshot_capture(
            driver, start_time, screenshots_dir, options_str
        )
    )

    # Apply options that require the page to be loaded/loading
    if "disableImagesJS" in options:
        print("Disabling images.......", session_id)
        disable_images_script = """
        var imgs = document.images;
        for (var i = 0; i < imgs.length; i++) {
            imgs[i].src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
        }
        """
        driver.execute_script(disable_images_script)

    if "disableCSS" in options:
        print("Applying disableCSS after page load.......", session_id)
        disable_css_script = """
        for (let i = 0; i < document.styleSheets.length; i++) {
            document.styleSheets[i].disabled = true;
        }
        """
        driver.execute_script(disable_css_script)

    await screenshot_task
    # Extract console logs
    logs = driver.get_log("browser")
    log_filename = create_filename(url, options_str, "console.log")

    with open(os.path.join(logs_dir, log_filename), "w") as file:
        for entry in logs:
            file.write(f"{entry['level']} - {entry['message']}\n")

    print("Finished capturing screenshots", options_str)

    # Create a video using the options_str
    video_filename = create_filename(url, options_str, "video.mp4")
    create_video_from_screenshots(
        screenshots_dir,
        os.path.join(f"static/{session_id}", video_filename),
        options_str,
    )
    driver.quit()
    print(f"Session {session_id} completed.")
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


# Calculate the timing of when to take screenshots based on navigation events
def calculate_delays(navigation_timing, start_time):
    current_time = time.time() * 1000  # Current time in milliseconds
    navigation_start = navigation_timing["navigationStart"]

    def calc_delay(event_time):
        return (event_time - navigation_start) / 1000.0 - (
            current_time - start_time
        ) / 1000.0

    # Calculate delays for all events
    events = [
        "connectEnd",
        "connectStart",
        "domComplete",
        "domContentLoadedEventEnd",
        "domContentLoadedEventStart",
        "domInteractive",
        "domLoading",
        "domainLookupEnd",
        "domainLookupStart",
        "fetchStart",
        "loadEventEnd",
        "loadEventStart",
        "requestStart",
        "responseEnd",
        "responseStart",
        "secureConnectionStart",
    ]

    return [
        (event, calc_delay(navigation_timing[event]))
        for event in events
        if navigation_timing[event] != 0
    ]


# Capture screenshots by dynamic intervals (0.01s, 0.1s, 1s, 10s)
async def dynamic_interval_screenshot_capture(
    driver, start_time, screenshots_dir, options_str
):
    elapsed_time = 0
    while elapsed_time < 26:
        interval = (
            0.001 if elapsed_time < 5 else 0.1
        )  # Shorter intervals in the first 5 seconds
        screenshot_filename = (
            f"{screenshots_dir}/{int(time.time() - start_time)}-{options_str}.png"
        )

        await take_screenshot(driver, screenshot_filename)
        await asyncio.sleep(interval)
        elapsed_time = time.time() - start_time


# Capture screenshots by navigation timing
async def capture_response_screenshots(driver, timings, screenshots_dir, options_str):
    for timing in timings:
        event_name, delay = timing
        if delay > 0:
            await asyncio.sleep(delay)
        screenshot_filename = f"{screenshots_dir}/{event_name}-{options_str}.png"
        await take_screenshot(driver, screenshot_filename)


# Capture screenshots by intervals
async def capture_load_screenshots(
    driver, interval, duration, screenshots_dir, options_str
):
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            screenshot_filename = (
                f"{screenshots_dir}/{int(time.time() - start_time)}-{options_str}.png"
            )
            # driver.save_screenshot(screenshot_filename)
            await take_screenshot(driver, screenshot_filename)

        except Exception as e:
            print(f"Error capturing screenshot: {e}")
        await asyncio.sleep(interval)


async def take_screenshot(driver, filename):
    loop = asyncio.get_running_loop()
    # Use run_in_executor to run the blocking function in a separate thread
    await loop.run_in_executor(executor, driver.save_screenshot, filename)


def create_video_from_screenshots(
    screenshots_dir, output_file, options_str, video_duration=10
):
    absolute_screenshots_dir = os.path.abspath(screenshots_dir)
    absolute_output_file = os.path.abspath(output_file)

    pattern = f"{absolute_screenshots_dir}/*-{options_str}.png"

    screenshot_files = glob.glob(pattern)
    # Check if there are any files matching the pattern
    if not screenshot_files:
        print(f"No images found for pattern: {pattern}")
        return
    # Calculate frame rate
    frame_count = len(screenshot_files)
    frame_rate = max(1, frame_count / video_duration)  # Ensure frame rate is at least 1
    print("Frame rate:", frame_rate)
    print("Creating video for ", options_str, "......")
    ffmpeg_command = [
        "ffmpeg",
        "-framerate",
        "1",  # Manually set or use str(frame_rate)
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
    print("Processed video for", options_str, " !")
