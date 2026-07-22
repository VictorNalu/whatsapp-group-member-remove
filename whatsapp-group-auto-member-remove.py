from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

# ----------------------------------------------------------------------
# Set up Chrome options
# ----------------------------------------------------------------------
chrome_options = Options()

# NOTE: On Windows you do NOT need to set binary_location manually -
# Chrome will be found automatically as long as it's installed normally.
# (The original script had a Mac-only path here, which was breaking things.)

# --- Anti-automation-detection settings ---
# By default, Selenium leaves fingerprints (like navigator.webdriver = true)
# that sites can use to detect and deliberately throttle/degrade automated
# browsers. WhatsApp Web appears to be doing exactly that - manual clicks
# work instantly, but the same click performed via Selenium hangs. These
# settings hide the most common automation fingerprints.
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# This tells Chrome to store/reuse a login session in a folder on your
# machine, so you don't have to re-scan the WhatsApp QR code every run.
# It will be created automatically the first time you run this script.
user_data_dir = os.path.join(os.path.expanduser("~"), "whatsapp_chrome_profile")
chrome_options.add_argument(f"user-data-dir={user_data_dir}")
chrome_options.add_argument("profile-directory=Default")

# Set up WebDriver service (auto-downloads the correct ChromeDriver version)
service = Service(ChromeDriverManager().install())

# Initialize WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Extra layer: directly override the navigator.webdriver property that
# many sites (including WhatsApp Web) check to detect automated browsers.
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

# Open WhatsApp Web
driver.get("https://web.whatsapp.com")

# Wait for the user to log in manually (scan the QR code if this is the
# first run using this profile folder). Instead of guessing a fixed sleep
# time, we actively wait (up to 2 minutes) until WhatsApp Web has actually
# loaded the chat list / search box, which only appears after you're logged in.
print("If a QR code appears, scan it with your phone now...")
print("Waiting for WhatsApp Web to finish loading (up to 3 minutes)...")
try:
    WebDriverWait(driver, 180).until(
        EC.visibility_of_element_located((By.XPATH, "//input[@aria-label='Search or start a new chat']"))
    )
    print("WhatsApp Web loaded successfully.")
except Exception:
    # Save a screenshot and the page HTML so we can see what was actually
    # on screen when the wait timed out, instead of guessing blindly.
    screenshot_path = os.path.join(os.getcwd(), "whatsapp_debug.png")
    html_path = os.path.join(os.getcwd(), "whatsapp_debug.html")
    driver.save_screenshot(screenshot_path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"Timed out waiting for WhatsApp Web to load.")
    print(f"Saved a screenshot to: {screenshot_path}")
    print(f"Saved the page HTML to: {html_path}")
    driver.quit()
    raise SystemExit(1)

# Helper: dismiss WhatsApp's one-time "What's new" popup (or any similar
# dialog) if one happens to be open right now.
def dismiss_popup_if_present(driver, wait_seconds=3):
    try:
        dismiss_xpath = (
            "//div[@role='dialog']//button[contains(., 'Continue')] "
            "| //div[@role='dialog']//*[@data-icon='x'] "
            "| //div[@role='dialog']//*[@aria-label='Close']"
        )
        popup_dismiss_button = WebDriverWait(driver, wait_seconds).until(
            EC.element_to_be_clickable((By.XPATH, dismiss_xpath))
        )
        driver.execute_script("arguments[0].click();", popup_dismiss_button)
        print("Dismissed a popup dialog.")
        time.sleep(1)
        return True
    except Exception:
        return False


# Try once early, in case the popup is already up
dismiss_popup_if_present(driver, wait_seconds=5)


# Function to scroll an element into view
def scroll_to_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)


# Function to hover over an element
def hover_over_element(driver, element):
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()


# Saves a screenshot + HTML snapshot labeled with the step name, so we can
# see exactly what the page looked like at the moment something failed.
def debug_capture(driver, step_name):
    screenshot_path = os.path.join(os.getcwd(), f"whatsapp_debug_{step_name}.png")
    html_path = os.path.join(os.getcwd(), f"whatsapp_debug_{step_name}.html")
    driver.save_screenshot(screenshot_path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"[DEBUG] Failed at step '{step_name}'.")
    print(f"[DEBUG] Screenshot: {screenshot_path}")
    print(f"[DEBUG] HTML:       {html_path}")


