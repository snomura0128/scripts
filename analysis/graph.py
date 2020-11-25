import matplotlib.pyplot as plt
import pandas as pd
from store.repository import Repository

plt.rcParams['font.family'] = 'IPAexGothic'


def timedelta_to_HM(td):
    sec = td.total_seconds()
    return '{hh}:{mm}'.format(hh=f'{int(sec // 3600):02}', mm=f'{int(sec % 3600 // 60):02}')


def create_graph_image(held, race_number):
    repository = Repository()
    query = """
    select * 
    from timely_odds
    where held = '{held}' and race_number = {race_number}"""
    df = pd.read_sql_query(sql=query.format(held=held, race_number=race_number), con=repository.engine)
    if len(df) == 0:
        return
    df['acquisition_time'] = df['acquisition_time'].apply(timedelta_to_HM)
    df = df.set_index('acquisition_time')
    horse_count = len(df.query('acquisition_time == "00:05"'))

    arranged_df = pd.Series(dtype='float64')
    for i in range(horse_count):
        tmp_df = df.query(f"horse_number == {i + 1}")
        if tmp_df['odds'].median() > 100:
            continue
        new_column_name = str(tmp_df.at['00:05', 'horse_number']) + '_' + tmp_df.at['00:05', 'horse_name']
        tmp_df = tmp_df.rename(columns={'odds': new_column_name})
        series = tmp_df[new_column_name]
        arranged_df = pd.concat([arranged_df, series], axis=1)
    arranged_df = arranged_df.drop(0, axis=1)
    arranged_df.plot()
    plt.legend(fontsize=7)
    plt.grid(linestyle='--')
    plt.xlabel("日時")
    plt.ylabel("オッズ")
    title = held + "_R" + str(race_number)
    plt.title(title)
    graph_img_name = title + '.png'
    plt.savefig('./images/' + graph_img_name, dpi=200)
    return graph_img_name
