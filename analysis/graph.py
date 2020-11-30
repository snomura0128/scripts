import matplotlib.pyplot as plt
import pandas as pd
import datetime
from store.repository import Repository

plt.rcParams['font.family'] = 'IPAexGothic'
plt.rcParams['figure.facecolor'] = 'silver'
plt.rcParams['axes.facecolor'] = 'silver'
hat_color_master = {1: 'white', 2: 'black', 3: 'red', 4: 'blue', 5: 'yellow', 6: 'green', 7: 'orange', 8: 'hotpink'}


def __timedelta_to_HM(td):
    sec = td.total_seconds()
    return '{hh}:{mm}'.format(hh=f'{int(sec // 3600):02}', mm=f'{int(sec % 3600 // 60):02}')


def __graph_decorations(df, less_popular=False):
    waku_count_map = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
    hat_color_list, linestyle_list, delete_column_list = [], [], []
    for i in range(len(df.columns)):
        # 馬番ごとの枠の色をセットする。
        umaban = i + 1
        if umaban <= 8:
            waku_count_map[umaban] += 1
        else:
            waku_count_map[8 - (umaban - 1) % 8] += 1
    for i in range(len(waku_count_map)):
        for j in range(waku_count_map[i + 1]):
            hat_color_list.append(hat_color_master[i + 1])
    for i in range(len(df.columns)):
        number_per_waku = hat_color_list[:i + 1].count(hat_color_list[i])
        if number_per_waku == 1:
            linestyle_list.append('-')
        elif number_per_waku == 2:
            linestyle_list.append('--')
        elif number_per_waku == 3:
            linestyle_list.append(':')

        # 最終オッズが200倍以上の馬はグラフに表示させない
        if df.iloc[-1, i] > 200:
            delete_column_list.append(i)
            continue

        if less_popular:
            if df.iloc[:, i].describe()['50%'] > 30:
                delete_column_list.append(i)
        else:
            if df.iloc[:, i].describe()['50%'] <= 30:
                delete_column_list.append(i)
    delete_column_list.sort(reverse=True)
    df = df.drop(df.columns[delete_column_list], axis=1)
    for i in delete_column_list:
        hat_color_list.pop(i)
        linestyle_list.pop(i)
    return df, hat_color_list, linestyle_list


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
    df['acquisition_time'] = df['acquisition_time'].apply(__timedelta_to_HM)
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

    fig, ax = plt.subplots(2, 1, figsize=(9, 12))
    for i, less_popular in enumerate([False, True]):
        new_df, hat_color_list, linestyle_list = __graph_decorations(arranged_df, less_popular=less_popular)

        for j in range(len(new_df.columns)):
            ax[i].plot(new_df.index, new_df.iloc[:, j], linewidth=1.0,
                       color=hat_color_list[j], linestyle=linestyle_list[j], label=new_df.columns[j])
        x_labels = []
        if not only_last_one_hour:
            base_time = datetime.timedelta(hours=8)
            while True:
                x_labels.append(__timedelta_to_HM(base_time))
                base_time += datetime.timedelta(minutes=30)
                if base_time > df.iloc[0]['start_time']:
                    break
        ax[i].legend(fontsize=9, loc='upper left', facecolor='silver')
        ax[i].set_xticks(x_labels)
        ax[i].tick_params(axis='x', labelrotation=90)
        ax[i].grid(True)
    postfix = ''
    if only_last_one_hour:
        postfix = '_last1H'
    title = held + "_R" + str(race_number) + postfix
    fig.suptitle(title)
    graph_img_name = title + '.png'
    # fig.savefig('../images/' + graph_img_name, dpi=300)
    fig.show()
    return graph_img_name


if __name__ == '__main__':
    held = '5回東京9日'
    race_number = 5
    create_graph_image(held, race_number, only_last_one_hour=False)
    # create_graph_image(held, race_number, only_last_one_hour=True)

    # for i in range(12):
    #     race_num = i + 1
    #     create_graph_image(held, race_num, only_last_one_hour=False)
    # create_graph_image(held, race_num, only_last_one_hour=True)
