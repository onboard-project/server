import requests


def create_error_json(status_code_val, error_key, detail_it):
    """
    Funzione di utilità per creare la struttura JSON standardizzata per le risposte di errore.
    Il campo 'error' è in inglese, 'detail' contiene entrambe le lingue.
    """
    return {
        "status_code": status_code_val,
        "error": error_key,
        "detail": detail_it
    }

def create_local_waiting_time_json(type, value = None):
    """
    Funzione di utilità per creare la struttura JSON standardizzata per le risposte di errore.
    Il campo 'error' è in inglese, 'detail' contiene entrambe le lingue.
    """
    return {
        "type": type,
        "value": value
    }


def make_request(url, headers=None, params=None, timeout=15):
    try:
        print(f"Fetching URL: {url}, Params: {params}")  # Log request details
        # The 'params' dictionary is automatically converted to query string by requests
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        # Try parsing as JSON first, as it's the most common API response type
        try:
            data = response.json()
            content_type = 'application/json'
        except requests.exceptions.JSONDecodeError:
            # If JSON parsing fails, return the raw text content
            data = response.text
            content_type = response.headers.get('Content-Type', 'text/plain')  # Get original content type or default

        return data, content_type, response.status_code

    except requests.exceptions.Timeout:
        error_msg = {
            "code": 504,
            "error": "REQUEST_TIMEOUT",
            "details": "Request timed out while fetching upstream data"
        }
        print(f"Timeout error fetching {url}")
        return error_msg, "application/json", 504  # Gateway Timeout
    except requests.exceptions.HTTPError as e:
        # Handle errors reported by the target API (e.g., 404 Not Found, 401 Unauthorized)
        error_msg = {
            "code": 502,
            "error": "BAD_GATEWAY",
            "details": f"Error fetching {url}. Response: {e.response.text[:500]}"
        }

        print(f"HTTPError {e.response.status_code} fetching {url}: {error_msg['details']}")
        # Return the status code received from the upstream API
        return error_msg, "application/json", 502
    except requests.exceptions.RequestException as e:
        # Handle broader network issues (DNS failure, connection refused, etc.)
        error_msg = {
            "code": 502,
            "error": "BAD_GATEWAY",
            "details": f"Could not connect to upstream API - {str(e)}"
        }

        print(f"RequestException fetching {url}: {str(e)}")
        return error_msg, "application/json", 502  # Bad Gateway


GIROMILANO_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "cookie": "_ga=GA1.1.1094638075.1734094086; _ga=GA1.1.1094638075.1734094086; _ga_5W1ZB23GRH=GS1.1.1734094181.1.1.1734094217.0.0.0; _ga_RD7BG8RLV0=GS1.1.1734541890.5.0.1734541890.0.0.0; TS01ac3475=0199b2c74a55444afe1aa05c9b25acfc9d695088d80dbca4018f777758e5691d1801f3a9fc6311b2e72d707e00653e493a7e4f4cc7",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}