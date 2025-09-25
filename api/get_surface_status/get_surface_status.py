from api.constants import make_request, GIROMILANO_HEADERS
from api.parsing.surface.parse_surface_status import parse_surface_status


def get_surface_status():
    url = "https://giromilano.atm.it/proxy.tpportal/api/tpPortal/tpl/atm/ait"
    data, content_type, status_code = make_request(url, headers=GIROMILANO_HEADERS)
    if status_code == 200:
        return parse_surface_status(data), "application/json", 200
    return data, content_type, status_code
