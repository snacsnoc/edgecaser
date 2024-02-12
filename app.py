import asyncio
from quart import Quart, render_template, websocket, redirect, url_for, request

import uuid
from create_results_page import create_standalone_html_file

# from web_run import process_with_selenium
from web_pw_run import load_page_with_screenshots

from logger import logger

app = Quart(__name__)


@app.route("/", methods=["GET", "POST"])
async def index():
    if request.method == "POST":
        form_data = await request.form
        url = form_data["url"]
        options = form_data.getlist("options")
        # TODO: implement resultions
        resolution = form_data.get("resolution", "1024x768")
        session_id = str(uuid.uuid4())

        # Load the page with selected option and create screenshots
        tasks = []
        for option in options:
            task = asyncio.create_task(
                load_page_with_screenshots(
                    session_id,
                    option,  # Pass the test type
                    url,
                    screenshot_interval=0.05,
                    load_duration=10,
                    disable_js="disableJavascript" in options,
                    disable_images="disableImages" in options,
                    slow_route="highLatency" in options,
                    slow_network_chrome="slowNetwork" in options,
                )
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        # Process return data from the select test options to render on page
        formatted_results = format_results(session_id, options)
        output_path = await create_standalone_html_file(session_id, formatted_results)
        logger.info(f"Created standalone HTML file at {output_path}")

        return redirect(
            url_for("static", filename=f"results/{session_id}/results_page.html")
        )
    return await render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)


def format_results(session_id, options):
    formatted_results = []

    # Each option results in a single test execution
    for option in options:
        # Filenames are derived from the option directly
        video_filename = f"{option}.mp4"
        log_filename = f"{option}.log"  # Placeholder

        result = {
            # TOOD: implement saving logs from Playwright
            "log_url": url_for(
                "static", filename=f"results/{session_id}/logs/{log_filename}"
            ),
            "options_str": option.replace("_", " ").title(),
            "video_url": url_for(
                "static", filename=f"results/{session_id}/{video_filename}"
            ),
        }
        formatted_results.append(result)

    return formatted_results
