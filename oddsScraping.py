import time
import datetime
import re
import dataclasses
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import analysis.graph as graph
import sns.line as line
from store.repository import Repository, TimelyOdds


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
        self.now = datetime.datetime.now().strftime("%H:%M")

    def __del__(self):
        self._driver.close()
        self._driver.quit()

    def get_all_race_info(self):

        def initialize_race():
            current_race_num, current_course_num = 0, 0
            # course_buttons = self._driver.find_elements_by_xpath(
            #     "//*[@id='contentsBody']/ul[1]/li")
            course_buttons = self._driver.find_elements_by_xpath(
                f"//*[@id='contentsBody']/div/div/div/ul/li[{self.held_day_count}]/\
                div/div[@class='content']/div/div")
            for index, course_button in enumerate(course_buttons):
                if course_button.get_attribute("class") == 'current':
                    current_course_num = index
                    break
            held = course_buttons[current_course_num].text
            race_buttons = self._driver.find_elements_by_xpath(
                "//*[@id='contentsBody']/ul/li")
            for index, race_button in enumerate(race_buttons):
                if race_button.get_attribute("class") == 'current':
                    current_race_num = index
                    break
            race_num = current_race_num + 1
            temp_start_time = self._driver.find_element_by_xpath(
                "//*[@id='syutsuba']/table/caption").find_element_by_css_selector('.cell.time').text
            start_time = temp_start_time.replace("発走時刻：", "").replace("時", ":").replace("分", "")
            return Race(held, race_num, self.now, start_time)

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

        def is_not_started(now, start_time):
            date_now = datetime.datetime.strptime(now, '%H:%M')
            date_start_time = datetime.datetime.strptime(start_time, '%H:%M') + datetime.timedelta(minutes=2)
            return date_now <= date_start_time

        def can_create_graph_image(now, start_time):
            date_now = datetime.datetime.strptime(now, '%H:%M')
            date_start_time = datetime.datetime.strptime(start_time, '%H:%M')
            return 300 <= (date_start_time - date_now).total_seconds() <= 360

        while True:
            race = initialize_race()
            if is_not_started(self.now, race.start_time):
                horse_list = self.get_horse_info()
                for horse in horse_list:
                    timelyOdds = TimelyOdds(held=race.held, race_number=race.race_num, horse_number=horse.number,
                                            acquisition_time=race.now, start_time=race.start_time, odds=horse.odds,
                                            popular=horse.popular, horse_name=horse.name)
                    self._repository.insert(timelyOdds)
                if can_create_graph_image(self.now, race.start_time):
                    graph_img_name = graph.create_graph_image(held=race.held, race_number=race.race_num)
                    line.notify(graph_img_name, './images/' + graph_img_name)
                    graph_img_name = graph.create_graph_image(held=race.held, race_number=race.race_num, only_last_one_hour=True)
                    line.notify(graph_img_name, './images/' + graph_img_name)
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
                "div[@class='odds']/div[@class='odds_line']/span[@class='num']").text
            popular = name_line.find_elements_by_xpath(
                "div[@class='odds']/div[@class='odds_line']/span[@class='pop_rank']")
            # 出走取り消しの場合は取得できないためスキップ
            if len(popular) > 0:
                popular = popular[0].text.replace("番人気)", "").replace("(", "")
                horse_list.append(Horse(i + 1, name, int(popular), float(odds)))
            else:
                horse_list.append(Horse(i + 1, name, None, None))
        return horse_list

    def count_held(self):
        # 開催日程を取得
        elements = self._driver.find_elements_by_xpath("//*[@id='main']/div")
        del elements[0]

        event_open_dates = list(map(lambda element: re.findall(
            r'\d+月\d+日', element.find_element_by_xpath("*[@class='sub_header']").text)[0], elements))
        for i, event_open_date in enumerate(event_open_dates):
            if event_open_date == today_mmdd:
                held_count = elements[i].find_elements_by_xpath("div[@class='content']/div/div[@class='waku']/a")
                return len(held_count)

    def get_one_held_race(self, held_number):
        # 開催日程を取得
        elements = self._driver.find_elements_by_xpath("//*[@id='main']/div")
        del elements[0]
        event_open_dates = list(map(lambda element: re.findall(
            r'\d+月\d+日', element.find_element_by_xpath("*[@class='sub_header']").text)[0], elements))
        for i, event_open_date in enumerate(event_open_dates):
            if event_open_date == today_mmdd:
                self.held_day_count = i + 1
                # 会場、開催日をクリック
                first_course = elements[i].find_element_by_xpath(
                    f"div[@class='content']/div/div[@class='waku'][{held_number}]/a")
                first_course.click()
                time.sleep(1)
                # レースをクリック
                race_element = self._driver.find_element_by_xpath(
                    "//*[@id='race_list']/tbody/tr[1]").find_element_by_class_name('syutsuba')
                race_element.click()
                self.get_all_race_info()
