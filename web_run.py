import threading

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import time
import subprocess


def process_with_selenium(url, options, resolution, session_id, current_time):
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

    max_time = 15
    # Options processing
    if "disableJavascript" in options:
        print("Disabling javascript........", session_id)
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.javascript": 2}
        )

    if "disableImages" in options:
        print("Disabling images........", session_id)
        chrome_options.add_argument("--disable-images")
        chrome_options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )
    # Set up capabilities to capture browser logs
    caps = DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"browser": "ALL"}
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    # Initialize WebDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )

    if "disableCSS" in options:
        print("Disabling css........", session_id)
        chrome_options.add_argument("--disable-css")
        disable_css_script = """
        for (let i = 0; i < document.styleSheets.length; i++) {
            document.styleSheets[i].disabled = true;
        }
        """
        driver.execute_script(disable_css_script)

    # Apply network conditions if selected

    if "slowNetwork" in options:
        print("Slow network.......", session_id)
        driver.set_network_conditions(
            offline=False,
            latency=5,  # 5ms of latency
            download_throughput=100 * 1024,  # 100 kb/s
            upload_throughput=100 * 1024,
        )
    if "offlineMode" in options:
        print("Offline mode", session_id)
        driver.set_network_conditions(
            offline=True,
            latency=0,
            download_throughput=0,
            upload_throughput=0,
        )

    if "highLatency" in options:
        print("High latency", session_id)
        driver.set_network_conditions(
            latency=1000,
            download_throughput=500 * 1024,  # 500 kb/s
            upload_throughput=500 * 1024,
        )  # 1000ms of latency

    # Test run options
    options_str = "_".join(options).lower() if options else "default"

    # Create directories for screenshots and logs
    screenshots_dir = f"static/{session_id}/screenshots"
    logs_dir = f"static/{session_id}/logs"
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    def capture_screenshots():
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > max_time:
                break
            screenshot_filename = create_filename(
                url, f"{options_str}_{elapsed_time:.1f}", "screenshot.png"
            )
            screenshot_path = os.path.join(
                f"static/{session_id}/screenshots", screenshot_filename
            )
            print("Saving screenshot....")
            driver.save_screenshot(os.path.join(screenshots_dir, screenshot_filename))
            print("Sleeping.....")
            time.sleep(0.1)

    # This works.. but not well
    screenshot_thread = threading.Thread(target=capture_screenshots)
    screenshot_thread.start()

    driver.get(url)

    screenshot_thread.join()
    print("Capturing screenshots.......", options_str)

    video_filename = create_filename(url, options_str, "video.mp4")
    create_video_from_screenshots(
        screenshots_dir, os.path.join(f"static/{session_id}", video_filename)
    )

    # Extract console logs
    logs = driver.get_log("browser")
    log_filename = create_filename(url, options_str, "console.log")

    with open(os.path.join(logs_dir, log_filename), "w") as file:
        for entry in logs:
            file.write(f"{entry['level']} - {entry['message']}\n")

    # Allow time for page to load and render
    # time.sleep(10)

    driver.quit()

    return session_id, log_filename, options_str, video_filename


def create_filename(url, options_str, file_type):
    sanitized_url = url.replace("http://", "").replace("https://", "").replace("/", "_")
    filename = f"{sanitized_url}_{options_str}_{file_type}"
    return filename


def create_video_from_screenshots(screenshots_dir, output_file):
    absolute_screenshots_dir = os.path.abspath(screenshots_dir)
    absolute_output_file = os.path.abspath(output_file)

    ffmpeg_command = [
        "ffmpeg",
        "-framerate",
        "10",
        "-pattern_type",
        "glob",
        "-i",
        os.path.join(absolute_screenshots_dir, "*.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        absolute_output_file,
    ]
    print("Processing video......")
    subprocess.run(ffmpeg_command)
