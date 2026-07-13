import os
import re
from dotenv import load_dotenv
from playwright.sync_api import Playwright, sync_playwright, expect

# Load secrets from your local .env file
load_dotenv()
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

if not EMAIL or not PASSWORD:
    raise RuntimeError("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD in environment variables!")


def run(playwright: Playwright) -> None:
    # --- ANTI-BLOCK CAMOUFLAGE ---
    # Launch standard Chrome with automation indicators completely turned off
    browser = playwright.chromium.launch(
        headless=False,
        ignore_default_args=["--enable-automation"]
    )
    
    # Fake a completely normal Windows Desktop browser profile
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()

    try:
        print("1. Navigating to Naukri...")
        page.goto("https://www.naukri.com/")
        page.get_by_role("link", name="Login", exact=True).click()

        print("2. Submitting your login credentials...")
        page.get_by_role("textbox", name="Enter your active Email ID /").click()
        page.get_by_role("textbox", name="Enter your active Email ID /").fill(EMAIL)
        page.get_by_role("textbox", name="Enter your active Email ID /").press("Tab")

        page.get_by_role("textbox", name="Enter your password").fill(PASSWORD)
        page.get_by_role("button", name="Login", exact=True).click()

        print("3. Waiting for login dashboard landing page...")
        page.wait_for_url("**/mnjuser/homepage*", timeout=30000)

        print("4. Navigating straight to profile editor view...")
        page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")

        # --- Explicitly wait for the lazy-loaded profile container to become visible ---
        print("5. Waiting for profile layout elements to render...")
        edit_button = page.locator("#lazyResumeHead").locator(".edit")
        edit_button.wait_for(state="visible", timeout=20000)

        print("5b. Clicking the headline edit pencil icon...")
        edit_button.click()

        # Target the headline text area element
        headline_field = page.locator("#resumeHeadlineTxt")
        headline_field.click()

        # Explicitly wait for Naukri's background script to fill the text box with your current headline
        print("6. Waiting for headline text field to populate data...")
        page.wait_for_function(
            "el => el.value.trim().length > 0",
            arg=headline_field.element_handle(),
            timeout=10000
        )

        # Read the live text string inside your headline profile
        current_headline = headline_field.input_value().strip()
        print(f"   -> Live headline found: '{current_headline}'")

        # --- CONDITION: Dynamically toggle the trailing pipe character ---
        if current_headline.endswith("|"):
            new_headline = current_headline[:-1].rstrip()
            print("   -> Action: Removing trailing pipe character.")
        else:
            new_headline = f"{current_headline} |"
            print("   -> Action: Appending trailing pipe character.")

        # Clear out old data and inject the toggled string
        headline_field.clear()
        headline_field.fill(new_headline)

        print("7. Clicking Save...")
        page.get_by_role("button", name="Save").click()

        # Small safety sleep to allow the API transaction to finish
        page.wait_for_timeout(3000)
        print(f"Success! Headline updated to: '{new_headline}'")

    except Exception as e:
        # Generate diagnostic files if something unexpected breaks down the line
        page.screenshot(path="error.png", full_page=True)
        with open("error.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"Automation execution broken: {e}")
        raise
    finally:
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)

