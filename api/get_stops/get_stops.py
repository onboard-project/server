import json


def get_stops():
    with open("api/get_stops/onboard_stops.json", 'r') as f:
        data = json.load(f)
        content_type = "application/json"
        status_code = 200
        return data, content_type, status_code
