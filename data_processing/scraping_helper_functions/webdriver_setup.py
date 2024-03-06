# This python script is used to write a helper function that initialized the
# selenium webdriver for dynamic web-scraping (later used in `get_author_info.py`
# and `get_pub_info.py`)

# Resources consulted online:
    # 1) https://chromedriver.chromium.org/getting-started
    # 2) https://selenium-python.readthedocs.io/getting-started.html
    # 3) https://www.browserstack.com/guide/python-selenium-to-run-web-automation-test

from selenium import webdriver

def initialize_driver():
    '''
    Initialize the selenium webdriver.

    Inputs: None
    
    Returns: selenium webdriver
    '''

    # Set up options for Chrome webdriver
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--headless=new')
    
    # Initialize and return the WebDriver
    driver = webdriver.Chrome(options=options)
    return driver