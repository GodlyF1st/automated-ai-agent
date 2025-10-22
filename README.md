# AI Web Automation Agent API (main.py)

This repository contains a FastAPI app that starts a background automation agent that uses Google Gemini, Playwright to interact with web pages by typing the agent the goal that needs to be achieved.

## What this code does
- Exposes a POST endpoint `/startapi` which accepts a JSON body with `task` and `apikey`.
- The endpoint starts a background automation task that:
  - Launches a Playwright browser
  - Captures the page accessibility tree and a short HTML snippet
  - Calls the Google Gemini model to create a JSON plan
  - Executes the plan using Playwright actions (click, type, click_text)

## Setup and Installation

Follow these steps to set up and run the project locally.

## Prerequisites
*   Python 3.8 or newer.
*   Access to the Google Gemini API and a valid API key.

## Installation Steps

1.  **Clone the Repository**
    ```bash
    git clone (https://github.com/GodlyF1st/automated-ai-agen)
    cd <YOUR_FOLDER_NAME>
    ```

2.  **Install Python Dependencies**
    Install all the required libraries from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browsers**
    This command downloads the necessary browser binaries (like Chromium) for Playwright to use.
    ```bash
    playwright install
    ```

## How to Run the Application

Once the setup is complete, you can start the API server using Uvicorn.

```bash
uvicorn main:app --host "127.0.0.1" --port 9900
```

Web:
You can use the URL `http://127.0.0.1:9900/docs` and execute the code from there.

Example using curl (PowerShell):

```powershell
$body = @{
    task = "Log in with username 'student' and password 'Password123', and then log out."
    apikey = "YOUR_API_KEY"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:9900/startapi -Method Post -Body $body -ContentType 'application/json'
```

After the endpoint responds, the agent runs in the background and logs progress to the console where the server is running.

## Security
- Do NOT hardcode API key.



