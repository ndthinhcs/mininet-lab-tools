from pageloader import PageLoader

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

import os

from logging import warning, info, debug, error

class YoutubePlayer(PageLoader):
    '''
    YoutubePlayer class is used to load a youtube video and wait for the video to load completely.
    url: A youtube url to load
    delay: Time to wait for the video to load
    preferences: A list of tuples of (preference_name, preference_value) to set in the firefox profile
    addons: A list of paths to the addons to be added to the firefox profile
    '''
    def __init__(self, url=None, delay=20, preferences=None, addons=None):
        super(YoutubePlayer, self).__init__((By.CLASS_NAME, 'html5-main-video'),
                                            delay, addons)
        self.start_driver()
        if url:
            self.load(url)

    def load(self, url):
        # check url is from youtube domain
        if 'youtube.com' in url:
            super().load(url)
        else:
            error('Not a valid youtube url')

    def play_button(self):
        try:
            self.driver.find_element(By.CLASS_NAME,'ytp-play-button').click()
        except AttributeError as e:
            error('Required to load() first')

class YoutubeLivePlayer(YoutubePlayer):
    def __init__(self, url=None, delay=20, preferences=None, addons=None):
        super(YoutubeLivePlayer, self).__init__(url, delay, preferences, addons)
    
    def _get_stream_url_list(self):
        pass

    def _play_stream(self, stream_url):
        pass

class GMeetHost(PageLoader):
    def __init__(self, timeout=20):
        # !TODO: Change the locator to homepage of meet
        # super(GoogleMeetPageLoader, self).__init__((By.CLASS_NAME, 'google-material-icons'), delay)
        pass

    def load(self, url):
        pass

    def create_meeting(self):
        pass

    def join_meeting(self):
        pass

    def leave_meeting(self):
        pass

    def get_invite_code(self):
        pass

    def start_virtual_camera(self):
        pass

    def stop_virtual_camera(self):
        pass

class GMeetGuest(PageLoader):
    def __init__(self, delay=20):
        pass

    def join_meeting_by_code(self, invite_code):
        pass

    def join_meeting_by_url(self, url):
        pass

    def start_virtual_camera(self):
        pass

    def stop_virtual_camera(self):
        pass

    def leave_meeting(self):
        pass

class GDriveDownloader(PageLoader):
    '''
    GDriveDownloader class is used to download a file from google drive.
    url: A google drive url to download
    download_folder: path to the folder where the file will be downloaded
    timeout: Time to wait for the page to load
    preferences: A list of tuples of (preference_name, preference_value) to set in the firefox profile
    '''
    def __init__(self, url=None, download_folder='./temp', timeout=20, addons=None):
        # check if it is absolute path or relative path
        if not os.path.isabs(download_folder):
            download_folder = f'{os.getcwd()}/{download_folder}'
        if not download_folder.endswith('/'):
            download_folder = f'{download_folder}/'

        # check if download folder exists
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        super(GDriveDownloader, self).__init__((By.ID, 'uc-download-link'),
                                               preferences=[('browser.download.folderList', 2),
                                                            ('browser.download.dir', f'{download_folder}'),
                                                            ('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')],
                                               timeout=timeout, addons=addons)

        self.download_folder = download_folder
        self.start_driver()
        if url:
            self.load(url)

    def load(self, url) -> None:
        if 'drive.google.com' in url:
            super().load(url)
        else:
            error('Not a valid google drive url')

    def download(self) -> None:
        self.driver.find_element(By.ID, 'uc-download-link').click()

    def clean_download(self) -> None:
        # delete all files in download folder
        for file in os.listdir(self.download_folder):
            os.remove(f"{self.download_folder}/{file}")

class GDocsPageLoader(PageLoader):
    def __init__(self, timeout=20, preferences=None, addons=None):
        super(GDocsPageLoader, self).__init__((), timeout, preferences, addons)

    # def 

class GPhotosPageLoader(PageLoader):
    def __init__(self, locator, delay=3, extension=''):
        super().__init__(locator, delay, extension)

    def load(self, url):
        super().load(url)