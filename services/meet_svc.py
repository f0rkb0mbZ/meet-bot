from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
import random
from helpers.utils import reliable_click
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from models.models import Layout
import undetected_chromedriver as uc


def join_google_meet(driver: uc.Chrome, bot_name: str, meet_url: str):
    """
    Join a Google Meet session using provided webdriver
    """
    try:
        # Navigate to the Google Meet URL
        print(f"Navigating to {meet_url}")
        driver.get(meet_url)

        # Wait for the page to load
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("Page loaded successfully")
        driver.save_screenshot("screenshots/page_loaded.png")

        # Add random delay
        time.sleep(random.uniform(2.5, 4.0))

        # Turn off microphone with verification
        reliable_click(
            driver,
            (By.XPATH, "//div[@role='button' and @aria-label='Turn off microphone']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Turn on microphone']"),
            "mic off",
            max_attempts=3,
        )
        driver.save_screenshot("screenshots/mic_off.png")

        # Turn off video with verification
        reliable_click(
            driver,
            (By.XPATH, "//div[@role='button' and @aria-label='Turn off camera']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Turn on camera']"),
            "video off",
            max_attempts=3,
        )
        driver.save_screenshot("screenshots/video_off.png")

        # Click on name input field (no verification needed)
        text_box_found = reliable_click(
            driver,
            (By.XPATH, "//input[@type='text' and @placeholder='Your name']"),
            None,
            "name input field",
        )

        if text_box_found:
            # Get the text box element again to type in it
            text_box = driver.find_element(
                By.XPATH, "//input[@type='text' and @placeholder='Your name']"
            )

            # Type name with random delays between keystrokes
            for char in bot_name:
                text_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes

            time.sleep(random.uniform(0.5, 1.0))
            print("Name entered")
            driver.save_screenshot("screenshots/name_entered.png")

        # Try to find and click join button

        # Try "Ask to join" button
        reliable_click(
            driver,
            (By.XPATH, "//span[contains(text(), 'Ask to join') or contains(text(), 'Join now')]"),
            None,
            "'Ask to join' button",
            max_attempts=2,
        )
        driver.save_screenshot("screenshots/ask_to_join.png")

        print("Join attempt completed, waiting to let in by the host...")

        mutation_observer_script = """
        // 1. Build your regex once
        const joinedRe = /\\bjoined$/i;
        const leftRe = /\\bhas left the meeting$/i;

        // 2. Observer callback
        function onMutations(mutationsList) {
            for (const mutation of mutationsList) {
                // We only care about nodes being added
                if (mutation.type !== 'childList' || mutation.addedNodes.length === 0)
                    continue;

                for (const node of mutation.addedNodes) {
                    // If it’s an element, grab its text; if it’s a text node, use it directly
                    const text = (node.nodeType === Node.TEXT_NODE)
                        ? node.nodeValue
                        : node.textContent;
                    if (text) {
                        if (joinedRe.test(text.trim())) {
                            console.log('Someone joined! Text matched “joined”:', text.trim());
                            // fire your notification or message here…
                            window._join_message = text.trim();
                            return;  // stop once we’ve detected one
                        }
                        if (leftRe.test(text.trim())) {
                            console.log('Someone left! Text matched “has left the meeting”:', text.trim());
                            // fire your notification or message here…
                            window._left_message = text.trim();
                            return;  // stop once we’ve detected one
                        }   
                    }
                    if (node.tagName === 'BUTTON' && node.getAttribute('aria-label') === 'Meeting details') {
                        console.log('Meeting details button found!');
                        // fire your notification or message here…
                        window._join_accepted = true;
                        return;  // stop once we’ve detected one
                    }
                }
            }
        }

        // 3. Create & attach the observer
        const observer = new MutationObserver(onMutations);
        observer.observe(document.body || document.documentElement, {
            childList: true,
            subtree: true
        });
        """
        driver.execute_cdp_cmd(
            "Runtime.evaluate",
            {
                "expression": mutation_observer_script,
                "awaitPromise": False,
                "includeCommandLineAPI": True,
            },
        )

    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")


def check_if_joined(driver, bot_name: str):
    # Wait for 10 minutes to confirm that the host accepted the bot
    people_button = WebDriverWait(driver, timeout=600, poll_frequency=5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='People']"))
    )
    people_button.click()
    time.sleep(2)
    driver.save_screenshot("screenshots/people_button.png")

    participants_list = WebDriverWait(driver, timeout=10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@role='list' and @aria-label='Participants']")
        )
    )

    time.sleep(2)
    driver.save_screenshot("screenshots/participants_list.png")

    # Get all participant items within the list
    participant_items = participants_list.find_elements(
        By.XPATH, ".//div[@role='listitem']"
    )
    joined = False

    # Iterate through each participant
    for participant in participant_items:
        if bot_name == participant.get_attribute("aria-label"):
            print(f"Bot {bot_name} successfully joined the meeting")
            joined = True
            break
    return joined


