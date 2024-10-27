'''
Модуль содержит парсинг-функции
Результат должен состоять из OKsw, df_ : статус запроса страницы и фрейм с лентой новостей.
Фрейм стандартизирован: ['feid','fsid','u_etitle','u_summary','etitle','summary','elink','published','elink_img']
'''
import re
from time import sleep
import pandas as pd
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import os.path
import datetime
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import locale


# максимальное время ожидания ответа от сайта
REQUEST_TIMEOUT = 20
# формат даты
DATE_FORMAT = '%d/%m/%Y. %H/%M/%S'

service = ChromeService(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument("headless")
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}
search_requests = []
with open('.\conf\search_requests.txt', 'r', encoding='utf-8') as f:
    search_requests = f.read().splitlines()


def get_newdf():
    return pd.DataFrame([], columns=['feid', 'fsid', 'u_etitle', 'u_summary', 'etitle', 'summary', 'elink', 'published', 'elink_img'])


def func_neftegas(go_deep=1, pages_cnt=1):
    # ОБЩИЙ РАЗДЕЛ
    SRC_URL = 'https://neftegas.info/news/'
    main_url = 'https://neftegas.info'
    page = requests.get(SRC_URL)
    OKsw = page.status_code
    df_ = get_newdf() #pd.DataFrame([], columns=[])

    allNews = []
    soup = BeautifulSoup(page.text, features="html.parser")#, "html.parser")
    page.close()

    # ИНДИВИДУАЛЬНЫЙ РАЗДЕЛ
    allNews = soup.findAll('a', class_='news-list-all')

    # for n in allNews[:15]:
    #     print(n.attrs['href'])
    #     print(n.find('span', class_='news-list-all-date').text.strip())
    #     print(n.find('h2').text)
    
    for i, e in enumerate(allNews):
        one_feed = {}
        one_feed['feid'] = ''
        one_feed['fsid'] = ''
        one_feed['u_etitle'] = e.find('h2').text #e.title if 'title' in e else f'title {i}'
        one_feed['u_summary'] = e.find('h2').text #e.summary if 'summary' in e else f'no summary {i}'
        one_feed['etitle'] = one_feed['u_etitle']
        one_feed['summary'] = one_feed['u_summary']
        one_feed['elink'] = main_url + e.attrs['href'] if 'href' in e.attrs else f'link {i}'
        one_feed['published'] = e.find('span', class_='news-list-all-date').text.strip() #e.published if 'published' in e else f'no published {i}'
        one_feed['elink_img'] = f'no link_img {i}' #e.links[1].href if 'links' in e and len(e.links)>1 else f'no link_img {i}'
        # one_feed['score'] = -1
        # one_feed['topic'] = ''
        # one_feed['uname'] = '' #session_state2.u_name

        df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    
    return OKsw, df_


