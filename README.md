## edgecaser
Run your web app through multiple network conditions and test for unexpected issues

## How It Works
- **Quart**: Uses the async framework Quart handles HTTP requests and serves the web interface.
- **Playwright**: Replaces Selenium WebDriver (see `web_run.py`) with Playwright for browser automation. Playwright supports testing across Chrome, Firefox, and WebKit with a single API.
- **Dynamic Screenshot Capturing**: Utilizes Playwright's screenshot capabilities to capture the state of the webpage at regular intervals.
- **Chrome Network Condition Simulation**: Uses Chrome DevTools Profile ability to simulate various network conditions (such as Slow 3G, Fast 3G, LTE, 5G, and custom profiles) to test how network performance impacts user experience.
- **Video Creation**: Combines captured screenshots into a video using `ffmpeg`.

## Features
- **Cross-Browser Testing**: Utilizes Playwright for testing across Chrome, Firefox, and WebKit (Safari).
- **Headless Mode**: Supports headless testing in all browsers.
- **Custom Settings**: Offers adjustable resolution and network condition simulation for specific testing scenarios.

## Future Plans
- **Advanced Interactions**: Enables complex user interactions (clicks, submissions) via Playwright's API.
- **Logging and Diagnostics**: Plans to capture detailed logs and metrics for enhanced analysis.

## Setup and Running

### Setup
Ensure you have Python 3.7+ and a smile on your face. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application
- Start Quart in debug mode:
```bash
quart --debug run
```