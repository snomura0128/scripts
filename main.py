import dbm
import threading
from oddsScraping import OddsScraping, today_yyyymmdd


def main():
    held_count: int
    with dbm.open('cache', 'c') as db:
        if today_yyyymmdd.encode() in db.keys():
            held_count = int(db[today_yyyymmdd].decode())
        else:
            oddsScrapingTmp = OddsScraping()
            held_count = oddsScrapingTmp.count_held()
            db[today_yyyymmdd] = str(held_count)
            del oddsScrapingTmp

    oddsScrapings = []
    thread_list = []
    for i in range(held_count):
        oddsScrapings.append(OddsScraping())
        thread_list.append(threading.Thread(target=oddsScrapings[i].get_one_held_race, args=(i + 1,)))
        thread_list[i].start()


if __name__ == '__main__':
    main()
