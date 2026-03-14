def get_stop_accessibility(stop_id, params=None):
    if not stop_id:
        return {"error": "Stop ID is required in the path"}, "application/json", 400
    import json

    try:
        with open("api/get_stops/onboard_stops.json", 'r') as f:
            stops_list = json.load(f)
            stop = [s for s in stops_list if s["info"]['id'] == stop_id][0]
            return {"accessibility": stop["details"]["accessibility"]}, "application/json", 200

    except IndexError as e:
        return {"error": "Stop ID not found"}, "application/json", 404
    except Exception as e:
        return {"error": str(e)}, "application/json", 500