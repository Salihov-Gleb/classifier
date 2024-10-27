# from numpy.core.numeric import Inf
import streamlit as st
import pandas as pd
# https://pypi.org/project/streamlit-aggrid/
from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder  # , JsCode
import sqlite3 as sq
import SessionState
import requests
import io
import os
import datetime
import re

# d = feedparser.parse('http://feedparser.org/docs/examples/atom10.xml')

# st.set_page_config(layout='wide')
curfolder = os.path.abspath(os.getcwd())
DB_NAME = st.secrets['DB']['db_name']
CUST_NAMESRC = st.secrets['DB']['cust_namesrc']


# @st.cache
def get_srs(src_cache_id):
    sconn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
    # _ = src_cache_id
    sdf_ = pd.read_sql_query("SELECT * FROM feed_sources", sconn)
    sconn.close()
    return sdf_


@st.cache(ttl=60)
def get_feeds():
    sconn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')

    sdf_ = pd.read_sql_query("SELECT s.sname, e.* FROM feed_entries e, feed_sources s WHERE e.fsid=s.fsid", sconn,
                             coerce_float=False)
    sconn.close()
    return sdf_


def intro():
    st.sidebar.success("Select a module above.")


#     st.markdown(
#         """
# Сервер feeds.
# Комплекс feeds.
#     """
#     )

def cleanhtml(raw_html):
    '''Чистит теги и другой мусор'''
    # CLEANR = re.compile('<.*?>')
    CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    return re.sub(CLEANR, '', raw_html)


