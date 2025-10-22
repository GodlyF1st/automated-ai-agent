# Arthur Gluzman
# Challenge 2: Making It Shareable

import time
import json
import os
import uvicorn
import google.generativeai as genai
from playwright.sync_api import sync_playwright
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="AI Web Automation Agent API")

class api_request(BaseModel):
    task: str
    apikey: str

def get_page_context(page):
    try:
        # Capture the accessibility tree and HTML content for the LLM
        accessibility_tree = page.accessibility.snapshot()
        html_content = page.content()
        
        # Limit HTML size to avoid exceeding the LLM's token limit
        return {"accessibility_tree": accessibility_tree, "html_snippet": html_content[:5000]}
    except Exception as e:
        print(f"Error getting page context: {e}")
        return {}


def make_plan(goal, context, llm):
    # The AI prompt that instructs the LLM.
    prompt = f"""
    You are an expert web automation AI. Your high-level goal is: "{goal}"
    Your task is to analyze the page context and create a precise JSON plan to achieve the goal.

    Here is the page context (accessibility tree and HTML) provided by the MCP:
    ```json
    {json.dumps(context, indent=2)}
    ```

    --- YOUR STRICT REASONING PROCESS ---
    1.  **Analyze the Goal vs. Current Page:** Look at your goal. Are you trying to log in, or are you already logged in and trying to log out? Base your plan ONLY on what you see on the page right now.
    2.  **Find the Key Element:** Identify the most important element needed for the next step from the `accessibility_tree`. For example, a 'textbox' named 'Username'.
    3.  **Find its ID in the HTML:** Look in the `html_snippet` for that exact element and find its `id` attribute.
    4.  **Create a PERFECT CSS Selector:**
        - If an `id` exists (e.g., `<input id="username">`), the selector MUST be `"#username"`.
        - If no `id` exists, but the element has clear visible text (e.g., a "Log out" button), you MUST use the `click_text` action.
    5.  **Construct the Plan:** Create a JSON plan of actions for the CURRENT page.

    --- VALID ACTIONS (Your Tools) ---
    - To type in a field with an ID: {{"action": "type", "selector": "#the_id", "text": "text_to_type"}}
    - To click a button with an ID: {{"action": "click", "selector": "#the_id"}}
    - To click an element by its visible text: {{"action": "click_text", "text": "Visible text on the element"}}
    - When the entire goal is finished: {{"action": "end"}}
        
    Your response MUST be a valid JSON object with a single key "plan".
    """
    try:
        response = llm.generate_content(prompt)
        # Convert AI output into a Python dictionary
        plan = json.loads(response.text)
        return plan
    except Exception as e:
        print(f"LLM failed to generate a valid plan: {e}")
        return {"plan": []}

def execute_plan(page, plan):
    # executes the steps using Playwright
    if not plan.get("plan"):
        print("Received an empty or invalid plan. Cannot execute.")
        return False

    for step in plan["plan"]:
        action = step.get("action")
        
        try:
            # Perform browser actions based on the generated plan
            if action == "type":
                page.locator(step["selector"]).first.fill(step["text"])
            elif action == "click":
                page.locator(step["selector"]).first.click(timeout=3000)
            elif action == "click_text":
                page.get_by_text(step["text"]).first.click(timeout=3000)
            elif action == "end":
                return True # Signal that the goal is complete
            else:
                print(f"Unknown action: {action}")
            
            time.sleep(1) # Wait for the page to react to the action
        except Exception as e:
            print(f"Action failed during execution: {step}. Error: {e}")
            return False # An action failed, stop execution

    # Return False if the loop finishes without an 'end' action
    return False


def run_automation(task, apikey):
    # Main loop
    os.environ["GOOGLE_API_KEY"] = apikey
    genai.configure(api_key=apikey)

    print(f"Goal: '{task}'")
    
    # Initialize the Gemini AI model
    llm = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={"response_mime_type": "application/json"})
        
    print("\n=== Starting the AI Automation ===")
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        page.goto("https://practicetestautomation.com/practice-test-login/")

        while True:
            # Get the page context for the AI
            print("Getting the page context.")
            context = get_page_context(page)
            
            if not context:
                print("Could not get page context. Ending run.")
                break

            # AI creates a dynamic plan
            print("LLM is generating the steps.")
            plan = make_plan(task, context, llm)

            # Execute the AI-generated plan
            print("Executing the plan.")
            goal_achieved = execute_plan(page, plan)
            
            if goal_achieved:
                print("\nSuccess! The agent completed the goal!")
                break
            
            # If the plan was empty or failed, break the loop to avoid getting stuck
            if not plan.get("plan"):
                print("The AI could not create a valid plan. The goal was not achieved.")
                break

        print("\nClosing browser.")
        browser.close()

@app.post("/startapi")
def start_api_automation(request: api_request, background_tasks: BackgroundTasks):
    """ Example: {"task": "Log in with username 'student' and password 'Password123', and then log out." "apikey": key_here}"""
    # Run the automation in the background to avoid blocking the API response
    background_tasks.add_task(run_automation, request.task, request.apikey)
    
    return {"message": "Agent started."} 



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9900)
