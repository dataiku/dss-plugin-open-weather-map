from datetime import datetime, timedelta, timezone
from dataiku.customrecipe import *
import dataiku
import pandas as pd
from exceptions import OpenWeatherMapAPIError
from requests import HTTPError


def round_time(dt=None, dateDelta=timedelta(minutes=1)):
    round_to = dateDelta.total_seconds()
    if not dt:
        dt = datetime.now()
    seconds = (dt - dt.min).seconds
    rounding = (seconds + round_to / 2) // round_to * round_to
    return dt + timedelta(0, rounding - seconds, -dt.microsecond)


def datetime_to_timestamp(dt):
    return int(dt.replace(tzinfo=timezone.utc).timestamp())


def timestamp_to_datetime(ts):
    return datetime.fromtimestamp(int(ts))


def datetime_to_str(dt, formatter="%Y-%m-%d"):
    return dt.strftime(formatter)


def str_to_datetime(date_str, formatter="%Y-%m-%d"):
    return datetime.strptime(date_str, formatter)


def get_input_output():
    if len(get_input_names_for_role('input_dataset')) == 0:
        raise ValueError('No input dataset.')
    input_dataset_name = get_input_names_for_role('input_dataset')[0]
    input_dataset = dataiku.Dataset(input_dataset_name)
    output_dataset_name = get_output_names_for_role('output_dataset')[0]
    output_dataset = dataiku.Dataset(output_dataset_name)
    return input_dataset, output_dataset


def make_column_names_unique(df):
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [
            dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))
        ]
    df.columns = cols


def flatten_dict_rec(el, names, new_dict):
    if not el:
        new_dict['.'.join(names)] = ''
    if isinstance(el, dict):
        for k, v in el.items():
            flatten_dict_rec(v, names+[str(k)], new_dict)
    elif isinstance(el, list):
        for i, e in enumerate(el):
            flatten_dict_rec(e, names+[str(i)], new_dict)
    else:
        new_dict['.'.join(names)] = el


def flatten_dict(d):
    new_dict = {}
    flatten_dict_rec(d, [], new_dict)
    return new_dict


def requests_error_handler(function):
    def wrapper(*args, **kwargs):
        try:
            res = function(*args, **kwargs)
            return res, OpenWeatherMapAPIError(status_code=200, text='')
        except OpenWeatherMapAPIError as owm_error:
            return [{}], owm_error
        except HTTPError as http_error:
            owm_error = OpenWeatherMapAPIError(
                http_error.response.text,
                status_code=int(http_error.response.status_code),
                text=http_error.response.text
            )
            if owm_error.status_code == 401:
                raise owm_error
            return [{}], owm_error
        except Exception as err:
            raise err
    return wrapper


def debug_func(function):
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as err:
            print('################################ LOCAL VARIABLES #################################################')
            print(locals())
            print('##################################################################################################')
            raise err
    return wrapper


def cast_field(value, type_):
    if not value:
        return value
    if type_ == 'date':
        return timestamp_to_datetime(value).isoformat() + 'Z'
    if type_ == 'float':
        return float(value)
    if type_ == 'int':
        return int(value)
    if type_ == 'boolean':
        return value in ['true', True, 'T', 1, 'Vrai', 'V']
    return str(value)


def dbg_msg(msg):
    print('######################################### DEBUG MESSAGE ##################################################')
    print(msg)
    print('##########################################################################################################')
