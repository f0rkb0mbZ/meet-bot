import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import random
import math

import os
os.system('pip install Faker')

from faker import Faker

fake = Faker()

def reliable_click(driver, target_locator, verification_locator=None, description="element", max_attempts=3, wait_time=10):
    """
    Performs a reliable click operation with multiple attempts and verification
    
    Args:
        driver: WebDriver instance
        target_locator: Tuple of (By.X, "locator") for the element to click
        verification_locator: Tuple of (By.X, "locator") to verify click worked, or None if no verification
        description: Description of the element for logging
        max_attempts: Maximum number of attempts to make
        wait_time: How long to wait for elements to appear
        
    Returns:
        bool: Whether the click was successful
    """
    success = False
    
    for attempt in range(max_attempts):
        try:
            print(f"{description} click attempt {attempt+1}/{max_attempts}")
            
            # Find the element
            element = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable(target_locator)
            )
            
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(random.uniform(0.2, 0.5))
            
            # First try: ActionChains click
            try:
                action = ActionChains(driver)
                action.move_to_element(element)
                action.click()
                action.perform()
                time.sleep(0.8)
                
                # Verify if needed
                if verification_locator:
                    try:
                        WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located(verification_locator)
                        )
                        print(f"{description} action confirmed (ActionChains click)")
                        success = True
                        break
                    except:
                        print(f"ActionChains click didn't verify, trying JavaScript click")
                        # Second try: JavaScript click
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(0.8)
                        
                        try:
                            WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located(verification_locator)
                            )
                            print(f"{description} action confirmed (JavaScript click)")
                            success = True
                            break
                        except:
                            print(f"JavaScript click didn't verify, trying next attempt")
                else:
                    # No verification needed, assume success
                    print(f"{description} clicked (no verification needed)")
                    success = True
                    break
                    
            except Exception as e:
                print(f"Click operation failed: {e}")
                # Try JavaScript click as fallback
                try:
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(0.8)
                    
                    if verification_locator:
                        try:
                            WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located(verification_locator)
                            )
                            print(f"{description} action confirmed (fallback JavaScript click)")
                            success = True
                            break
                        except:
                            print("Fallback JavaScript click didn't verify")
                    else:
                        # No verification needed, assume success
                        print(f"{description} clicked with fallback (no verification needed)")
                        success = True
                        break
                except Exception as e2:
                    print(f"JavaScript fallback failed: {e2}")
            
        except Exception as e:
            print(f"Could not find {description} on attempt {attempt+1}: {e}")
        
        # Wait before next attempt
        time.sleep(1.5)
    
    if not success and verification_locator:
        print(f"WARNING: Could not confirm {description} action after {max_attempts} attempts")
    
    return success

def join_google_meet(meet_url, headless=False):
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
    options.add_argument("--use-fake-device-for-media-stream")
    options.add_argument("--use-fake-ui-for-media-stream")
    
    if headless:
        options.add_argument("--headless")
    
    # Create undetected ChromeDriver instance
    driver = uc.Chrome(options=options)
    driver.maximize_window()
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
        
        # Turn off video with verification
        reliable_click(
            driver,
            (By.XPATH, "//div[@role='button' and @aria-label='Turn off camera']"),
            (By.XPATH, "//div[@role='button' and @aria-label='Turn on camera']"),
            "video off",
            max_attempts=3
        )
        
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
            name = fake.name()
            for char in name:
                text_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes
                
            time.sleep(random.uniform(0.5, 1.0))
            print("Name entered")
        
        # Try to find and click join button
        
        # Try "Ask to join" button
        reliable_click(
            driver,
            (By.XPATH, "//span[contains(text(), 'Ask to join')]"),
            None,
            "'Ask to join' button",
            max_attempts=2
        )
        
        print("Join attempt completed, waiting in the meeting...")
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
    
    # Join the meeting
    join_google_meet(meet_url, headless=False)
