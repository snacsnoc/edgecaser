from quart import render_template_string
from pathlib import Path


# Create a standalone HTML file for the given session ID and results
# Returns the relative path from 'static/' for use in 'url_for'
async def create_standalone_html_file(
    session_id, formatted_results, base_dir="static/results"
):
    # Create a unique directory for this session under 'static/results'
    output_dir = Path(base_dir) / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file_path = output_dir / "results_page.html"

    # Render the HTML template with results
    rendered_html = await render_template_string(
        results_html_template, results=formatted_results
    )

    output_file_path.write_text(rendered_html)

    return output_file_path.relative_to("static").as_posix()


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
                <a href="{{ result.video_url }}" download>Download Video</a>
                <br>
                <a href="{{ result.log_url }}" download>Download Log File</a>
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""
