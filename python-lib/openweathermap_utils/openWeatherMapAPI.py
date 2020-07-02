import requests
import logging
from itertools import chain
import os
import openweathermap_utils.utils as utils
from datetime import datetime, timedelta
from exceptions import OpenWeatherMapAPIError
from constants import DataType, Granularity
import constants

logger = logging.getLogger(__name__)


class OpenWeatherMapAPI:
    def __init__(self, api_key, cache):
        self.api_key = api_key
        self.api_version = "2.5"
        self.base_url = f"https://api.openweathermap.org/data/{self.api_version}/"
        self.datetime_schema = "%Y-%m-%d"
        self.available_columns = constants.COL_TYPES
        self.cache = cache
        self.api_calls_nb = 0

    def _get_query(self, endpoint, params):
        """
        Performs an HTTP GET query on the endpoint using Requests library.
        :param endpoint: Endpoint to query
        :param params: Querystring parameters
        :return: Response body as a dict if successful else raise an exception
        """
        params["appid"] = self.api_key
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
        endpoint = "onecall"
        params = {
            "lat": lat,
            "lon": lon,
        }
        if date:
            params["dt"] = utils.datetime_to_timestamp(date)
            endpoint += "/timemachine"
        self.api_calls_nb += 1
        return self._get_query(endpoint, dict(params, **kwargs))

    def _format_output(self, output, lat, lon, data_type, granularity, error_msg=""):
        """
        Format the data before sending them to a dataset
        :param output: The data before formatting (as a dict)
        :param lat: Latitude of the location
        :param lon: Longitude of the location
        :param data_type: Whether to format for historical or forecast data
        :param granularity: Desired granularity between "hourly" and "daily"
        :param error_msg: If there have been an error in the retrieval, write here the error message
        :return: The output formatted as wanted
        """
        columns = self._retrieve_columns_type(data_type, granularity)
        formatted_output = dict(
            output,
            output_geopoint="POINT({} {})".format(str(lon), str(lat)),
            data_type=data_type.capitalize(),
            granularity=granularity.capitalize(),
            error=error_msg)
        formatted_output = utils.flatten_dict(formatted_output)
        formatted_output = {k: utils.cast_field(v, columns.get(k, "string")) for k, v in formatted_output.items()}
        return formatted_output

    @utils.requests_error_handler
    def _get_forecast_weather_data(self, lat, lon, granularity=None, **kwargs):
        weather_data = self._one_call(lat, lon, **kwargs)
        return weather_data.get(granularity) if granularity else weather_data

    @utils.requests_error_handler
    def _get_historical_weather_data(self, lat, lon, date, granularity=None, **kwargs):
        cache_key = self._get_cache_key(lat=lat, lon=lon, date=date, data_type=DataType.HISTORICAL.value, **kwargs)
        try:
            weather_data = self.cache[cache_key]
        except KeyError as err:
            weather_data = self._one_call(lat, lon, date, **kwargs)
            self.cache[cache_key] = weather_data

        if granularity:
            return [weather_data.get("current")] if granularity == Granularity.DAILY.value \
                else weather_data.get(Granularity.HOURLY.value)
        return weather_data

    @utils.requests_error_handler
    def _find_date_in_weather_list(self, weather_list, date, granularity, data_type):
        """
        From a list of dicts, find the weather as close as possible fron the desired date
        :param weather_list: List of dicts. Each dicts represents weather for a specific day or hour
        :param date: The date you want to match the weather on
        :param granularity: "hourly" or "daily"
        :param data_type: "historical"or "forecast"
        :return: The dict corresponding to the closest date
        """
        for weather_item in weather_list:
            if not weather_item: break
            dt_floorer = lambda x: utils.floor_time(x, "day" if granularity == Granularity.DAILY.value else "hour")
            owm_dt = utils.datetime_to_timestamp(dt_floorer(utils.timestamp_to_datetime(weather_item["dt"])))
            if owm_dt == utils.datetime_to_timestamp(dt_floorer(date)):
                return [weather_item]
        raise OpenWeatherMapAPIError(
            status_code=400,
            text='{{"cod":"404", "message":"{} weather for date {} not found"}}'.format(
                data_type.capitalize(),
                utils.datetime_to_str(date, self.datetime_schema)
            ))

    def _retrieve_columns_type(self, data_type, granularity):
        """
        Get the schema of the output dataset according to the data_type and granularity
        """
        if data_type == "all":
            historical_columns = dict(
                self.available_columns[DataType.HISTORICAL.value][DataType.ALL.value],
                **self.available_columns[DataType.HISTORICAL.value][granularity]
            )
            forecast_columns = dict(
                self.available_columns[DataType.FORECAST.value][DataType.ALL.value],
                **self.available_columns[DataType.FORECAST.value][granularity]
            )
            return dict(self.available_columns[DataType.ALL.value], **dict(
                historical_columns, **forecast_columns
            ))
        return dict(self.available_columns[DataType.ALL.value], **dict(
            self.available_columns[data_type][DataType.ALL.value], **self.available_columns[data_type][granularity]
        ))

    def _is_hourly_forecast_available(self, date):
        return date < datetime.today() + timedelta(hours=constants.NB_HOURS_MAX_FORECAST)

    def _is_forecast_available(self, date):
        return date < datetime.today() + timedelta(days=constants.NB_DAYS_MAX_FORECAST)

    def _is_historical_available(self, date):
        return date > datetime.today() - timedelta(days=constants.NB_DAYS_MAX_HISTORICAL)

    def _get_cache_key(self, **kwargs):
        return kwargs

    def get_forecast_dt_weather_data(self, lat, lon, date, **kwargs):
        weather_data, error = self._get_forecast_weather_data(lat, lon, **kwargs)
        granularity = Granularity.HOURLY.value if self._is_hourly_forecast_available(date) else Granularity.DAILY.value
        res, error2 = self._find_date_in_weather_list(
            weather_data.get(granularity, {}), date, granularity, DataType.FORECAST.value)
        return self._format_output(
            res[0], lat, lon, DataType.FORECAST.value, granularity, error.text if error.text else error2.text)

    def get_historical_dt_weather_data(self, lat, lon, date, **kwargs):
        weather_data, error = self._get_historical_weather_data(lat, lon, date, Granularity.DAILY.value, **kwargs)
        return self._format_output(weather_data[0], lat, lon, DataType.HISTORICAL.value, Granularity.DAILY.value, error.text)

    def get_any_dt_weather_data(self, lat, lon, date, **kwargs):
        if date < datetime.today():
            return self.get_historical_dt_weather_data(lat, lon, date, **kwargs)
        return self.get_forecast_dt_weather_data(lat, lon, date, **kwargs)

    def get_forecast_weather_data_gen(self, lat, lon, granularity, parse_output=True, **kwargs):
        weather_data, error = self._get_forecast_weather_data(lat, lon, granularity, **kwargs)
        for d in weather_data:
            weather_output = self._format_output(d, lat, lon, DataType.FORECAST.value, granularity, error.text)
            yield weather_output if parse_output else {constants.UNPARSED_COL_NAME: weather_output}

    def get_historical_weather_data_gen(self, lat, lon, granularity, limit_days=5, parse_output=True, **kwargs):
        today = utils.floor_time(datetime.today(), "day").replace(hour=12)
        days_before = 1
        while days_before <= limit_days:
            date = today - timedelta(days=days_before)
            weather_data, error = self._get_historical_weather_data(lat, lon, date, granularity, **kwargs)
            if error.status_code == 400: break
            for d in weather_data:
                weather_output = self._format_output(d, lat, lon, DataType.HISTORICAL.value, granularity, error.text)
                yield weather_output if parse_output else {constants.UNPARSED_COL_NAME: weather_output}
            days_before += 1

    def get_weather_data_gen(self, lat, lon, granularity, data_type, **kwargs):
        gens = []
        if data_type in (DataType.HISTORICAL.value, DataType.ALL.value):
            gens.append(self.get_historical_weather_data_gen(lat, lon, granularity, **kwargs))
        if data_type in (DataType.FORECAST.value.value, DataType.ALL.value):
            gens.append(self.get_forecast_weather_data_gen(lat, lon, granularity, **kwargs))
        return chain(*gens)

    def retrieve_schema(self, data_type, granularity):
        return {
            "columns": [{"name": k, "type": v} for k, v in self._retrieve_columns_type(data_type, granularity).items()]}
