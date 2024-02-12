import asyncio
from pathlib import Path
import subprocess
import time
from playwright.async_api import async_playwright

from logger import logger

network_conditions = {
    "Slow 3G": {
        "downloadThroughput": int((500 * 1000) / 8 * 0.8),
        "uploadThroughput": int((500 * 1000) / 8 * 0.8),
        "latency": int(400 * 5),
    },
    "Fast 3G": {
        "downloadThroughput": int((1.6 * 1000 * 1000) / 8 * 0.9),
        "uploadThroughput": int((750 * 1000) / 8 * 0.9),
        "latency": int(150 * 3.75),
    },
    "LTE": {
        "downloadThroughput": int((50 * 1000 * 1000) / 8 * 0.9),  # 90% of 50 Mbps
        "uploadThroughput": int((25 * 1000 * 1000) / 8 * 0.9),  # 90% of 25 Mbps
        "latency": 50,  # Average latency
    },
    "5G": {
        "downloadThroughput": int((1 * 1000 * 1000 * 1000) / 8 * 0.8),  # 80% of 1 Gbps
        "uploadThroughput": int((100 * 1000 * 1000) / 8 * 0.8),  # 80% of 100 Mbps
        "latency": 20,  # Average latency
    },
    "Home Internet": {
        "downloadThroughput": int((50 * 1000 * 1000) / 8),  # 50 Mbps
        "uploadThroughput": int((5 * 1000 * 1000) / 8),  # 5 Mbps
        "latency": 30,  # Average latency
    },
}


async def capture_screenshots(page, interval, duration, screenshot_dir, file_prefix):
    start_time = time.time()
    count = 0
    while time.time() - start_time < duration:
        screenshot_path = screenshot_dir / f"{file_prefix}_{count}.png"
        await page.screenshot(path=str(screenshot_path))
        count += 1
        logger.info(f"Captured screenshot {count}")
        await asyncio.sleep(interval)


async def create_video(screenshot_dir, file_prefix, output_filename):
    pattern = str(screenshot_dir / f"{file_prefix}_*.png")
    screenshot_files = list(screenshot_dir.glob(f"{file_prefix}_*.png"))
    frame_count = len(screenshot_files)
    if frame_count == 0:
        logger.info("No screenshots found, video will not be created.")
        return
    frame_rate = max(1, frame_count / 20)  # Ensure frame rate is at least 1

    logger.info(f"Creating video at {frame_rate} frames per second.")
    ffmpeg_command = [
        "ffmpeg",
        "-framerate",
        str(frame_rate),
        "-pattern_type",
        "glob",
        "-i",
        pattern,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_filename),
    ]
    subprocess.run(ffmpeg_command)
    logger.info(f"Video created at: {output_filename}")


async def load_page_with_screenshots(
    session_id,
    test_type,  # Add this parameter to define the test type
    url,
    screenshot_interval,
    load_duration,
    disable_js,
    disable_images,
    slow_route,
    slow_network_chrome,
    delay_ms=2000,
):
    screenshot_dir = Path(f"static/results/{session_id}")  # Update path
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    file_prefix = test_type

    logger.info(f"Test type: {test_type}")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(java_script_enabled=not disable_js)

        if disable_images:
            await context.route(
                "**/*",
                lambda route: route.abort()
                if route.request.resource_type == "image"
                else route.continue_(),
            )

        page = await context.new_page()

        async def handle_slow_route(route):
            await asyncio.sleep(delay_ms / 1000)  # Convert milliseconds to seconds
            await route.continue_()

        if slow_route:
            await context.route("**", handle_slow_route)

        if slow_network_chrome:
            # TODO: allow passing of variantion of network conditions
            cdp_session = await context.new_cdp_session(page)
            await cdp_session.send("Network.enable")
            await cdp_session.send(
                "Network.emulateNetworkConditions",
                {
                    "offline": False,
                    "latency": network_conditions["Fast 3G"]["latency"],
                    "downloadThroughput": network_conditions["Fast 3G"][
                        "downloadThroughput"
                    ],
                    "uploadThroughput": network_conditions["Fast 3G"][
                        "uploadThroughput"
                    ],
                },
            )

        screenshot_task = asyncio.create_task(
            capture_screenshots(
                page, screenshot_interval, load_duration, screenshot_dir, file_prefix
            )
        )
        await page.goto(url)
        await screenshot_task

        await page.close()
        await context.close()
        await browser.close()

    await create_video(
        screenshot_dir, file_prefix, screenshot_dir / f"{file_prefix}.mp4"
    )