def set_feeds():
    session_state2 = SessionState.get(token_body='', u_name='Без авторизации', src_cache_id=1)

    import custom_parser_funcs as cpf
    # import custom_parser_funcs
    from inspect import getmembers, isfunction

    def adsw():
        return 1 if st.secrets['DEBUG']['admin'] == session_state2.u_name else 0

    def athsw():
        '''Проверка авторизации'''
        return 1 if session_state2.u_name != 'Без авторизации' else 0

    import feedparser  # https://feedparser.readthedocs.io/en/latest/common-rss-elements.html
    # @st.cache


    def get_parse(url_):
        try:
            resp = requests.get(url_, timeout=20.0, verify=False)
            content = io.BytesIO(resp.content)
            code = resp.status_code
            resp.close()
        except Exception as e:  # requests.ReadTimeout:
            # logger.warn("Timeout when reading RSS %s", url_)
            content = ''
            code = e.args

        # lr = feedparser.parse(url_)
        # Put it to memory stream object universal feedparser
        # Parse content
        lr = feedparser.parse(content)
        return lr, code

    # st.write(curfolder)
    functions_list = [f[0] for f in getmembers(cpf) if isfunction(f[1]) and f[0].startswith('func_')]

    def gb_sets_src(gb_):
        # customize gridOptions
        gb_.configure_side_bar()

        gb_.configure_selection('single')

        gb_.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb_.configure_grid_options(domLayout='normal')

    sdf = get_srs(session_state2.src_cache_id)

    import plotly.express as px
    st.sidebar.info(f'{sdf.shape[0]} источников')

    fig = px.pie(sdf, names='rss_sw', title='Структура по признаку RSS', width=300, height=300)
    fig.update_traces(textposition='inside', textinfo='value+percent')
    st.sidebar.write(fig)

    gb = GridOptionsBuilder.from_dataframe(sdf)

    gb_sets_src(gb)

    go = gb.build()

    ag = AgGrid(
        sdf,
        gridOptions=go,
        height=350,
        width='100%',
        data_return_mode=DataReturnMode.FILTERED,  # return_mode_value,
        update_mode=GridUpdateMode.SELECTION_CHANGED,  # update_mode_value,
        fit_columns_on_grid_load=True,  # fit_columns_on_grid_load,
        allow_unsafe_jscode=True,  # Set it to True to allow jsfunction to be injected
        enable_enterprise_modules=True,  # enable_enterprise_modules,
        # reload_data=False,
    )

    # df = ag['data']
    selected = ag['selected_rows']
    if len(selected) == 0:
        st.success('Выбор источника..')
        st.stop()

    if athsw() == 0:
        st.info('Управление базой возможно после авторизации')
        st.stop()
    # st.subheader("Selected rows")
    # st.dataframe(ag['selected_rows'])
    singl_src = ag['selected_rows'][0]  # pd.DataFrame(ag['selected_rows'])

    # source_list = list(sdf.slink.values)

    with st.expander('Добавить\обновить источник'):
        st.markdown(' > В тексте не должно быть кавычек')
        col1, col2 = st.columns([2, 2])
        with col1:
            st.subheader('Новый')
            with st.form('src_new', clear_on_submit=True):
                sName = st.text_input('sName')
                sLink = st.text_input('sLink')
                sRSSsw = st.text_input('sRSSsw')
                save_btn = st.form_submit_button('Save', 'Записать в БД')
                st.markdown('> - Для загрузки списков обратитесь к администратору')
                if save_btn:
                    if sName == '' or sLink == '':
                        st.info('Не все поля заполнены')
                    else:
                        if sRSSsw != '1':
                            sRSSsw = 0
                        econn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
                        with econn:
                            try:
                                ecur = econn.cursor()
                                ecur.execute(
                                    f"INSERT INTO feed_sources VALUES(null, '{sName}','{sLink}','{sRSSsw}','','','','',datetime('now', 'localtime'));")
                                st.success('')
                            except Exception as e:
                                st.warning(e)
                            st.success(f'Источник {sName} добавлен.')
                            econn.commit()
                    session_state2.src_cache_id += 1
                # st.write(session_state2.src_cache_id)
        with col2:
            st.subheader('Текущий')
            with st.form('src_update', clear_on_submit=True):
                # st.markdown(' > В тексте не должно быть кавычек')
                sName_u = st.text_input('sName', singl_src['sname'])
                sLink_u = st.text_input('sLink', singl_src['slink'])
                sRSSsw_u = st.text_input('sRSSsw', singl_src['rss_sw'])
                sStitle_u = st.text_input('sStitle', singl_src['stitle'])
                sFunc_u = st.text_input('sFunc', singl_src['sfunc'])
                save_btn2 = st.form_submit_button('Update', 'Записать в БД')
                if save_btn2:
                    if sName_u == '' or sLink_u == '':
                        st.info('Не все поля заполнены')
                    else:
                        if sRSSsw_u != '1':
                            sRSSsw_u = 0
                        econn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
                        with econn:
                            try:
                                ecur = econn.cursor()
                                sql_upd = f''' UPDATE feed_sources
                                        SET sname = '{sName_u}' ,
                                            slink = '{sLink_u}' ,
                                            rss_sw = '{sRSSsw_u}' ,
                                            stitle = '{sStitle_u}' ,
                                            sfunc = '{sFunc_u}' ,
                                            rdate = datetime('now', 'localtime') 
                                        WHERE fsid = {singl_src['fsid']} '''
                                ecur.execute(sql_upd)
                            except Exception as e:
                                st.warning(e)
                            st.success(f'Источник {sName_u} обновлён.')
                            econn.commit()
                    session_state2.src_cache_id += 1

    with st.expander('Список парсеров'):
        st.write(functions_list)  # list(custom_parser_funcs.__dict__.keys()))

    # DEBUG FUNC !
    # gla = globals()
    if adsw() == 1:
        if st.button('Delete ALL feeds', help=f'Создаётся новая БД если не существует с именем {DB_NAME}.db'):
            econn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
            ecur = econn.cursor()
            try:
                ecur.execute("""DROP TABLE feed_entries;""")  # ("""DELETE from feed_entries;""")
                ecur.execute("""DROP TABLE feed_entries_temp;""")
            except:
                pass
            ecur.execute("""CREATE TABLE IF NOT EXISTS feed_entries(
                                feid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                                fsid INT,
                                u_etitle TEXT,
                                u_summary TEXT,
                                etitle TEXT,
                                summary TEXT,
                                elink TEXT,
                                published TEXT,
                                elink_img TEXT,
                                score INT DEFAULT -1,
                                group_topic TEXT,
                                topic TEXT,
                                group_theme TEXT,
                                theme TEXT,
                                project TEXT,
                                uname TEXT,
                                rdate TEXT);
                                """)
            econn.commit()
            ecur.execute("""CREATE TABLE IF NOT EXISTS feed_sources(
                                fsid INTEGER PRIMARY KEY AUTOINCREMENT,
                                sname TEXT,
                                slink TEXT,
                                rss_sw INT DEFAULT 0,
                                sfunc TEXT,
                                rdate TEXT);
                                """)
            # stitle TEXT,
            # description TEXT,
            # slink_img TEXT,
            econn.commit()
            econn.close()
    # DEBUG FUNC !

    # st.write(singl_src)
    st.markdown('---')
    col1, col2 = st.columns([1, 2])
    with col1:
        up_btn = st.button(f"Загрузить из источника > {singl_src['sname']} <")
    with col2:
        with st.expander('Настройки обновления'):
            upd_chb1 = st.checkbox('Выгрузка с подробной страницы', True,
                                   help='Обход индивидуальных страниц по каждой новости')
            upd_chb2 = st.checkbox('Обход страниц', False,
                                   help='Выгрузка из всех страниц ресурса при наличии пагинации')
            if upd_chb2:
                upd_pgs = st.number_input('Количество страниц', help='Если 0, то все страницы', step=1, min_value=0)
            upd_chb3 = st.checkbox('Полное обновление', False, help='Обновление содержания по существующим записям')
    if up_btn:
        if singl_src['rss_sw'] == 1:
            # dp = get_parse(source_list[nsrc])
            dp, code = get_parse(singl_src['slink'])
            if code != 200:
                st.error(f'Ошибка при запросе: {code}')
                st.stop()
            st.write('Всего записей', len(dp.entries))

            # st.write(dp.feed.title, '\n', dp.feed.link, '\n', dp.feed.description)#, '\n', dp.feed.published)
            st.write(
                f"{getattr(dp.feed, 'title', '')} {getattr(dp.feed, 'link', '')} {getattr(dp.feed, 'description', '')}")

            try:
                st.image(dp.feed.image.href)
            except:
                pass

            df = pd.DataFrame([])

            for i, e in enumerate(dp.entries):
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = singl_src['fsid']  # sdf.fsid[nsrc]
                one_feed['u_etitle'] = e.title if 'title' in e else f'title {i}'
                one_feed['u_summary'] = cleanhtml(e.summary) if 'summary' in e else f'no summary {i}'
                one_feed['elink'] = e.link if 'link' in e else f'link {i}'

                # загрузка подробного содержания
                if singl_src['sfunc'] != '' and upd_chb1 and one_feed['elink'] != f'link {i}':
                    try:
                        deep_sum = ''
                        parse_func = getattr(cpf, singl_src['sfunc'])
                        oksw, deep_sum = parse_func(one_feed['elink'])
                        if oksw == 200 and deep_sum != '':
                            one_feed['u_summary'] = cleanhtml(deep_sum)
                    except:
                        pass

                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = cleanhtml(one_feed['u_summary'])
                one_feed['published'] = e.published if 'published' in e else f'no published {i}'
                one_feed['elink_img'] = e.links[1].href if 'links' in e and len(e.links) > 1 else f'no link_img {i}'
                one_feed['score'] = -1
                one_feed['group_topic'] = ''
                one_feed['topic'] = ''
                one_feed['group_theme'] = ''
                one_feed['theme'] = ''
                one_feed['project'] = ''
                one_feed['uname'] = session_state2.u_name

                df = df.append(pd.DataFrame([one_feed]), ignore_index=True)

            with st.expander('Структура одного сообщения'):
                if len(dp.entries) > 0:
                    st.write(dp.entries[0])
                else:
                    st.write('Записи не найдены')
        else:
            if singl_src['sfunc'] == '':
                st.error('Для этого источника не назначен парсер')
                st.stop()
            parse_func = getattr(cpf, singl_src['sfunc'])
            if parse_func != '':
                req_status, df = parse_func(1 if upd_chb1 else 0, upd_pgs if upd_chb2 else 1)
                if req_status != 200:
                    st.info(f'Page request status = {req_status} ')
                    st.stop()
                df['fsid'] = singl_src['fsid']
                df['score'] = -1
                df['group_topic'] = ''
                df['topic'] = ''
                df['group_theme'] = ''
                df['theme'] = ''
                df['project'] = ''
                df['uname'] = session_state2.u_name

        st.write(df)

        econn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
        with econn:
            ecur = econn.cursor()

            ecur.execute("""DROP TABLE IF EXISTS feed_entries_temp;""")
            econn.commit()
            df.to_sql('feed_entries_temp', econn, if_exists='replace', index=False)  # , dtype={"fsid": int()})
            econn.commit()
            if upd_chb3:  # включён флаг обновления существующих новостей
                edf_ = pd.read_sql_query("""SELECT * 
                            FROM feed_entries_temp 
                            WHERE (fsid, elink) in 
                                (SELECT fsid, elink 
                                FROM feed_entries)""", econn, coerce_float=False)

                edf_.drop_duplicates(['fsid', 'elink'], inplace=True, ignore_index=True)

                newrows = [tuple(r) for i, r in edf_[
                    ['u_etitle', 'u_summary', 'etitle', 'summary', 'elink', 'published', 'elink_img', 'fsid',
                     'elink']].iterrows()]

                sql = f''' UPDATE feed_entries 
                        SET u_etitle = ? ,
                            u_summary = ? ,
                            etitle = ? ,
                            summary = ? ,
                            elink = ? ,
                            published = ? ,
                            elink_img = ? ,
                            uname = '{session_state2.u_name}' ,
                            rdate = datetime('now', 'localtime') 
                        WHERE fsid = ? and elink = ?; '''
                try:
                    ecur.executemany(sql, list(newrows))
                except Exception as e:
                    st.warning(e)
                st.success(f'{ecur.rowcount} строк обновлено.')
                econn.commit()
                # st.write(newrows)

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
            entrs = [tuple(r) for i, r in edf_[
                ['fsid', 'u_etitle', 'u_summary', 'etitle', 'summary', 'elink', 'published', 'elink_img', 'score',
                 'group_topic', 'topic', 'group_theme', 'theme', 'project', 'uname']].iterrows()]

            # st.write(entrs[:2])

            ecur.executemany(
                "INSERT INTO feed_entries VALUES(null, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now', 'localtime'));",
                list(entrs))
            st.success(f'{ecur.rowcount} строк добавлено.')
            econn.commit()

    st.markdown('---')
    with st.expander('Загрузка новостей из файла'):
        if not sdf.sname.isin([CUST_NAMESRC]).any():
            st.warning(f'Не найден источник {CUST_NAMESRC}')
            st.stop()
        else:
            CUST_FSID = sdf[sdf.sname.isin([CUST_NAMESRC])].fsid.values[0]
            # st.write(CUST_FSID)
        up_cols = ['sname', 'etitle', 'summary', 'elink', 'published', 'elink_img', 'score', 'group_topic', 'topic',
                   'group_theme', 'theme', 'project']  # столбцы для загрузки
        st.info(f'Столбцы для загрузки {str(up_cols)}')
        col1, col2 = st.columns([1, 3])
        with col1:
            # st.subheader('Файл')
            atfn = st.file_uploader('здесь загружается файл с новостями', ['csv'],
                                    help='тип CSV кодировка UTF-8 разделитель запятая')
        with col2:
            if atfn is not None:
                adf = pd.read_csv(atfn, sep=',')
                ok_df_sw = 0
                if set(up_cols).issubset(set(list(adf.columns))):
                    st.success('Данные из файла получены')
                    st.write(adf[up_cols])
                    ok_df_sw = 1
                else:
                    # st.error("Не подходящая структура файла. Проверь наличие полей: 'fsid','etitle','summary','elink','published','elink_img','score','group_topic','topic','group_theme','theme','project' ")
                    st.error(f"Не подходящая структура файла. Проверь наличие полей: {str(up_cols)} ")
                    st.write(adf)

                if ok_df_sw == 1:
                    # no_s_df = adf[~adf.fsid.isin(sdf.fsid.unique())]
                    # s_df = adf[adf.fsid.isin(sdf.fsid.unique())]
                    no_s_df = adf[~adf.sname.isin([CUST_NAMESRC])]
                    s_df = adf[adf.sname.isin([CUST_NAMESRC])].reset_index(drop=True)
                    s_df['fsid'] = CUST_FSID

                    if no_s_df.shape[0] != 0:
                        st.warning(f'Эти строки не будут загружены - не найден код для источника {CUST_NAMESRC}')
                        st.write(no_s_df)
                    with st.form('file_update', clear_on_submit=True):
                        try:
                            save_btn2 = st.form_submit_button('Upload', 'Загрузить в БД')
                            if save_btn2:

                                econn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
                                with econn:
                                    ecur = econn.cursor()
                                    ecur.execute("""DROP TABLE IF EXISTS feed_entries_temp;""")
                                    econn.commit()
                                    s_df.to_sql('feed_entries_temp', econn, if_exists='replace',
                                                index=False)  # , dtype={"fsid": int()})
                                    econn.commit()

                                    edf_ = pd.read_sql_query("""SELECT * 
                                                FROM feed_entries_temp 
                                                WHERE (fsid, elink) in 
                                                    (SELECT fsid, elink 
                                                    FROM feed_entries)""", econn, coerce_float=False)

                                    edf_.drop_duplicates(['fsid', 'elink'], inplace=True, ignore_index=True)
                                    edf_['u_etitle'] = edf_['etitle']
                                    edf_['u_summary'] = edf_['summary']

                                    newrows = [tuple(r) for i, r in edf_[
                                        ['u_etitle', 'u_summary', 'etitle', 'summary', 'elink', 'published',
                                         'elink_img', 'fsid', 'elink']].iterrows()]

                                    sql = f''' UPDATE feed_entries 
                                            SET u_etitle = ? ,
                                                u_summary = ? ,
                                                etitle = ? ,
                                                summary = ? ,
                                                elink = ? ,
                                                published = ? ,
                                                elink_img = ? ,
                                                uname = '{session_state2.u_name}' ,
                                                rdate = datetime('now', 'localtime') 
                                            WHERE fsid = ? and elink = ?; '''
                                    try:
                                        ecur.executemany(sql, list(newrows))
                                    except Exception as e:
                                        st.warning(e)
                                    st.success(f'{ecur.rowcount} строк обновлено.')
                                    econn.commit()
                                    # st.write(newrows)

                                    edf_ = pd.read_sql_query("""SELECT * 
                                                                FROM feed_entries_temp 
                                                                WHERE (fsid, elink) in 
                                                                    (SELECT fsid, elink 
                                                                    FROM feed_entries_temp 
                                                                    EXCEPT 
                                                                    SELECT fsid, elink 
                                                                    FROM feed_entries)""", econn, coerce_float=False)

                                    edf_.drop_duplicates(['fsid', 'elink'], inplace=True, ignore_index=True)
                                    edf_['u_etitle'] = edf_['etitle']
                                    edf_['u_summary'] = edf_['summary']
                                    edf_['uname'] = session_state2.u_name

                                    edf_ = edf_[
                                        ['fsid', 'u_etitle', 'u_summary', 'etitle', 'summary', 'elink', 'published',
                                         'elink_img', 'score', 'group_topic', 'topic', 'group_theme', 'theme',
                                         'project', 'uname']]

                                    entrs = [tuple(r) for i, r in edf_.iterrows()]

                                    # st.write(entrs[:2])

                                    ecur.executemany(
                                        "INSERT INTO feed_entries VALUES(null, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now', 'localtime'));",
                                        list(entrs))
                                    st.success(f'{ecur.rowcount} строк добавлено.')
                                    econn.commit()
                        except Exception as e:
                            st.warning(e)
                else:
                    st.info('Файл не загружен.')
        st.markdown('---')


