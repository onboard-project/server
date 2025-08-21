import json
import re  # Per la corrispondenza dei percorsi con espressioni regolari
from urllib.parse import unquote, parse_qs  # Per gestire percorsi e stringhe di query

from api.get_line_details.get_line_details import get_line_details
from api.get_lines.get_lines import get_lines
from api.get_stop_details.get_stop_details import get_stop_details
from api.get_stops.get_stops import get_stops
from api.get_metro_status.get_metro_status import get_metro_status
from api.constants import create_error_json


async def app(scope, receive, send):
    if scope['type'] != 'http':
        return

    path = scope['path']
    method = scope['method']

    query_string = scope.get('query_string', b'')
    query_params = parse_qs(query_string.decode('utf-8'))

    # Impostazioni predefinite per la risposta (verranno sovrascritte se un percorso viene trovato)
    status_code = 404
    content_type = "application/json"  # Gli errori sono sempre JSON
    data = create_error_json(
        status_code,
        "NOT_FOUND",
        "La risorsa richiesta non è stata trovata"
    )

    # --- Instradamento Richieste ---
    if method == 'GET':
        if path == '/':
            status_code = 200
            content_type = "application/json"
            # Informazioni API in italiano, con campi chiave standard
            data = {
                "titolo": "API Trasporto Pubblico",
                "descrizione_generale": "Benvenuto nelle API per le informazioni sul trasporto pubblico.",
                "endpoints": {
                    "StatoMetro": {
                        "Path": "/status/metro",
                        "Descrizione": "Restituisce lo stato attuale delle linee metropolitane."
                    },
                    "ElencoLinee": {
                        "Path": "/lines",
                        "Descrizione": "Restituisce un elenco di tutte le linee di trasporto disponibili."
                    },
                    "DettagliLinea": {
                        "Path": "/lines/{lineId}",
                        "Descrizione": "Restituisce informazioni dettagliate per una specifica linea, inclusi i suoi percorsi e fermate.",
                        "ParametriDiQuery": {
                            "all": {
                                "tipo": "boolean", "default": "false",
                                "descrizione": "Se 'true', indica di recuperare anche i percorsi alternativi o le varianti della linea (corrisponde a alternativeRoutesMode nell'API upstream)."
                            }
                        }
                    },
                    "ElencoFermate": {
                        "Path": "/stops",
                        "Descrizione": "Restituisce un elenco statico di tutte le fermate."
                    },
                    "DettagliFermata": {
                        "Path": "/stops/{stopId}",
                        "Descrizione": "Restituisce informazioni dettagliate per una specifica fermata, potenzialmente includendo dati in tempo reale. Non supporta parametri aggiuntivi."
                        # "ParametriDiQuery" rimosso poiché 'short' è stato eliminato
                    }
                }
            }

        elif path == '/lines':
            print(f"Routing per /lines")
            data, content_type, status_code = get_lines()

        elif match := re.fullmatch(r'/lines/([^/]+)', path):
            line_id = unquote(match.group(1))
            print(f"Routing per /lines/{line_id}, parametri: {query_params}")

            # Estrae il parametro 'all' e lo mappa a 'alternativeRoutesMode' per l'API upstream.
            data, content_type, status_code = get_line_details(line_id, params={
                "alternativeRoutesMode": query_params.get("all", ["false"])[0].lower()
            })

        elif path == '/stops':
            print(f"Routing per /stops")
            data, content_type, status_code = get_stops()

        elif match := re.fullmatch(r'/stops/([^/]+)', path):
            stop_id = unquote(match.group(1))
            print(f"Routing per /stops/{stop_id}")
            # Passa i query_params direttamente. get_stop_details gestirà i parametri che conosce.
            # Il parametro 'short' non è più documentato/supportato attivamente a questo livello.
            data, content_type, status_code = get_stop_details(stop_id)
        
        elif path == '/status/metro':
            print(f"Routing per /status/metro")
            data, content_type, status_code = get_metro_status()
        # Se nessun percorso GET specifico viene trovato, la risposta 404 predefinita rimane.

    else:  # Gestisce metodi HTTP non GET
        status_code = 405
        content_type = "application/json"  # Gli errori sono sempre JSON
        data = create_error_json(
            status_code,
            "METHOD_NOT_ALLOWED",
            "Questo metodo HTTP non è consentito per la risorsa richiesta"
        )

    # --- Preparazione e Invio Risposta Finale ---
    response_body_bytes = b""

    if content_type == 'application/json':
        try:
            response_body_bytes = json.dumps(data, indent=2).encode('utf-8')
        except TypeError as e:
            # Errore durante la serializzazione dei dati in JSON
            print(f"Errore di serializzazione JSON: {e}. Dati originali (troncati): {str(data)[:200]}...")
            status_code = 500
            # Sovrascrive 'data' con un messaggio di errore standardizzato JSON
            error_payload = create_error_json(
                status_code,
                "INTERNAL_SERVER_ERROR",
                "Impossibile serializzare i dati della risposta in JSON."
            )
            response_body_bytes = json.dumps(error_payload, indent=2).encode('utf-8')
            # content_type è già 'application/json' per gli errori
    elif isinstance(data, str):  # Se il gestore restituisce una stringa
        response_body_bytes = data.encode('utf-8')
    elif isinstance(data, bytes):  # Se il gestore restituisce bytes direttamente
        response_body_bytes = data
    else:
        # Tipo di dati imprevisto restituito dal gestore
        original_data_type_name = type(data).__name__
        print(f"Errore: Tipo di dati imprevisto '{original_data_type_name}' ricevuto dal gestore.")
        status_code = 500
        content_type = 'application/json'  # Gli errori sono sempre JSON
        error_payload = create_error_json(
            status_code,
            "INTERNAL_SERVER_ERROR",
            f"Formato dati imprevisto ricevuto dal gestore: {original_data_type_name}"
        )
        response_body_bytes = json.dumps(error_payload, indent=2).encode('utf-8')

    response_headers = [
        (b'content-type', content_type.encode('utf-8')),
        (b'content-length', str(len(response_body_bytes)).encode('utf-8')),
        (b'access-control-allow-origin', b'*'),  # Permetti l'utilizzo dei risultati da qualsiasi dominio frontend
    ]

    await send({
        'type': 'http.response.start',
        'status': status_code,
        'headers': response_headers,
    })

    await send({
        'type': 'http.response.body',
        'body': response_body_bytes,
        'more_body': False  # Indica che questo è il corpo completo della risposta
    })


# --- Opzionale: Esecuzione locale per test ---
if __name__ == "__main__":
    print("--- Server di Sviluppo Locale ---")
    print("\nPer eseguire localmente:")
    print("1. Assicurati che 'requests' e 'uvicorn' siano installati: pip install requests uvicorn")
    print("2. Esegui il comando: uvicorn api.index:app --reload --port 8000")
    print("---------------------------------")
    print("\nEsempi di endpoint da testare nel browser o con curl:")
    print(f"  Informazioni API (Root): http://localhost:8000/")
    print(f"  Stato Metro:             http://localhost:8000/status/metro")
    print(f"  Lista Linee:             http://localhost:8000/lines")
    print(f"  Dettagli Linea (base):   http://localhost:8000/lines/19|0")  # ID Linea d'esempio
    print(f"  Dettagli Linea (param):  http://localhost:8000/lines/19|0?all=true")
    print(f"  Tutte le Fermate:        http://localhost:8000/stops")
    print(f"  Dettagli Fermata:        http://localhost:8000/stops/16634")  # ID Fermata d'esempio