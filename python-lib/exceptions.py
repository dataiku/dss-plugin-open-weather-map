from requests import HTTPError


class OpenWeatherMapAPIError(HTTPError):
    def __init__(self, *args, **kwargs):
        self.status_code = int(kwargs.pop('status_code', 404))
        self.text = str(kwargs.pop('text', ''))
        super(OpenWeatherMapAPIError, self).__init__(*args, **kwargs)

    def __str__(self):
        return repr(self.text)