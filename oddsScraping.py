import time
import datetime
import re
import dataclasses
from selenium import webdriver
from store.utils import Repository, TimelyOdds
from selenium.webdriver.chrome.options import Options


today_yyyymmdd = datetime.datetime.now().strftime('%Y%m%d')
today_mmdd = datetime.datetime.now().strftime("%-m月%-d日")


@dataclasses.dataclass
class Horse:
    number: int
    name: str
    popular: int
    odds: float


@dataclasses.dataclass
class Race:
    held: str
    race_num: int
    now: str
    start_time: str


class OddsScraping:
    HOME_URL = "https://www.jra.go.jp/"
    DRIVER_PATH = './chromedriver'

    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(executable_path=self.DRIVER_PATH, options=options)
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(10)
        driver.get(self.HOME_URL)
        driver.find_element_by_xpath("//*[@id='quick_menu']/div/ul/li[2]").click()
        self._repository = Repository()
        self._driver = driver

    def __del__(self):
        self._driver.close()
        self._driver.quit()

    def initialize_race(self):
        current_race_num, current_course_num = 0, 0
        course_buttons = self._driver.find_elements_by_xpath(
            "//*[@id='contentsBody']/ul[1]/li")
        for index, course_button in enumerate(course_buttons):
            if course_button.get_attribute("class") == 'current':
                current_course_num = index
                break
        held = course_buttons[current_course_num].text
        race_buttons = self._driver.find_elements_by_xpath(
            "//*[@id='contentsBody']/ul[2]/li")
        for index, race_button in enumerate(race_buttons):
            if race_button.get_attribute("class") == 'current':
                current_race_num = index
                break
        race_num = current_race_num + 1
        temp_start_time = self._driver.find_element_by_xpath(
            "//*[@id='syutsuba']/table/caption").find_element_by_css_selector('.cell.time').text
        start_time = temp_start_time.replace("発走時刻：", "").replace("時", ":").replace("分", "")
        now = datetime.datetime.now().strftime("%H:%M")
        return Race(held, race_num, now, start_time)

    def get_all_race_info(self):
        def has_next_race():
            current_race_num = 0
            race_buttons = self._driver.find_elements_by_xpath(
                "//*[@id='contentsBody']/ul[2]/li")
            for i, race_button in enumerate(race_buttons):
                if race_button.get_attribute("class") == 'current':
                    current_race_num: int = i
                    break
            return len(race_buttons) != current_race_num + 1

        def click_next_race():
            current_race_num = 0
            race_buttons = self._driver.find_elements_by_xpath(
                "//*[@id='contentsBody']/ul[2]/li")
            for i, race_button in enumerate(race_buttons):
                if race_button.get_attribute("class") == 'current':
                    current_race_num = i
                    break
            race_buttons[current_race_num + 1].click()

        while True:
            race = self.initialize_race()
            horse_list = self.get_horse_info()
            for horse in horse_list:
                print(vars(horse))
                timelyOdds = TimelyOdds(held=race.held, race_number=race.race_num, horse_number=horse.number,
                                        acquisition_time=race.now, start_time=race.start_time, odds=horse.odds,
                                        popular=horse.popular, horse_name=horse.name)
                self._repository.insert(timelyOdds)
            if has_next_race():
                click_next_race()
            else:
                self._repository.commit()
                break

    def get_horse_info(self):
        horse_list = []
        horse_tr_list = self._driver.find_elements_by_xpath("//*[@id='syutsuba']/table/tbody/tr")
        for i, horse_tr in enumerate(horse_tr_list):
            name_line = horse_tr.find_element_by_xpath("td[@class='horse']/div[@class='name_line']")
            name = name_line.find_element_by_xpath("div[@class='name']").text
            odds = name_line.find_element_by_xpath(
                "div[@class='odds']/div[@class='odds_line']/strong").text
            popular = name_line.find_elements_by_xpath(
                "div[@class='odds']/div[@class='odds_line']/span")
            # 出走取り消しの場合は取得できない
            if len(popular) > 0:
                popular = popular[0].text.replace("番人気)", "").replace("(", "")
            else:
                popular = None
            horse_list.append(Horse(i + 1, name, int(popular), float(odds)))
        return horse_list

    def count_held(self):
        # 開催日程を取得
        elements = self._driver.find_elements_by_xpath("//*[@id='main']/div")
        del elements[0]

        event_open_dates = list(map(lambda element: re.findall(
            r'\d+月\d+日', element.find_element_by_xpath("*[@class='sub_header']").text)[0], elements))
        for i, event_open_date in enumerate(event_open_dates):
            if event_open_date == today_mmdd:
                # 会場、開催日をクリック
                held_count = elements[i].find_elements_by_xpath("div[@class='content']/ul/li/a")
                return len(held_count)

    def get_one_held_race(self, held_number):
        # 開催日程を取得
        elements = self._driver.find_elements_by_xpath("//*[@id='main']/div")
        del elements[0]
        event_open_dates = list(map(lambda element: re.findall(
            r'\d+月\d+日', element.find_element_by_xpath("*[@class='sub_header']").text)[0], elements))
        for i, event_open_date in enumerate(event_open_dates):
            if event_open_date == today_mmdd:
                # 会場、開催日をクリック
                first_course = elements[i].find_element_by_xpath(
                    f"div[@class='content']/ul/li[{held_number}]/a")
                first_course.click()
                time.sleep(1)
                # レースをクリック
                race_element = self._driver.find_element_by_xpath(
                    "//*[@id='race_list']/tbody").find_element_by_class_name('race_num')
                race_element.click()
                self.get_all_race_info()