try:
    # Specify the group name
    group_name = "Your Group Name Here"  # Replace this with your group's name

    # Locate the search box, type the group name, and select the group
    print("Locating the search box and typing the group name...")
    search_box_xpath = "//input[@aria-label='Search or start a new chat']"  # XPath for the search box
    try:
        search_box = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, search_box_xpath)))
        try:
            search_box.click()
        except Exception:
            # Click was likely blocked by a popup dialog - dismiss it and retry
            print("Search box click was blocked, checking for a popup...")
            dismiss_popup_if_present(driver, wait_seconds=5)
            search_box.click()
        search_box.send_keys(group_name)
        print("Group name typed")
    except Exception:
        debug_capture(driver, "01_search_box")
        raise

    # Click on the group from the search results
    print("Locating and clicking on the group...")
    # The visible text is a small <span> nested inside the real clickable
    # row (a div with data-testid="cell-frame-container"). Clicking the
    # span directly (even via JS) doesn't reliably trigger navigation, so
    # we find that ancestor row and click it with a real mouse click.
    group_xpath = f"//span[@title='{group_name}']/ancestor::div[@data-testid='cell-frame-container']"
    conversation_header_xpath = "//div[@data-testid='conversation-header']"
    try:
        group_row = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, group_xpath)))
        ActionChains(driver).move_to_element(group_row).click().perform()
        print("Group clicked, waiting for chat to open...")

        chat_opened = False
        try:
            # This account has a large amount of data (many groups/unread
            # messages), so WhatsApp Web can take well over a minute to
            # fully render the chat panel. Give it a generous window.
            print("Waiting up to 3 minutes for the chat panel to render (this account has a lot of data)...")
            WebDriverWait(driver, 180).until(
                EC.presence_of_element_located((By.XPATH, conversation_header_xpath))
            )
            chat_opened = True
            print("Group clicked and chat confirmed open")
        except Exception:
            # Genuinely not open yet - try clicking again (relocating the
            # row fresh, in case the page re-rendered) before giving up.
            print("Chat did not open in time - trying the click again...")
            try:
                group_row = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, group_xpath)))
                ActionChains(driver).move_to_element(group_row).click().perform()
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, conversation_header_xpath))
                )
                chat_opened = True
                print("Group clicked and chat confirmed open on second attempt")
            except Exception:
                print("Warning: could not confirm the chat opened after a second attempt, "
                      "but continuing anyway - the next step will confirm for real.")
    except Exception:
        debug_capture(driver, "02_open_group")
        raise

    # Click on the Group Info button
    print("Locating and clicking Group Info...")
    group_info_xpath = "//div[@data-testid='conversation-info-header']"
    # WhatsApp sometimes restores the Group Info panel as already open from
    # a previous session, so check first before clicking again.
    already_open_xpath = "//span[text()='Group info']"
    try:
        if driver.find_elements(By.XPATH, already_open_xpath):
            print("Group Info panel already open, skipping click.")
        else:
            group_info_element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, group_info_xpath)))
            ActionChains(driver).move_to_element(group_info_element).click().perform()
            print("Group Info clicked")
            time.sleep(1)
    except Exception:
        debug_capture(driver, "03_group_info")
        raise

    # Locate and scroll to the member list
    print("Locating and scrolling to the member list...")
    div_xpath = "//div[@data-testid='group-info-participants-section']"
    try:
        div_element = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, div_xpath)))
        scroll_to_element(driver, div_element)
        print("Scrolled to member list")
    except Exception:
        debug_capture(driver, "04_member_list")
        raise

    # Loop through members and remove each one
    member_xpath = "(//div[@data-testid='group-info-participants-section']//div[@data-testid='cell-frame-container'])[3]"
    consecutive_failures = 0
    max_consecutive_failures = 8  # safety net - stop only after repeated real failures in a row
    removed_count = 0
    debug_captured_once = False

    while True:
        # First, check if there's actually a member left to remove at all.
        # This is the real "are we done?" signal - distinct from a
        # transient error further down, which should just be retried.
        member_rows = driver.find_elements(By.XPATH, member_xpath)
        if not member_rows:
            print(f"No more members found in the list. Removed {removed_count} member(s) total.")
            break

        try:
            print("Locating and hovering over the member...")

            # The options/chevron icon for a member row is a button with
            # data-testid="context-btn" that appears on hover. Retry a
            # couple of times in case this particular row is still
            # finishing its render - re-fetching the element fresh each
            # time, since WhatsApp's list can re-render in the background
            # and invalidate ("stale") our earlier reference.
            down_arrow_xpath = ".//button[@data-testid='context-btn']"
            down_arrow_element = None
            member_element = None
            for hover_attempt in range(3):
                try:
                    member_element = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, member_xpath))
                    )
                    hover_over_element(driver, member_element)
                    time.sleep(0.5)
                    down_arrow_element = WebDriverWait(driver, 5).until(
                        lambda d: member_element.find_element(By.XPATH, down_arrow_xpath)
                    )
                    break
                except Exception:
                    time.sleep(1)

            if down_arrow_element is None:
                raise Exception("Could not locate the member options/down-arrow icon after retries")

            driver.execute_script("arguments[0].click();", down_arrow_element)
            print("Down arrow / options icon clicked")

            # Click the Remove option
            print("Locating and clicking the Remove option...")
            remove_xpath = "//li[contains(., 'Remove')] | //div[@role='button'][contains(., 'Remove')]"
            remove_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, remove_xpath)))
            driver.execute_script("arguments[0].click();", remove_element)
            print("Remove option clicked")

            # Confirm removal
            print("Locating and clicking the final Remove button...")
            final_remove_xpath = "//div[@role='dialog']//button[contains(., 'Remove')]"
            final_remove_element = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, final_remove_xpath)))
            driver.execute_script("arguments[0].click();", final_remove_element)
            print("Final Remove button clicked")

            removed_count += 1
            consecutive_failures = 0  # reset - this iteration succeeded
            print(f"Removed {removed_count} member(s) so far.")

            # Wait for the page to update
            time.sleep(2)  # Adjust if necessary

        except Exception as e:
            consecutive_failures += 1
            print(f"Transient error on this member (attempt {consecutive_failures}/{max_consecutive_failures}): {e}")

            if not debug_captured_once:
                # Capture debug info the first time something goes wrong,
                # so we have evidence to diagnose if this keeps happening.
                debug_capture(driver, "05_remove_loop")
                debug_captured_once = True

            if consecutive_failures >= max_consecutive_failures:
                print(f"Stopping after {max_consecutive_failures} consecutive failures. "
                      f"Removed {removed_count} member(s) total before stopping.")
                debug_capture(driver, "05_remove_loop_final")
                break

            # Otherwise, pause briefly and let the while loop try again -
            # it will re-check whether a member row still exists first.
            time.sleep(2)

finally:
    # Close the browser
    time.sleep(50)  # Allow some time to see results
    driver.quit()