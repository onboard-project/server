from api.parsing.lines.parse_line import parse_line

# Si presume che api.constants fornisca make_request e ATM_HEADERS.
# Se api.constants non esiste o non fornisce questi elementi, questo import
# dovrà essere modificato o tali costanti dovranno essere definite/mantenute localmente.
from api.constants import make_request, ATM_HEADERS, create_error_json

# API_URL è specifico per il recupero di tutti i percorsi di linea (journey patterns)
API_URL = "https://giromilano.atm.it/proxy.tpportal/api/tpportal/tpl/journeyPatterns/"

def get_lines(): # Rinominato per coerenza con l'uso in api/index.py
    """
    Recupera i dati delle linee dall'API ATM Giromilano utilizzando un gestore
    di richieste condiviso, li elabora e applica una gestione degli errori standardizzata.

    Restituisce:
        tuple: Una tupla contenente:
            - data (list o dict): I dati delle linee elaborati come lista di dizionari,
                                   o un dizionario di errore se si verifica un problema.
            - content_type (str): Il tipo di contenuto, tipicamente "application/json".
            - status_code (int): Il codice di stato HTTP.
    """
    # Chiama la funzione condivisa make_request
    # ATM_HEADERS è importato da api.constants
    # Il timeout è gestito dal valore predefinito di make_request o può essere passato se necessario
    data, content_type, status_code = make_request(API_URL, headers=ATM_HEADERS)

    if status_code == 200:
        # A questo punto, data dovrebbe essere il JSON analizzato dall'API upstream
        # se make_request ha avuto successo e ha restituito JSON.
        # Si assume che make_request restituisca un dizionario Python se il parsing JSON ha successo.
        if not isinstance(data, dict):
            # Questo caso dovrebbe idealmente essere gestito da make_request se garantisce
            # JSON per 200 OK, o restituisce un errore appropriato.
            # Se make_request potrebbe restituire dati non JSON per un 200, questo controllo è necessario.
            errore = create_error_json(
                502,
                "BAD_GATEWAY",
                "L'API upstream ha restituito uno stato di successo ma la risposta non era nel formato JSON previsto."
            )
            return errore, "application/json", 502

        linee_elaborate = []
        journey_patterns_list = data.get("JourneyPatterns")

        if not isinstance(journey_patterns_list, list):
            # Questo è un errore di validazione dei dati dopo una chiamata API riuscita
            errore = create_error_json(
                502, # O 500 se considerato un errore di elaborazione interna di dati upstream validi
                "BAD_GATEWAY", # O INTERNAL_SERVER_ERROR
                "Formato dati non valido dall'API upstream: il campo 'JourneyPatterns' è mancante o non è una lista."
            )
            return errore, "application/json", 502

        # Per rispecchiare get_line_details.py, le eccezioni durante parse_line si propagheranno.
        # Se si desidera una gestione degli errori locale più robusta per il parsing,
        # un blocco try-except potrebbe essere aggiunto attorno a questo ciclo o alla chiamata parse_line.
        for pattern_item in journey_patterns_list:
            if not isinstance(pattern_item, dict):
                # Opzionalmente, registra o gestisci elementi malformati nella lista
                print(f"Attenzione: elemento saltato in JourneyPatterns perché non è un dizionario: {pattern_item}")
                continue  # Salta elementi non dizionario

            # line_details_raw = pattern_item.get("Line") # Questa variabile non era usata ulteriormente (codice morto rimosso)
            elemento_elaborato = parse_line(pattern_item)
            if elemento_elaborato:  # parse_line restituisce None per elementi saltati o non validi
                linee_elaborate.append(elemento_elaborato)

        return linee_elaborate, "application/json", 200
    else:
        # Se status_code non è 200, data da make_request è già
        # il payload di errore standardizzato (assumendo che make_request lo faccia).
        # content_type dovrebbe essere "application/json" in caso di errore da make_request.
        return data, content_type, status_code