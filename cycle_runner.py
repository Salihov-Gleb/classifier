import datetime
import sqlite3 as sq
import custom_parser_funcs as cpf
from inspect import getmembers, isfunction
import pandas as pd
import os
import requests
import io
import re
import feedparser # https://feedparser.readthedocs.io/en/latest/common-rss-elements.html


curfolder = os.path.abspath(os.getcwd())
LOG_FOLDER = f"./log/log_{datetime.datetime.now().strftime('%d%m%Y')}"
# DB_NAME = st.secrets['DB']['db_name']


# @st.cache
def get_parse(url_):
    try:
        resp = requests.get(url_, timeout=20.0)
        content = io.BytesIO(resp.content)
        resp.close()
    except: # requests.ReadTimeout:
        # logger.warn("Timeout when reading RSS %s", url_)
        content = ''

    # lr = feedparser.parse(url_)
    # Put it to memory stream object universal feedparser
    # Parse content
    lr = feedparser.parse(content)
    return lr


def cleanhtml(raw_html):
    '''Чистит теги и другой мусор'''
    # CLEANR = re.compile('<.*?>')
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleans = re.compile(r'/^\s+|\s+$|\s+(?=\s)/g')
    return re.sub(cleans, ' ', re.sub(cleanr, '', raw_html))

# functions_list = [f[0] for f in getmembers(cpf) if isfunction(f[1]) and f[0].startswith('func_')]


def main(src_dict_, DB_NAME_):
    '''Основной процесс для цикла обновления по всем источникам'''
    # 'Настройки обновления'
    upd_chb1 = True # 'Выгрузка с подробной страницы','Обход индивидуальных страниц по каждой новости'
    upd_chb2 = True # 'Обход страниц', 'Выгрузка из всех страниц ресурса при наличии пагинации'
    upd_pgs = 2 #'Количество страниц', 'Если 0, то все страницы'
    upd_chb3 = False #'Полное обновление', 'Обновление содержания по существующим записям'

    if src_dict_['rss_sw'] == 1: # Данные из rss источника

        # dp = get_parse(source_list[nsrc])
        print(f"{src_dict_['sname'].rjust(25)} - подключение... ")
        dp = get_parse(src_dict_['slink'])
        
        feed_title = ''
        try:
            feed_title = dp.feed.title
        except:
            pass
        print(f"{src_dict_['sname'].rjust(25)} - Всего записей {len(dp.entries)} : {feed_title}")

        if len(dp.entries) == 0:
            with open(os.path.join(LOG_FOLDER, 'empty_feeds_log.csv'), 'a') as f:
                f.write(f"{src_dict_['fsid']};{src_dict_['sname']};{src_dict_['slink']};{src_dict_['sfunc']};1\n")

        # st.write(dp.feed.title, '\n', dp.feed.link, '\n', dp.feed.description)#, '\n', dp.feed.published)
        # try:
        #     st.image(dp.feed.image.href)
        # except:
        #     pass

        df = pd.DataFrame([])

        for i, e in enumerate(dp.entries):
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = src_dict_['fsid'] #sdf.fsid[nsrc]
            one_feed['u_etitle'] = e.title if 'title' in e else f'title {i}'
            one_feed['u_summary'] = cleanhtml(e.summary) if 'summary' in e else f'no summary {i}'
            one_feed['elink'] = e.link if 'link' in e else f'link {i}'

            # загрузка подробного содержания
            if src_dict_['sfunc'] != '' and upd_chb1 and one_feed['elink'] != f'link {i}':
                try:
                    deep_sum = ''
                    parse_func = getattr(cpf, src_dict_['sfunc'])
                    oksw, deep_sum = parse_func(one_feed['elink'])
                    if oksw == 200 and deep_sum != '':
                        one_feed['u_summary'] = cleanhtml(deep_sum)
                    else:
                        print(f"Неудачная попытка получения подробного текста новости. Источник {src_dict_['sname'].rjust(25)} . Парсер {src_dict_['sfunc'].rjust(15)} . Ссылка {one_feed['elink']}")
                except Exception as err:
                    print(f"Неудачная попытка получения подробного текста новости. Ошибка {err} . Источник {src_dict_['sname'].rjust(25)} . Парсер {src_dict_['sfunc'].rjust(15)} . Ссылка {one_feed['elink']}")
            
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['published'] = e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = e.links[1].href if 'links' in e and len(e.links)>1 else f'no link_img {i}'
            one_feed['score'] = -1
            one_feed['group_topic'] = ''
            one_feed['topic'] = ''
            one_feed['group_theme'] = ''
            one_feed['theme'] = ''
            one_feed['project'] = ''
            one_feed['uname'] = 'AUTOUPDATE' #session_state2.u_name

            df = pd.concat([df, pd.DataFrame([one_feed])], ignore_index=True)

    else: # Данные из НЕ rss источника
        df = pd.DataFrame([])
        if src_dict_['sfunc'] != '': # Если назначен парсер

            parse_func = getattr(cpf, src_dict_['sfunc'])

            if parse_func != '': # если парсер найден

                print(f"{src_dict_['sname'].rjust(25)} - подключение... ")
                req_status, df = parse_func(1 if upd_chb1 else 0, upd_pgs if upd_chb2 else 1)
                if req_status != 200:
                    # st.info(f'Page request status = {req_status} ')
                    print(f"Неудачная попытка запуска парсера для неRSS источника. request status =  {req_status} . Источник {src_dict_['sname'].rjust(25)} . Парсер {src_dict_['sfunc'].rjust(15)} .")
                else:
                    print(f"{src_dict_['sname'].rjust(25)} - Всего записей {df.shape[0]} ")
                    if df.shape[0] == 0:
                        with open(os.path.join(LOG_FOLDER, 'empty_feeds_log.csv'), 'a') as f:
                            f.write(f"{src_dict_['fsid']};{src_dict_['sname']};{src_dict_['slink']};{src_dict_['sfunc']};0\n")
                    df['fsid'] = src_dict_['fsid']
                    df['score'] = -1
                    df['group_topic'] = ''
                    df['topic'] = ''
                    df['group_theme'] = ''
                    df['theme'] = ''
                    df['project'] = ''
                    df['uname'] = 'AUTOUPDATE' #session_state2.u_name

    # st.write(df)

    if df.shape[0] > 0:
        econn = sq.connect(f'{curfolder}\dbs\{DB_NAME_}.db')
        with econn:
            ecur = econn.cursor()

            ecur.execute("""DROP TABLE IF EXISTS feed_entries_temp;""")
            econn.commit()
            df.to_sql('feed_entries_temp', econn, if_exists='replace', index=False) #, dtype={"fsid": int()})
            econn.commit()

            if upd_chb3: # включён флаг обновления существующих новостей
                edf_ = pd.read_sql_query("""SELECT * 
                            FROM feed_entries_temp 
                            WHERE (fsid, elink) in 
                                (SELECT fsid, elink 
                                FROM feed_entries)""", econn, coerce_float=False)

                edf_.drop_duplicates(['fsid', 'elink'], inplace=True, ignore_index=True)

                newrows = [tuple(r) for i,r in edf_[['u_etitle','u_summary','etitle','summary','elink','published','elink_img','fsid','elink']].iterrows()]

                sql = f''' UPDATE feed_entries 
                        SET u_etitle = ? ,
                            u_summary = ? ,
                            etitle = ? ,
                            summary = ? ,
                            elink = ? ,
                            published = ? ,
                            elink_img = ? ,
                            uname = 'AUTOUPDATE' ,
                            rdate = datetime('now', 'localtime') 
                        WHERE fsid = ? and elink = ?; '''
                try:
                    ecur.executemany(sql, list(newrows))
                except Exception as e:
                    print(e)
                print(f'{ecur.rowcount} строк обновлено.')
                econn.commit()

            edf_ = pd.read_sql_query("""SELECT * 
                                        FROM feed_entries_temp 
                                        WHERE (fsid, elink) in 
                                            (SELECT fsid, elink 
                                            FROM feed_entries_temp 
                                            EXCEPT 
                                            SELECT fsid, elink 
                                            FROM feed_entries)""", econn, coerce_float=False)

            edf_.drop_duplicates(['fsid', 'elink'], inplace=True, ignore_index=True)
            
            # entrs = [tuple(r) for i,r in edf_[list(edf_.columns[1:])].iterrows()]
            entrs = [tuple(r) for i, r in edf_[['fsid', 'u_etitle', 'u_summary', 'etitle', 'summary', 'elink',
                                                'published', 'elink_img', 'score', 'group_topic', 'topic',
                                                'group_theme', 'theme', 'project', 'uname']].iterrows()]

            ecur.executemany("INSERT INTO feed_entries VALUES(null, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now', 'localtime'));", list(entrs))
            print(f'{ecur.rowcount} строк добавлено.')
            econn.commit()
        try:
            econn.close()
        except:
            pass


