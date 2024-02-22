from selenium import webdriver

def initialize_driver():
    '''
    Initialize the selenium webdriver.

    Inputs: None
    
    Returns: selenium webdriver
    '''

    # Here, ensure that chromedriver.exe is in system PATH
    # Check by `where chromedriver`` (for Windows) or `which chromedriver` (for MAC)
    # If not, move it to the system PATH to avoid running webdriver.ChromeService()
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--headless=new')
    
    # Initialize and return the WebDriver
    driver = webdriver.Chrome(options=options)
    return driver