import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import random
from faker import Faker
from selenium.webdriver.common.keys import Keys

from helpers.utils import reliable_click

fake = Faker()

def join_google_meet(bot_name, meet_url, headless=False):
    """
    Join a Google Meet session using undetected ChromeDriver
    
    Args:
        meet_url (str): The URL of the Google Meet session
        headless (bool): Whether to run Chrome in headless mode
    """
    # Configure ChromeDriver options
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=CalculateNativeWinOcclusion")
    # options.add_argument("--use-fake-device-for-media-stream")
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--window-size=1920,1080")
    
    if headless:
        options.add_argument("--headless")
    
    # Create undetected ChromeDriver instance
    driver = uc.Chrome(options=options)
    # driver.maximize_window()
    driver.execute_cdp_cmd("Browser.grantPermissions",
    {
        "origin": "https://meet.google.com",
        "permissions": ["audioCapture", "videoCapture"]
    })
    
    try:
        # Keep window on focus
        driver.execute_script("window.onblur = function() { window.onfocus() }")
        # time.sleep(15)

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
            max_attempts=3
        )
        driver.save_screenshot("screenshots/mic_off.png")
        
        # Turn off video with verification
        reliable_click(
            driver,
            (By.XPATH, "//div[@role='button' and @aria-label='Turn off camera']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Turn on camera']"),
            "video off",
            max_attempts=3
        )
        driver.save_screenshot("screenshots/video_off.png")

        # Click on name input field (no verification needed)
        text_box_found = reliable_click(
            driver,
            (By.XPATH, "//input[@type='text' and @placeholder='Your name']"),
            None,
            "name input field"
        )
        
        if text_box_found:
            # Get the text box element again to type in it
            text_box = driver.find_element(By.XPATH, "//input[@type='text' and @placeholder='Your name']")
            
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
            (By.XPATH, "//span[contains(text(), 'Ask to join')]"),
            None,
            "'Ask to join' button",
            max_attempts=2
        )
        driver.save_screenshot("screenshots/ask_to_join.png")

        print("Join attempt completed, waiting in the meeting...")

        # Wait for 10 minutes to confirm that the host accepted the bot
        people_button = WebDriverWait(driver, timeout=600, poll_frequency=5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='People']"))
        )
        people_button.click()
        time.sleep(2)
        driver.save_screenshot("screenshots/people_button.png")

        participants_list = WebDriverWait(driver, timeout=10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='list' and @aria-label='Participants']"))
        )
        
        time.sleep(2)
        driver.save_screenshot("screenshots/participants_list.png")

        # Get all participant items within the list
        participant_items = participants_list.find_elements(By.XPATH, ".//div[@role='listitem']")

        # Iterate through each participant
        for participant in participant_items:
            if bot_name == participant.get_attribute("aria-label"):
                print(f"Bot {bot_name} successfully joined the meeting")
                break
            else:
                print(f"Bot {bot_name} was unable to join the meeting")
                exit()
        
        chat_button = WebDriverWait(driver, timeout=10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Chat with everyone']"))
        )
        chat_button.click()
        print("Chat button clicked")
        time.sleep(2)
        driver.save_screenshot("screenshots/chat_button.png")

        chat_input = WebDriverWait(driver, timeout=10).until(
            EC.presence_of_element_located((By.XPATH, "//textarea[@aria-label='Send a message']"))
        )
        chat_input.send_keys("Hello, how are you?")
        chat_input.send_keys(Keys.ENTER)
        print("Message sent")
        time.sleep(2)
        driver.save_screenshot("screenshots/message_sent.png")
        
        while True:
            time.sleep(1)
            
    
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Uncomment the line below if you want the browser to close automatically
        driver.quit()
        pass

if __name__ == "__main__":
    # Google Meet URL
    meet_url = "https://meet.google.com/gpz-dyny-hkr"
    bot_name = fake.name()

    # Join the meeting
    join_google_meet(bot_name, meet_url, headless=False)
