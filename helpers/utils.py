import random
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import Tuple
import undetected_chromedriver as uc


def reliable_click(driver: uc.Chrome, target_locator: Tuple[By, str], wait_time: int = 10) -> bool:
    """
    Click element with actionchains or JavaScript, whichever works
    """
    try:        
        # Find the element
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable(target_locator)
        )
        
        # Try ActionChains click
        try:
            action = ActionChains(driver)
            action.move_to_element(element)
            action.click()
            action.perform()
            return True
        except Exception as e:
            print(f"ActionChains click failed: {e}, trying JavaScript click")
            # Fall back to JavaScript click
            driver.execute_script("arguments[0].click();", element)
            return True
            
    except Exception as e:
        print(f"Could not click: {e}")
        return False


def setup_mutation_observer(driver: uc.Chrome) -> None:
    """
    Sets up a JS mutation observer to monitor DOM changes. 
    Monitors for participants joining or leaving meetings, and when the bot is accepted into the meeting.
    """
    mutation_observer_script = """
    // Regex definitions for join / leave toast notifications
    const joinedRe = /\\bjoined$/i;
    const leftRe = /\\bhas left the meeting$/i;

    // callback function for mutation observer
    function onMutations(mutationsList) {
        for (const mutation of mutationsList) {
            // We only care about nodes being added
            if (mutation.type !== 'childList' || mutation.addedNodes.length === 0)
                continue;

            for (const node of mutation.addedNodes) {
                // If it's an element, grab its text; if it's a text node, use it directly
                const text = (node.nodeType === Node.TEXT_NODE)
                    ? node.nodeValue
                    : node.textContent;
                if (text) {
                    if (joinedRe.test(text.trim())) {
                        console.log('Someone joined! Text matched "joined":', text.trim());
                        window._join_message = text.trim(); // storing info in global window object
                        return;
                    }
                    if (leftRe.test(text.trim())) {
                        console.log('Someone left! Text matched "has left the meeting":', text.trim());
                        window._left_message = text.trim(); // storing info in global window object
                        return;
                    }   
                }
                if (node.tagName === 'BUTTON' && node.getAttribute('aria-label') === 'Meeting details') {
                    console.log('Meeting details button found!');
                    window._join_accepted = true; // storing info in global window object
                    return;
                }
            }
        }
    }

    // Create & attach the observer
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

def clear_got_it_dialogs(driver):
    """
    Removes any "Got it" tutorial/intro dialog boxes that might obstruct interaction with the UI
    """
    try:
        got_it_buttons = driver.find_elements(
            By.XPATH, "//button[.//span[normalize-space(.)='Got it']]"
        )
        for button in got_it_buttons:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(1)
    except Exception as e:
        print(f"Error clearing got it dialogs: {e}")

def find_mute_status(driver: uc.Chrome) -> str:
    """
    Determines the current microphone mute status.
    """
    try:
        mic_off_buttons = driver.find_elements(
            By.XPATH, "//button[@aria-label='Turn off microphone']"
        )
        mic_on_buttons = driver.find_elements(
            By.XPATH, "//button[@aria-label='Turn on microphone']"
        )

        if len(mic_off_buttons) > 0:
            return "unmuted"
        elif len(mic_on_buttons) > 0:
            return "muted"
        else:
            return "unknown"
    except Exception as e:
        print(f"Error checking mute status: {e}")
        return "unknown"
    
def find_video_status(driver: uc.Chrome) -> str:
    """
    Determines the current camera video status.
    """
    try:
        video_off_buttons = driver.find_elements(
            By.XPATH, "//button[@aria-label='Turn off camera']"
        )
        video_on_buttons = driver.find_elements(
            By.XPATH, "//button[@aria-label='Turn on camera']"
        )

        if len(video_off_buttons) > 0:
            return "video_on"
        elif len(video_on_buttons) > 0:
            return "video_off"
        else:
            return "unknown"
    except Exception as e:
        print(f"Error checking video status: {e}")
        return "unknown"