if __name__ == '__main__':
    DB_NAME = 'data_feeds'
    print(f"ОБНОВЛЕНИЕ БАЗЫ НОВОСТЕЙ - {DB_NAME}")

    curfolder = os.path.dirname(os.path.abspath(__file__))
    print(curfolder)

    sconn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
    with sconn:
        sdf_ = pd.read_sql_query("SELECT * FROM feed_sources ", sconn) # Читаем справочник источников  #where fsid in (1,2) 

    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
    with open(os.path.join(LOG_FOLDER, 'parser_error_log.csv'), 'w') as f:
        f.write(f'fsid;sname;slink;sfunc;error\n')
    with open(os.path.join(LOG_FOLDER, 'empty_feeds_log.csv'), 'w') as f:
        f.write('fsid;sname;slink;sfunc;rss\n')
    for s in sdf_.iterrows(): # Запуск выгрузки по каждому источнику
        try:
            # if dict(s[1])['sname'] != 'Dzen':
            #     continue
            main(dict(s[1]), DB_NAME)
        except Exception as e:
            print(f"Ошибка при попытке парсинга: \n{dict(s[1])}\n")
            print(e.args)
            with open(os.path.join(LOG_FOLDER, 'parser_error_log.csv'), 'a') as f:
                if len(e.args) > 0:
                    error = e.args[0]
                else:
                    error = ''
                f.write(f"{dict(s[1])['fsid']};{dict(s[1])['sname']};{dict(s[1])['slink']};{dict(s[1])['sfunc']};{error}\n")
