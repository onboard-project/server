# WARNING
# Is the code below absolue shit? YES
# Does it work? YES
# Will i do *ANYTHING* to rewrite it? NO


from api.parsing.stops.parse_stop import parse_stop
from api.constants import make_request, GIROMILANO_HEADERS


def get_stop_details(stop_id, params=None):
    if not stop_id:
        return {"error": "Stop ID is required in the path"}, "application/json", 400

    url = f"https://giromilano.atm.it/proxy.tpportal/api/tpPortal/tpl/stops/{stop_id}/linesummary"

    data, content_type, status_code = make_request(url, headers=GIROMILANO_HEADERS, params=params)

    if status_code == 200:
        transformed_data = parse_stop(data)
        return transformed_data, content_type, status_code
    return data, content_type, status_code