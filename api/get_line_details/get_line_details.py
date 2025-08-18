# WARNING
# Is the code below absolue shit? YES
# Does it work? YES
# Will i do *ANYTHING* to rewrite it? NO


from api.parsing.lines.parse_line import parse_line
from api.constants import make_request, ATM_HEADERS


def get_line_details(line_id, params=None):
    if not line_id:
        return {"error": "Line ID is required in the path"}, "application/json", 400

    url = f"https://giromilano.atm.it/proxy.tpportal/api/tpportal/tpl/journeyPatterns/{line_id}"

    data, content_type, status_code = make_request(url, headers=ATM_HEADERS, params=params)

    if status_code == 200:
        transformed_data = parse_line(data)
        return transformed_data, content_type, status_code
    return data, content_type, status_code

