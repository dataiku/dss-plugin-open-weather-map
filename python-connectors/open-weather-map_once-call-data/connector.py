from dataiku.connector import Connector
from openweathermap_utils import OpenWeatherMapAPI, CacheHandler


class OpenWeatherMapConnector(Connector):

    def __init__(self, config, plugin_config):
        Connector.__init__(self, config, plugin_config)

        preset_config = self.config.get("preset_config")
        self.api_key = str(self.plugin_config.get("preset_config").get("api_key"))
        self.latitude = str(self.config.get("latitude"))
        self.longitude = str(self.config.get("longitude"))
        self.data_type = str(self.config.get("data_type"))
        self.granularity = str(self.config.get("granularity"))
        self.units = preset_config.get("units") if self.config.get("units") == 'default' else self.config.get("units")
        self.lang = preset_config.get("lang") if self.config.get("lang") == 'default' else self.config.get("lang")

        self.weather_api = OpenWeatherMapAPI(self.api_key, CacheHandler(enabled=False))

    def get_read_schema(self):
        return self.weather_api.retrieve_schema(self.data_type, self.granularity)

    def generate_rows(self, dataset_schema=None, dataset_partitioning=None,
                      partition_id=None, records_limit=-1):
        return self.weather_api.get_forecast_weather_data_gen(
            lat=self.latitude,
            lon=self.longitude,
            granularity=self.granularity,
            units=self.units,
            lang=self.lang
        ) if self.data_type == 'forecast' else self.weather_api.get_historical_weather_data_gen(
            lat=self.latitude,
            lon=self.longitude,
            granularity=self.granularity,
            units=self.units,
            lang=self.lang
        )
