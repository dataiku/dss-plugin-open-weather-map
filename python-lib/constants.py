from enum import Enum

COL_TYPES = {
    'all': {
        'dt': 'date',
        'pressure': 'float',
        'humidity': 'float',
        'dew_point': 'float',
        'clouds': 'float',
        'visibility': 'float',
        'wind_speed': 'float',
        'wind_gust': 'float',
        'wind_deg': 'float',
        'output_geopoint': 'string',
        'error': 'string'
    },
    'forecast': {
        'all': {},
        'daily': {
            'sunrise': 'date',
            'sunset': 'date',
            'temp.morn': 'float',
            'temp.day': 'float',
            'temp.eve': 'float',
            'temp.night': 'float',
            'temp.min': 'float',
            'temp.max': 'float',
            'feels_like.morn': 'float',
            'feels_like.day': 'float',
            'feels_like.eve': 'float',
            'feels_like.night': 'float',
            'uvi': 'float',
            'rain': 'float',
            'snow': 'float',
        },
        'hourly': {
            'feels_like': 'float',
            'temp': 'float',
            'rain.1h': 'float',
            'rain.3h': 'float',
            'snow.1h': 'float',
            'snow.3h': 'float',
        },

    },
    'historical': {
        'all': {
            'feels_like': 'float',
            'temp': 'float',
            'sunrise': 'date',
            'sunset': 'date'
        },
        'daily': {
            'uvi': 'float',
            'rain': 'float',
            'snow': 'float',
        },
        'hourly': {
            'rain.1h': 'float',
            'rain.3h': 'float',
            'snow.1h': 'float',
            'snow.3h': 'float',
        },
    },
}

COL_DESCRIPTORS = {
    'dt': 'Weather datetime (UTC)',
    'pressure': 'Atmospheric pressure on the sea level (in unit_system[pressure])',
    'humidity': 'Humidity (in %)',
    'dew_point': 'Temperature below which dew can form (in {unit_system[temp]})',
    'clouds': 'Cloudiness (in %)',
    'uvi': 'UV index',
    'visibility': 'Average visibility (in meters)',
    'wind_speed': 'Wind speed (in {unit_system[speed]})',
    'wind_gust': 'Wind gust (in {unit_system[speed]})',
    'wind_deg': 'Wind direction (in degrees)',
    'output_geopoint': 'Desired location (POINT(lon, lat))',
    'error': 'Error message if any',
    'sunrise': 'Sunrise time (UTC)',
    'sunset': 'Sunset time (UTC)',
    'temp': 'Temperature (in {unit_system[temp]})',
    'temp.morn': 'Morning temperature (in {unit_system[temp]})',
    'temp.day': 'Day temperature (in {unit_system[temp]})',
    'temp.eve': 'Evening temperature (in {unit_system[temp]})',
    'temp.night': 'Night temperature (in {unit_system[temp]})',
    'temp.min': 'Min daily temperature (in {unit_system[temp]})',
    'temp.max': 'Max daily temperature (in {unit_system[temp]})',
    'feels_like': 'Temperature according to human perception (in {unit_system[temp]})',
    'feels_like.morn': 'Morning temperature according to human perception (in {unit_system[temp]})',
    'feels_like.day': 'Day temperature according to human perception (in {unit_system[temp]})',
    'feels_like.eve': 'Evening temperature according to human perception (in {unit_system[temp]})',
    'feels_like.night': 'Night temperature according to human perception (in {unit_system[temp]})',
    'rain': 'Precipitation volume, mm (in mm)',
    'rain.1h': 'Rain volume for last hour (in mm)',
    'rain.3h': 'Rain volume for 3 last hours (in mm)',
    'snow': 'Snow volume, mm (in mm)',
    'snow.1h': 'Snow volume for last hours (in mm)',
    'snow.3h': 'Snow volume for 3 last hours (in mm)',
    'weather.id': 'Weather condition id',
    'weather.main': 'Group of weather parameters',
    'weather.description': 'Weather condition within the group (in {lang})',
    'weather.icon': 'Weather icon id',
    'unparsed_weather': 'Weather info unparsed'
}

UNITS_LABEL = {
    "standard": {
        "speed": "meter/s",
        "temp": "°K",
        "pressure": "hPas"
    },
    "metric": {
        "speed": "meter/s",
        "temp": "°C",
        "pressure": "hPas"
    },
    "imperial": {
        "speed": "mile/h",
        "temp": "°F",
        "pressure": "hPas"
    }
}

LANG_LABEL = {
    "en": "English",
    "fr": "French",
    "de": "German"
}

CACHE_RELATIVE_DIR = '.cache/dss/plugins/open_weather_map'
NB_DAYS_MAX_FORECAST = 7
NB_HOURS_MAX_FORECAST = 47
NB_DAYS_MAX_HISTORICAL = 5


class DataType(Enum):
    HISTORICAL = 'historical'
    FORECAST = 'forecast'
    ALL = 'all'


class Granularity(Enum):
    DAILY = 'daily'
    HOURLY = 'hourly'


LOG_SEPARATOR_CHAR = '-'
LOG_SEPARATOR_LEN = 20
UNPARSED_COL_NAME = 'unparsed_weather'
