import re
import pandas as pd
import os.path


CONFIG_DIR = './config'


def load_theme_dict():
    result = []
    files = list(filter(lambda file: bool(re.search(r'theme.*\.csv', file)) > 0, os.listdir(CONFIG_DIR)))
    files.sort()
    for file in files:
        theme_dict = {}
        with open(f'{CONFIG_DIR}/{file}', 'r', newline='', encoding='utf-8') as f:
            row = f.readline().split(';')
            kw_count = len(list(filter(lambda x: x.lower().find('key') > -1, row)))
            sw_count = len(list(filter(lambda x: x.lower().find('stop') > -1, row)))
            row = f.readline().lower().rstrip('\n\r').split(';')
            while len(row) > 2:
                index = 3
                rule = 1 if row[2] == '1' else 0
                kw = list(filter(lambda x: len(x) > 0, row[index:index + kw_count]))
                index += kw_count
                sw = list(filter(lambda x: len(x) > 0, row[index:index + sw_count]))
                if row[1] in theme_dict:
                    theme_dict[row[1]].append({"kw": kw, "sw": sw, "rule": rule})
                else:
                    theme_dict.update({row[1]: [{"kw": kw, "sw": sw, "rule": rule}]})
                row = f.readline().lower().rstrip('\n\r').split(';')
        result.append(theme_dict)
    return result


def is_class_test(text, words):
    key = []
    stop = []
    result = False
    for pattern in words:
        result_local = False
        local_stop = False
        for sw in pattern['sw']:
            match = re.findall(sw, text)
            if match:
                stop.extend(match)
                local_stop = True
        kw_counter = 0
        for kw in pattern['kw']:
            match = re.findall(kw, text)
            if match:
                kw_counter += 1
                key.extend(match)
        if not local_stop and kw_counter > 0:
            result_local = True
            if pattern['rule'] == 1:
                if len(pattern['kw']) != kw_counter:
                    result_local = False
        result = result_local or result
    return result, ', '.join(key), ', '.join(stop)


def row_classification(text, theme_dict):
    themes = []
    key_words = []
    stop_words = []
    for theme, words in theme_dict.items():
        flag, key, stop = is_class_test(text, words)
        if flag:
            themes.append(theme)
        key_words.append(key)
        stop_words.append(stop)
    return pd.Series([', '.join(themes), '|'.join(key_words), '|'.join(stop_words)])


def classify_csv(file_name, text_field_name, theme_dict_list):
    df = pd.read_csv(file_name, delimiter=';', encoding='utf-8')
    df = clean(df, text_field_name)
    i = 1
    for theme_dict in theme_dict_list:
        df[[f'theme{i}', f'keys{i}', f'stop{i}']] = df[text_field_name].apply(
            lambda row: row_classification(str(row).lower(), theme_dict)
        )
        i += 1
    df.drop_duplicates()
    df.to_csv(file_name, sep=';', encoding='utf-8', index=False)


def classify_xlsx(file_name, text_field_name, theme_dict_list):
    df = pd.read_excel(file_name)
    df = clean(df, text_field_name)
    i = 1
    for theme_dict in theme_dict_list:
        df[[f'theme{i}', f'key{i}', f'stop{i}']] = df[text_field_name].apply(
            lambda row: row_classification(str(row).lower(), theme_dict)
        )
        i += 1
    df.drop_duplicates()
    df.to_excel(file_name, index=False)


def clean(df, col):
    '''Чистит теги и другой мусор'''
    cleanr = re.compile(r'<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleans = re.compile(r'\s+')
    df[col] = df[col].replace(cleanr, ' ', regex=True)
    df[col] = df[col].replace(cleans, ' ', regex=True)
    return df


if __name__ == '__main__':
    theme_dict_list = load_theme_dict()
    conf = {}
    with open(f'{CONFIG_DIR}/config.csv', 'r', encoding='utf-8') as f:
        conf_line = f.readline().rstrip('\n\r').split(';')
        while len(conf_line) > 1:
            conf.update({conf_line[0]: conf_line[1]})
            conf_line = f.readline().rstrip('\n\r').split(';')
    with open(conf.get('FILE_NAME', ''), encoding='utf-8') as f:
        pass
    if conf.get('FILE_NAME', '').split('.')[-1] == 'csv':
        classify_csv(conf.get('FILE_NAME', ''), conf.get('TEXT_FIELD_NAME', 'u_summary'), theme_dict_list)
    elif conf.get('FILE_NAME', '').split('.')[-1] == 'xlsx':
        classify_xlsx(conf.get('FILE_NAME', ''), conf.get('TEXT_FIELD_NAME', 'u_summary'), theme_dict_list)
    else:
        raise Exception('неподдерживаемое расширение файла')