def func_mir_smazok(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://mirsmazok.ru'
    url = 'https://mirsmazok.ru/news/?PAGEN_1='

    OKsw = None
    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    for p in range(1, pages_cnt + 1):
        try:
            purl = f"{url}{p}"
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(purl)
            WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "news-page"))
            driver.implicitly_wait(10)
            OKsw = 200
            all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all(
                'div',
                attrs={'class': 'news-item-small'}
            )
            if p == 1:
                all_news.append(BeautifulSoup(driver.page_source, features="html.parser").find(
                    'div',
                    attrs={'class': 'hidden-xs main-news-item'}
                ))
            driver.close()
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''

                if 'main-news-item' in news.attrs['class']:
                    one_feed['u_etitle'] = news.find(
                        'div',
                        attrs={'class': 'news-item-large-title'}
                    ).text
                    summery = news.find('div', attrs={'class': 'main-news-item-desc'})
                    if summery is not None:
                        one_feed['u_summary'] = summery.text
                    else:
                        one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    one_feed['published'] = news.find(
                        'div',
                        attrs={'class': 'news-item-date'}
                    ).text.strip()
                    img = news.find('div', attrs={'style': True})
                    if img is not None:
                        img_link = img.attrs['style']
                        img_link = re.search(r'\((.+)\)', img_link)[0][1:-1]
                        one_feed['elink_img'] = f"{main_url}{img_link}"
                else:
                    one_feed['u_etitle'] = news.find(
                        'div',
                        attrs={'class': 'news-item-small-title'}
                    ).text
                    one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    one_feed['published'] = news.find(
                        'div',
                        attrs={'class': 'news-item-date'}
                    ).text.strip()
                    img = news.find('div', attrs={'class': 'news-item-small-img'})
                    if img is not None:
                        img_link = img.attrs['style']
                        img_link = re.search(r'\((.+)\)', img_link)[0][1:-1]
                        one_feed['elink_img'] = f"{main_url}{img_link}"

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.get(one_feed['elink'])
                        WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "news-detail-page"))
                        driver.implicitly_wait(2)
                        soup = BeautifulSoup(driver.page_source, features="html.parser").find('div', attrs={'class': 'news-detail'})
                        driver.close()
                        one_feed['u_etitle'] = soup.find('h1').text.strip()
                        one_feed['etitle'] = one_feed['u_etitle']
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'news-detail-text'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                        img = soup.find(
                            'div',
                            attrs={'class': 'news-detail-img'}
                        ).find('img')
                        if img is not None:
                            one_feed['elink_img'] = f"{main_url}{img.attrs['src']}"
                    except Exception as e:
                        pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_rss_8_neftegaz(url_, pages_cnt=1):
    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")  # , "html.parser")
    summary = soup.find(
        'div',
        attrs={'class': 'articleBodyСlass'}
    ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')

    page.close()
    return OK_SW, summary


def func_11_lukoil(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'

    main_url = 'https://lukoil-masla.ru/ru'
    url = f'{main_url}/mediacentre/News'

    OKsw = None
    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(3)
        for p in range(1, pages_cnt):
            try:
                button = driver.find_element(By.CLASS_NAME,
                                             'load-more-button')
                driver.execute_script("arguments[0].click();", button)
                driver.implicitly_wait(3)
            except Exception as e:
                pass
        OKsw = 200
        if OKsw == 200:
            all_news = BeautifulSoup(
                driver.page_source,
                features="html.parser"
            ).find_all('div', attrs={'role': 'tablist'})
            driver.close()
            for news in all_news:
                try:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''

                    one_feed['u_etitle'] = news.find('span', attrs={'class': 'title'}).text.strip()
                    one_feed['u_summary'] = news.find('p', attrs={'data-bind': 'html: Announcement'}).get_text()
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = news.find('a').attrs['href']
                    published = datetime.datetime.strptime(news.find('span', attrs={'class': 'date'}).text.strip(), '%d.%m.%Y -')
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    img = news.find('img')
                    if img is not None:
                        one_feed['elink_img'] = img.attrs['src']

                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            driver = webdriver.Chrome(service=service, options=options)
                            driver.get(one_feed['elink'])
                            driver.implicitly_wait(2)
                            soup = BeautifulSoup(driver.page_source, features="html.parser")
                            driver.close()
                            one_feed['u_etitle'] = soup.find('h3', attrs={
                                'class': 'press-release-page-title'}).text.strip()
                            one_feed['etitle'] = one_feed['u_etitle']
                            content = soup.find('div', attrs={'class': 'content'})
                            content.span.decompose()
                            one_feed['u_summary'] = ' '.join([tag.text for tag in content.find_all('p')]).strip()
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
                except Exception as e:
                    pass
    except Exception as e:
        pass
    try:
        driver.close()
    except Exception as e:
        pass

    return OKsw, df_


def func_16_tatneft(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.tatneft.ru'
    url = 'https://www.tatneft.ru/press-tsentr/?lang=ru'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.find('div', id='press-releases-list')
    allNews = allNews.findAll('div', class_='material')

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            # a = e.find('div', class_='panel-heading').find('a')
            # b = e.find('div', class_='panel-body')
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_= 'material__title_wrapper').text.strip()
            one_feed['u_summary'] = e.find('div', class_='material__description_wrapper hidden-xs').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_= 'material__image-wrapper').find('a').attrs['href']
            one_feed['published'] = e.find('span', class_= 'material__date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('img', class_= 'material__image').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        s = ''
                        one_feed['u_summary'] = soup_one.find('div', class_='news-content').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except Exception as e:
                    print(e)

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            print(e)

    return OKsw, df_


def func_17_idemitsu(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.idemitsu.ru'
    url = 'https://www.idemitsu.ru/news'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='news-item col-md-4 col-sm-6')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='info_new').find('a').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('a').find('div').attrs['style'].replace('background: url(','').replace(') no-repeat;','')
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='new_prev_text').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_19_exxonmobil(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.exxonmobil.ru/ru-RU'
    url = 'https://www.exxonmobil.ru/ru-RU/News/Newsroom'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='contentCollection--item')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('a').text.strip()
            one_feed['u_summary'] = e.find('span', class_='contentCollection--description p').text
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('span', class_='date').find('span').attrs['data-date']  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = one_feed['u_summary'] + soup_one.find('span', class_= 'p').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_20_totalcom(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://lubricants.totalenergies.com'
    url = 'https://lubricants.totalenergies.com/news-press-releases'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='mega-gabarit edito edito_1col one-columns lgrey-color')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('span', class_='news-list-title').text.strip()
            one_feed['u_summary'] = e.find('div', class_= 'total-block-edito-text__desc').find('p').text
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('span', class_='date-display-single').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = e.find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_= 'text-rte').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_21_totalru(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://services.totalenergies.ru'
    url = 'https://services.totalenergies.ru/press-release'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.find('div', class_='list-articles block-news').findAll('li')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('span', class_='news-list-title').text.strip()
            one_feed['u_summary'] = e.find('p').text
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('span', class_='date-display-single').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_= 'text-rte').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_22_chevron(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.chevron.com'
    url = 'https://www.chevron.com/stories'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='stretch-container centered-xs')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('span', class_='underline').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('span', class_='date body-3 dark-gray').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_= 'inner-container col centered width-800').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_23_komatsu(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.komatsu.ru'
    url = 'https://www.komatsu.ru/about/news'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='page--news--item clearfix')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='ovh cross_page_right_content_block page--news-title').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='ovh cross_page_right_content_block page--news-title').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='ffb page--news--date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_= 'news_full--block_content').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_24_zic(go_deep=1, pages_cnt=1):

    main_url = 'https://zicoil.ru'
    url = 'https://zicoil.ru/about/news'
    df_ = get_newdf()
    locale.setlocale(locale.LC_ALL, 'ru')
    months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь',
              'Ноябрь', 'Декабрь']

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")
    all_news = soup.find_all('div', class_='line')
    page.close()

    for i, e in enumerate(all_news):
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='text').find('h5').find('a').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='text').find('h5').find('a').attrs['href']
            published = datetime.datetime(datetime.datetime.today().year, 1, int(e.find('div', class_='date').find('span', class_='day mobile').text))
            published = published.replace(month=months.index(e.find('div', class_='date').find('span', class_='month').text, 0) + 1)
            one_feed['published'] = published.strftime(DATE_FORMAT)
            one_feed['elink_img'] = main_url + e.find('div', class_='img-block').find('img').attrs['src']

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='content').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        published = published.replace(year=int(soup_one.find('div', class_='date').text.strip().split('|')[-1]))
                        one_feed['published'] = published.strftime(DATE_FORMAT)
                except Exception as e:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_rss_5_autostat(url_, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests

    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")#, "html.parser")
    alltext = soup.findAll('div', class_='text inner_content')
    summary = ''

    for n in alltext:

        summary += n.text

    page.close()
    return OK_SW, summary


def func_rss_9_rosneft(url_, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests

    page = requests.get(url_)
    page.encoding = 'utf8'
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")#, "html.parser")
    summary = soup.find('div', class_='common-text').text
    page.close()
    return OK_SW, summary


def func_26_hyundai(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.hyundai.ru'
    url = 'https://www.hyundai.ru/news'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='col-lg-3 col-md-6')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='news__text').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('a').find('div', class_ = 'news__date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='news__img').attrs['style'].replace('background-image: url(','').replace(')','')
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_= 'news-content__bottom').find('div', class_= 'col-md-12').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_6_fuellubes(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.fuelsandlubes.com'
    url = 'https://www.fuelsandlubes.com/fli-article'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='single_post post_type3 mb30')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='single_post_text').find('h4', class_='entry-title').text
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = e.find('div', class_='single_post_text').find('h4', class_='entry-title').find('a').attrs['href']
            one_feed['published'] = ''  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = e.find('div', class_='post_img').find('a', class_='post-thumbnail').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        s = ''
                        for tag in soup_one.find('div', class_='padding20 white_bg'):
                            if tag.name == 'p':
                                s += tag.text
                        one_feed['u_summary'] = s
                        one_feed['summary'] = one_feed['u_summary']
                        one_feed['published'] = soup_one.find('div', class_= 'author').find('a').text.strip()
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_28_exxoncom(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://corporate.exxonmobil.com'
    url = 'https://corporate.exxonmobil.com/News/Newsroom/News-releases'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='contentCollection--content')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('a').text.strip()
            one_feed['u_summary'] = e.find('span', class_='contentCollection--description p').text
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('span', class_='date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = one_feed['u_summary'] + soup_one.find('span', class_='p').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_29_castrol(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.castrol.com'
    url = 'https://www.castrol.com/ru_ru/russia/home/castrol-story/newsroom.html'
    df_ = get_newdf()

    page = requests.get(url, timeout=10)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='nr-cards-component nr-component aem-GridColumn aem-GridColumn--default--12')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h3').text.strip()
            one_feed['u_summary'] = e.find('div', class_='nr-cards__description').find('p').text
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = ''  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='nr-text-component nr-component aem-GridColumn aem-GridColumn--default--12').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        one_feed['published'] = soup_one.find('div', class_='nr-text-component nr-component aem-GridColumn aem-GridColumn--default--12').find('p').find('i').text.replace('Москва, ','')
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_30_maz(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'http://maz.by'
    url = 'http://maz.by/media/news'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='col-sm-6 col-md-4 col-lg-3 wow fadeIn pb-50')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='post-prev-title').find('h3').text
            one_feed['u_summary'] = e.findAll('div')[3].text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='post-prev-img').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='post-prev-info').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='post-prev-img').find('a').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='mb-50').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_31_liebherr(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.liebherr.com'
    url = 'https://www.liebherr.com/ru/rus/%D0%B0%D0%BA%D1%82%D1%83%D0%B0%D0%BB%D1%8C%D0%BD%D0%B0%D1%8F-%D0%B8%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D1%8F/%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8-%D0%B8-%D0%BF%D1%80%D0%B5%D1%81%D1%81-%D1%80%D0%B5%D0%BB%D0%B8%D0%B7%D1%8B/%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8-%D0%B8-%D0%BF%D1%80%D0%B5%D1%81%D1%81-%D1%80%D0%B5%D0%BB%D0%B8%D0%B7%D1%8B.html'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='item')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='text').find('h2').text.strip()
            one_feed['u_summary'] = e.find('div', class_='text').findAll('p')[1].text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='text').find('h2').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='text').find('p').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='image').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('article', class_='grid_15 contentColumn').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_32_mbtrucks(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.mercedes-benz-trucks.com'
    url = 'https://www.mercedes-benz-trucks.com/ru_RU/brand/news.html'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='e-teaser-2__content')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h3', class_='e-hdl-6 e-teaser-2__headline').text.strip()
            one_feed['u_summary'] = e.find('p', class_='e-teaser-2__text').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a', class_='e-teaser-2__link mbo-e-link–rewrite').attrs['href']
            one_feed['published'] = ''  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='wb-col-mq1-12 wb-col-mq3-8').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_33_neste(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.neste-lub.ru'
    url = 'https://www.neste-lub.ru/%D0%B8%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D1%8F-%D0%BE-neste/%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('article', class_='c-lb views-row views-row-first views-row-last u-separate-bottom')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='c-lb__content').find('a').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='c-lb__content').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='c-lb__aside').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='field__item even').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_34_kixx(go_deep=1, pages_cnt=1):

    main_url = 'https://kixx.su'
    url = 'https://kixx.su/news'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")
    all_news = soup.find_all('div', class_='news-item wow fadeInLeft')
    page.close()

    for i, e in enumerate(all_news):
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h2').find('a').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            published = datetime.datetime.strptime(e.find('div', class_='news-date-time').text.strip(), '%d.%m.%Y')
            one_feed['published'] = published.strftime(DATE_FORMAT)
            one_feed['elink_img'] = main_url + e.find('a').find('img').attrs['src']

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='news-detail').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_rss_36_osk(url_, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests

    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")#, "html.parser")
    summary = soup.find('div', class_='news__text guideline').text.strip()
    page.close()
    return OK_SW, summary


def func_37_powerm(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://power-m.ru'
    url = 'https://power-m.ru/press-center/news'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='one-news-page list-news one-news-page06 clearfix')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='info-news').find('a').text.strip()
            one_feed['u_summary'] = e.find('div', class_='info-news').find('p').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='info-news').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='post_date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='text-box').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_38_mtu(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.mtu-solutions.com'
    url = 'https://www.mtu-solutions.com/eecis/en/news-and-media/media-center.html'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='mtu-grid-col-xs-12 mtu-grid-col-m-6 mtu-grid-col-xl-3')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('p', class_='mtu-e-title mtu-e-title--card').find('span').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = e.find('div', class_='mtu-m-teaser__image mtu-m-teaser__image--4x3').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='mtu-m-teaser__info').find('time', class_='mtu-m-teaser__date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='mtu-m-teaser__image mtu-m-teaser__image--4x3').find('a').find('mtu-e-lazy-image').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='mtu-js-main-article mtu-grid-col-xs-12 mtu-grid-col-m-8 mtu-grid-offset-m-2').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_39_kia(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.kia.ru'
    url = 'https://www.kia.ru/press/news'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('article', class_='articles-item flex flex-col')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='articles-item__preview text-s2-b desktop:text-s1').find('span').find('span').attrs['aria-label']
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='articles-item__date text-s3 desktop:text-s2 color-disabled-gray mt-1').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = e.find('figure').attrs['style'].replace('background-image:url(','').replace(');','')
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='articles-detail__content text-s2i').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_40_renault(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.renault.ru'
    url = 'https://www.renault.ru/news.html'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='ArticleFeedContainer ArticleFeed__card')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('span', class_='ArticleTitle__title').text
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='ArticleTitle ArticleFeedContainer__title').find('a').attrs['href']
            one_feed['published'] = e.find('p', class_='ArticleTitle__subTitle').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='ArticleBody').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_41_volvo(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.volvotrucks.ru'
    url = 'https://www.volvotrucks.ru/ru-ru/news/press-releases.html'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('li', class_='articlelist__item')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('p', class_='articlelist__headerTitle').find('a').text.strip()
            one_feed['u_summary'] = e.find('div', class_='articlelist__content').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = e.find('p', class_='articlelist__headerTitle').find('a').attrs['href']
            one_feed['published'] = e.find('p', class_='articlelist__headerTime').find('span', class_='articlelist__headerTimeDate').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = e.find('div', class_='articlelist__image').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='text__container').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_42_totachi(go_deep=1, pages_cnt=1):

    main_url = 'https://www.totachi.ru'
    url = 'https://www.totachi.ru/media/news/'

    df_ = get_newdf()
    for p in range(pages_cnt):
        purl = f'{url}?p={p}'

        page = requests.get(purl, timeout=REQUEST_TIMEOUT)
        OKsw = page.status_code

        soup = BeautifulSoup(page.text, features="html.parser")
        all_news = soup.find('div', attrs={'class': 'news__set'}).find_all('div', attrs={'class': 'news__beside'})
        page.close()

        for news in all_news:
            try:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                one_feed['u_etitle'] = news.find('a').text
                one_feed['u_summary'] = news.find('div', attrs={'class': 'news__text'}).get_text().strip()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = main_url + news.find('a').attrs['href']
                published = news.find('div', attrs={'class': 'news__date'}).get_text()
                published = datetime.datetime.strptime(published, '%d.%m.%Y')
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['elink_img'] = ''

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        spage = requests.get(one_feed['elink'])
                        if spage.status_code == 200:
                            soup_one = BeautifulSoup(spage.text, features="html.parser")
                            spage.close()
                            one_feed['u_summary'] = soup_one.find('div', attrs={'class': 'novelty__content'}).text.strip()
                            one_feed['summary'] = one_feed['u_summary']
                    except:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
            except:
                pass

    return OKsw, df_


def func_43_eurol(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://eurol-rus.ru'
    url = 'https://eurol-rus.ru/news/'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='simple-news-item')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('a').text
            one_feed['u_summary'] = e.find('div', class_='simple-news-excerpt').text
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = e.find('a', class_='simple-news-item-link').attrs['href']
            one_feed['published'] = e.find('div', class_='simple-news-date').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='post-content').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_rss_44_addinol(url_, pages_cnt=1):

    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")
    summary = soup.find('div', class_='fusion-text fusion-text-1').text.strip()
    page.close()
    return OK_SW, summary


