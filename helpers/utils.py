import random
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def reliable_click(driver, target_locator, wait_time=10):
    try:        
        # Find the element
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable(target_locator)
        )
        
        # Scroll into view
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", element
        )
        time.sleep(random.uniform(0.2, 0.5))
        
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


def setup_mutation_observer(driver) -> None:
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
                // If it's an element, grab its text; if it's a text node, use it directly
                const text = (node.nodeType === Node.TEXT_NODE)
                    ? node.nodeValue
                    : node.textContent;
                if (text) {
                    if (joinedRe.test(text.trim())) {
                        console.log('Someone joined! Text matched "joined":', text.trim());
                        // fire your notification or message here…
                        window._join_message = text.trim();
                        return;  // stop once we've detected one
                    }
                    if (leftRe.test(text.trim())) {
                        console.log('Someone left! Text matched "has left the meeting":', text.trim());
                        // fire your notification or message here…
                        window._left_message = text.trim();
                        return;  // stop once we've detected one
                    }   
                }
                if (node.tagName === 'BUTTON' && node.getAttribute('aria-label') === 'Meeting details') {
                    console.log('Meeting details button found!');
                    // fire your notification or message here…
                    window._join_accepted = true;
                    return;  // stop once we've detected one
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
    
def find_video_status(driver):
    try:
        # Check if video is on
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
