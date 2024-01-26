import asyncio
import time
from quart import Quart, render_template, websocket, redirect, url_for, request

import uuid
from create_results_page import create_standalone_html_file
from web_run import process_with_selenium

app = Quart(__name__)


@app.route("/", methods=["GET", "POST"])
async def index():
    if request.method == "POST":
        current_time = time.time()
        form_data = await request.form
        url = form_data["url"]
        options = form_data.getlist("options")
        resolution = form_data.get("resolution", "1024x768")  # Default resolution
        session_id = str(uuid.uuid4())

        # List to store asyncio tasks
        tasks = []

        for option in options:
            task = asyncio.create_task(
                process_with_selenium(
                    url,
                    [option],
                    resolution,
                    session_id,
                    current_time,
                )
            )
            tasks.append(task)

        # Wait for all asyncio tasks to complete
        results = await asyncio.gather(*tasks)

        formatted_results = format_results(results)
        # print(formatted_results)

        # Render a template to show results
        output_file = await create_standalone_html_file(formatted_results, current_time)
        # print(f"Standalone HTML file created: {output_file}")
        return redirect(url_for("static", filename=output_file[len("static/") :]))

    return await render_template("index.html")


def format_results(results):
    formatted_results = []

    for session_id, log, options, video_filename in results:
        # Options is a list of option strings
        # This is bad
        options_str = ", ".join([opt.replace("_", " ").title() for opt in options])
        result = {
            "log_url": url_for("static", filename=f"{session_id}/logs/{log}"),
            "options_str": options_str,
            "video_url": url_for("static", filename=f"{session_id}/{video_filename}"),
        }
        formatted_results.append(result)

    return formatted_results
