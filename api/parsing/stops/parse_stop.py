def parse_stop(data):
    """Transforms the given data into the desired format."""

    from api.parsing.lines.parse_line import parse_line

    stop_point = data

    if data.get("StopPoint"):
        stop_point = data["StopPoint"]

    lines = []

    if "Lines" in data:
        lines = data["Lines"]

    transformed_data = {
        "info": {
            "id": stop_point["Code"]
        },
        "details": {
            "name": stop_point["Description"],
            "type": "surface"  # Default to "surface"
        },
        "location": {
            "X": str(stop_point["Location"]["X"]),
            "Y": str(stop_point["Location"]["Y"])
        },
    }

    if int(stop_point["Code"]) < 0:
        transformed_data["details"]["type"] = "metro"

    parsed_lines = []

    for line_data in lines:
        line = line_data
        transformed_line = parse_line(line)

        parsed_lines.append(transformed_line)

    transformed_data["lines"] = list(filter(None, parsed_lines))

    return transformed_data