def func_45_wolf(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'

    main_url = 'https://www.wolflubes.com'
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    url = f'https://ru.wolflubes.com/ru-ru/news?pageSize=50&page={pages_cnt}&viewSize=100'

    months = ['янв.', 'февр.', 'мар.', 'апр.', 'мая', 'июн.',
              'июл.', 'авг.', 'сент.', 'окт.', 'нояб.', 'дек.']

    OKsw = None

    df_ = get_newdf()
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        driver.implicitly_wait(3)
        OKsw = 200
        if OKsw == 200:
            all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all(
                'article',
                attrs={'class': 'c-newscard'}
            )
            driver.close()
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                one_feed['u_etitle'] = news.find('h3',attrs={'class': 'h5'}).get_text().strip()
                one_feed['u_summary'] = news.find(
                    'div',
                    attrs={'class': 'c-newscard__description'}
                ).get_text().strip()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                day, month, year, _ = news.find('div', attrs={'class': 'c-newscard__date'}).get_text().strip().split()
                published = datetime.datetime(int(year), months.index(month, 0) + 1, int(day))
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['elink_img'] = news.find('img').attrs['src']

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.get(one_feed['elink'])
                        driver.implicitly_wait(3)
                        soup = BeautifulSoup(driver.page_source, features="html.parser")
                        driver.close()
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'c-news-article'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_46_daf(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.daf.ru'
    url = 'https://www.daf.ru/ru-ru/news-and-media'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='card card--news')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h3', class_='card-title').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('span', class_='card-date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='card__image js-responsive-background').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='rte').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_47_isuzu(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.isuzu.ru'
    url = 'https://www.isuzu.ru/company/news/'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='news-list__item')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('a', class_='news-list__title').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('p', class_='news-list__date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='news-list__image').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='news-detail__text content__text').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_27_argus(go_deep=1, pages_cnt=1):
    main_url = 'https://www.argusmedia.com'
    url = 'https://www.argusmedia.com/ru/news?language=Russian'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")
    all_news = soup.find_all('div', class_='article-content-container')
    page.close()

    for i, e in enumerate(all_news):
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h1').find('span').text
            one_feed['u_summary'] = e.find('div', class_='article-copy').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('h1').find('a').attrs['href']
            one_feed['published'] = e.find('header').find('div', class_='article-date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        s = ''
                        for tag in soup_one.find('div', class_='news-container cf').find('article'):
                            if tag.name == 'p':
                                s += tag.text
                        one_feed['u_summary'] = s
                        one_feed['summary'] = one_feed['u_summary']
                except Exception as e:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_rss_49_globuc(url_, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests

    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")#, "html.parser")
    summary = soup.find('div', class_='text-main big').text.strip()
    page.close()
    return OK_SW, summary


def func_18_shellcom(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.shell.com'
    url = 'https://www.shell.com/media/news-and-media-releases.html'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_ ='promo-list__text')
    page.close()

    for i, e in enumerate(allNews[:50]):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('a').text.strip()
            one_feed['u_summary'] = e.findAll('p')[1].text
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('p', class_= 'promo-list__date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='text-image__text').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_14_shellru(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.shell.com.ru'
    url = 'https://www.shell.com.ru/shell-media-center.html'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_ ='promo-list__text')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('a').text.strip()
            one_feed['u_summary'] = e.findAll('p')[1].text
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a').attrs['href']
            one_feed['published'] = e.find('p', class_= 'promo-list__date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='text-image__text').text.strip()
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_rss_50_liquimoly(url_, pages_cnt=1):

    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")
    summary = soup.find('div', class_='newsdetail').text.strip()
    page.close()
    return OK_SW, summary


def func_51_motul(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.motul.com/ru'
    url = 'https://www.motul.com/ru/ru/news'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='columns medium-6 grid-item news-grid-tile news-item-product product') + soup.findAll('div', class_='columns medium-6 grid-item news-grid-tile news-item-group group')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='news-item-body').find('a').text.strip()
            one_feed['u_summary'] = e.find('div', class_='news-item-body').find('p').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = e.find('div').find('a').attrs['href']
            one_feed['published'] = e.find('span', class_='news-item-date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='masonry_bricks border').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_52_deere(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.deere.ru/ru/'
    url = 'https://www.deere.ru/ru/%D0%BF%D1%80%D0%B5%D1%81%D1%81-%D1%80%D0%B5%D0%BB%D0%B8%D0%B7%D1%8B/'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('a', class_='news-listing-component container available active')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h3').text.strip()
            one_feed['u_summary'] = e.find('p').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = e.attrs['href']
            one_feed['published'] = e.find('h4').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        s = ''
                        for tag in soup.find('div', class_='col-sm-12 col-md-12').find('div', class_='content'):
                            if tag.name == 'p':
                                s += tag.text
                        one_feed['u_summary'] = s
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_53_cummins(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import re
    import pandas as pd

    main_url = 'http://www.cummins.ru'
    url = 'http://www.cummins.ru/%D0%BE-%D0%BD%D0%B0%D1%81/%D0%9D%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_=re.compile('views-row views-row-'))
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h2', class_='field-content').text.strip()
            one_feed['u_summary'] = e.find('div', class_='views-field views-field-body').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('h2', class_='field-content').find('a').attrs['href']
            one_feed['published'] = ''  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = e.find('div', class_='field-content pull-left').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='field-item even').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_54_infineum(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.infineum.com'
    url = 'https://www.infineum.com/en-gb/news/'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('a', class_='background-colormain | news-item')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h3', class_='news-item__name').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.attrs['href']
            one_feed['published'] = e.find('span', class_='news-item__date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('article', class_='main-col--wide content text-wrapper career-article').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_rss_55_api(url_, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests

    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")#, "html.parser")
    summary = soup.find('div', class_='centered-content').text.strip()
    page.close()
    return OK_SW, summary


def func_56_aimol(go_deep=1, pages_cnt=1):

    main_url = 'https://aimol.ru'
    url = 'https://aimol.ru/company/news/'

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    df_ = get_newdf()

    for p in range(1, pages_cnt + 1):
        purl = f'{url}?PAGEN_1={p}'
        page = requests.get(purl, timeout=REQUEST_TIMEOUT)
        OKsw = page.status_code

        soup = BeautifulSoup(page.text, features="html.parser")
        all_news = soup.find_all('div', attrs={'class': 'item-wrapper'})
        page.close()

        for news in all_news:
            try:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                one_feed['u_etitle'] = news.find('div', attrs={'class': 'title'}).find('a').text.strip()
                one_feed['u_summary'] = one_feed['u_etitle']
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}{news.find('div', attrs={'class': 'title'}).find('a').attrs['href']}"
                day, month, year = news.find('span', attrs={'class': 'date'}).text.split()
                published = datetime.datetime(int(year), months.index(month) + 1, int(day))
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['elink_img'] = f"{main_url}{news.find('div', attrs={'class': ['image', 'shine']}).find('span').attrs['data-src']}"

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        spage = requests.get(one_feed['elink'])
                        if spage.status_code == 200:
                            soup_one = BeautifulSoup(spage.text, features="html.parser")
                            spage.close()
                            one_feed['u_summary'] = soup_one.find('div', attrs={'class': 'inner_wrapper_text'}).get_text()
                            one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
            except Exception as e:
                pass

    return OKsw, df_


def func_57_insight(go_deep=1, pages_cnt=1):
    main_url = 'https://www.infineuminsight.com/en-gb'
    url = 'https://www.infineuminsight.com/en-gb/articles/'

    df_ = get_newdf()

    OKsw = 200

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'

    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    driver.implicitly_wait(2)
    article = driver.find_element(By.XPATH, '//*[@id="articles-results"]/div[1]').get_attribute('innerHTML')
    driver.close()

    soup = BeautifulSoup(article, features="html.parser")
    all_news = soup.find_all('div', class_='col-md-6 col-lg-3')

    for i, e in enumerate(all_news):
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h2', class_='heading article-list__title').text.strip()
            one_feed['u_summary'] = e.find('a').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = f"{main_url[:-6]}{e.find('a').attrs['href']}"
            one_feed['published'] = ''
            one_feed['elink_img'] = main_url + e.find('img').attrs['src']
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'], headers=headers)
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='container container--md | rte-area').find('p', class_='fs4').get_text() + ' ' + soup_one.find('div', class_='container container--md pbs | rte-area white').get_text() + ' ' + soup_one.find('div', class_='container container--md mtm | rte-area').get_text()
                        one_feed['summary'] = one_feed['u_summary']
                        published = datetime.datetime.strptime(soup_one.find('div', class_='container container--md | rte-area').find('p', class_='article__date fs-1').text, '%d %B %Y')
                        one_feed['published'] = published.strftime(DATE_FORMAT)

                except Exception as e:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_58_lubrizol(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from selenium import webdriver
    import os, os.path
    from selenium.webdriver.common.by import By
    from bs4 import BeautifulSoup
    import pandas as pd
    import requests

    main_url = 'https://www.lubrizol.com'
    url = 'https://www.lubrizol.com/Newscenter'

    df_ = get_newdf()

    OKsw = 200
    allNews = []

    abs_path = os.path.abspath(os.curdir) + '\\'
    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}\\chromedriver_win32'

    driver = webdriver.Chrome(service=service, options=options)  # (options=chr_options)
    driver.get(url)
    driver.implicitly_wait(2)
    article = driver.find_element(By.XPATH, '//*[@id="body-content"]/div/div[2]/div[1]').get_attribute('innerHTML')
    driver.close()

    soup = BeautifulSoup(article, features="html.parser")
    allNews = soup.findAll('div', class_='col-xs-12 col-md-4')

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='caption').find('a').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='thumbnail').find('a').attrs['href']
            one_feed['published'] = '' # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='thumbnail').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='col-md-8').text
                        one_feed['summary'] = one_feed['u_summary']
                        one_feed['published'] = soup_one.find('div', class_='col-xs-4').text
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_59_rostselmash(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from selenium import webdriver
    import os, os.path
    from selenium.webdriver.common.by import By
    from bs4 import BeautifulSoup
    import pandas as pd
    import requests

    main_url = 'https://rostselmash.com'
    url = 'https://rostselmash.com/media/news/'

    df_ = get_newdf()

    OKsw = 200
    allNews = []

    abs_path = os.path.abspath(os.curdir) + '\\'
    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}\\chromedriver_win32'

    driver = webdriver.Chrome(service=service, options=options)  # (options=chr_options)
    driver.get(url)
    driver.implicitly_wait(2)
    article = driver.find_element(By.XPATH, '/html/body/div[2]/div[7]/div/div').get_attribute('innerHTML')
    driver.close()

    soup = BeautifulSoup(article, features="html.parser")
    allNews = soup.findAll('div', class_='card-news')

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='card-news__text').find('h4', class_='card-news__title').text.strip()
            one_feed['u_summary'] = e.find('div', class_='card-news__text').find('p', class_='card-news__des').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a', class_='card-news__link').attrs['href']
            one_feed['published'] = e.find('div', class_='card-news__inner').find('span', class_='card-news__label text-label text-mute').text.strip() # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='card-news__image-wrapper').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='content__user-text user-text text-default').text
                        one_feed['summary'] = one_feed['u_summary']
                        one_feed['published'] = soup_one.find('span', class_='factor__number-value').text + soup_one.find('div', class_='factor__text text-default').text
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_rss_60_gazprom(url_, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests

    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")#, "html.parser")
    summary = soup.find('div', class_='text-block').text.strip()
    page.close()
    return OK_SW, summary


def func_61_gpn(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.gazprom-neft.ru'
    url = 'https://www.gazprom-neft.ru/press-center/news/'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('article', class_='news-item news-item--short')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='news-item__body').find('span', class_='news-item__title').text
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='news-item__img').find('a', class_='news-item__link').attrs['href']
            one_feed['published'] = e.find('div', class_='details').find('time', class_='details__date').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='news-item__img').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='article__body article__body--old').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_rss_62_lukoil(url_, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests

    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")#, "html.parser")
    summary = soup.find('div', class_='content').text.strip()
    page.close()
    return OK_SW, summary


def func_63_devon(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.devongroup.ru'
    url = 'https://www.devongroup.ru'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='n-news-box')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='n-news-title').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a', class_='news-picture').attrs['href']
            one_feed['published'] = e.find('div', class_='n-news-date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('a', class_='news-picture').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='news-text-k').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_64_sintec(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.sintecgroup.ru'
    url = 'https://www.sintecgroup.ru/news/company-news/'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='news-list-item mb-2 col-12 col-lg-4')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('h6', class_='wm-news-card-title').find('a').text.strip()
            one_feed['u_summary'] = e.find('p', class_='wm-news-card-text card-text').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('h6', class_='wm-news-card-title').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='news-list-view news-list-post-params').find('span', class_='news-list-param').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='wm-news-card-img').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='news-detail-content').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_12_rnsm(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://rosneft-lubricants.ru'
    url = 'https://rosneft-lubricants.ru/about/news/'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='nMain-content')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('a', class_='nMain-title').text.strip()
            one_feed['u_summary'] = e.find('div', class_='nMain-text').find('p').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a', class_='nMain-title').attrs['href']
            one_feed['published'] = e.find('span', class_='nMain-date').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='nMain-photo nMain-photo--mob').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()

                        one_feed['u_summary'] = soup_one.find('div', class_='nSingle-content news-text').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    allNews = soup.findAll('div', class_='news-col news-col--33')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='nItem-text').find('p').text.strip()
            one_feed['u_summary'] = e.find('div', class_='nItem-descrpition').find('p').text.strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='nItem-content').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='nItem-date').text  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='nItem-image').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()

                        one_feed['u_summary'] = soup_one.find('div', class_='nSingle-content news-text').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_65_oronite(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from selenium import webdriver
    import os, os.path
    from selenium.webdriver.common.by import By
    from bs4 import BeautifulSoup
    import pandas as pd
    import requests

    main_url = 'https://www.oronite.com'
    url = 'https://www.oronite.com/about/news/default.aspx'

    df_ = get_newdf()

    OKsw = 200
    allNews = []

    abs_path = os.path.abspath(os.curdir) + '\\'
    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}\\chromedriver_win32'

    driver = webdriver.Chrome(service=service, options=options)  # (options=chr_options)
    driver.get(url)
    driver.implicitly_wait(2)
    article = driver.find_element(By.XPATH, '/html/body/main/div[1]').get_attribute('innerHTML')
    driver.close()

    soup = BeautifulSoup(article, features="html.parser")
    allNews = soup.findAll('div')

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('p').find('a').text
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('p').find('a').attrs['href']
            one_feed['published'] = e.find('h4').text # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('p').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_66_rzd(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://company.rzd.ru'
    url = 'https://company.rzd.ru/ru/9397'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('li', class_='search-results__item')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('a', class_='search-results__heading').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('a', class_='search-results__heading').attrs['href']
            one_feed['published'] = e.find('div', class_='search-results__date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = ''
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='news-card-text static-content').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


