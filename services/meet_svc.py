import random
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers.utils import reliable_click, setup_mutation_observer, clear_got_it_dialogs, find_mute_status, find_video_status
from models.models import Layout


def join_google_meet(driver: uc.Chrome, bot_name: str, meet_url: str):
    """
    Join a Google Meet session using provided webdriver, bot name and meeting url
    """
    try:
        # Navigate to the Google Meet URL
        print(f"Navigating to {meet_url}")
        driver.get(meet_url)

        # Waiting 30s for the page to load
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("Page loaded successfully")
        driver.save_screenshot("screenshots/join_meet/1_page_loaded.png")

        # Add random delay
        time.sleep(random.uniform(2.5, 4.0))

        # Turn off microphone
        mic_button_xpath = "//div[@role='button' and @aria-label='Turn off microphone']"
        reliable_click(driver, (By.XPATH, mic_button_xpath))
        print("Mic turned off")
        driver.save_screenshot("screenshots/join_meet/2_mic_off.png")

        # Turn off video
        video_button_xpath = "//div[@role='button' and @aria-label='Turn off camera']"
        reliable_click(driver, (By.XPATH, video_button_xpath))
        print("Video turned off")
        driver.save_screenshot("screenshots/join_meet/3_video_off.png")

        # Click on name input field (no verification needed)
        text_box_found = reliable_click(
            driver,
            (By.XPATH, "//input[@type='text' and @placeholder='Your name']"),
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
            driver.save_screenshot("screenshots/join_meet/4_name_entered.png")

        # Trying "Ask to join" button or "Join now" button for rejoin
        reliable_click(
            driver,
            (By.XPATH, "//span[contains(text(), 'Ask to join') or contains(text(), 'Join now')]"),
        )
        driver.save_screenshot("screenshots/join_meet/5_ask_to_join.png")

        print("Join attempt completed, waiting to let in by the host...")

        # Setup JS mutation observer to detect when the bot is accepted by the host, participant joined or left etc.
        setup_mutation_observer(driver)

    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")


def check_if_joined(driver: uc.Chrome, bot_name: str) -> bool:
    """
    Checks if the bot has successfully joined the meeting by looking for its name in the participants list.
    """
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


def toggle_mute_state(driver: uc.Chrome) -> str:
    """
    Toggles the microphone mute state using keyboard shortcut (Ctrl+D).
    """
    # Clear any "Got it" dialogs, so that elements are clickable
    clear_got_it_dialogs(driver)

    # Use keyboard shortcut to toggle mute state
    action = ActionChains(driver)
    action.key_down(Keys.CONTROL).send_keys("d").key_up(Keys.CONTROL).perform()

    # Allow time for the UI to update
    time.sleep(1)

    return find_mute_status(driver)


def toggle_video_state(driver: uc.Chrome) -> str:
    """
    Toggles the camera video state using keyboard shortcut (Ctrl+E).
    """
    # Clear any "Got it" dialogs, so that elements are clickable
    clear_got_it_dialogs(driver)

    # Use keyboard shortcut to toggle video state
    action = ActionChains(driver)
    action.key_down(Keys.CONTROL).send_keys("e").key_up(Keys.CONTROL).perform()

    # Allow time for the UI to update
    time.sleep(1)

    return find_video_status(driver)


def change_meeting_layout(driver: uc.Chrome, layout: Layout) -> None:
    """
    Changes the Google Meet layout to the specified option.
    """
    # Clear any "Got it" dialogs, so that elements are clickable
    clear_got_it_dialogs(driver)

    more_options_button = driver.find_element(
        By.XPATH,
        "//button[@aria-label='More options' and @data-use-native-focus-logic='true']",
    )
    more_options_button.click()
    time.sleep(1)
    driver.save_screenshot("screenshots/change_layout/1_more_options_menu.png")

    menu = WebDriverWait(driver, timeout=10).until(
        EC.presence_of_element_located((By.XPATH, "//ul[@aria-label='Call options']"))
    )

    # Find all li elements in the dropdown menu
    menu_items = menu.find_elements(By.XPATH, "//li[@role='menuitem']")

    # Look for the "Change layout" option
    layout_option = None
    for item in menu_items:
        try:
            # Find any span containing the text "Change layout"
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
    driver.save_screenshot("screenshots/change_layout/2_change_layout_menu.png")

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
                driver.save_screenshot(f"screenshots/change_layout/3_layout_{layout_name.lower()}.png")
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
    driver.save_screenshot("screenshots/change_layout/4_close_button.png")


def send_chat_message(driver: uc.Chrome, message: str) -> None:
    """
    Sends a chat message to all participants in the meeting.
    """
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
    driver.save_screenshot("screenshots/send_chat_message/1_chat_button.png")

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
    driver.save_screenshot("screenshots/send_chat_message/2_message_sent.png")

    action = ActionChains(driver)
    action.key_down(Keys.ESCAPE).key_up(Keys.ESCAPE).perform()
    time.sleep(1)


def exit_meeting(driver: uc.Chrome) -> None:
    """
    Leaves the current Google Meet session.
    """
    # Clear any "Got it" dialogs, so that elements are clickable
    clear_got_it_dialogs(driver)

    leave_button = WebDriverWait(driver, timeout=10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Leave call']"))
    )
    leave_button.click()
    time.sleep(1)
    driver.save_screenshot("screenshots/leave_meeting/1_leave_button.png")
