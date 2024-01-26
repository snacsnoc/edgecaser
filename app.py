import time
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    render_template_string,
    redirect,
)
from web_run import process_with_selenium
from concurrent.futures import ThreadPoolExecutor
import os

app = Flask(__name__)
import uuid
from create_results_page import create_standalone_html_file


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        current_time = time.time()
        url = request.form["url"]
        options = request.form.getlist("options")
        resolution = request.form.get("resolution", "1024x768")  # Default resolution
        session_id = str(uuid.uuid4())

        # List to store futures
        futures = []
        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Launch parallel tasks
            for option in options:
                future = executor.submit(
                    process_with_selenium,
                    url,
                    [option],
                    resolution,
                    session_id,
                    current_time,
                )
                futures.append(future)

            # Wait for all tasks to complete and collect results
            for future in futures:
                results.append(future.result())

        # Format results for display
        formatted_results = format_results(results)
        print(formatted_results)

        # Render a different template to show results
        output_file = create_standalone_html_file(formatted_results, current_time)
        # print(f"Standalone HTML file created: {output_file}")
        return redirect(url_for("static", filename=output_file[len("static/") :]))

    return render_template("index.html")


def format_results(results):
    formatted_results = []

    for session_id, log, options_str, video_filename in results:
        result = {
            # This is left in the event we only want to return a single screenshot to the user
            # "screenshot_url": url_for(
            #     "static", filename=f"{session_id}/screenshots/{screenshot}"
            # ),
            "log_url": url_for("static", filename=f"{session_id}/logs/{log}"),
            "options_str": options_str.replace("_", " ").title(),
            "video_url": url_for("static", filename=f"{session_id}/{video_filename}"),
        }
        formatted_results.append(result)

    return formatted_results
