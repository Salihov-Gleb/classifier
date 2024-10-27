import re
import sqlite3 as sq
import os
import pandas as pd


DB_NAME = 'data_feeds'


def load_theme_dict():
    theme_dict = {}
    with open('./conf/theme.csv', 'r', newline='', encoding='utf-8') as f:
        row = f.readline().split(';')
        kw_count = len(list(filter(lambda x: x.lower().find('key') > -1, row)))
        sw_count = len(list(filter(lambda x: x.lower().find('stop') > -1, row)))
        rx_count = len(list(filter(lambda x: x.lower().find('reg') > -1, row)))
        row = f.readline().lower().rstrip('\n\r').split(';')
        while len(row) > 2:
            index = 3
            rule = 1 if row[2] == '1' else 0
            kw = list(filter(lambda x: len(x) > 0, row[index:index + kw_count]))
            index += kw_count
            sw = list(filter(lambda x: len(x) > 0, row[index:index + sw_count]))
            index += sw_count
            rx = list(filter(lambda x: len(x) > 0, row[index:index + rx_count]))
            theme_dict.update({row[1]: {"kw": kw, "sw": sw, "rx": rx, "rule": rule}})
            row = f.readline().lower().rstrip('\n\r').split(';')
    return theme_dict


def is_class(text, words):
    for sw in words['sw']:
        if text.find(sw) != -1:
            return False
    if words['rule'] == 1:
        for kw in words['kw']:
            if text.find(kw) == -1:
                return False
        for rx in words['rx']:
            if re.search(rx, text) is None:
                return False
        return True
    else:
        for kw in words['kw']:
            if text.find(kw) != -1:
                return True
        for rx in words['rx']:
            if re.search(rx, text):
                return True
    return False


def row_classification(text, theme_dict):
    ts = set()
    for theme, words in theme_dict.items():
        if is_class(text, words):
            ts.add(theme)
    return ', '.join(list(ts))


def classify(db_name, theme_dict):
    curfolder = os.path.abspath(os.getcwd())
    with sq.connect(f'{curfolder}\dbs\{db_name}.db') as econn:
        df = pd.read_sql_query("""SELECT * FROM feed_entries""", econn, coerce_float=False)
        df['theme'] = df['u_etitle'].apply(lambda row: row_classification(str(row).lower(), theme_dict))
        df['feid'] = df['feid'].astype('int32')
        df.drop_duplicates()
        econn.execute("""DELETE FROM feed_entries""")
        df.to_sql('feed_entries', econn, if_exists='append', index=False)
        econn.commit()
    try:
        econn.close()
    except:
        pass


if __name__ == '__main__':
    theme_dict = load_theme_dict()
    classify(DB_NAME, theme_dict)

