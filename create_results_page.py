import os
from quart import current_app, render_template_string


async def create_standalone_html_file(
    formatted_results, current_time, output_file="static/results"
):
    # Render the template with the formatted results
    rendered_html = await render_template_string(
        results_html_template, results=formatted_results
    )

    output_dir = os.path.join(output_file, f"{current_time}")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "results_page.html")

    with open(output_path, "w") as file:
        file.write(rendered_html)

    return output_path


results_html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Results</title>
    <style>
        .gallery {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-around;
        }
        .test-result {
            margin: 10px;
            text-align: center;
        }
        video {
            width: auto;
            height: 300px;
        }
    </style>
</head>
<body>
    <h1>Test Results</h1>
    <div class="gallery">
        {% for result in results %}
            <div class="test-result">
                <h2>Test: {{ result.options_str }}</h2>
                <video controls>
                    <source height=350px width=auto src="{{ result.video_url }}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <br>
                <a href="{{ result.log_url }}" download>Download Log File</a>
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""
