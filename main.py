import time
import datetime
# import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup


class Horse:
    def __init__(self, number, name, popular, odds):
        self.number = number
        self.name = name
        self.popular = popular
        self.odds = odds
    number = None
    name = None
    odds = None


class Race:
    def __init__(self, held, race_num, now, start_time):
        self.held = held
        self.race_num = race_num
        self.now = now
        self.start_time = start_time
    held = None
    race_num = None
    now = None
    start_time = None
    horses = None


def get_horse_info(driver):
    horse_list = []
    horse_tr_list = driver.find_elements_by_xpath("//*[@id='syutsuba']/table/tbody/tr")
    for i, horse_tr in enumerate(horse_tr_list):
        name_line = horse_tr.find_element_by_xpath("td[@class='horse']/div[@class='name_line']")
        number = i + 1
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
        horse_list.append(Horse(number, name, popular, odds))
    return horse_list


def has_next_race(driver):
    global current_race_num
    race_buttons = driver.find_elements_by_xpath(
        "//*[@id='contentsBody']/ul[2]/li")
    for i, race_button in enumerate(race_buttons):
        if(race_button.get_attribute("class") == 'current'):
            current_race_num = i
            break
    return len(race_buttons) != current_race_num + 1


def click_next_race(driver):
    global current_race_num
    race_buttons = driver.find_elements_by_xpath(
        "//*[@id='contentsBody']/ul[2]/li")
    for i, race_button in enumerate(race_buttons):
        if(race_button.get_attribute("class") == 'current'):
            current_race_num = i
            break
    race_buttons[current_race_num + 1].click()


def has_next_course(driver):
    global current_race_num
    course_buttons = driver.find_elements_by_xpath(
        "//*[@id='contentsBody']/ul[1]/li")
    for i, course_button in enumerate(course_buttons):
        if(course_button.get_attribute("class") == 'current'):
            current_race_num = i
            break
    return len(course_buttons) != current_race_num + 1


def click_next_course(driver):
    global current_course_num
    course_buttons = driver.find_elements_by_xpath(
        "//*[@id='contentsBody']/ul[1]/li")
    for i, course_button in enumerate(course_buttons):
        if(course_button.get_attribute("class") == 'current'):
            current_course_num = i
            break
    course_buttons[current_course_num + 1].click()
    race1_button = driver.find_element_by_xpath("//*[@id='contentsBody']/ul[2]/li[1]")
    race1_button.click()


def get_all_race_info(driver):
    while True:
        race = initialize_race(driver)
        race.horses = get_horse_info(driver)
        print(vars(race))
        for horse in race.horses:
            print(vars(horse))
        if(has_next_race(driver)):
            click_next_race(driver)
        else:
            break


def initialize_race(driver):
    global current_race_num, current_course_num
    course_buttons = driver.find_elements_by_xpath(
        "//*[@id='contentsBody']/ul[1]/li")
    for index, course_button in enumerate(course_buttons):
        if course_button.get_attribute("class") == 'current':
            current_course_num = index
            break
    held = course_buttons[current_course_num].text
    race_buttons = driver.find_elements_by_xpath(
        "//*[@id='contentsBody']/ul[2]/li")
    for index, race_button in enumerate(race_buttons):
        if race_button.get_attribute("class") == 'current':
            current_race_num = index
            break
    race_num = current_race_num + 1
    temp_start_time = driver.find_element_by_xpath(
        "//*[@id='syutsuba']/table/caption").find_element_by_css_selector('.cell.time').text
    start_time = temp_start_time.replace("発走時刻：", "").replace("時", ":").replace("分", "")
    now = datetime.datetime.now().strftime("%H:%M")
    return Race(held, race_num, now, start_time)


if __name__ == '__main__':
    DRIVER_PATH = './chromedriver'
    url = "https://www.jra.go.jp/"

    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=options)
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(10)
    driver.get(url)

    today = datetime.datetime.now().strftime("%-m月%-d日")

    # 「出馬票」をクリック
    driver.find_element_by_xpath("//*[@id='quick_menu']/div/ul/li[2]").click()

    # 開催日程を取得
    elements = driver.find_elements_by_xpath("//*[@id='main']/div")
    elements.pop(0)
    # event_open_dates = list(map(lambda element: re.findall(
    #     r'\d+月\d+日', element.find_element_by_xpath("*[@class='sub_header']").text)[0], elements))

    event_open_dates = ['11月14日']

    for i, event_open_date in enumerate(event_open_dates):
        if event_open_date == today:
            # 会場、開催日をクリック
            cofirst_course = elements[i].find_element_by_xpath(
                "div[@class='content']/ul/li[@class='waku']")
            cofirst_course.click()
            time.sleep(1)
            # レースをクリック
            race_element = driver.find_element_by_xpath(
                "//*[@id='race_list']/tbody").find_element_by_class_name('race_num')
            race_element.click()
            race = initialize_race(driver)
            get_all_race_info(driver)

            while has_next_course(driver):
                click_next_course(driver)
                race = initialize_race(driver)
                get_all_race_info(driver)
    driver.close()
    driver.quit()