# def func_68_lada(go_deep=1, pages_cnt=1):        #НЕСТАБИЛЬНАЯ РАБОТА САЙТА
#     # https://habr.com/ru/post/544828/
#     from bs4 import BeautifulSoup
#     import requests
#     import pandas as pd
#
#     main_url = 'https://www.lada.ru'
#     url = 'https://www.lada.ru/press-releases'
#
#     df_ = get_newdf()
#
#     page = requests.get(url, timeout=REQUEST_TIMEOUT)
#     OKsw = page.status_code
#     allNews = []
#
#     soup = BeautifulSoup(page.text, features="html.parser")
#     allNews = soup.findAll('li', class_='styles_item__19Tmv')
#     page.close()
#
#     for i, e in enumerate(allNews):
#         # print(main_url+ n.find('a').attrs['href'])
#         # print(main_url+ n.find('a').find('img').attrs['src'])
#         # print(n.find('span').text)
#         # print(n.find('div', class_='date-block').text)
#         try:
#             one_feed = {}
#             one_feed['feid'] = ''
#             one_feed['fsid'] = ''
#             one_feed['u_etitle'] = e.find('div', class_='styles_titleNews__2CGKU').text.strip()
#             one_feed['u_summary'] = ''
#             one_feed['etitle'] = one_feed['u_etitle']
#             one_feed['summary'] = one_feed['u_summary']
#             one_feed['elink'] = main_url + e.find('a').attrs['href']
#             one_feed['published'] = e.find('div', class_='styles_created__39D9Y').text.strip()  # e.published if 'published' in e else f'no published {i}'
#             one_feed['elink_img'] = e.find('div', class_='styles_wrapper__3tECN').find('img').attrs['src']
#             # one_feed['score'] = -1
#             # one_feed['topic'] = ''
#             # one_feed['uname'] = ''
#             if go_deep != 0:  # обход ссылок по каждой новости
#                 try:
#                     spage = requests.get(one_feed['elink'])
#                     if spage.status_code == 200:
#                         soup_one = BeautifulSoup(spage.text, features="html.parser")
#                         spage.close()
#                         one_feed['u_summary'] = soup_one.find('div', class_='styles_description__2TPQz').text
#                         one_feed['summary'] = one_feed['u_summary']
#                         # print(s)
#                     # else:
#                     # print(one_feed['elink'])
#
#                 except:
#                     pass
#
#             df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
#         except:
#             pass
#
#     return OKsw, df_


def func_70_novatek(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd

    main_url = 'https://www.novatek.ru'
    url = 'https://www.novatek.ru/ru/press/releases/'

    df_ = get_newdf()

    page = requests.get(url, timeout=REQUEST_TIMEOUT)
    OKsw = page.status_code
    allNews = []

    soup = BeautifulSoup(page.text, features="html.parser")
    allNews = soup.findAll('div', class_='onenews w30')
    page.close()

    for i, e in enumerate(allNews):
        # print(main_url+ n.find('a').attrs['href'])
        # print(main_url+ n.find('a').find('img').attrs['src'])
        # print(n.find('span').text)
        # print(n.find('div', class_='date-block').text)
        try:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            one_feed['u_etitle'] = e.find('div', class_='text').text.strip()
            one_feed['u_summary'] = ''
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = main_url + e.find('div', class_='text').find('a').attrs['href']
            one_feed['published'] = e.find('div', class_='date').text.strip()  # e.published if 'published' in e else f'no published {i}'
            one_feed['elink_img'] = main_url + e.find('div', class_='img').find('img').attrs['src']
            # one_feed['score'] = -1
            # one_feed['topic'] = ''
            # one_feed['uname'] = ''
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    spage = requests.get(one_feed['elink'])
                    if spage.status_code == 200:
                        soup_one = BeautifulSoup(spage.text, features="html.parser")
                        spage.close()
                        one_feed['u_summary'] = soup_one.find('div', class_='text').text
                        one_feed['summary'] = one_feed['u_summary']
                        # print(s)
                    # else:
                    # print(one_feed['elink'])

                except:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass

    return OKsw, df_


def func_13gazpromneft_sm(go_deep=1, pages_cnt=1):

    main_url = 'http://www.gazpromneft-sm.ru'
    url = f'{main_url}/press-center'

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    OKsw = None
    for p in range(1, pages_cnt + 1):
        purl = f'{url}?content=news&page={p}&per-page=12'
        try:
            page = requests.get(purl, headers=headers)
            OKsw = page.status_code
            if OKsw != 200:
                continue
            soup = BeautifulSoup(page.text, features="html.parser")
            all_news = soup.find_all('div', attrs={'class': 'custom-col-4'})
            for i, news in enumerate(all_news):
                one_feed = {}
                try:
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    day, month, year = news.find(
                        'div',
                        attrs={'class': 'main-news-section__block-item-date'}
                    ).get_text().strip().split()
                    published = datetime.datetime(int(year), months.index(month, 0) + 1, int(day))
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['u_etitle'] = news.find(
                        'div',
                        attrs={'class': 'main-news-section__block-item-title'}
                    ).get_text().strip()
                    one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}/{news.a.attrs['href']}"

                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            page = requests.get(one_feed['elink'], headers=headers)
                            stp = page.status_code
                            if stp == 200:
                                soup = BeautifulSoup(page.text, features="html.parser")
                                soup = soup.find('section', attrs={'class': 'section'}).find('div', attrs={'class': 'main'})
                                one_feed['u_summary'] = soup.find('div', attrs={'class': 'text-block'}).get_text()
                                img = soup.find('img')
                                if img is not None:
                                    one_feed['elink_img'] = f"{main_url}{img.attrs['src']}"
                                one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass
                except Exception as e:
                    pass
                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_71acea_auto(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd
    # https://sites.google.com/chromium.org/driver/
    from selenium import webdriver
    # from selenium.webdriver.common.keys import Keys
    # from selenium.webdriver.support.ui import Select
    # from selenium.webdriver.common.by import By

    # from selenium.webdriver.chrome.options import Options
    # from selenium.webdriver.common.action_chains import ActionChains
    import os, os.path

    abs_path = os.path.abspath(os.curdir) + '\\'
    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://www.acea.auto'
    url = f'{main_url}/nav/?content=press-releases'
    OKsw = -200

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    driver = webdriver.Chrome(service=service, options=options)
    for p in range(1, pages_cnt + 1):
        if p > 1:
            purl = f'{url}&pageNumber={p}'
        else:
            purl = url
        try:
            driver.get(purl)
            # page = requests.get(purl)
            OKsw = 200  # page.status_code
            allNews = []
            if OKsw == 200:
                # soup = BeautifulSoup(page.text, features="html.parser")
                # page.close()
                driver.implicitly_wait(2)
                allNews = driver.find_elements_by_class_name('content-part.row')

                for i, e in enumerate(allNews):
                    a = e.find_element_by_class_name('thumb-link')
                    h = a.get_attribute('href')
                    ims = a.find_element_by_tag_name('img').get_attribute('src')
                    psd = e.find_element_by_class_name('meta-part').find_element_by_tag_name('span').text

                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''

                    tdiv = e.find_element_by_class_name('excerpt.col-md-6')
                    a2 = tdiv.find_element_by_tag_name('a')
                    t = a2.text
                    su = tdiv.text.replace(t, '').replace('READ MORE', '').replace(psd, '').replace('\n', '')

                    one_feed['u_etitle'] = t
                    one_feed['u_summary'] = su
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = h
                    one_feed['published'] = psd
                    one_feed['elink_img'] = ims  # main_url+ e.find('a').find('img').attrs['src']

                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            spage = requests.get(one_feed['elink'])
                            stp = spage.status_code
                            if stp == 200:
                                soup_one = BeautifulSoup(spage.text, features="html.parser")
                                su = ''
                                for s in soup_one.findAll('div', class_='block-container'):
                                    su += ' ' + s.text.replace('\n', '')
                                spage.close()

                        except Exception as e:
                            # print(e)
                            pass

                    if s != '':
                        one_feed['u_summary'] = su
                        one_feed['summary'] = one_feed['u_summary']

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_72mitsubishi_motors(go_deep=1, pages_cnt=1):
    # https://habr.com/ru/post/544828/
    from bs4 import BeautifulSoup
    import requests
    import pandas as pd
    import datetime
    # https://sites.google.com/chromium.org/driver/
    from selenium import webdriver
    # from selenium.webdriver.common.keys import Keys
    # from selenium.webdriver.support.ui import Select
    # from selenium.webdriver.common.by import By

    # from selenium.webdriver.chrome.options import Options
    # from selenium.webdriver.common.action_chains import ActionChains
    import os, os.path

    abs_path = os.path.abspath(os.curdir) + '\\'
    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://www.mitsubishi-motors.ru'
    url = f'{main_url}/news/'
    OKsw = -200

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    now_y = datetime.datetime.now().year

    driver = webdriver.Chrome(service=service, options=options)
    for p in range(1, pages_cnt + 1):
        if p > 1:
            purl = f'{url}year-{now_y - p + 1}/'
        else:
            purl = url
        try:
            driver.get(purl)
            # page = requests.get(purl)
            OKsw = 200  # page.status_code
            allNews = []
            if OKsw == 200:

                driver.implicitly_wait(2)
                divnews = driver.find_element_by_class_name('col-12.col-sm-12.col-md-7.pl-4')
                allNews = divnews.find_elements_by_class_name('row')

                y = divnews.find_element_by_class_name('p-2.pl-5').text[-9:-4]

                for i, e in enumerate(allNews):
                    a = e.find_element_by_class_name('news_text_inner').find_element_by_tag_name('a')
                    h = a.get_attribute('href')
                    t = a.text
                    ims = ''  # a.find_element_by_tag_name('img').get_attribute('src')
                    psd = f"{e.find_element_by_class_name('h5.pb-0').text}{y}"

                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''

                    one_feed['u_etitle'] = t
                    one_feed['u_summary'] = t
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = h
                    one_feed['published'] = psd
                    one_feed['elink_img'] = ims  # main_url+ e.find('a').find('img').attrs['src']

                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            spage = requests.get(one_feed['elink'])
                            stp = spage.status_code
                            if stp == 200:
                                su = ''
                                soup_one = BeautifulSoup(spage.text, features="html.parser")
                                psd = soup_one.find('div', class_='col-12 col-sm-9 col-md-10').attrs['content']
                                one_news = soup_one.find('div', class_='news_text_inner')
                                su = one_news.text.replace('\n', '')
                                ims = one_news.find('img')
                                if ims:
                                    ims = ims.attrs['src']
                                spage.close()

                        except Exception as e:
                            # print(e)
                            pass

                    if su != '':
                        one_feed['u_summary'] = su
                        one_feed['summary'] = one_feed['u_summary']
                    one_feed['published'] = psd
                    one_feed['elink_img'] = ims

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except:
            pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_rss_73_metal_info(url_, pages_cnt=1):
    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")
    summary = soup.find(
        'section',
        attrs={'itemprop': 'text'}
    ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')

    page.close()
    return OK_SW, summary


def func_74_one_prime(go_deep=1, pages_cnt=1):
    main_url = 'https://1prime.ru'
    url = f'{main_url}/industry_and_energy/'

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt

    purl = url
    page = requests.get(purl)
    OKsw = page.status_code
    soup = BeautifulSoup(page.text, features="html.parser")
    for p in range(1, pages_cnt + 1):
        try:
            if p > 1:
                purl = f"{main_url}{soup.find('a', attrs={'class': 'button button_inline button_rounded button_more'}).attrs['href']}"
                page.close()
                page = requests.get(purl)
                if page.status_code != 200:
                    break
                soup = BeautifulSoup(page.text, features="html.parser")

            soup_one = soup.find('div', attrs={'class': 'rubric-list__articles'})
            all_news = soup_one.find_all('article', attrs={'class': 'rubric-list__article rubric-list__article_default'})
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                one_feed['published'] = news.time.attrs.get('datetime', '')
                one_feed['u_etitle'] = news.div.h2.a.text
                one_feed['u_summary'] = one_feed['u_etitle']
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}{news.div.h2.a.attrs['href']}"
                one_feed['elink_img'] = news.div.figure.a.img.attrs['src']

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        page = requests.get(one_feed['elink'])
                        if page.status_code == 200:
                            soup_one = BeautifulSoup(page.text, features="html.parser")
                            one_feed['u_etitle'] = soup_one.find(['div', 'h1'], attrs={'class': 'article-header__title'}).text
                            one_feed['etitle'] = one_feed['u_etitle']
                            soup_one = soup_one.find('div', attrs={'class': 'article-body__content'})
                            one_feed['u_summary'] = ''.join([tag.text.strip() for tag in soup_one.find_all('p')]).strip().replace('\n', '')
                            one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True).drop_duplicates()
        except:
            pass

    return OKsw, df_


