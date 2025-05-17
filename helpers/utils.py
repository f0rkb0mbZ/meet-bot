from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


import random
import time


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