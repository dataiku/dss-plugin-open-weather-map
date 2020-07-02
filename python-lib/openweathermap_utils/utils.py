import logging
from datetime import datetime, timedelta, timezone
import pandas as pd
from exceptions import OpenWeatherMapAPIError
from requests import HTTPError
import pwd
import constants
import os


logger = logging.getLogger(__name__)


def floor_time(dt=None, round_to="day"):
    """
    Floors the time to closest previous "round_to". If round_to = "day", it return the day without time information
    :param dt: Input datetime to floor
    :param round_to: Granularity you want to floor on (day, hour, minute...)
    :return: New time floored
    """
    datetime_els = ["year", "month", "day", "hour", "minute", "second", "microsecond"]
    if not round_to in datetime_els:
        raise KeyError(f"Error in flooring dt: You have to choose a value between these: {datetime_els}")
    rt_index = datetime_els.index(round_to)
    return dt.replace(**{k: 0 if rt_index + i > 1 else 1 for i, k in enumerate(datetime_els[rt_index + 1:])})


def datetime_to_timestamp(dt):
    return int(dt.timestamp())


def timestamp_to_datetime(ts):
    return datetime.fromtimestamp(int(ts))


def datetime_to_str(dt, formatter="%Y-%m-%d"):
    return dt.strftime(formatter)


def str_to_datetime(date_str, formatter="%Y-%m-%d"):
    return datetime.strptime(date_str, formatter)


def make_column_names_unique(df):
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [
            dup + "_" + str(i) if i != 0 else dup for i in range(sum(cols == dup))
        ]
    df.columns = cols


def flatten_dict_rec(el, names, new_dict):
    if not el:
        new_dict[".".join(names)] = ""
    if isinstance(el, dict):
        for k, v in el.items():
            flatten_dict_rec(v, names + [str(k)], new_dict)
    elif isinstance(el, list):
        for i, e in enumerate(el):
            flatten_dict_rec(e, names + [str(i)], new_dict)
    else:
        new_dict[".".join(names)] = el


def flatten_dict(d):
    new_dict = {}
    flatten_dict_rec(d, [], new_dict)
    return new_dict


def get_cache_location_from_configs(cache_location, default):
    home_dir = pwd.getpwuid(os.getuid()).pw_dir
    # Only solution to get user $HOME directory (getpass.getuser()
    # doesn't work). We cannot write in the data_dir because of
    # the implementation of MUS instances where permission problems
    # could happen.
    if cache_location == "original":
        return os.path.join(home_dir, constants.CACHE_RELATIVE_DIR)
    elif cache_location == "none":
        return ""
    return default


def requests_error_handler(function):
    """
    Raises an exception or ignore it according to the type of error.
    :param function: Function decorated
    :return: (data, error) if error ignore else raises an Exception. If there is no error, the second argument is empty
    """
    def wrapper(*args, **kwargs):
        try:
            res = function(*args, **kwargs)
            return res, OpenWeatherMapAPIError(status_code=200, text="")
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


def log_sep():
    return "\n{}\n".format("".center(constants.LOG_SEPARATOR_LEN, constants.LOG_SEPARATOR_CHAR))


def log_txt(txt):
    output_txt = "\n"
    output_txt += log_sep()
    output_txt += txt
    output_txt += log_sep()
    return output_txt


def debug_func(function):
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as err:
            logger.debug(log_txt("LOCAL VARIABLES"))
            logger.debug(locals())
            logger.debug(log_sep())
            raise err
    return wrapper


def cast_field(value, type_):
    if not value:
        return value
    if type_ == "date":
        return timestamp_to_datetime(value).isoformat() + "Z"
    if type_ == "float":
        return float(value)
    if type_ == "int":
        return int(value)
    if type_ == "boolean":
        return value in ["true", True, "T", 1, "Vrai", "V", "1", "True"]
    return str(value)


def dbg_msg(msg, title=""):
    logger.debug(log_txt(" DEBUG MESSAGE: {} ".format(title)))
    logger.debug(msg)
    logger.debug(log_sep())


def info_msg(msg):
    logger.info(log_txt(msg))


def update_columns_descriptor(dataset, unit_system, lang):
    dataset_schema = dataset.read_schema()
    for col_info in dataset_schema:
        col_name = ".".join(list(filter(lambda x: not x.isdigit(), col_info.get("name").split("."))))
        col_info["comment"] = constants.COL_DESCRIPTORS.get(col_name, "").format(
            unit_system=constants.UNITS_LABEL[unit_system],
            lang=constants.LANG_LABEL[lang]
        )
    dataset.write_schema(dataset_schema)


def log_func(txt):
    def inner(f):
        def wrapper(*args, **kwargs):
            info_msg("Starting {} ({})".format(txt, datetime.now().strftime("%H:%M:%S")))
            res = f(*args, **kwargs)
            info_msg("Ending {} ({})".format(txt, datetime.now().strftime("%H:%M:%S")))
            return res
        return wrapper
    return inner


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__