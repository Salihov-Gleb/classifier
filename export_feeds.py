import datetime
import pandas as pd
import sqlite3 as sq
import os


DB_NAME = 'data_feeds'
FILE_NAME = 'b2x_news_export'
SHEET_NAME = 'b2x_news'


if __name__ == '__main__':
    try:
        start_date = datetime.datetime.strptime(os.getenv('DATE_START').split(',')[0], '%d.%m.%Y %H:%M:%S')
    except Exception as e:
        print(e.args)
        start_date = None
    curfolder = os.path.abspath(os.getcwd())
    with sq.connect(f'{curfolder}\dbs\{DB_NAME}.db') as econn:
        df = pd.read_sql_query(
            """SELECT s.sname, e.*
                FROM feed_entries AS e 
                 LEFT JOIN feed_sources AS s ON e.fsid = s.fsid""",
            econn, coerce_float=False)
    df['feid'] = df['feid'].astype('int32')
    df.drop_duplicates()
    df['rdate'] = pd.to_datetime(df['rdate'], errors='coerce', utc=True).dt.tz_localize(None)
    df = df[pd.notnull(df['rdate'])]
    df = df[df['rdate'] != 'NaT']
    if start_date is None:
        date_limit = datetime.datetime.now() - datetime.timedelta(days=8)
    else:
        date_limit = start_date
    df = df[df['rdate'] > date_limit]
    df.to_excel(
        f"{curfolder}\export\{FILE_NAME}_{datetime.datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
        sheet_name=SHEET_NAME, index=False
    )