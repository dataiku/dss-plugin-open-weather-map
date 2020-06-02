import requests
import logging
from itertools import chain
import os
from openweathermap_utils.utils import (datetime_to_timestamp, flatten_dict, cast_field, requests_error_handler,
                                        floor_time, timestamp_to_datetime, datetime_to_str)
from datetime import datetime, timedelta
from exceptions import OpenWeatherMapAPIError
from constants import COL_TYPES

logger = logging.getLogger(__name__)


class OpenWeatherMapAPI:
    def __init__(self, api_key, cache):
        self.api_key = api_key
        self.base_url = 'https://api.openweathermap.org/data/2.5/'
        self.datetime_schema = '%Y-%m-%d'
        self.available_columns = COL_TYPES
        self.cache = cache
        self.api_calls_nb = 0

    def _get_query(self, endpoint, params):
        """
        Realises an HTTP GET query on the endpoint using Requests library.
        :param endpoint: Endpoint to query
        :param params: Querystring parameters
        :return: Response body as a dict if successful else raise an exception
        """
        params['appid'] = self.api_key
        url = os.path.join(self.base_url, endpoint)
        r = requests.get(url, params=params)

        # verification of the status code
        if r.status_code != 200:
            logger.info(f"Error in request (status code: {r.status_code})")
            logger.info(f"Response: {r.text}")
            r.raise_for_status()
        return r.json()

    def _one_call(self, lat, lon, date=None, **kwargs):
        """
        Queries OneCall service of OpenWeatherMap API
        :param lat: Latitude of the location you want the weather of
        :param lon: Longitude of the location you want the weather of
        :param date: Date you want the weather of
        :param kwargs: Other params to pass to _get_query()
        :return: Weather data of desired location for the desired date
        """
        endpoint = 'onecall'
        params = {
            'lat': lat,
            'lon': lon,
        }
        if date:
            params['dt'] = datetime_to_timestamp(date)
            endpoint += '/timemachine'
        self.api_calls_nb += 1
        return self._get_query(endpoint, dict(params, **kwargs))

    def _format_output(self, output, lat, lon, data_type, granularity, error_msg=''):
        """
        Format the data before sending them to a dataset
        :param output: The data before formatting (as a dict)
        :param lat: Latitude of the location
        :param lon: Longitude of the location
        :param data_type: Whether to format for historical or forecast data
        :param granularity: Desired granularity between 'hourly' and 'daily'
        :param error_msg: If there have been an error in the retrieval, write here the error message
        :return: The output formatted as wanted
        """
        columns = self._retrieve_columns_type(data_type, granularity)
        formatted_output = dict(
            output,
            output_geopoint='POINT({} {})'.format(str(lon), str(lat)),
            data_type=data_type.capitalize(),
            granularity=granularity.capitalize(),
            error=error_msg)
        formatted_output = flatten_dict(formatted_output)
        formatted_output = {k: cast_field(v, columns.get(k, 'string')) for k, v in formatted_output.items()}
        return formatted_output

    @requests_error_handler
    def _get_forecast_weather_data(self, lat, lon, granularity=None, **kwargs):
        weather_data = self._one_call(lat, lon, **kwargs)
        return weather_data.get(granularity) if granularity else weather_data

    @requests_error_handler
    def _get_historical_weather_data(self, lat, lon, date, granularity=None, **kwargs):
        cache_key = self._get_cache_key(lat=lat, lon=lon, date=date, data_type='historical', **kwargs)
        try:
            weather_data = self.cache[cache_key]
        except KeyError as err:
            weather_data = self._one_call(lat, lon, date, **kwargs)
            self.cache[cache_key] = weather_data

        if granularity:
            return [weather_data.get('current')] if granularity == 'daily' else weather_data.get('hourly')
        return weather_data

    @requests_error_handler
    def _find_date_in_weather_list(self, weather_list, date, granularity, data_type):
        """
        From a list of dicts, find the weather as close as possible fron the desired date
        :param weather_list: List of dicts. Each dicts represents weather for a specific day or hour
        :param date: The date you want to match the weather on
        :param granularity: 'hourly' or 'daily'
        :param data_type: 'historical'or 'forecast'
        :return: The dict corresponding to the closest date
        """
        for weather_item in weather_list:
            if not weather_item: break
            dt_floorer = lambda x: floor_time(x, 'day' if granularity == 'daily' else 'hour')
            owm_dt = datetime_to_timestamp(dt_floorer(timestamp_to_datetime(weather_item['dt'])))
            if owm_dt == datetime_to_timestamp(dt_floorer(date)):
                return [weather_item]
        raise OpenWeatherMapAPIError(
            status_code=400,
            text='{{"cod":"404", "message":"{} weather for date {} not found"}}'.format(
                data_type.capitalize(),
                datetime_to_str(date, self.datetime_schema)
            ))

    def _retrieve_columns_type(self, data_type, granularity):
        """
        Get the schema of the output dataset according to the data_type and granularity
        """
        if data_type == 'all':
            historical_columns = dict(
                self.available_columns['historical']['all'], **self.available_columns['historical'][granularity]
            )
            forecast_columns = dict(
                self.available_columns['forecast']['all'], **self.available_columns['forecast'][granularity]
            )
            return dict(self.available_columns['all'], **dict(
                historical_columns, **forecast_columns
            ))
        return dict(self.available_columns['all'], **dict(
                self.available_columns[data_type]['all'], **self.available_columns[data_type][granularity]
        ))

    def _is_hourly_forecast_available(self, date):
        return date < datetime.today() + timedelta(hours=47)

    def _get_cache_key(self, **kwargs):
        return kwargs

    def get_forecast_dt_weather_data(self, lat, lon, date, **kwargs):
        weather_data, error = self._get_forecast_weather_data(lat, lon, **kwargs)
        granularity = 'hourly' if self._is_hourly_forecast_available(date) else 'daily'
        res, error2 = self._find_date_in_weather_list(weather_data.get(granularity), date, granularity, 'forecast')
        return self._format_output(res[0], lat, lon, 'forecast', granularity, error.text if error else error2.text)

    def get_historical_dt_weather_data(self, lat, lon, date, **kwargs):
        weather_data, error = self._get_historical_weather_data(lat, lon, date, 'daily', **kwargs)
        return self._format_output(weather_data[0], lat, lon, 'historical', 'daily', error.text)

    def get_any_dt_weather_data(self, lat, lon, date, **kwargs):
        if date < datetime.today():
            return self.get_historical_dt_weather_data(lat, lon, date, **kwargs)
        return self.get_forecast_dt_weather_data(lat, lon, date, **kwargs)

    def get_forecast_weather_data_gen(self, lat, lon, granularity, **kwargs):
        weather_data, error = self._get_forecast_weather_data(lat, lon, granularity, **kwargs)
        return (self._format_output(d, lat, lon, 'forecast', granularity, error.text) for d in weather_data)

    def get_historical_weather_data_gen(self, lat, lon, granularity, limit_days=5, **kwargs):
        today = floor_time(datetime.today(), 'day').replace(hour=12)
        days_before = 1
        while days_before <= limit_days:
            date = today - timedelta(days=days_before)
            weather_data, error = self._get_historical_weather_data(lat, lon, date, granularity, **kwargs)
            if error.status_code == 400: break
            for d in weather_data:
                yield self._format_output(d, lat, lon, 'historical', granularity, error.text)
            days_before += 1

    def get_weather_data_gen(self, lat, lon, granularity, data_type, **kwargs):
        gens = []
        if data_type in ('historical', 'all'):
            gens.append(self.get_historical_weather_data_gen(lat, lon, granularity, **kwargs))
        if data_type in ('forecast', 'all'):
            gens.append(self.get_forecast_weather_data_gen(lat, lon, granularity, **kwargs))
        return chain(*gens)

    def retrieve_schema(self, data_type, granularity):
        return {'columns': [{'name': k, 'type': v} for k, v in self._retrieve_columns_type(data_type, granularity).items()]}