def func_75_dprom_online(go_deep=1, pages_cnt=1):
    main_url = 'https://dprom.online'
    url = f'{main_url}/mainthemes/novosti/'

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt

    OKsw = None
    for p in range(1, pages_cnt + 1):
        purl = f'{url}page/{p}/' if p > 1 else url
        try:
            page = requests.get(purl)
            OKsw = page.status_code
            if OKsw != 200:
                continue
            soup = BeautifulSoup(page.text, features="html.parser")
            soup = soup.find('div', attrs={'class': 'horizontalBar textAround news'})
            all_news = soup.find_all('a')
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                published = news.find('span', attrs={'class': 'date'})
                if published is not None:
                    one_feed['published'] = published.text.strip()
                one_feed['u_etitle'] = news.find('span', attrs={'class': 'horizontalBar__RightTitle'}).text.strip()
                one_feed['u_summary'] = news.find('span', attrs={'class': 'horizontalBar__RightText'}).text.strip()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = news.attrs['href']

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        page = requests.get(one_feed['elink'])
                        if page.status_code == 200:
                            soup = BeautifulSoup(page.text, features="html.parser")
                            one_feed['u_etitle'] = soup.h1.text.strip()
                            one_feed['etitle'] = one_feed['u_etitle']
                            one_feed['published'] = soup.find('span', attrs={'class': 'date'}).text.strip()
                            soup = soup.find('div', attrs={'class': 'single__contentLeftText'})
                            one_feed['u_summary'] = ''.join(
                                [tag.text.strip() for tag in soup.find_all('p')]).strip().replace('\n', '')
                            one_feed['summary'] = one_feed['u_summary']
                            img = soup.find('img')
                            if img is not None:
                                one_feed['elink_img'] = img.attrs['src']
                            else:
                                one_feed['elink_img'] = ''
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_76_komersant_business(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://www.kommersant.ru'
    url = f'{main_url}/rubric/4'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(3)
        for p in range(1, pages_cnt):
            try:
                button = driver.find_element(By.CLASS_NAME,
                    'js-archive-more-button')
                driver.execute_script("arguments[0].click();", button)
                driver.implicitly_wait(3)
            except Exception as e:
                pass
        OKsw = 200
        if OKsw == 200:
            all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('article', attrs={'class': 'uho rubric_lenta__item js-article'})
            driver.close()
            for news in all_news:

                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''

                one_feed['u_etitle'] = news.find('span', 'vam').text
                summery = news.find('a', attrs={'class': 'uho__link'})
                if summery is not None:
                    one_feed['u_summary'] = summery.text
                else:
                    one_feed['u_summary'] = one_feed['u_etitle']
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}" \
                                    f"{news.find('a', attrs={'class': 'uho__link uho__link--overlay'}).attrs['href']}"
                one_feed['published'] = news.find(
                    'p',
                    attrs={'class': 'uho__tag rubric_lenta__item_tag hide_mobile'}
                ).text.strip()
                img = news.find('img')
                if img is not None:
                    one_feed['elink_img'] = img.attrs['src']

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.get(one_feed['elink'])
                        driver.implicitly_wait(2)
                        soup = BeautifulSoup(driver.page_source, features="html.parser")
                        driver.close()
                        one_feed['u_etitle'] = soup.find('h1', attrs={'class': 'doc_header__name js-search-mark'}).text.strip()
                        one_feed['etitle'] = one_feed['u_etitle']
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'article_text_wrapper js-search-mark'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                        img = soup.find('img', attrs={'class': 'doc_media__media js-lazyimage-source'})
                        if img is not None:
                            one_feed['elink_img'] = img.attrs['src']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except:
        pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_77_komersant_economy(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://www.kommersant.ru'
    url = f'{main_url}/rubric/3'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(3)
        for p in range(1, pages_cnt):
            try:
                button = driver.find_element(By.CLASS_NAME,
                    'js-archive-more-button')
                driver.execute_script("arguments[0].click();", button)
                driver.implicitly_wait(3)
            except Exception as e:
                pass
        OKsw = 200
        if OKsw == 200:
            all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('article', attrs={'class': 'uho rubric_lenta__item js-article'})
            driver.close()
            for news in all_news:

                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''

                one_feed['u_etitle'] = news.find('span', 'vam').text
                summery = news.find('a', attrs={'class': 'uho__link'})
                if summery is not None:
                    one_feed['u_summary'] = summery.text
                else:
                    one_feed['u_summary'] = one_feed['u_etitle']
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}" \
                                    f"{news.find('a', attrs={'class': 'uho__link uho__link--overlay'}).attrs['href']}"
                one_feed['published'] = news.find(
                    'p',
                    attrs={'class': 'uho__tag rubric_lenta__item_tag hide_mobile'}
                ).text.strip()
                img = news.find('img')
                if img is not None:
                    one_feed['elink_img'] = img.attrs['src']

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.get(one_feed['elink'])
                        driver.implicitly_wait(2)
                        soup = BeautifulSoup(driver.page_source, features="html.parser")
                        driver.close()
                        one_feed['u_etitle'] = soup.find('h1', attrs={'class': 'doc_header__name js-search-mark'}).text.strip()
                        one_feed['etitle'] = one_feed['u_etitle']
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'article_text_wrapper js-search-mark'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                        img = soup.find('img', attrs={'class': 'doc_media__media js-lazyimage-source'})
                        if img is not None:
                            one_feed['elink_img'] = img.attrs['src']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except:
        pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_rss_78_za_rulem(url_, pages_cnt=1):
    page = requests.get(url_)
    OK_SW = page.status_code

    soup = BeautifulSoup(page.text, features="html.parser")
    summary = soup.find(
        'div',
        attrs={'id': 'inPageAd'}
    ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')

    page.close()
    return OK_SW, summary


def func_79_autonews(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://www.autonews.ru'
    url = f'{main_url}/tags/?tag=%D0%9D%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D0%B8'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(3)
        for p in range(1, pages_cnt):
            try:
                bottom = driver.find_elements(By.CLASS_NAME, 'item-big__inner')[-1]
                driver.execute_script("return arguments[0].scrollIntoView(true);", bottom)
                driver.implicitly_wait(3)
            except Exception as e:
                pass
        OKsw = 200
        if OKsw == 200:
            all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all(
                'div',
                attrs={'class': 'item-big__inner'}
            )
            driver.close()
            for news in all_news:

                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''

                one_feed['u_etitle'] = news.find(
                    'span',
                    attrs={'class': 'item-big__title js-rm-central-column-item-text'}
                ).text
                summery = news.find('div', attrs={'class': 'item-big__description'})
                if summery is not None:
                    one_feed['u_summary'] = summery.text
                else:
                    one_feed['u_summary'] = one_feed['u_etitle']
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = news.find(
                    'a',
                    attrs={'class': 'item-big__link js-rm-central-column-item-link'}
                ).attrs['href']
                one_feed['published'] = news.find(
                    'span',
                    attrs={'class': 'item-big__date'}
                ).text.strip()
                if one_feed['published'].find(':') > -1:
                    one_feed['published'] = f"{datetime.datetime.now().date()} {one_feed['published']}"
                img = news.find('img')
                if img is not None:
                    one_feed['elink_img'] = img.attrs['src']

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.get(one_feed['elink'])
                        driver.implicitly_wait(2)
                        soup = BeautifulSoup(driver.page_source, features="html.parser")
                        driver.close()
                        one_feed['u_etitle'] = soup.find('h1', attrs={'itemprop': 'headline'}).text.strip()
                        one_feed['etitle'] = one_feed['u_etitle']
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'article__text'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                        img = soup.find(
                            'div',
                            attrs={'class': 'article__main-image article__main-image_big'}
                        ).find('img')
                        if img is not None:
                            one_feed['elink_img'] = img.attrs['src']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except:
        pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_80_nvg(go_deep=1, pages_cnt=1):
    main_url = 'https://ngv.ru'
    url = f'{main_url}/news/?tag=Нефть&PAGEN_2='

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt

    OKsw = None
    for p in range(1, pages_cnt + 1):
        purl = f'{url}{p}/'
        try:
            page = requests.get(purl)
            OKsw = page.status_code
            if OKsw != 200:
                continue
            soup = BeautifulSoup(page.text, features="html.parser")
            soup = soup.find('div', attrs={'class': 'main-grid'})
            all_news = soup.find_all('div', attrs={'class': 'big-news-card'}) + soup.find_all('div', attrs={'class': 'news-card'})
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                if news.attrs['class'][0] == 'big-news-card':
                    one_feed['published'] = news.find('span', attrs={'class': 'big-news-card__date p --m'}).text.strip()
                    one_feed['u_etitle'] = news.find('a', attrs={'class': 'stretched-link'}).text.strip()
                    summary = news.find('div', attrs={'class': 'big-news-card__description --p'})
                    if summary is not None:
                        one_feed['u_summary'] = summary.text.strip()
                    else:
                        one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a', attrs={'class': 'stretched-link'}).attrs['href']}"
                    one_feed['elink_img'] = f"{main_url}{news.find('source', attrs={'type': 'image/jpeg'}).attrs['srcset']}"
                else:
                    one_feed['published'] = news.find('span', attrs={'class': 'news-card__date'}).text.strip()
                    one_feed['u_etitle'] = news.find('a', attrs={'class': 'stretched-link'}).text.strip()
                    summary = news.find('dev', attrs={'class': 'news-card__description p --m'})
                    if summary is not None:
                        one_feed['u_summary'] = summary.text.strip()
                    else:
                        one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a', attrs={'class': 'stretched-link'}).attrs['href']}"
                    one_feed['elink_img'] = f"{main_url}{news.find('source', attrs={'type': 'image/jpeg'}).attrs['srcset']}"
                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        page = requests.get(one_feed['elink'])
                        if page.status_code == 200:
                            soup = BeautifulSoup(page.text, features="html.parser")
                            one_feed['u_etitle'] = soup.find('h1', attrs={'class': 'project__title h2'}).text
                            one_feed['etitle'] = one_feed['u_etitle']
                            one_feed['u_summary'] = soup.find(
                                'div',
                                attrs={'class': 'project__wraper'}
                            ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_81_cngr(go_deep=1, pages_cnt=1):
    main_url = 'https://cnrg-oil.ru'
    url = f'{main_url}/news/?PAGEN_1='

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt

    OKsw = None
    for p in range(1, pages_cnt + 1):
        purl = f'{url}{p}/'
        try:
            page = requests.get(purl)
            OKsw = page.status_code
            if OKsw != 200:
                continue
            soup = BeautifulSoup(page.text, features="html.parser").find('div', attrs={'class': 'iblocklist'})
            all_news = soup.find_all('div', recursive=False)
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                one_feed['published'] = news.find('b').get_text().strip()
                news.find('b').decompose()
                one_feed['u_etitle'] = news.find('div', attrs={'class': 'name'}).get_text().strip()
                one_feed['u_summary'] = news.find('div', attrs={'class': 'text'}).text.strip()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"
                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        page = requests.get(one_feed['elink'])
                        if page.status_code == 200:
                            soup = BeautifulSoup(page.text, features="html.parser")
                            one_feed['u_etitle'] = soup.find('h1', attrs={'class': 'pagetitle'}).text
                            one_feed['etitle'] = one_feed['u_etitle']
                            one_feed['u_summary'] = soup.find(
                                'div',
                                attrs={'class': 'text'}
                            ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_82_mic_gsm(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://oiltest.ru'
    url = f'{main_url}/news/'

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    df_ = get_newdf()
    OKsw = None

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        driver.implicitly_wait(2)
        soup = BeautifulSoup(driver.page_source, features="html.parser").find('ul', attrs={'class': 'news_ul'})
        OKsw = 200
        driver.close()
        all_news = soup.find_all('li', recursive=False)
        for news in all_news:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            day, month, year = news.find('p', attrs={'class': 'data'}).get_text().strip().split()
            published = datetime.datetime(int(year), months.index(month, 0) + 1, int(day))
            one_feed['published'] = published.strftime(DATE_FORMAT)
            one_feed['u_etitle'] = news.find('p', attrs={'class': 'title_slider_index'}).get_text().strip()
            one_feed['u_summary'] = one_feed['u_etitle']
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
            img_link = news.attrs['style']
            img_link = re.search(r'url\(.+\)', img_link)[0][5:-1]
            one_feed['elink_img'] = f"{main_url}{img_link}"
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    driver = webdriver.Chrome(service=service, options=options)
                    driver.get(one_feed['elink'])
                    driver.implicitly_wait(2)
                    soup = BeautifulSoup(driver.page_source, features="html.parser").find(
                        'div',
                        attrs={'class': 'wrap_single'}
                    )
                    driver.close()
                    one_feed['u_etitle'] = soup.find('p', attrs={'class': 'title'}).text
                    soup.find('p', attrs={'class': 'title'}).decompose()
                    day, month, year = soup.find('p', attrs={'class': 'date_single'}).text.strip().split()
                    published = datetime.datetime(int(year), months.index(month, 0) + 1, int(day))
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    soup.find('p', attrs={'class': 'date_single'}).decompose()
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['u_summary'] = soup.get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                    one_feed['summary'] = one_feed['u_summary']
                    img = soup.find('img')
                    if img is not None:
                        one_feed['elink_img'] = f"{main_url}{img.attrs['src']}"
                except Exception as e:
                    driver.close()

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass
    try:
        driver.close()
    except Exception as e:
        pass

    return OKsw, df_


def func_83_jandex_dzen(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'
    main_url = 'https://dzen.ru'

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    df_ = get_newdf()
    OKsw = None

    for request in search_requests:
        url = f"{main_url}/news/search?issue_tld=ru&text={'+'.join(request.strip().split())}"
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            driver.implicitly_wait(2)
            driver.find_element(
                By.CLASS_NAME,
                'news-dzen-header-redesign-search__input'
            ).send_keys(request)
            button = driver.find_element(
                By.CLASS_NAME,
                'news-dzen-header-redesign-search__find-button'
            )
            driver.execute_script("arguments[0].click();", button)
            driver.implicitly_wait(3)
            sleep(0.2)
            for p in range(1, pages_cnt):
                try:
                    button = driver.find_element(By.CLASS_NAME, 'Button2')
                    driver.execute_script("arguments[0].click();", button)
                    driver.implicitly_wait(3)
                    sleep(0.2)
                except Exception as e:
                    pass
            soup = BeautifulSoup(driver.page_source, features="html.parser").find('div', attrs={'role': 'main'})
            OKsw = 200
            driver.close()
            all_news = soup.find_all('div', attrs={'class': 'news-search-story__snippet'})
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                published = news.find(
                    'span',
                    attrs={'class': 'mg-snippet-source-info__time'}
                ).get_text().strip()
                published = published.replace(
                    'вчера в', str(datetime.datetime.now().date() - datetime.timedelta(days=1))
                )
                published = published.replace(
                    'Вчера', (datetime.datetime.now().date() - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
                )
                published = published.replace(
                    'Сегодня', (datetime.datetime.now().date()).strftime('%Y-%m-%d %H:%M')
                )
                published = published.replace('Час ', '1 час')
                if published.find('назад') != -1:
                    published = (datetime.datetime.now() - datetime.timedelta(hours=int(published.split()[0]))).strftime('%Y-%m-%d %H:%M')
                if len(published) <= 5:
                    published = f"{datetime.datetime.now().date()} {published}"
                if published.split()[1] in months:
                    if len(published.split()) > 3:
                        day, month, _, time = published.split()
                    else:
                        day, month, time = published.split() + ['00:00']
                    published = f'{datetime.datetime.today().year}-{months.index(month) + 1}-{day} {time}'
                published = datetime.datetime.strptime(published, '%Y-%m-%d %H:%M')
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['u_etitle'] = news.find('div', attrs={'class': 'mg-snippet__title'}).get_text().strip()
                one_feed['u_summary'] = news.find('div', attrs={'class': 'mg-snippet__description'}).get_text().strip()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = news.parent.find('a').attrs['href']
                one_feed['elink_img'] = ''
                if go_deep != 0 and one_feed['elink'] != '':  # обход ссылок по каждой новости
                    if one_feed['elink'].find('//dzen.ru/') == -1:
                        continue
                    try:
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.get(one_feed['elink'])
                        driver.implicitly_wait(2)
                        soup = BeautifulSoup(driver.page_source, features="html.parser")
                        driver.close()
                        summary = soup.find(
                            'div',
                            attrs={'class': 'news-story-redesign__summarization'}
                        )
                        if summary is None:
                            summary = soup.find(
                                'div',
                                attrs={'class': 'mg-story-summarization'}
                            )
                        one_feed['u_summary'] = summary.get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        try:
                            driver.close()
                        except Exception as e:
                            pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass
        try:
            driver.close()
        except Exception as e:
            pass

    return OKsw, df_


def func_84_ravenol(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://blog.ravenol.ru'
    url = f'{main_url}/blog/novosti-kompanii/'

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    df_ = get_newdf()
    OKsw = None

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        driver.implicitly_wait(2)
        soup = BeautifulSoup(driver.page_source, features="html.parser").find('div', attrs={'id': 'post-stream'})
        OKsw = 200
        driver.close()
        all_news = soup.find_all('div', attrs={'itemprop': 'blogPosts'})
        for news in all_news:
            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''
            day, month, year = news.find('span').get_text().strip().split()
            published = datetime.datetime(int(year), months.index(month, 0) + 1, int(day))
            one_feed['published'] = published.strftime(DATE_FORMAT)
            one_feed['u_etitle'] = news.find('h3').get_text().strip()
            one_feed['u_summary'] = news.find('div', attrs={'class': 'text'}).get_text().strip()
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = news.find('a').attrs['href']
            one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"
            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                    if page.status_code != 200:
                        continue
                    soup = BeautifulSoup(page.text,  features="html.parser")
                    one_feed['u_summary'] = soup.find(
                        'div',
                        attrs={'class': 'text', 'itemprop': 'articleBody'}
                    ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                    one_feed['summary'] = one_feed['u_summary']
                except Exception as e:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass
    try:
        driver.close()
    except Exception as e:
        pass

    return OKsw, df_


def func_85_teboil(go_deep=1, pages_cnt=1):

    main_url = 'https://www.teboil.ru'
    url = f'{main_url}/news/'

    df_ = get_newdf()
    OKsw = None

    try:
        page = requests.get(url, timeout=REQUEST_TIMEOUT)
        OKsw = page.status_code
        if OKsw == 200:
            soup = BeautifulSoup(page.text, features="html.parser")
            all_news = soup.find_all('div', attrs={'class': ['news__item', 'news-item']})
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                published = datetime.datetime.strptime(news.find('div', attrs={'class': 'news-item__date'}).get_text(), '%d.%m.%Y')
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['u_etitle'] = news.find('h3', attrs={'class': 'news-item__title'}).get_text().strip()
                one_feed['u_summary'] = news.find('div', attrs={'class': 'news-item__text'}).get_text().strip()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}{news.find('a', attrs={'class': 'news-item__link'}).attrs['href']}"
                one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"
                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                        if page.status_code != 200:
                            continue
                        soup = BeautifulSoup(page.text,  features="html.parser")
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'news_detail__text'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass

    return OKsw, df_


def func_86_gtoil(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://gtoil.ru'
    url = 'https://gtoil.ru/news/'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(3)
        for p in range(1, pages_cnt):
            try:
                button = driver.find_element(By.CLASS_NAME, 'btn-outline-dark')
                driver.execute_script("arguments[0].click();", button)
                time.sleep(0.5)
            except Exception as e:
                pass
        OKsw = 200
        if OKsw == 200:
            all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('div', attrs={'class': 'col-md-6'})
            driver.close()
            for news in all_news:

                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''

                one_feed['u_etitle'] = news.find('h3', attrs={'class': 'f-news-card__title'}).text
                one_feed['u_summary'] = news.find('p').get_text()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}" \
                                    f"/{news.find('a', attrs={'class': 'f-news-card'}).attrs['href']}"
                published = datetime.datetime.strptime(
                    news.find('time', attrs={'class': 'f-news-card__date'}).text.strip(), '%d.%m.%Y'
                )
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        page = requests.get(one_feed['elink'], headers=headers, timeout=REQUEST_TIMEOUT)
                        if page.status_code != 200:
                            continue
                        soup = BeautifulSoup(page.text, features="html.parser")
                        one_feed['u_summary'] = ' '.join([
                            x.get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            for x in soup.find(
                                'div', attrs={'class': 'p-news-page__body'}
                            ).find(
                                'div',
                                attrs={'class': ['offset-md-1', 'col-md-10']}
                            ).find_all('p')
                        ])
                        one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except:
        pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_87_lemarc(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://lemarc.ru'
    url = 'https://lemarc.ru/news'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        driver.implicitly_wait(3)
        OKsw = 200
        all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('a', attrs={'class': 'news__item'})
        driver.close()
        for news in all_news:

            one_feed = {}
            one_feed['feid'] = ''
            one_feed['fsid'] = ''

            one_feed['u_etitle'] = news.find('h3', attrs={'class': 'news__item-title'}).get_text()
            one_feed['u_summary'] = one_feed['u_etitle']
            one_feed['etitle'] = one_feed['u_etitle']
            one_feed['summary'] = one_feed['u_summary']
            one_feed['elink'] = f"{main_url}{news.attrs['href']}"
            published = datetime.datetime.strptime(
                news.find('span', attrs={'class': 'news__item-date'}).text.strip(), '%d.%m.%Y'
            )
            one_feed['published'] = published.strftime(DATE_FORMAT)
            one_feed['elink_img'] = news.find('img').attrs['src']

            if go_deep != 0:  # обход ссылок по каждой новости
                try:
                    driver = webdriver.Chrome(service=service, options=options)
                    driver.get(one_feed['elink'])
                    driver.implicitly_wait(3)
                    soup = BeautifulSoup(driver.page_source, features="html.parser")
                    driver.close()
                    one_feed['u_summary'] = soup.find(
                        'div',
                        attrs={'class': 'new__content'}
                    ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                    one_feed['summary'] = one_feed['u_summary']
                except Exception as e:
                    pass

            df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_88_holv(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://holv-group.com'
    url = 'https://holv-group.com/news/'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    for p in range(1, pages_cnt + 1):
        purl = f'{url}?page={p}/'
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(purl)
            driver.implicitly_wait(3)
            OKsw = 200
            if OKsw == 200:
                all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('article', attrs={'class': 'post'})
                driver.close()
                for news in all_news:

                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    one_feed['u_etitle'] = news.find('h2').get_text()
                    one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}/{news.find('a').attrs['href']}"
                    day = news.find('div', attrs={'class': 'day'}).get_text()
                    month = news.find('div', attrs={'class': 'month'}).get_text()
                    year = datetime.datetime.today().year
                    published = datetime.datetime.strptime(f"{day}.{month}.{year}", '%d.%b.%Y')
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['elink_img'] = f"{main_url}/{news.find('img').attrs['src']}"

                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            driver = webdriver.Chrome(service=service, options=options)
                            driver.get(one_feed['elink'])
                            driver.implicitly_wait(3)
                            soup = BeautifulSoup(driver.page_source, features="html.parser")
                            driver.close()
                            one_feed['u_summary'] = soup.find(
                                'div',
                                attrs={'class': 'blog-body'}
                            ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_89_nordoil(go_deep=1, pages_cnt=1):

    main_url = 'https://nord-oil.com'
    url = 'https://nord-oil.com/news/'

    df_ = get_newdf()
    OKsw = None
    for p in range(1, pages_cnt + 1):
        purl = f'{url}?PAGEN_1={p}'

        try:
            page = requests.get(purl, timeout=REQUEST_TIMEOUT)
            OKsw = page.status_code
            if OKsw == 200:
                soup = BeautifulSoup(page.text, features="html.parser")
                all_news = soup.find_all('div', attrs={'class': 'news-list__item'})
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    published = datetime.datetime.strptime(news.find(
                        'span',
                        attrs={'class': 'news-preview-element__date'}
                    ).get_text().strip(), '%d\%m\%Y')
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['u_etitle'] = news.find('div', attrs={'class': 'news-preview-element__title'}).get_text().strip()
                    one_feed['u_summary'] = news.find('div', attrs={'class': 'news-preview-element__text'}).get_text().strip()
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"
                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                            if page.status_code != 200:
                                continue
                            soup = BeautifulSoup(page.text,  features="html.parser")
                            one_feed['u_summary'] = soup.find(
                                'div',
                                attrs={'class': 'news-element__text'}
                            ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_90_seagull(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://seagull-acg.com'
    url = 'https://seagull-acg.com/stati/'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        driver.implicitly_wait(3)
        OKsw = 200
        if OKsw == 200:
            all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('div', attrs={'class': 'news-item'})
            driver.close()
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                one_feed['u_etitle'] = news.find('b').get_text()
                one_feed['u_summary'] = one_feed['u_etitle']
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                published = datetime.datetime.strptime(
                    news.find('span', attrs={'class': 'news-date-time'}).get_text(),
                    '%d.%m.%Y'
                )
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"

                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.get(one_feed['elink'])
                        driver.implicitly_wait(3)
                        soup = BeautifulSoup(driver.page_source, features="html.parser")
                        driver.close()
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'news-detail'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_91_enoc(go_deep=1, pages_cnt=1):

    main_url = 'https://www.enoc-lub.ru'
    url = 'https://www.enoc-lub.ru/news/'

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    df_ = get_newdf()
    OKsw = None
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    try:
        page = requests.get(url, timeout=REQUEST_TIMEOUT)
        OKsw = page.status_code
        if OKsw == 200:
            soup = BeautifulSoup(page.text, features="html.parser")
            all_news = soup.find_all('div', attrs={'class': 'module-news-list__item'})
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                day, month, year, _ = news.find(
                    'div',
                    attrs={'class': 'module-news-list__date'}
                ).get_text().strip().split()
                published = datetime.datetime(int(year), months.index(month, 0) + 1, int(day))
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['u_etitle'] = news.find('div', attrs={'class': 'module-news-list__title'}).get_text().strip()
                one_feed['u_summary'] = news.find('div', attrs={'class': 'module-news-list__text'}).get_text().strip()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                one_feed['elink_img'] = f"{main_url}{news.find('picture').find('img').attrs['data-src']}"
                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                        if page.status_code != 200:
                            continue
                        soup = BeautifulSoup(page.text,  features="html.parser")
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'module-news-detail__text'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass

    return OKsw, df_


def func_92_vitex(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://vitex.mobi'
    url = 'https://vitex.mobi/novosti/'

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    for p in range(1, pages_cnt + 1):
        purl = f'{url}page/{p}/'
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(purl)
            driver.implicitly_wait(3)
            OKsw = 200
            if OKsw == 200:
                all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('div', attrs={'class': 'item'})
                driver.close()
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    one_feed['u_etitle'] = news.find(
                        'div',
                        attrs={'class': 'data'}
                    ).find(
                        'a',
                        attrs={'class': False, 'style': True}
                    ).get_text().strip()
                    one_feed['u_summary'] = news.find('div', attrs={'class': 'body'}).get_text().strip()
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = news.find('a').attrs['href']
                    day, month, year = news.find('div', attrs={'class': 'date'}).get_text().strip().split()
                    published = datetime.datetime(int(year), months.index(month, 0) + 1, int(day))
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['elink_img'] = news.find('img').attrs['src']

                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            driver = webdriver.Chrome(service=service, options=options)
                            driver.get(one_feed['elink'])
                            driver.implicitly_wait(3)
                            soup = BeautifulSoup(driver.page_source, features="html.parser")
                            driver.close()
                            one_feed['u_summary'] = soup.find(
                                'div',
                                attrs={'class': 'simple_page_data'}
                            ).find(
                                'div',
                                attrs={'class': 'wr'}
                            ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_93_fuchs(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://www.fuchs-oil.ru'
    url = 'https://www.fuchs-oil.ru/news/novosti/'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    for p in range(1, pages_cnt + 1):
        purl = f'{url}page-{p}/'
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(purl)
            driver.implicitly_wait(3)
            OKsw = 200
            if OKsw == 200:
                all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('div', attrs={'class': 'article'})
                driver.close()
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    one_feed['u_etitle'] = news.find('span', attrs={'class': 'article__title'}).get_text().strip()
                    one_feed['u_summary'] = news.find('span', attrs={'class': 'article__summary'}).get_text().strip()
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    published = datetime.datetime.strptime(
                        news.find('span', attrs={'class': 'news__item-meta'}).get_text().strip(),
                        '%d.%m.%Y'
                    )
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    img = news.find('img')
                    if img is not None:
                        one_feed['elink_img'] = f"{main_url}{img.attrs['src']}"
                    else:
                        one_feed['elink_img'] = ''

                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            driver = webdriver.Chrome(service=service, options=options)
                            driver.get(one_feed['elink'])
                            driver.implicitly_wait(3)
                            soup = BeautifulSoup(driver.page_source, features="html.parser").find('div', attrs={'class': 'content__inner'})
                            driver.close()
                            soup.find('h1').decompose()
                            soup.find('link').decompose()
                            soup.find('div', attrs={'class': 'bx-breadcrumb'}).decompose()
                            summary = soup.get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['u_summary'] = summary[0:summary.find('Еще почитать')]
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_94_kirel(go_deep=1, pages_cnt=1):

    main_url = 'https://kirei-chemical.ru'
    url = 'https://kirei-chemical.ru/novosti/'

    df_ = get_newdf()
    OKsw = None
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    try:
        page = requests.get(url, timeout=REQUEST_TIMEOUT)
        OKsw = page.status_code
        if OKsw == 200:
            soup = BeautifulSoup(page.text, features="html.parser")
            all_news = soup.find_all('div', attrs={'class': 'news-lastlist'})
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                published = datetime.datetime.strptime(news.find('time').get_text().strip(), '%d.%m.%Y')
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['u_etitle'] = news.find('div', attrs={'class': 'name'}).get_text().strip()
                one_feed['u_summary'] = news.find('div', attrs={'class': 'desc'}).get_text().strip()
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"
                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                        if page.status_code != 200:
                            continue
                        soup = BeautifulSoup(page.text,  features="html.parser")
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'class': 'textLayer'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass

    return OKsw, df_


def func_95_opnmz(go_deep=1, pages_cnt=1):

    main_url = 'https://opnmz.ru'
    url = 'https://opnmz.ru/media/'

    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

    df_ = get_newdf()
    OKsw = None
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    for p in range(1, pages_cnt + 1):
        purl = f'{url}?PAGEN_1={p}'

        try:
            page = requests.get(purl, timeout=REQUEST_TIMEOUT)
            OKsw = page.status_code
            if OKsw == 200:
                soup = BeautifulSoup(page.text, features="html.parser")
                soup.find('div', attrs={'class': 'bx-pagination'}).decompose()
                all_news = soup.find('div', attrs={'class': 'news'}).find_all('a')
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    day, month, year = news.find('span', attrs={'class': 'news-item__date'}).get_text().strip().split()
                    published = datetime.datetime(int(year), months.index(month, 0) + 1, int(day))
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['u_etitle'] = news.find('span', attrs={'class': 'news-item__title'}).get_text().strip()
                    one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.attrs['href']}"
                    one_feed['elink_img'] = main_url + news.find(
                        'span',
                        attrs={'class': 'news-item__img'}
                    ).attrs['style'].replace('background-image: url(', '').replace(');', '')
                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                            if page.status_code != 200:
                                continue
                            soup = BeautifulSoup(page.text, features="html.parser")
                            one_feed['u_summary'] = soup.find(
                                'div',
                                attrs={'class': 'news-detail'}
                            ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_96_sbk(go_deep=1, pages_cnt=1):

    main_url = 'https://chemie.ru'
    url = 'https://chemie.ru/news/'

    df_ = get_newdf()
    OKsw = None
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    for p in range(1, pages_cnt + 1):
        purl = f'{url}?PAGEN_1={p}'

        try:
            page = requests.get(purl, timeout=REQUEST_TIMEOUT)
            OKsw = page.status_code
            if OKsw == 200:
                soup = BeautifulSoup(page.text, features="html.parser")
                all_news = soup.find_all('div', attrs={'class': 'front-news-item'})
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    published = datetime.datetime.strptime(news.find(
                        'span',
                        attrs={'class': 'front-news-item__date'}
                    ).text.strip(), '%d.%m.%Y')
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['u_etitle'] = news.find('a').get_text().strip()
                    one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                            if page.status_code != 200:
                                continue
                            soup = BeautifulSoup(page.text, features="html.parser").find('div', attrs={'class': 'news-detail'})
                            soup.find('span', attrs={'class': 'news-date-time'}).decompose()
                            soup.find('h3').decompose()
                            one_feed['u_summary'] = soup.get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                            img = soup.find('img')
                            if img is not None:
                                one_feed['elink_img'] = f"{main_url}{img.attrs['src']}"
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_97_neochemical(go_deep=1, pages_cnt=1):

    main_url = 'https://neochemical.ru'
    url = 'https://neochemical.ru/press-tsentr/novosti/'

    df_ = get_newdf()
    OKsw = None
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    for p in range(1, pages_cnt + 1):
        purl = f'{url}?PAGEN_1={p}'

        try:
            page = requests.get(purl, timeout=REQUEST_TIMEOUT)
            OKsw = page.status_code
            if OKsw == 200:
                soup = BeautifulSoup(page.text, features="html.parser").find('div', attrs={'class': 'news_inner'})
                all_news = soup.find_all('div', attrs={'class': 'in'})
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    published = datetime.datetime.strptime(news.find('div', attrs={'class': 'date'}).text.strip(), '%d.%m.%Y')
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['u_etitle'] = news.find('a').get_text().strip()
                    one_feed['u_summary'] = one_feed['u_etitle']
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                            if page.status_code != 200:
                                continue
                            soup = BeautifulSoup(page.text, features="html.parser").find('div', attrs={'class': 'content'})
                            one_feed['u_summary'] = soup.find('div', attrs={'class': 'text-with-pic'}).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                            img = soup.find('img')
                            if img is not None:
                                one_feed['elink_img'] = f"{main_url}{img.attrs['src']}"
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_98_fuchs_news(go_deep=1, pages_cnt=1):

    main_url = 'https://www.fuchs-oil.ru'
    url = 'https://www.fuchs-oil.ru/news/novosti/'

    df_ = get_newdf()
    OKsw = None
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    for p in range(1, pages_cnt + 1):
        purl = f'{url}page-{p}/'

        try:
            page = requests.get(purl, timeout=REQUEST_TIMEOUT)
            OKsw = page.status_code
            if OKsw == 200:
                soup = BeautifulSoup(page.text, features="html.parser").find('div', attrs={'class': 'articles__inner'})
                all_news = soup.find_all('div', attrs={'class': 'article'})
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    published = datetime.datetime.strptime(news.find('span', attrs={'class': 'news__item-meta'}).text.strip(), '%d.%m.%Y')
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['u_etitle'] = news.find(
                        'span',
                        attrs={'class': 'article__title'}
                    ).get_text().strip()
                    one_feed['u_summary'] = news.find(
                        'span',
                        attrs={'class': 'article__summary'}
                    ).get_text().strip()
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"
                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                            if page.status_code != 200:
                                continue
                            soup = BeautifulSoup(page.text, features="html.parser").find('div', attrs={'class': 'content__inner'})
                            soup.find('h1').decompose()
                            try:
                                soup.find('div', attrs={'class': 'articles'}).decompose()
                            except Exception as e:
                                pass
                            one_feed['u_summary'] = soup.get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '').replace('Еще почитать', '')
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_99_fuchs_press(go_deep=1, pages_cnt=1):

    main_url = 'https://www.fuchs-oil.ru'
    url = 'https://www.fuchs-oil.ru/news/press_relizy/'

    df_ = get_newdf()
    OKsw = None
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    for p in range(1, pages_cnt + 1):
        purl = f'{url}page-{p}/'

        try:
            page = requests.get(purl, timeout=REQUEST_TIMEOUT)
            OKsw = page.status_code
            if OKsw == 200:
                soup = BeautifulSoup(page.text, features="html.parser").find('div', attrs={'class': 'articles__inner'})
                all_news = soup.find_all('div', attrs={'class': 'article'})
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    published = datetime.datetime.strptime(news.find('span', attrs={'class': 'news__item-meta'}).text.strip(), '%d.%m.%Y')
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['u_etitle'] = news.find(
                        'span',
                        attrs={'class': 'article__title'}
                    ).get_text().strip()
                    one_feed['u_summary'] = news.find(
                        'span',
                        attrs={'class': 'article__summary'}
                    ).get_text().strip()
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    one_feed['elink_img'] = f"{main_url}{news.find('img').attrs['src']}"
                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            page = requests.get(one_feed['elink'], timeout=REQUEST_TIMEOUT)
                            if page.status_code != 200:
                                continue
                            soup = BeautifulSoup(page.text, features="html.parser").find('div', attrs={'class': 'content__inner'})
                            soup.find('h1').decompose()
                            try:
                                soup.find('div', attrs={'class': 'articles'}).decompose()
                            except Exception as e:
                                pass
                            one_feed['u_summary'] = soup.get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '').replace('Еще почитать', '')
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
        except Exception as e:
            pass

    return OKsw, df_


def func_100_exsoil(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://exsoil.com'
    url = 'https://exsoil.com/news'
    OKsw = None

    df_ = get_newdf()
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        driver.implicitly_wait(3)
        OKsw = 200
        if OKsw == 200:
            all_news = BeautifulSoup(driver.page_source, features="html.parser").find_all('li', attrs={
                'class': 'js-feed-post'}
            )
            driver.close()
            for news in all_news:
                one_feed = {}
                one_feed['feid'] = ''
                one_feed['fsid'] = ''
                one_feed['u_etitle'] = news.find('div', attrs={'class': 'js-feed-post-title'}).get_text()
                summery = news.find('div', attrs={'class': 'js-feed-post-descr'})
                if summery is not None:
                    one_feed['u_summary'] = summery.get_text()
                else:
                    one_feed['u_summary'] = one_feed['u_etitle']
                one_feed['etitle'] = one_feed['u_etitle']
                one_feed['summary'] = one_feed['u_summary']
                one_feed['elink'] = news.find('div', attrs={'class': 'js-feed-post-title'}).find('a').attrs['href']
                published = datetime.datetime.strptime(
                    news.find('span', attrs={'class': 'js-feed-post-date'}).get_text(),
                    '%d.%m.%Y'
                )
                one_feed['published'] = published.strftime(DATE_FORMAT)
                one_feed['elink_img'] = news.find('div', attrs={'class': 'js-feed-post-image'}).attrs['data-original']
                if go_deep != 0:  # обход ссылок по каждой новости
                    try:
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.get(one_feed['elink'])
                        driver.implicitly_wait(3)
                        soup = BeautifulSoup(driver.page_source, features="html.parser")
                        driver.close()
                        one_feed['u_summary'] = soup.find(
                            'div',
                            attrs={'id': 'feed-text'}
                        ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                        one_feed['summary'] = one_feed['u_summary']
                    except Exception as e:
                        pass

                df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
    except Exception as e:
        pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_


def func_101_additech(go_deep=1, pages_cnt=1):

    os.environ['PATH'] = os.getenv('PATH') + f';{os.path.dirname(os.path.abspath(os.curdir))}'  # \\chromedriver_win32'

    main_url = 'https://additech.by'
    url = 'https://additech.by/index.php/ru/press-tsentr/novosti'

    df_ = get_newdf()
    OKsw = None
    pages_cnt = 10 if pages_cnt == 0 else pages_cnt  # берём 10 страниц если пришел 0 в параметре

    count = 0
    for p in range(1, pages_cnt + 1):
        purl = f'{url}?start={count}'

        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(purl)
            driver.implicitly_wait(3)
            OKsw = 200
            if OKsw == 200:
                soup = BeautifulSoup(driver.page_source, features="html.parser").find('div', attrs={'class': 'article-list'})
                driver.close()
                all_news = soup.find_all('div', attrs={'class': 'article'})
                for news in all_news:
                    one_feed = {}
                    one_feed['feid'] = ''
                    one_feed['fsid'] = ''
                    published = datetime.datetime.strptime(news.find('time').attrs['datetime'], '%Y-%m-%dT%H:%M:%S%z')
                    one_feed['published'] = published.strftime(DATE_FORMAT)
                    one_feed['u_etitle'] = news.find('div', attrs={'class': 'article-header'}).get_text().strip()
                    one_feed['u_summary'] = news.find('div', attrs={'class': 'article-introtext'}).get_text().strip()
                    one_feed['etitle'] = one_feed['u_etitle']
                    one_feed['summary'] = one_feed['u_summary']
                    one_feed['elink'] = f"{main_url}{news.find('a').attrs['href']}"
                    img = news.find('img')
                    if img is not None:
                        one_feed['elink_img'] = f"{main_url}{img.attrs['src']}"
                    if go_deep != 0:  # обход ссылок по каждой новости
                        try:
                            driver = webdriver.Chrome(service=service, options=options)
                            driver.get(one_feed['elink'])
                            driver.implicitly_wait(3)
                            soup = BeautifulSoup(driver.page_source, features="html.parser")
                            driver.close()
                            one_feed['u_summary'] = soup.find(
                                'div',
                                attrs={'itemprop': 'articleBody'}
                            ).get_text(' ', strip=True).replace('\r', '').replace('\n', '').replace('\t', '')
                            one_feed['summary'] = one_feed['u_summary']
                        except Exception as e:
                            pass

                    df_ = pd.concat([df_, pd.DataFrame([one_feed])], ignore_index=True)
                count += len(all_news)
        except Exception as e:
            pass
    try:
        driver.close()
    except:
        pass

    return OKsw, df_

if __name__ == '__main__':
    print(func_101_additech(pages_cnt=3))
