from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from selenium import webdriver
import time
import os
import re

class AppointmentBot:
    
    def __init__(self):
        self.main_url = "https://inpol.mazowieckie.pl/"
        self.open_browser()

    def open_browser(self):
        """
        open_browser will open the genuine browser in remote rebugging port and then add related setting to make it undetectable
        """

        # open chrome in debuggin port
        # os.system("google-chrome-beta --remote-debugging-port=9222&")
        os.system("google-chrome-unstable --remote-debugging-port=9222&")

        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--disable-notifications")
        self.options.add_argument("--deny-permission-prompts")
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        # self.options.add_argument('--no-sandbox')

        self.driver = webdriver.Chrome(self.options)

        url = "https://www.google.com"
        self.driver.get(url)
        time.sleep(2)

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.refresh()
        time.sleep(2)

    def book_app(self):
        """
        Book the app
        """
        cases_url = "https://inpol.mazowieckie.pl/home/cases"
        self.driver.get(cases_url)
        time.sleep(1)

        case_ele = self.find_element("css selector", "mat-table > tr:nth-of-type(4)")
        case_ele.click()
        time.sleep(2)

        # click
        self.find_element("xpath", "//h3[text()='Make an appointment at the office']/../button").click()
        time.sleep(1)
    
        # click dropdown 1
        self.find_element("xpath", "//mat-select").click()
        time.sleep(1)

        # select first option
        self.find_element("xpath", "//mat-option[2]").click()
        time.sleep(1)

        # click dropdown 2
        # document.querySelector("*[name='queueName']")
        self.find_element("xpath", "(//mat-select)[2]").click()
        time.sleep(1)

        # select first option
        # document.querySelector("*[name='queueName']")
        self.find_element("xpath", "//mat-option[2]").click()
        time.sleep(2)

        # after selecting both drop downs a alert box will be opened

        # check if the captcha
        if "Captcha verification" in self.driver.page_source:
            time.sleep(1)
            if not self.solve_popup():
                raise Exception("POPup Captcha Solving Failed at selecting dropdowns.")
        
        self.book_time_slots()

        
    def book_time_slots(self):
        # find the next button
        next_ = self.find_element("xpath", "//button[@aria-label='Next month']")
        prev_ = self.find_element("xpath", "//button[@aria-label='Previous month']")

        next_.click()
        time.sleep(1)
        prev_.click()

        # loop 5 times to check if dates available else click next
        for i in range(5):
            # get available dates
            all_available_dates = self.find_all_elements("xpath", "//td[not(@aria-disabled) and @tabindex='-1']")
            if not all_available_dates:
                next_.click()
                continue
            
            # if dates exist
            if self.book_hour_slot(all_available_dates):
                break
        
        return False, "No Available Dates"
    
    def book_hour_slot(self, all_available_dates):
        for a_date in all_available_dates:
            # click date
            a_date.click()

            # solve the popup captcha
            if not self.solve_popup():
                raise Exception("POPup Captcha Solving Failed at selecting dates.")
            
            all_hours_slots = self.find_all_elements("css selector", "button.tiles__link")

            if not all_hours_slots:
                continue
                # return False, "No Available Hours"
            
            for hour_slot in all_hours_slots:
                # click slot
                hour_slot.click()

                # confirm
                yes_ele = self.find_element("xpath", "//button[text()='Yes']")
                if yes_ele:
                    yes_ele.click()
                    print("SLOT PICKED SUCCESSFULLY.")
                    time.sleep(3)
                    return True
            

    def validate_login(self):
        self.driver.get(self.main_url)
        time.sleep(1)

        ele = self.find_element("xpath", "//div[@class='user__header']/span")
        if not ele:
            is_loggedin, message = self.__login()
            if not is_loggedin:
                raise Exception(message)
    
    def __login(self):
        try:
            # accept cookies if it asks
            self.find_element("xpath", "//*[text()='Got it!']").click()
            time.sleep(1)
        except:
            pass

        # click and enter email
        email_ele = self.find_element("xpath", "//*[@data-placeholder='Email']")
        if not email_ele:
            custom_error = "Email Element Not Found"
            return False, custom_error
        email_ele.click()
        time.sleep(1)

        # enter mail
        self.send_keys(os.getenv("U_EMAIL"), email_ele)

        pass_ele = self.click_pwd()
        if not pass_ele:
            custom_error = "Password Element Not Found"
            return False, custom_error
        
        # enter pass
        self.send_keys(os.getenv("U_PASS"), pass_ele)
        time.sleep(2)

        if not self.click_checkbox():
            custom_error = "Checkbox Not Clicked"
            return False, custom_error
        
        s_key = self.get_site_key()
        print("SITE_KEY:", s_key)
        
        signin_ele = self.find_element("xpath", "//button[@class='btn btn--submit']")
        if not signin_ele:
            custom_error = "Signin Element Not Found"
            return False, custom_error
        
        try:
            # sign in
            signin_ele.click()
        except Exception as e:
            custom_error = "Captcha Not Solved."

            # TODO
            input("SOLVE CAPTCHA and Press ENTER.")
            signin_ele.click()
            return False, custom_error
        
        return True, "Login Successfully"

    def click_checkbox(self) -> bool:
        """
        click the I am not robot box
        """
        try:
            # click password
            pass_ele = self.click_pwd()

            self.send_keys(Keys.TAB + Keys.ENTER, pass_ele)
            time.sleep(1)
            return True
        except Exception as e:
            print("ERROR:\t%s"%e)
            return False

    def get_site_key(self):
        try:
            ele = self.find_element("xpath", "//iframe[@title='reCAPTCHA']")
            site_key_url = ele.get_attribute('src')
            
            pattern = r'k=([^&]+)'
            match = re.search(pattern, site_key_url)
            return match.group(1)
        except Exception as e:
            print("ERROR:\t%s"%e)
            return False

    def click_pwd(self):
        """
        click the password field
        """
        try:
            # click and enter password
            pass_ele = self.find_element("xpath", "//*[@data-placeholder='Password']")
            pass_ele.click()
            return pass_ele
        except Exception as e:
            print("ERROR:\t%s"%e)
            return False
        
    def solve_captcha(self, msg : str):
        input("Please sove CAPTCHA For:\t%s"%msg)
        return True

    def solve_popup(self, msg : str = "solving_popup"):

        # find the captcha dialog
        ele = self.find_element("css selector", "#captchaDialogForm")
        # click r
        self.send_keys(Keys.ENTER, ele)

        # find the captcha images
        captcha_image = ele.find_element("xpath", "//img")
        if captcha_image:
            # if captcha_image solve captcha
            if not self.solve_captcha(msg):
                raise Exception("CAPTCHA not solved for:\t%s"%msg)

        time.sleep(1)

        verify_ele = self.find_element("xpath", "//button/span[text()='Verify']/..")
    
        # click verify if exists
        verify_ele.click()

        return True

    def find_element(self, selector_type, selector, timeout : int = 10):
        try:
            ele = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((selector_type, selector)))
            self.driver.execute_script("arguments[0].scrollIntoView();", ele)
            return ele if ele else False
        except Exception as e:
            # print("ERROR:\t%s"%e)
            return False
    
    def find_all_elements(self, selector_type, selector : str, timeout = 10):
        try:
            eles = WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located((selector_type, selector)))
            return eles
        except Exception as e:
            return False

    def send_keys(self, keys : str, ele = None):
        """
        send_keys will send keys to element if given otherwise will send to the browser
        """
        try:
            ac = ActionChains(self.driver, duration=2000)
            if ele:
                ac.send_keys_to_element(ele, keys)
            else:
                ac.send_keys(keys)
            ac.perform()
            return True
        except Exception as e:
            print("ERROR:\t%s"%e)
            return False

if __name__ == "__main__":
    
    # load the env var
    load_dotenv()

    bot = AppointmentBot()

    bot.validate_login()
    
    time.sleep(2)

    # book the appointment the next available date
    bot.book_app()

    # bot.driver.execute_script("arguments[0].scrollIntoView();", element)

    bot.driver.quit()
    
    # click_robot_checkbox(driver)

    # https://inpol.mazowieckie.pl/home/cases/00efe80a-34eb-43a4-8664-6e4baddeb8ec

    # u1 = f"https://2captcha.com/in.php?key={os.getenv('APIKEY_2CAPTCHA')}&method=userrecaptcha&googlekey={s_key}&pageurl={url}&json=1&invisible=1"


