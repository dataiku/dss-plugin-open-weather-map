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