def bid_news():
    session_state2 = SessionState.get(token_body='', u_name='незнакомка', src_cache_id=1)

    def adsw():
        return 1 if st.secrets['DEBUG']['admin'] == session_state2.u_name else 0

    def athsw():
        '''Проверка авторизации'''
        return 1 if session_state2.u_name != 'Без авторизации' else 0

    # RE_TAGS = re.compile(r"<([^>]+)>", re.UNICODE)
    # def strip_tags(text,marker=''):
    #     '''Remove tags from s using RE_TAGS.
    #     >>> strip_tags('<href="http://google.com">')
    #     ''
    #     >>> 
    #     '''
    #     return RE_TAGS.sub(marker, text)

    edf = get_feeds()

    import plotly.express as px
    st.sidebar.info(f'{edf.shape[0]} сообщений')

    fig = px.pie(edf, names='score', title='Структура по рейтингу', width=300, height=300)
    fig.update_traces(textposition='inside', textinfo='value+percent')
    st.sidebar.write(fig)

    with st.expander('Фильтры'):
        with st.form(key='filtrs'):
            fcols = ['sname', 'score', 'group_topic', 'topic', 'group_theme', 'theme', 'project', 'uname']
            filtdict = {}
            for fc, col in zip(fcols, st.columns(len(fcols))):
                with col:
                    filtdict[fc] = st.multiselect(f'Фильтр по {fc}', edf[fc].unique().tolist())
            filter_btn = st.form_submit_button('Применить')

    df_filter = (edf[fcols[0]] == edf[fcols[0]])
    for fc in fcols:
        if filtdict[fc]:
            t_df_filter = (edf[fc].isin(filtdict[fc]))
            df_filter &= t_df_filter  # сформировали общий фильтр из всех

    # if  df_filter!=[]:
    all_news_count = edf.shape[0]
    edf = edf[df_filter].reset_index(drop=True)  # применили фильтр

    # @st.cache
    # def convert_df(df):
    #     # IMPORTANT: Cache the conversion to prevent computation on every rerun
    #     return df.to_csv(index=False).encode('cp1251') #('utf-8')

    @st.cache(allow_output_mutation=True)
    def buf_export(df):
        import pandas as pd
        import io

        buffer = io.BytesIO()

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Write each dataframe to a different worksheet.
            df.to_excel(writer, sheet_name='b2x_news', index=False, encoding='cp1251')

            # Close the Pandas Excel writer and output the Excel file to the buffer
            writer.save()

        return buffer

    filt_news_count = edf.shape[0]
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f'Отфильтровано {filt_news_count} из {all_news_count}')
    with col2:
        st.download_button(
            label="Export data as Excel",
            data=buf_export(edf),
            file_name=f"b2x_news_export_{datetime.datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
            mime="application/vnd.ms-excel"
        )

        # st.download_button(
        # label="Export data as CSV",
        # data=convert_df(edf),
        # file_name=f"b2x_news_export_{datetime.datetime.now().strftime('%d%m%Y_%H%M')}.csv",
        # mime='text/csv',
        # )
        # st.download_button('Сохранить себе', data=edf.to_excel('test_export.xlsx', sheet_name='b2x_news'))#, engine='xlsxwriter'))

    # https://github.com/PablocFonseca/streamlit-aggrid/blob/main/examples/main_example.py
    # Example controlers
    with st.sidebar.expander('Grid settings'):

        sample_size = filt_news_count  # st.number_input("rows", min_value=10, value=10)
        grid_height = st.number_input("Grid height", min_value=200, max_value=800, value=350, step=5)

        st.subheader("Pagination options")
        # enable_pagination = st.checkbox("Enable pagination", value=True)
        # if enable_pagination:

        # Пагинацию страниц делаем вручную т.к. Aggrid вылетает при количестве строк более 500 !!!
        paginationAutoSize = st.checkbox("Auto pagination size", value=True, help='default 15')
        paginationPageSize = min(filt_news_count, 15)
        if not paginationAutoSize:
            paginationPageSize = st.number_input("Page size", value=min(filt_news_count, 15), min_value=1, max_value=50,
                                                 step=1)
        st.text("___")
    if filt_news_count == 0:
        st.info('Нет в БД новостей')
        st.stop()

    max_page_num = sample_size // paginationPageSize  # всего страниц
    max_page_num += 1 if max_page_num * paginationPageSize < sample_size else 0
    cur_pag_page = st.slider(f'Выбор текущей страницы. Всего {max_page_num}.', 0 if max_page_num == 1 else 1,
                             max_page_num, 1, 1)  # текущая страница
    pag_bounds = [max(0, cur_pag_page - 1) * paginationPageSize,
                  cur_pag_page * paginationPageSize]  # границы выборки строк текущей страницы

    aedf = edf[pag_bounds[0]:pag_bounds[1]]  # фрейм для фронта

    def gb_sets(gb_):

        gb_.configure_side_bar()

        gb_.configure_selection('single')

        gb_.configure_grid_options(domLayout='normal')

    gb = GridOptionsBuilder.from_dataframe(aedf)

    gb.configure_side_bar()

    gb.configure_selection('single')

    gb.configure_grid_options(domLayout='normal')

    gb.configure_columns(['sname'], width=120, pinned=True)
    gb.configure_columns(['topic'], width=120, pinned=True)
    gb.configure_columns(['score'], width=100, pinned=True)
    gb.configure_columns(['u_etitle'], width=280, wrapText=True,
                         autoHeight=True)  # ,rowHeight=35,  cellEditorPopup=True
    gb.configure_columns(['u_summary'], width=280, wrapText=True)
    gb.configure_columns(['fsid'], width=100)
    gb.configure_columns(['feid'], width=100)
    # gb_sel.configure_grid_options(autoHeight=True)#rowHeight=65)

    go = gb.build()

    ag = AgGrid(
        aedf,
        gridOptions=go,
        height=grid_height,
        width='100%',
        data_return_mode=DataReturnMode.FILTERED,  # return_mode_value,
        update_mode=GridUpdateMode.SELECTION_CHANGED,  # update_mode_value,
        fit_columns_on_grid_load=True,  # fit_columns_on_grid_load,
        allow_unsafe_jscode=True,  # Set it to True to allow jsfunction to be injected
        enable_enterprise_modules=True,  # enable_enterprise_modules,
        try_to_convert_back_to_original_types=False,
        conversion_errors='ignore',
        reload_data=False,
    )

    # df = ag['data']
    selected = ag['selected_rows']
    if len(selected) == 0:
        st.success('Выбор сообщений..')
        st.stop()

    # AgGrid(df)
    # titl = st.selectbox('Выбери сообщение', range(len(df.title.values)), format_func=lambda x: df.title.values[x])
    for ir, rw in pd.DataFrame(selected).iterrows():  # selected_df.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(rw.u_etitle)
            st.write(rw.u_summary)
        with col2:
            try:
                st.image(rw.elink_img, width=200)
            except:
                pass
            st.write(rw.published)

    if athsw() == 0:
        st.info('Управление базой возможно после авторизации')
        st.stop()

    if selected and athsw() == 1:
        with st.expander('Редактировать'):
            # st.write(selected)
            # st.markdown(' > В тексте не должно быть кавычек')
            col1, col2 = st.columns([2, 2])
            with col1:
                st.subheader('Текущий')
                with st.form('feed_update', clear_on_submit=True):
                    updrow_one = {}
                    for re_cols in ['score', 'group_topic', 'topic', 'group_theme', 'theme', 'project']:
                        updrow_one[re_cols] = st.text_input(re_cols, selected[0][re_cols])

                    updrow_one['u_etitle'] = st.text_area('u_etitle - *editable', selected[0]['u_etitle'], 45)
                    updrow_one['etitle'] = st.text_area('etitle', selected[0]['etitle'])
                    updrow_one['u_summary'] = st.text_area('u_summary - *editable', selected[0]['u_summary'], 45)
                    updrow_one['summary'] = st.text_area('summary', selected[0]['summary'])

                    save_btn = st.form_submit_button('Save', 'Записать в БД')
                    # st.markdown('> - Для загрузки списков обратитесь к администратору')
                    if save_btn:
                        econn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
                        with econn:
                            try:
                                ecur = econn.cursor()
                                sql = f''' UPDATE feed_entries
                                        SET group_topic = ? ,
                                            topic = ? ,
                                            group_theme = ? ,
                                            theme = ? ,
                                            project = ? ,
                                            score = ? ,
                                            u_etitle = ? ,
                                            u_summary = ? ,
                                            uname = '{session_state2.u_name}' ,
                                            rdate = datetime('now', 'localtime') 
                                        WHERE fsid = ? and feid = ?'''
                                ecur.execute(sql, list((updrow_one['group_topic'], updrow_one['topic'],
                                                        updrow_one['group_theme'], updrow_one['theme'],
                                                        updrow_one['project'], updrow_one['score'],
                                                        updrow_one['u_etitle'], updrow_one['u_summary'],
                                                        selected[0]['fsid'], selected[0]['feid'])))
                            except Exception as e:
                                st.warning(e)
                            st.success(f'Запись обновлена')
                            econn.commit()
                        session_state2.src_cache_id += 1

            with col2:
                st.subheader('Файл')
                fupd_cols = ['score', 'group_topic', 'topic', 'group_theme', 'theme', 'project', 'feid', 'fsid',
                             'u_etitle', 'u_summary']
                st.info(f'Столбцы ожидаемые в файле {str(fupd_cols)}')
                atfn = st.file_uploader('здесь загружается файл с атрибутами ленты', ['csv'])
                if atfn is not None:
                    adf = pd.read_csv(atfn, sep=',')
                    ok_df_sw = 0
                    if set(fupd_cols).issubset(set(list(adf.columns))):
                        st.write(adf[fupd_cols])
                        ok_df_sw = 1
                    else:
                        st.error(f"Не подходящая структура файла. Проверь наличие полей: {str(fupd_cols)} ")
                        st.write(adf)

                    if ok_df_sw == 1:
                        with st.form('file_update', clear_on_submit=True):
                            try:
                                save_btn2 = st.form_submit_button('Upload', 'Загрузить в БД')
                                if save_btn2:
                                    econn = sq.connect(f'{curfolder}\dbs\{DB_NAME}.db')
                                    with econn:
                                        ecur = econn.cursor()
                                        # udf = pd.DataFrame(selected)
                                        sql = f''' UPDATE feed_entries
                                                SET group_topic = ? ,
                                                    topic = ? ,
                                                    group_theme = ? ,
                                                    theme = ? ,
                                                    project = ? ,
                                                    score = ? ,
                                                    u_etitle = ? ,
                                                    u_summary = ? ,
                                                    uname = '{session_state2.u_name}' ,
                                                    rdate = datetime('now', 'localtime') 
                                                WHERE fsid = ? and feid = ?'''
                                        newrows = [tuple(r) for i, r in adf[
                                            ['group_topic', 'topic', 'group_theme', 'theme', 'project', 'score',
                                             'u_etitle', 'u_summary', 'fsid', 'feid']].iterrows()]
                                        ecur.executemany(sql, list(newrows))
                                        st.success(f'{ecur.rowcount} строк обновлено.')
                                        econn.commit()
                                    session_state2.src_cache_id += 1
                            except Exception as e:
                                st.warning(e)
                    else:
                        st.info('Файл не загружен.')

    if adsw() == 1:
        with st.expander('Grid Options'):
            st.write(go)
