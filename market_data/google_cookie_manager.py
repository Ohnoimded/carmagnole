from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from asgiref.sync import sync_to_async
import json


class GoogleCookieManager:
    def __init__(self, redis):
        self.redis = redis
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_experimental_option('browserStartupTimeout', 1000000)
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        chrome_driver_path = "/usr/bin/chromedriver"
        self.driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)


    @sync_to_async
    def fetch_store_google_cookies(self):
        try:
            self.driver.get('https://www.google.com/')
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            
            self.driver.get(f'https://www.google.com/finance/quote/NIFTY_50:INDEXNSE')
            self.driver.execute_script('document.getElementsByTagName("html")[0].style.scrollBehavior = "auto"')
            
            WebDriverWait(self.driver, 120).until(EC.element_to_be_clickable((By.XPATH, '''/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]'''))).click()
            
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            
            all_cookies=self.driver.get_cookies()
            
            cookies_dict = {}
            cookies_str=''
            for cookie in all_cookies:
                cookies_dict[cookie['name']] = cookie['value']
                cookies_str+=str(cookie['name']+ '=' +cookie['value']+';')
                
            cookies_dict = json.dumps(cookies_dict)
            self.redis.set("cookies_google",cookies_str)
            self.redis.set("cookies_google_dict",cookies_dict)
        except Exception as e:
            raise Exception("Could not access google or set the cookies")
        finally:
            self.driver.quit()


