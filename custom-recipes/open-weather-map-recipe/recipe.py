from dataiku.customrecipe import (get_input_names_for_role, get_output_names_for_role,
                                  get_plugin_config, get_recipe_config)
from dataiku import Dataset
from openweathermap_utils import OpenWeatherMapAPI, CacheHandler
import openweathermap_utils.utils as utils
from datetime import datetime
import pandas as pd
import constants


def load_cache_config(config):
    plugin_config = get_plugin_config()
    recipe_config = get_recipe_config()
    
    config.cache_location = utils.get_cache_location_from_configs(
        cache_location=plugin_config.get("cache_location"),
        default=plugin_config.get("cache_location_custom", "")
    )

    config.cache_size = plugin_config.get("cache_size", 1000) * 1000
    config.cache_policy = plugin_config.get("cache_policy", "least-recently-stored")
    config.cache_enabled = recipe_config.get("cache_enabled") and config.cache_location


def load_recipe_config(config):
    recipe_config = get_recipe_config()
    preset_config = recipe_config.get("preset_config")

    config.latitude_column_name = recipe_config.get("latitude_column")
    config.longitude_column_name = recipe_config.get("longitude_column")

    config.date_mode = recipe_config.get("date_mode")
    if config.date_mode == "current":
        config.date = datetime.now()
    config.date_column_name = recipe_config.get("date_column", None)

    config.units = preset_config.get("units") if recipe_config.get("units") == "default" else recipe_config.get("units")
    config.lang = preset_config.get("lang") if recipe_config.get("lang") == "default" else recipe_config.get("lang")

    config.parse_output = recipe_config.get("parse_output", True)


def load_api_key(config):
    recipe_config = get_recipe_config()
    preset_config = recipe_config.get("preset_config")

    config.api_key = preset_config.get("api_key")

    if not config.api_key:
        raise ValueError("An OpenWeatherMap API key in mandatory to use the plugin. Please set one in a preset.")


def load_input_output(config):
    if not get_input_names_for_role("input_dataset"):
        raise ValueError("No input dataset.")
    input_dataset_name = get_input_names_for_role("input_dataset")[0]
    config.input_dataset = Dataset(input_dataset_name)

    output_dataset_name = get_output_names_for_role("output_dataset")[0]
    config.output_dataset = Dataset(output_dataset_name)


@utils.log_func(txt="config retrieval")
def load_config():
    config = utils.AttributeDict()

    load_cache_config(config)
    load_input_output(config)
    load_api_key(config)
    load_recipe_config(config)

    return config


@utils.log_func(txt="data recuperation")
def build_output_df(open_weather_map_API, config, row_processor):
    input_df = config.input_dataset.get_dataframe()
    weather_df = pd.DataFrame(list(input_df.apply(
        row_processor,
        axis=1,
        loc_configs=config,
        owm_func=open_weather_map_API.get_any_dt_weather_data,
        parse_output=config.parse_output,
        units=config.units,
        lang=config.lang
    )))
    output_df = pd.concat([input_df, weather_df], axis=1)
    utils.make_column_names_unique(output_df)
    utils.info_msg(f"API calls #: {open_weather_map_API.api_calls_nb}")
    return output_df


@utils.log_func(txt="OpenWeatherMap recipe")
def run():
    def process_row(row, loc_configs, owm_func, parse_output=True, **kwargs):
        if loc_configs.date_mode == "current":
            dt = loc_configs.date
        else:
            dt = row[loc_configs.date_column_name].to_pydatetime()
        lat, lon = row[loc_configs.latitude_column_name], row[loc_configs.longitude_column_name]
        output = owm_func(lat, lon, dt, **kwargs)
        return output if parse_output else {constants.UNPARSED_COL_NAME: output}

    config = load_config()

    # Creating a fake or real cache depending on user's choice
    with CacheHandler(config.cache_location, enabled=config.cache_enabled,
                      size_limit=config.cache_size, eviction_policy=config.cache_policy) as cache:
        openWeatherMapAPI = OpenWeatherMapAPI(config.api_key, cache)

        output_df = build_output_df(openWeatherMapAPI, config, process_row)
        config.output_dataset.write_with_schema(output_df)
        utils.update_columns_descriptor(config.output_dataset, config.units, config.lang)


run()
