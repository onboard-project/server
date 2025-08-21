from api.constants import make_request
from api.parsing.metro.parse_metro_status import parse_metro_status


def get_metro_status():
    url = "https://www.atm.it/it/Pagine/default.aspx"
    data, content_type, status_code = make_request(url)
    if status_code == 200:
        return parse_metro_status(data), "application/json", 200
    return data, content_type, status_code
