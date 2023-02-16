from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

from logging import warning, info, debug, error

class PageLoader():
    '''
    PageLoader class is used to load a webpage and wait for the page to load completely.
    locator: A tuple of (By, locator) to wait for the page to load
    delay: Time to wait for the page to load
    preferences: A list of tuples of (preference_name, preference_value) to set in the firefox profile
    addons: A list of paths to the addons to be added to the firefox profile
    '''
    def __init__(self, locator, timeout=3, preferences=None, addons=None):
        self.locator = locator
        self.delay = timeout
        self.preferences = preferences # [(preference_name, preference_value]
        self.extension = addons # [addon_paths]
        
    def start_driver(self):
        self.firefox_profile = FirefoxProfile()
        if self.preferences:
            for preference in self.preferences:
                self.firefox_profile.set_preference(preference[0], preference[1])
        
        if self.extension:
            self.firefox_profile.add_extension(self.extension)

        self.driver = webdriver.Firefox()

    def load(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located(self.locator))
            info("Page is ready!")
        except TimeoutException:
            info("Loading took too much time!")
            self.close_driver()
        except AttributeError as e:
            error('Required to start_driver() first')
        except Exception as e:
            error(e)
            self.close_driver()
            raise e
    
    def get_page_source(self):
        return self.driver.page_source
    
    def close_driver(self, quit=False):
        if quit:
            self.driver.quit()
        self.driver.close()
