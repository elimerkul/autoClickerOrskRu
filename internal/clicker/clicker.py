import datetime
import logging
import os
import time

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class Clicker:
    def __init__(self, cfg):
        assert cfg.state in ['prod', 'dev']

        self.cfg = cfg

        self.s = Service(self.cfg.driver.path)
        self.options = webdriver.ChromeOptions()

        if cfg.state == 'prod':
            user_agent = UserAgent().random
            self.options.add_argument(f"user-agent={user_agent}")
            self.options.add_argument("--headless=new")
            self.options.headless = True
            self.options.add_argument("--no-sandbox")
            self.options.add_argument("--disable-dev-shm-usage")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--window-size=1920,1080")
            self.options.binary_location = cfg.driver.binary_location

        self.logger = logging.getLogger(__name__)

        self.driver = None
        self.login = os.environ.get("AUTH_LOGIN", "").strip()
        self.password = os.environ.get("AUTH_PASSWORD", "").strip()
        if not self.login or not self.password:
            raise ValueError(
                "AUTH_LOGIN and AUTH_PASSWORD environment variables are required"
            )

    def auth(self) -> bool:
        login = self.login
        password = self.password

        for i in range(self.cfg.clicker.auth_attempt):
            try:
                # auth
                self.logger.info("auth")
                login_input = self.driver.find_element(By.ID,
                                                       "loginform-username")
                login_input.clear()
                login_input.send_keys(login)
                time.sleep(1)

                password_input = self.driver.find_element(By.ID,
                                                          "loginform-password")
                password_input.clear()
                password_input.send_keys(password)
                time.sleep(5)
            except Exception as _:
                continue
            return True

        return False

    def driver_get(self, url) -> bool:
        for i in range(self.cfg.clicker.connect_attempt):
            try:
                self.driver.get(url=url)
                time.sleep(7)
            except Exception as _:
                continue
            return True

        return False

    def click_ad(self, btn, msg) -> bool:
        self.logger.info(msg)
        for i in range(self.cfg.clicker.click_attempt):
            time.sleep(self.cfg.clicker.click_sleep)
            try:
                btn.click()
                self.logger.info('ok')
            except Exception as _:
                self.logger.info('error up')
                continue

            return True

        return False

    def up_ad(self, n_page: int, color_green: bool,
              cat_top: bool = False) -> bool:
        category = self.cfg.clicker.category
        category_count = [0] * len(category)

        url = self.cfg.clicker.url
        for cat_id, cat in enumerate(category[::-1]):
            self.logger.info(f"start up category {cat}")
            for i in range(n_page, 0, -1):
                pages_url = f'{url}%2Findex&page={i}&per-page=100'

                if not self.driver_get(pages_url):
                    self.logger.warning(f"error driver get on {pages_url}")
                    return False

                control_btns = self.driver.find_elements(By.CLASS_NAME,
                                                         "control-button")[:]
                items = self.driver.find_elements(By.CLASS_NAME, "item")[:]

                for j in range(len(control_btns) - 1, -1, -1):
                    status = control_btns[j]. \
                        find_element(By.CLASS_NAME, "glyphicon"). \
                        get_attribute('title')

                    category_item = items[j].find_elements(By.CLASS_NAME,
                                                           'item_category')
                    category_item_name = category_item[0].text. \
                        split(' / ')[-1]

                    if (cat not in category_item_name):
                        continue

                    color = items[j].get_attribute('class')

                    color_in = 'ads-partner' in color
                    if not color_green:
                        color_in = not color_in

                    if not color_in:
                        continue

                    if status == 'Показано' and \
                            (not cat_top or
                             category_count[cat_id] <
                             self.cfg.clicker.n_category_top):

                        try:
                            btn = control_btns[j]. \
                                find_element(By.CLASS_NAME, "content-up"). \
                                find_element(By.CLASS_NAME, "glyphicon")

                            price = items[j].find_elements(By.CLASS_NAME,
                                                           'price')[0].text

                            msg = f"n={str(j)}," \
                                  f"category_item_name={category_item_name}," \
                                  f"status={status}," \
                                  f"price={price}," \
                                  f"color={color}"

                            if not self.click_ad(btn, msg):
                                self.logger.info("fail up")
                        except Exception as e:
                            self.logger.warning(e)

                        category_count[cat_id] += 1

                time.sleep(self.cfg.clicker.page_sleep)
        return True

    def move_and_get_last_page(self) -> int:

        try:
            # move on last page
            self.driver.find_element(By.CLASS_NAME, "last"). \
                find_element(By.CLASS_NAME, "glyphicon").click()
            time.sleep(3)

            # count of page
            n_page = int(self.driver.find_element(By.CLASS_NAME, "pagination").
                         find_element(By.CLASS_NAME, 'active').text)
        except Exception as e:
            n_page = 1

        return n_page

    def start_up_ad(self, up: str = "all"):
        assert up in ["all", "green", "white"]

        self.driver = webdriver.Chrome(
            service=self.s,
            options=self.options
        )

        url = self.cfg.clicker.url

        if not self.driver_get(url):
            self.logger.warning(f"error driver get on {url}")
            return

        if not self.auth():
            self.logger.warning("error auth")
            return

        try:
            self.driver.find_element(By.CLASS_NAME, "form-actions"). \
                find_element(By.CLASS_NAME, "btn").click()
            time.sleep(3)

            n_page = self.move_and_get_last_page()

            if up in ["all", "green"]:
                self.logger.info('starting to mark green ads')
                if not self.up_ad(n_page,
                                  color_green=True,
                                  cat_top=self.cfg.clicker.category_top):
                    return

            if up in ["all", "white"]:
                self.logger.info('starting to mark white ads')
                if not self.up_ad(n_page, color_green=False):
                    return

        except Exception as ex:
            self.logger.warning(ex)
        finally:
            self.driver.close()
            self.driver.quit()

    def get_start_end_datetime(self):
        start_time = self.cfg.clicker.start_time
        end_time = self.cfg.clicker.end_time

        time_now = datetime.datetime.now()
        time_start = datetime.datetime(time_now.year,
                                       time_now.month,
                                       time_now.day,
                                       hour=start_time.hour,
                                       minute=start_time.minute,
                                       second=start_time.second)
        end_time = datetime.datetime(time_now.year,
                                     time_now.month,
                                     time_now.day,
                                     hour=end_time.hour,
                                     minute=end_time.minute,
                                     second=end_time.second)
        mid_time = datetime.datetime(time_now.year,
                                     time_now.month,
                                     time_now.day,
                                     hour=23,
                                     minute=59,
                                     second=59)

        return time_start, end_time, mid_time

    def work_time(self) -> bool:
        time_now = datetime.datetime.now()

        time_start, end_time, _ = self.get_start_end_datetime()

        sleep = (time_now >= time_start) and (time_now < end_time)
        self.logger.info(f"time_start: {time_start}, "
                         f"time_end: {end_time}, "
                         f"time_now: {time_now}")
        return sleep

    def sleep(self):
        time_start, end_time, mid_time = self.get_start_end_datetime()
        time_now = datetime.datetime.now()
        time_sleep = time_start - time_now
        if time_now < mid_time:
            time_sleep += datetime.timedelta(days=1)
        self.logger.info(f"time_start: {time_start}, "
                         f"time_end: {end_time}, "
                         f"sleep: {time_sleep}")
        time.sleep(time_sleep.seconds)
