import logging
from openweathermap_utils import OpenWeatherMapAPI, CacheHandler
from openweathermap_utils.utils import (get_plugin_config, get_recipe_config, get_cache_location_from_configs,
                                        get_input_output, make_column_names_unique, update_columns_descriptor)
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def get_configs():
    configs = {}
    plugin_configs = get_plugin_config()
    recipe_configs = get_recipe_config()
    preset_configs = recipe_configs.get('preset_config')

    configs['cache_location'] = get_cache_location_from_configs(
        cache_location=plugin_configs.get('cache_location'),
        default=plugin_configs.get('cache_location_custom', '')
    )

    configs['cache_size'] = plugin_configs.get('cache_size', 1000) * 1000
    configs['cache_policy'] = plugin_configs.get('cache_policy', 'least-recently-stored')
    configs['cache_enabled'] = recipe_configs.get('cache_enabled') and configs['cache_location']

    configs['input_dataset'], configs['output_dataset'] = get_input_output()
    configs['api_key'] = preset_configs.get('api_key')

    if not configs['api_key']:
        raise ValueError("An OpenWeatherMap API key in mandatory to use the plugin. Please set one in a preset.")

    configs['latitude_column_name'] = recipe_configs.get('latitude_column')
    configs['longitude_column_name'] = recipe_configs.get('longitude_column')

    configs['date_mode'] = recipe_configs.get('date_mode')
    if configs['date_mode'] == 'current':
        configs['date'] = datetime.now()
    configs['date_column_name'] = recipe_configs.get('date_column', None)

    configs['units'] = preset_configs.get('units') if recipe_configs.get('units') == 'default' else recipe_configs.get('units')
    configs['lang'] = preset_configs.get('lang') if recipe_configs.get("lang") == 'default' else recipe_configs.get('lang')

    configs['parse_output'] = recipe_configs.get('parse_output', True)

    return configs

def main():
    def process_row(row, loc_configs, owm_func, parse_output=True, **kwargs):
        if configs['date_mode'] == 'current':
            dt = configs['date']
        else:
            dt = row[loc_configs.get('date_column_name')].to_pydatetime()
        lat, lon = row[loc_configs.get('latitude_column_name')], row[loc_configs.get('longitude_column_name')]
        output = owm_func(lat, lon, dt, **kwargs)
        return output if parse_output else {'unparsed_weather': output}

    configs = get_configs()

    # Creating a fake or real cache depending on user's choice
    with CacheHandler(configs.get('cache_location'), enabled=configs.get('cache_enabled'),
                      size_limit=configs.get('cache_size'), eviction_policy=configs.get('cache_policy')) as cache:
        openWeatherMapAPI = OpenWeatherMapAPI(configs.get('api_key'), cache)

        logger.info('--- OpenWeatherMAp Recipe - Data recuperation. ---')
        input_df = configs.get('input_dataset').get_dataframe()
        weather_df = pd.DataFrame(list(input_df.apply(
            process_row,
            axis=1,
            loc_configs=configs,
            owm_func=openWeatherMapAPI.get_any_dt_weather_data,
            parse_output=configs.get('parse_output'),
            units=configs.get('units'),
            lang=configs.get('lang')
        )))
        output_df = pd.concat([input_df, weather_df], axis=1)
        make_column_names_unique(output_df)
        logger.info(
            f'--- OpenWeatherMAp Recipe - End of data recuperation. API calls #: {openWeatherMapAPI.api_calls_nb} ---'
        )
        configs.get('output_dataset').write_with_schema(output_df)
        update_columns_descriptor(configs.get('output_dataset'), configs['units'], configs['lang'])


main()
