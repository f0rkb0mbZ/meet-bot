import undetected_chromedriver as uc

def launch_webdriver(headless: bool = False):
    """
    Launch a undetected Chrome webdriver instance
    """
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless")
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
        
    # Create undetected ChromeDriver instance
    driver = uc.Chrome(options=options)
    # driver.maximize_window() # failed for fake xvfb display

    # Setting permissions for meet.google.com beforehand
    driver.execute_cdp_cmd("Browser.grantPermissions",
    {
        "origin": "https://meet.google.com",
        "permissions": ["audioCapture", "videoCapture"]
    })

    return driver
