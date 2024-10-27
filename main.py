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
            row = f.readline().rstrip('\n\r').lower().split(';')
            kw_count = len(list(filter(lambda x: x.lower().find('key') > -1, row)))
            sw_count = len(list(filter(lambda x: x.lower().find('stop') > -1, row)))
            try:
                filter_index = row.index('rules_filter')
                filters = list(map(
                    lambda x: x[len('filter') + 1:],
                    filter(lambda x: x.find('filter') == 0, row[filter_index + 1:])
                ))
                theme_dict = {"filters": filters}
            except ValueError:
                filter_index = None
                filters = []
            row = f.readline().lower().rstrip('\n\r').split(';')
            while len(row) > 2:
                index = 3
                rule = 1 if row[2] == '1' else 0
                kw = list(filter(lambda x: len(x) > 0, row[index:index + kw_count]))
                index += kw_count
                sw = list(filter(lambda x: len(x) > 0, row[index:index + sw_count]))
                if filter_index is not None:
                    filter_rule = row[filter_index]
                    filter_values = row[filter_index + 1: filter_index + 1 + len(filters)]
                else:
                    filter_rule = None
                    filter_values = []
                if row[1] in theme_dict:
                    theme_dict[row[1]].append({
                        "kw": kw, "sw": sw, "rule": rule, "filter_rule": filter_rule, "filter_values": filter_values
                    })
                else:
                    theme_dict.update({row[1]: [{
                        "kw": kw, "sw": sw, "rule": rule, "filter_rule": filter_rule, "filter_values": filter_values
                    }]})
                row = f.readline().lower().rstrip('\n\r').split(';')
        result.append(theme_dict)
    return result


def is_class_test(row, words, text_field_name, filters=None):
    key = []
    stop = []
    result = False
    if filters is None:
        filters = []
    for pattern in words:
        result_local = False
        local_stop = False
        filter_match_counter = 0
        for i, filter_col in enumerate(filters):
            if row[filter_col].lower() == pattern['filter_values'][i]:
                filter_match_counter += 1
        if pattern['filter_rule'] == '1' and filter_match_counter != len(filters):
            continue
        if pattern['filter_rule'] == '0' and filter_match_counter == 0 and len(filters) > 0:
            continue
        for sw in pattern['sw']:
            match = re.findall(sw, row[text_field_name])
            if match:
                stop.extend(match)
                local_stop = True
        kw_counter = 0
        for kw in pattern['kw']:
            match = re.findall(kw, row[text_field_name])
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


def row_classification(row, text_field_name, theme_dict):
    themes = []
    key_words = []
    stop_words = []
    filters = theme_dict.get('filters', None)
    for theme, words in theme_dict.items():
        if theme == 'filters':
            continue
        flag, key, stop = is_class_test(row, words, text_field_name, filters)
        if flag:
            themes.append(theme)
        key_words.append(key)
        stop_words.append(stop)
    return pd.Series([', '.join(themes), '|'.join(key_words), '|'.join(stop_words)])


def classify_csv(file_name, text_field_name, theme_dict_list):
    df = pd.read_csv(file_name, delimiter=';', encoding='utf-8')
    df.columns = map(str.lower, df.columns)
    df = clean(df, text_field_name)
    i = 1
    for theme_dict in theme_dict_list:
        df[[f'theme{i}', f'keys{i}', f'stop{i}']] = df.apply(
            lambda row: row_classification(row, text_field_name, theme_dict),
            axis=1
        )
        i += 1
    df.drop_duplicates()
    df.to_csv(file_name, sep=';', encoding='utf-8', index=False)


def classify_xlsx(file_name, text_field_name, theme_dict_list):
    df = pd.read_excel(file_name)
    df.columns = map(str.lower, df.columns)
    df = clean(df, text_field_name)
    i = 1
    for theme_dict in theme_dict_list:
        df[[f'theme{i}', f'keys{i}', f'stop{i}']] = df.apply(
            lambda row: row_classification(row, text_field_name, theme_dict),
            axis=1
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
        classify_csv(conf.get('FILE_NAME', ''), conf.get('TEXT_FIELD_NAME', 'u_summary').lower(), theme_dict_list)
    elif conf.get('FILE_NAME', '').split('.')[-1] == 'xlsx':
        classify_xlsx(conf.get('FILE_NAME', ''), conf.get('TEXT_FIELD_NAME', 'u_summary').lower(), theme_dict_list)
    else:
        raise Exception('неподдерживаемое расширение файла')

