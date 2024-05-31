import os.path
import re
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
import nltk
import datetime
import pymorphy3


CONFIG_DIR = './config'
FILE_NAME = 'frequency_analysis'
SHEET_NAME = 'sheet'

nltk.download('stopwords')


def get_text(file_name, column_name):
    if file_name.split('.')[-1] == 'csv':
        df = pd.read_csv(file_name, delimiter=';', encoding='utf-8')
    elif conf.get('FILE_NAME', '').split('.')[-1] == 'xlsx':
        df = pd.read_excel(file_name)
    else:
        raise Exception('неподдерживаемое расширение файла')
    text = ' '.join(list(df[column_name]))
    return clean(text)


def split_capital(match):
    if match.group() is not None:
        return f"{match.group(1)} {match.group(2)}{match.group(3)}"


def clean(text):
    text = re.sub(r'<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});', '', text)
    text = re.sub(r'([\.,_\'"!?\\\(\):;])', ' ', text)
    text = re.sub(r'([0-9а-яa-z])(A-ZА-Я)([0-9а-яa-z])', split_capital, text)
    text = re.sub(r'(\s)(\d{1,2}|\w)(\s)', ' ', text)
    text = re.sub(r'--+', ' ', text)
    text = re.sub(r'\s+', ' ', text).lower()
    text = ' ' + text.replace('ё', 'е') + ' '
    redundant_words = stopwords.words("russian") + stopwords.words("english")
    try:
        with open(f'{CONFIG_DIR}/redundant_words.txt', 'r', encoding='utf-8') as f:
            redundant_words.extend([word.strip() for word in f.read().split('\n')])
    except Exception as e:
        pass
    for sw in redundant_words:
        text = re.sub(fr"\s{sw}\s({sw}\s)*", ' ', text)
    return text


def freq_analysis(text, config):
    model = CountVectorizer(
        analyzer='word',
        ngram_range=(1, int(config.get('MAX_WORD_COUNT', 1))),
        token_pattern=r"(?u)\b\w+-?\w+\b"
    )
    if int(config.get('MAX_WORD_COUNT', 1)) == 1:
        morph = pymorphy3.MorphAnalyzer()
        text = ' '.join(list(map(lambda word: morph.parse(word)[0].normal_form, text.split())))
    x = model.fit_transform([text])
    names = model.get_feature_names_out()
    fr = x.toarray()[0]
    return list(sorted(
        filter(
            lambda el: el[1] >= int(config.get('MIN_FREQUENCY', 1)),
            zip(names, fr)
        ),
        key=lambda el: el[1], reverse=True)
    )


def export_excel(df):
    curfolder = os.path.abspath(os.getcwd())
    df.to_excel(
        f"{curfolder}\export\{FILE_NAME}_{datetime.datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
        sheet_name=SHEET_NAME, index=False
    )


def read_config(file_name):
    config = {}
    with open(file_name, 'r', encoding='utf-8') as f:
        conf_line = f.readline().rstrip('\n\r').split(';')
        while len(conf_line) > 1:
            config.update({conf_line[0]: conf_line[1]})
            conf_line = f.readline().rstrip('\n\r').split(';')
    return config


if __name__ == '__main__':
    conf = read_config(f'{CONFIG_DIR}/config.csv')
    with open(conf.get('FILE_NAME', ''), encoding='utf-8') as f:
        pass
    text = get_text(conf.get('FILE_NAME', 'ppn.csv'), conf.get('TEXT_FIELD_NAME', 'ppn'))
    fr = freq_analysis(text, conf)
    df = pd.DataFrame(fr, columns=['words', 'count'])
    export_excel(df)
