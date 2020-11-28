import matplotlib.pyplot as plt
import pandas as pd
import datetime
import numpy as np
from store.repository import Repository

plt.rcParams['font.family'] = 'IPAexGothic'
plt.rcParams['figure.facecolor'] = 'whitesmoke'
plt.rcParams['axes.facecolor'] = 'whitesmoke'
hat_color_master = {1: 'white', 2: 'black', 3: 'red', 4: 'blue', 5: 'yellow', 6: 'green', 7: 'orange', 8: 'hotpink'}
waku_count_map = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
# x_labels = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30',
#             '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00']


def timedelta_to_HM(td):
    sec = td.total_seconds()
    return '{hh}:{mm}'.format(hh=f'{int(sec // 3600):02}', mm=f'{int(sec % 3600 // 60):02}')


def create_graph_image(held, race_number, only_last_one_hour=False):
    repository = Repository()
    query = """
    select * 
    from timely_odds
    where held = '{held}' and race_number = {race_number}
    order by acquisition_time"""
    df = pd.read_sql_query(sql=query.format(held=held, race_number=race_number), con=repository.engine)

    if only_last_one_hour:
        delta = df["acquisition_time"].dt.total_seconds()
        last_one_hour = df.iloc[0]['start_time'] + datetime.timedelta(minutes=-65)
        sec = last_one_hour.total_seconds()
        df = df[(delta == 0) | (delta > sec)]
    if len(df) == 0:
        return
    df['acquisition_time'] = df['acquisition_time'].apply(timedelta_to_HM)
    df = df.set_index('acquisition_time')

    horse_count = len(df['horse_number'].unique())
    arranged_df = pd.Series(dtype='float64')
    for i in range(horse_count):
        tmp_df = df.query(f"horse_number == {i + 1}")
        new_column_name = str(i + 1) + '_' + tmp_df['horse_name'].head()[1]
        tmp_df = tmp_df.rename(columns={'odds': new_column_name})
        series = tmp_df[new_column_name]
        arranged_df = pd.concat([arranged_df, series], axis=1)
    arranged_df = arranged_df.drop(0, axis=1)

    for i in range(len(arranged_df.columns)):
        umaban = i + 1
        if umaban <= 8:
            waku_count_map[umaban] += 1
        else:
            waku_count_map[8 - (umaban - 1) % 8] += 1
    hat_color_list = []
    for i in range(len(waku_count_map)):
        for j in range(waku_count_map[i + 1]):
            hat_color_list.append(hat_color_master[i + 1])
    linestype_list = []
    for i in range(len(arranged_df.columns)):
        number_per_waku = hat_color_list[:i + 1].count(hat_color_list[i])
        if number_per_waku == 1:
            linestype_list.append('-')
        elif number_per_waku == 2:
            linestype_list.append('--')
        elif number_per_waku == 3:
            linestype_list.append(':')

    fig, ax = plt.subplots()
    for idx, label in enumerate(ax.get_xticklabels()):
        if idx % 15 == 0:
            label.set_visible(False)
    for i in range(len(arranged_df.columns)):
        ax.plot(arranged_df.index, arranged_df.iloc[:, i],
                color=hat_color_list[i], linestyle=linestype_list[i], label=arranged_df.columns[i])

    x_labels = []
    if only_last_one_hour:
        base_time = last_one_hour
    else:
        base_time = datetime.timedelta(hours=8)
    while True:
        x_labels.append(timedelta_to_HM(base_time))
        base_time += datetime.timedelta(minutes=30)
        if base_time > df.iloc[0]['start_time']:
            break

    ax.set_xticks(x_labels)
    plt.legend(fontsize=7, loc='upper left')
    plt.xlabel("日時")
    plt.ylabel("オッズ")
    plt.grid(True)
    postfix = ''
    if only_last_one_hour:
        postfix = '_last1H'
    title = held + "_R" + str(race_number) + postfix
    plt.title(title)
    graph_img_name = title + '.png'
    plt.savefig('./images/' + graph_img_name, dpi=200)
    # plt.show()
    return graph_img_name


if __name__ == '__main__':
    create_graph_image('5回阪神6日', 5, only_last_one_hour=False)
