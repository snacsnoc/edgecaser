## edgecaser
Run your web app through multiple network conditions and test for unexpected issues. This tool uses Selenium with Python to take screenshots of a webpage at various stages of its loading process, allowing for an analysis of how different elements and resources load over time.

## How It Works
- **Selenium WebDriver**: The script utilizes Selenium WebDriver to automate and control a web browser. It navigates to a specified URL and performs actions based on the given options.
- **Dynamic Screenshot Capturing**: The tool captures screenshots at regular intervals during the page loading process. This is achieved through an asyncio task that runs concurrently with the page loading.
- **Navigation Timing API**: Utilizes the Navigation Timing API to gather precise timing metrics of different stages of page loading.
- **Custom Options**: Allows for disabling JavaScript, images, CSS, and simulating various network conditions (like slow network, offline mode, high latency) to view their impacts on page loading.
- **Video Creation**: The captured screenshots are compiled into a video, providing a visual of the page load process.

## Features
- **Headless Browser Support**: Runs in headless mode (Chrome).
- **Adjustable Resolution**: Can set browser window size to desired resolution.
- **Customizable Intervals**: Ability to adjust the interval for capturing screenshots.
- **Logging**: Captures browser console logs for additional insights.

