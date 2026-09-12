import datetime
import logging
import os
import time

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


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
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", btn)
                btn.click()
                self.logger.info('ok')
            except Exception as _:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.logger.info('ok')
                except Exception as _:
                    self.logger.info('error up')
                    continue

            return True

        return False

    def wait_control_buttons(self, timeout: int = 15) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_elements(
                    By.CSS_SELECTOR, "div.control-button[data-key]")
            )
            return True
        except Exception:
            n = len(self.driver.find_elements(
                By.CSS_SELECTOR, "div.control-button[data-key]"))
            self.logger.warning(f"control buttons not ready, found={n}")
            return False

    def up_ad(self, n_page: int, color_green: bool,
              cat_top: bool = False) -> bool:
        categories = list(self.cfg.clicker.category)
        category_count = {cat: 0 for cat in categories}

        url = self.cfg.clicker.url
        for i in range(n_page, 0, -1):
            pages_url = f'{url}%2Findex&page={i}&per-page=100'

            if not self.driver_get(pages_url):
                self.logger.warning(f"error driver get on {pages_url}")
                return False

            self.wait_control_buttons()

            items = self.driver.find_elements(
                By.CSS_SELECTOR, ".container-items > .item[data-key]")
            controls = {
                el.get_attribute("data-key"): el
                for el in self.driver.find_elements(
                    By.CSS_SELECTOR, "div.control-button[data-key]")
            }
            self.logger.info(
                f"page={i}/{n_page} ads={len(items)} controls={len(controls)}"
            )

            for j, item in enumerate(reversed(items)):
                try:
                    ad_id = item.get_attribute("data-key")
                    control = controls.get(ad_id)
                    if control is None:
                        self.logger.warning(
                            f"no control-button for ad {ad_id}")
                        continue

                    state_icons = control.find_elements(
                        By.CSS_SELECTOR, ".content-state .glyphicon")
                    if not state_icons:
                        continue
                    status = (state_icons[0].get_attribute("title") or
                              "").strip()

                    category_item = item.find_elements(By.CLASS_NAME,
                                                       "item_category")
                    if not category_item:
                        continue
                    category_item_name = category_item[0].text.split(
                        " / ")[-1].strip()

                    matched_cat = next(
                        (cat for cat in reversed(categories)
                         if cat in category_item_name),
                        None,
                    )
                    if matched_cat is None:
                        continue

                    color = item.get_attribute("class") or ""
                    color_in = "ads-partner" in color
                    if not color_green:
                        color_in = not color_in
                    if not color_in:
                        continue

                    if status == "Показано" and (
                            not cat_top or
                            category_count[matched_cat] <
                            self.cfg.clicker.n_category_top):
                        btn = control.find_element(
                            By.CSS_SELECTOR, ".content-up span.glyphicon")
                        prices = item.find_elements(By.CLASS_NAME, "price")
                        price = prices[0].text if prices else ""
                        msg = (
                            f"n={j},id={ad_id},"
                            f"category_item_name={category_item_name},"
                            f"status={status},"
                            f"price={price},"
                            f"color={color}"
                        )
                        if not self.click_ad(btn, msg):
                            self.logger.info("fail up")
                        category_count[matched_cat] += 1
                except Exception as e:
                    self.logger.warning(e)
                    continue

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
            self.logger.info(f"n_page={n_page} up={up}")

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
            self.logger.warning("start_up_ad failed: %s", ex, exc_info=True)
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