def clear_got_it_dialogs(driver):
    try:
        # Find all buttons with aria-label "Got it"
        got_it_buttons = driver.find_elements(
            By.XPATH, "//button[.//span[normalize-space(.)='Got it']]"
        )
        for button in got_it_buttons:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(1)
    except Exception as e:
        print(f"Error clearing got it dialogs: {e}")


def find_mute_status(driver):
    # Check which button is present to determine mic status
    try:
        # Use find_elements which doesn't throw exceptions
        mic_off_buttons = driver.find_elements(
            By.XPATH, "//button[@aria-label='Turn off microphone']"
        )
        mic_on_buttons = driver.find_elements(
            By.XPATH, "//button[@aria-label='Turn on microphone']"
        )

        if len(mic_off_buttons) > 0:
            return "unmuted"  # Microphone is on (turn off button is visible)
        elif len(mic_on_buttons) > 0:
            return "muted"  # Microphone is off (turn on button is visible)
        else:
            return "unknown"  # Neither button found
    except Exception as e:
        print(f"Error checking mute status: {e}")
        return "unknown"


def toggle_mute_state(driver):
    # Clear any "Got it" dialogs, so that elements are clickable
    clear_got_it_dialogs(driver)

    # Focus on the Google Meet window
    action = ActionChains(driver)
    action.key_down(Keys.CONTROL).send_keys("d").key_up(Keys.CONTROL).perform()

    # Allow time for the UI to update
    time.sleep(1)

    return find_mute_status(driver)


def change_meeting_layout(driver, layout: Layout):
    # Clear any "Got it" dialogs, so that elements are clickable
    clear_got_it_dialogs(driver)

    more_options_button = driver.find_element(
        By.XPATH,
        "//button[@aria-label='More options' and @data-use-native-focus-logic='true']",
    )
    more_options_button.click()
    time.sleep(1)
    driver.save_screenshot("screenshots/more_options_menu.png")

    menu = WebDriverWait(driver, timeout=10).until(
        EC.presence_of_element_located((By.XPATH, "//ul[@aria-label='Call options']"))
    )

    # Find all li elements in the dropdown menu
    menu_items = menu.find_elements(By.XPATH, "//li[@role='menuitem']")

    # Look for the "Change layout" option
    layout_option = None
    for item in menu_items:
        try:
            # Find any span containing the text "Change layout" regardless of class
            span_elements = item.find_elements(By.XPATH, ".//span")
            for span in span_elements:
                if span.text.strip().lower() == "change layout":
                    layout_option = item
                    break
            if layout_option:
                break
        except Exception:
            continue

    if layout_option:
        # Click on "Change layout" option
        layout_option.click()
        time.sleep(1)
    driver.save_screenshot("screenshots/change_layout_menu.png")

    layout_radiogroup = WebDriverWait(driver, timeout=10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[@aria-label='Change layout' and @role='radiogroup']")
        )
    )

    # Find the correct radio based on the layout enum value
    layout_name = layout.value

    # Find all radio input elements within the radiogroup
    layout_options = layout_radiogroup.find_elements(
        By.XPATH, ".//input[@type='radio']"
    )

    found = False
    for radio in layout_options:
        try:
            # Find the parent label element that contains both the radio and the text
            label = radio.find_element(By.XPATH, "./ancestor::label")
            if layout_name in label.text.lower():
                radio.click()
                print(f"Changed layout to {layout_name}")
                time.sleep(1)
                driver.save_screenshot(f"screenshots/layout_{layout_name.lower()}.png")
                found = True
                break

        except Exception as e:
            print(f"Error checking layout option: {e}")
            continue
    if not found:
        print(f"Layout {layout_name} not found in available options")

    action = ActionChains(driver)
    action.key_down(Keys.ESCAPE).key_up(Keys.ESCAPE).perform()
    time.sleep(1)
    driver.save_screenshot("screenshots/close_button.png")


def send_chat_message(driver, message: str):
    # Clear any "Got it" dialogs, so that elements are clickable
    clear_got_it_dialogs(driver)

    chat_button = WebDriverWait(driver, timeout=10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[@aria-label='Chat with everyone']")
        )
    )
    chat_button.click()
    print("Chat button clicked")
    time.sleep(2)
    driver.save_screenshot("screenshots/chat_button.png")

    chat_input = WebDriverWait(driver, timeout=10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//textarea[@aria-label='Send a message']")
        )
    )
    for char in message:
        chat_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))
    chat_input.send_keys(Keys.ENTER)
    print("Message sent")
    time.sleep(2)
    driver.save_screenshot("screenshots/message_sent.png")

    action = ActionChains(driver)
    action.key_down(Keys.ESCAPE).key_up(Keys.ESCAPE).perform()
    time.sleep(1)


def exit_meeting(driver):
    # Clear any "Got it" dialogs, so that elements are clickable
    clear_got_it_dialogs(driver)


    leave_button = WebDriverWait(driver, timeout=10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Leave call']"))
    )
    leave_button.click()
    time.sleep(1)
    driver.save_screenshot("screenshots/leave_button.png")
