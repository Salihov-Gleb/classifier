
# from __future__ import division, unicode_literals

# import inspect
# import textwrap
from collections import OrderedDict

import streamlit as st
import SessionState
# from streamlit.logger import get_logger
# from streamlit.hello import demos
import feeds_engine_modules
# import cycle_runer
# import datetime
# import os

# import warnings
# warnings.filterwarnings('ignore')
# print('Warnings is ignored.')

st.set_page_config(page_title="B2X_FeedNews", layout="wide") #, initial_sidebar_state="collapsed")


# DEBUG FUNC !
st.sidebar.header(st.secrets['DEBUG']['status'])
# st.sidebar.write(st.secrets['USERS_TOKEN'])#['t1'])
# DEBUG FUNC !

session_state = SessionState.get(token_body='NN', u_name='Без авторизации', src_cache_id=1)

if session_state.token_body=='NN' or session_state.token_body == '':
    putpwd = st.sidebar.text_input('Укажите ваш TOKEN', value='NN', type='password', help='Токен выдаётся администратором. Позволяет фиксировать данные аналитика в БД.')

    if not putpwd in st.secrets['USERS_TOKEN'].keys():
        st.sidebar.info('Не найден токен в БД')
        st.stop()
    else:
        session_state.token_body = putpwd
        session_state.u_name = st.secrets['USERS_TOKEN'][putpwd]

# st.sidebar.subheader(session_state.u_name)

if st.sidebar.button('GetOut'):
    session_state.token_body = ''
    session_state.u_name = 'Без авторизации'
    st.sidebar.info('By!')
    st.stop()

# LOGGER = get_logger(__name__)

# usname = 'nonamer'
# try:
#     usname = os.getlogin()
# except Exception as identifier:
#     pass

# Dictionary of
# report_name -> (report_function, report_description)
MODULES = OrderedDict(
    [
        (session_state.u_name , (feeds_engine_modules.intro, None)),
        (
            "Новостные ресурсы",
            (
                feeds_engine_modules.set_feeds,
                """
Тут управляем источниками и запускаем загрузку новостей.
""",
            ),
        ),
        (
            "База новостей",
            (
                feeds_engine_modules.bid_news,
                """
Тут смотрим, классифицируем и редактируем новости в своей БД.
""",
            ),
        )
    ]
)


def run():
    # st.sidebar.subheader("Модули")
    module_name = st.sidebar.radio('''Модули''', list(MODULES.keys()), 0)
    
    module = MODULES[module_name][0]

    if module_name == session_state.u_name:
        # show_code = False
        # show_tdata = False
        st.markdown(f"# {session_state.u_name}")
        st.write(f"### Welcome to B2X_FeedNews service! 👋")
        st.markdown('---')
        st.markdown('''## B2X_FeedNews ''')
        st.markdown(''' > это сервис управления базой новостей. 
        > \n Здесь настраиваются источники, выгружаются новости, устанавливаются рейтинги и категории новостных блоков. ''')
        st.markdown('---')
        
    else:

        st.markdown(f"# {module_name}")
        description = MODULES[module_name][1]
        # print('Hi, %s' % usname+' '+str(datetime.datetime.now().strftime('%d_%m_%Y-%H_%M_%S')) + ' in ' + description)
        if description:
            st.markdown(f"> {description}")

        for i in range(10):
            st.empty()

    module()

    # if show_code:
    #     st.markdown("## Code")
    #     sourcelines, _ = inspect.getsourcelines(report)
    #     st.code(textwrap.dedent("".join(sourcelines[1:])))


if __name__ == "__main__":
    run()
