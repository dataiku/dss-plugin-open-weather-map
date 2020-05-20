from dataiku.connector import Connector
from openweathermap_utils import OpenWeatherMapAPI, CacheHandler
import os


class OpenWeatherMapConnector(Connector):

    def __init__(self, config, plugin_config):
        Connector.__init__(self, config, plugin_config)

        preset_config = self.config.get("preset_config")

        self.api_key = str(preset_config.get("api_key"))
        self.latitude = str(self.config.get("latitude"))
        self.longitude = str(self.config.get("longitude"))
        self.granularity = str(self.config.get("granularity"))

        self.data_type = str(self.config.get("data_type"))
        self.units = preset_config.get("units") if self.config.get("units") == 'default' else self.config.get("units")
        self.lang = preset_config.get("lang") if self.config.get("lang") == 'default' else self.config.get("lang")

        cache_location = self.plugin_config.get('cache_location')
        if cache_location == 'original':
            self.cache_location = os.environ["DIP_HOME"] + f'/caches/plugins/openweathermap'
        else:
            self.cache_location = self.plugin_config.get('cache_location_custom', '')

        self.cache_enabled = self.config.get("cache_enabled")
        self.cache_size = self.plugin_config.get('cache_size', 1000) * 1000
        self.cache_policy = str(self.plugin_config.get("cache_policy"))

        with CacheHandler(cache_location, enabled=self.cache_enabled,
                          size_limit=self.cache_size, eviction_policy=self.cache_policy) as cache:
            self.weather_api = OpenWeatherMapAPI(self.api_key, cache)

    def get_read_schema(self):
        return self.weather_api.retrieve_schema(self.data_type, self.granularity)

    def generate_rows(self, dataset_schema=None, dataset_partitioning=None,
                      partition_id=None, records_limit=-1):
        return self.weather_api.get_weather_data_gen(
            lat=self.latitude,
            lon=self.longitude,
            granularity=self.granularity,
            data_type=self.data_type,
            units=self.units,
            lang=self.lang
        )
