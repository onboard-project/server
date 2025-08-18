import re

from api.constants import create_local_waiting_time_json


# import json # Rimosso perché non utilizzato
# from operator import truediv # Rimosso perché non utilizzato


def _parse_location_name(name_str):
    """
    Parses a single location name string which might include 'con dir.' and 'e' alternatives.
    Returns a string with alternatives joined by '/'.
    """
    name_str = name_str.strip()
    name_str = re.match(r"(?:SOSTITUTIVO)?\s*(.*)", name_str, re.IGNORECASE).group(1).strip()
    name_str = re.match(r"(?:NOTTURNA)?\s*(.*)", name_str, re.IGNORECASE).group(1).strip()
    name_str = re.match(r"(N\w*\s*-\s*)?\s*(.*)", name_str, re.IGNORECASE).group(2).strip()

    con_dir_match = re.match(r"^(.*?) con dir\. (.*?)$", name_str, re.IGNORECASE)
    if con_dir_match:
        main_part_str = con_dir_match.group(1).strip()
        branches_part_str = con_dir_match.group(2).strip()

        all_sub_elements = []
        if main_part_str:
            all_sub_elements.extend(p.strip() for p in main_part_str.split(" e ") if p.strip())
        if branches_part_str:
            all_sub_elements.extend(p.strip() for p in branches_part_str.split(" e ") if p.strip())
        return "/".join(filter(None, all_sub_elements))
    elif ' e ' in name_str:
        return "/".join(p.strip() for p in name_str.split(" e ") if p.strip())
    else:
        return name_str


def parse_line_description(descrizione, parsing_da_stazione=False):
    """
    Analizza la stringa LineDescription per estrarre il codice della linea,
    i punti di partenza e i punti di arrivo.

    Args:
        descrizione (str): La stringa LineDescription da analizzare.
        codice_modalita_trasporto (int): Il codice che identifica il tipo di trasporto
                                         (es. 0 per Metro, 1 per Tram, ecc.).

    Returns:
        tuple: Una tupla contenente (codice_estratto, punti_inizio, punti_fine).
               Restituisce (None, None, None) se la descrizione non è una stringa.

               :param parsing_da_stazione:
    """
    # Controlla se la descrizione fornita è effettivamente una stringa
    if not isinstance(descrizione, str):
        return None, None, None

    codice_estratto = None  # Codice della linea estratto dalla descrizione (es. "M1", "19")
    parte_descrizione_percorso = descrizione  # Inizialmente, è l'intera descrizione;
    # verrà ridotta se si trova un prefisso di linea.

    corrispondenza_metro = re.match(r"Linea (M\d+)\s*(.*)", descrizione)
    corrispondenza_tram = re.match(r"Tram (\d+)\s*(.*)", descrizione)
    corrispondenza_xx_Nxx = re.match(r"Bus\s+(\w*)\s*N\d*\s*- \s*(.*)", descrizione, re.IGNORECASE)
    corrispondenza_Nxx = re.match(r"N(\w*)\s*-\s*(.*)", descrizione, re.IGNORECASE)
    corrispondenza_91 = re.match(r"Bus\s+91\s*(.*)", descrizione, re.IGNORECASE)
    corrispondenza_bus_generale = re.match(r"Bus (\w+)\s*(.*)", descrizione)
    if corrispondenza_metro:
        codice_estratto = corrispondenza_metro.group(1)  # Es. "M1"
        parte_descrizione_percorso = corrispondenza_metro.group(2).strip()  # Il resto della descrizione
        # Rimuove eventuali nomi di colore della linea (es. "(Rossa)")
        parte_descrizione_percorso = re.sub(r"\s*\((Rossa|Verde|Gialla|Blu|Lilla)\)", "", parte_descrizione_percorso,
                                            flags=re.IGNORECASE).strip()
    elif descrizione.startswith("Metro leggera"):
        codice_estratto = "MeLa"  # Codice specifico per Metro Leggera
        parte_descrizione_percorso = descrizione.replace("Metro leggera", "", 1).strip()



    elif corrispondenza_tram:
        codice_estratto = corrispondenza_tram.group(1)  # Es. "19"
        parte_descrizione_percorso = corrispondenza_tram.group(2).strip()  # Il resto




    elif corrispondenza_xx_Nxx:
        codice_estratto = f"{corrispondenza_xx_Nxx.group(1).strip()}/N{corrispondenza_xx_Nxx.group(1).strip()}"
        parte_descrizione_percorso = corrispondenza_xx_Nxx.group(2).strip()
    elif corrispondenza_Nxx:
        codice_estratto = f"{corrispondenza_Nxx.group(1).strip()}/N{corrispondenza_Nxx.group(1).strip()}"

        parte_descrizione_percorso = corrispondenza_Nxx.group(2).strip()
    elif corrispondenza_91:
        codice_estratto = "91/N91"
        parte_descrizione_percorso = corrispondenza_91.group(1).strip()
    elif corrispondenza_bus_generale:
        codice_estratto = corrispondenza_bus_generale.group(1).strip()
        parte_descrizione_percorso = corrispondenza_bus_generale.group(2).strip()

    elif codice_estratto is None and parsing_da_stazione == False:
        if descrizione:  # Assicura che la descrizione originale non sia None o vuota
            parti_descrizione = descrizione.split(" ", 1)
            codice_estratto = parti_descrizione[0]  # Prende la prima parola come codice
            # Il resto diventa la parte della descrizione del percorso
            parte_descrizione_percorso = parti_descrizione[1].strip() if len(parti_descrizione) > 1 else ""
        else:  # Se la descrizione originale era vuota o None
            codice_estratto = None
            parte_descrizione_percorso = ""  # Imposta a stringa vuota per sicurezza

    # Inizializzazione delle liste per i punti di inizio e fine
    tutti_inizi = []
    tutte_fini = []

    # Analisi della parte_descrizione_percorso per estrarre i punti di inizio e fine effettivi.
    # La descrizione può contenere "con dir." o " e " per indicare diramazioni o percorsi multipli.
    segmenti_principali = []
    if parte_descrizione_percorso and " con dir. " in parte_descrizione_percorso.lower():
        segmenti_principali = [parte_descrizione_percorso]  # Tratta come un unico segmento da splittare dopo
    elif parte_descrizione_percorso:  # Se è una stringa non vuota
        segmenti_principali = parte_descrizione_percorso.split(" e ")  # Divide per " e "
    # Se parte_descrizione_percorso è None o vuota, segmenti_principali rimane lista vuota

    # Itera su ogni segmento principale trovato
    for frammento_segmento in segmenti_principali:
        frammento_segmento = frammento_segmento.strip()
        # Ogni frammento è ulteriormente diviso dal separatore " - "
        parti = frammento_segmento.split(" - ")

        if len(parti) == 2:  # Caso standard: "Inizio - Fine"
            stringa_candidato_inizio = parti[0].strip()
            stringa_candidato_fine = parti[1].strip()
            # Chiama una funzione helper (non mostrata qui) per parsare i nomi delle località
            inizio_parsato = _parse_location_name(stringa_candidato_inizio)
            fine_parsata = _parse_location_name(stringa_candidato_fine)
            # Rimuove eventuali suffissi "(Circolare...)" dal punto di fine
            candidato_fine_pulito = re.sub(r"\s*\(Circolare.*?\)$", "", fine_parsata if fine_parsata else "",
                                           flags=re.IGNORECASE).strip()
            tutti_inizi.append(inizio_parsato)
            tutte_fini.append(candidato_fine_pulito)
        elif len(parti) == 1 and len(
                segmenti_principali) == 1:  # Unica parte, potrebbe essere circolare o un singolo punto
            descrizione_singola = parti[0].strip()
            if re.search(r"circolare", descrizione_singola, re.IGNORECASE):  # Se è una circolare
                nome_circolare_pulito = re.sub(r"\(?circolare.*?\)?", "", descrizione_singola,
                                               flags=re.IGNORECASE).strip()
                # Caso speciale per descrizioni come "Nome (Circolare unica)"
                if not nome_circolare_pulito and "unica" in descrizione_singola.lower():
                    nome_circolare_pulito = descrizione_singola  # Usa la descrizione originale
                nome_circolare_parsato = _parse_location_name(nome_circolare_pulito)
                tutti_inizi.append(nome_circolare_parsato)
                tutte_fini.append(nome_circolare_parsato)  # Inizio e fine sono uguali per circolari
            break  # Esce dal loop dopo aver processato il singolo segmento (circolare o meno)
        elif len(parti) > 2 and re.search(r"circolare", frammento_segmento, re.IGNORECASE):  # Circolare complessa
            # Esempio: "A - B - C (Circolare)"
            # Se le ultime due parti sono uguali (es. "X - Y - Y (Circolare)"), usa l'ultima come punto unico.
            if parti[-2].strip() == parti[-1].strip():
                stringa_nome_punto = parti[-1].strip()
                nome_punto_parsato = _parse_location_name(stringa_nome_punto)
                tutti_inizi.append(nome_punto_parsato)
                tutte_fini.append(nome_punto_parsato)
            else:  # Fallback per circolari complesse: usa l'intero frammento
                frammento_segmento_parsato = _parse_location_name(frammento_segmento)
                tutti_inizi.append(frammento_segmento_parsato)
                tutte_fini.append(frammento_segmento_parsato)
        elif len(parti) > 2:  # Percorso con punti intermedi: Inizio - Intermedio1 - ... - Fine
            stringa_candidato_inizio = parti[0].strip()
            stringa_candidato_fine = parti[-1].strip()  # Prende l'ultima parte come fine
            inizio_parsato = _parse_location_name(stringa_candidato_inizio)
            fine_parsata = _parse_location_name(stringa_candidato_fine)
            candidato_fine_pulito = re.sub(r"\s*\(Circolare.*?\)$", "", fine_parsata if fine_parsata else "",
                                           flags=re.IGNORECASE).strip()
            tutti_inizi.append(inizio_parsato)
            tutte_fini.append(candidato_fine_pulito)
        elif len(parti) == 1 and len(
                segmenti_principali) > 1:  # Segmento "orfano" in una linea multi-segmento (es. "A - B e C")
            pass  # Salta questo segmento orfano, come da logica originale

    # Unisce tutti i punti di inizio e fine trovati, separati da "/"
    # filter(None, ...) rimuove eventuali valori None prima di join
    punti_inizio = "/".join(filter(None, tutti_inizi)) if tutti_inizi else None
    punti_fine = "/".join(filter(None, tutte_fini)) if tutte_fini else None

    # Pulisce il codice estratto da eventuali spazi extra
    if codice_estratto:
        codice_estratto = codice_estratto.strip()

    return codice_estratto, punti_inizio, punti_fine


def parse_line(line_data_item):
    line_data_item["TrafficBulletins"] = ""
    """
    Parses a single line data item (which can be in one of a few formats)
    into the desired output format.

    Args:
        line_data_item (dict): A single dictionary item representing a line.

    Returns:
        dict: The processed line data, or None if skipped (e.g., TRENORD).
    """
    from api.parsing.stops.parse_stop import parse_stop  # Import locale

    if not isinstance(line_data_item, dict):
        # print(f"Warning: line_data_item is not a dict: {line_data_item}")
        return None

    # --- Blocco rimosso: is_line_long era inutilizzato e usava accesso non sicuro ---
    # is_line_long = False
    # if line_data_item["Id"]:
    #     is_line_long = True
    # --- Fine blocco rimosso ---

    # --- 1. Estrae gli attributi comuni dal sotto-dizionario "Line" ---
    line_attributes_dict = line_data_item.get("Line")
    if not isinstance(line_attributes_dict, dict):
        # Se "Line" manca o non è un dizionario, potremmo non avere abbastanza informazioni.
        # Per ora, impostiamo a dizionario vuoto per evitare errori con .get() successivi.
        line_attributes_dict = {}

    # --- 2. Estrae i campi per il blocco 'info' (Code, Id, Direction) ---
    # Preferisce i campi di primo livello, poi prova alternative.
    info_code = line_data_item.get("Code")
    info_id = line_data_item.get("Id")
    info_direction = line_data_item.get("Direction")

    # Fallback per il Formato 1 o se i campi di primo livello mancano
    if info_id is None:
        info_id = line_data_item.get("JourneyPatternId")  # Comune nel Formato 1

    if info_code is None:
        info_code = line_attributes_dict.get("LineId")  # Da "Line.LineCode"

    # Ulteriore fallback per info_id se necessario
    if info_id is None:
        info_id = line_attributes_dict.get("LineId")

    # --- 3. Estrae i 'details' dal sotto-dizionario "Line" ---
    details_headcode = None
    details_start = None
    details_end = None
    # Estrae la descrizione originale e il tipo di veicolo
    details_desc = line_attributes_dict.get("LineDescription")
    details_vehicle = line_attributes_dict.get("TransportMode")

    # Salta TRENORD (TransportMode == 2) e Qlines (TransportMode == 99)
    # Nota: parse_line_description ha logica per Qlines (99). Se devono essere processate,
    # rimuovere 'or details_vehicle == 99' da questa condizione.
    if details_vehicle == 2 or details_vehicle == 99:
        return None

    if line_data_item.get("JourneyPatternId"):
        if str(line_data_item.get("JourneyPatternId")).strip().startswith("Q"):
            return None

    # Esegue il parsing della descrizione solo se abbiamo una descrizione e un tipo di veicolo
    if details_desc is not None:
        extracted_code_from_desc, start_points, end_points = parse_line_description(
            details_desc,
            line_data_item.get("JourneyPatternId")

        )

        if line_data_item.get("JourneyPatternId") and not str(details_desc).startswith("N"):
            extracted_code_from_desc = line_data_item.get("BookletUrl2")

        details_headcode = extracted_code_from_desc
        details_start = start_points
        details_end = end_points

        if info_code == "91":
            details_headcode = "91/N91"
    # Se details_desc o details_vehicle sono None, headcode, start, end rimarranno None.

    # --- 4. Parsa le Fermate (Stops) - attese nella chiave "Stops" di primo livello ---
    details_stops = []
    stops_raw_list = line_data_item.get("Stops")  # Ottiene la lista di fermate, se presente
    if isinstance(stops_raw_list, list):
        for stop_data_item in stops_raw_list:

            if isinstance(stop_data_item, dict):  # Assicura che l'elemento sia un dizionario
                try:
                    parsed_stop = parse_stop(stop_data_item)
                    if parsed_stop:  # parse_stop potrebbe restituire None
                        details_stops.append(parsed_stop)
                except Exception as e:
                    # Opzionale: logga l'errore, es. print(f"Errore nel parsing della fermata per linea {info_id}: {e}")
                    print(f"Errore nel parsing della fermata per linea {info_id}: {e}")
                    pass  # Continua con la prossima fermata

    # --- 5. Parsa la Geometria (Geometry) - attesa nella chiave "Geometry" di primo livello ---
    details_geometry = []
    geometry_data_dict = line_data_item.get("Geometry")
    if isinstance(geometry_data_dict, dict):
        segments_list = geometry_data_dict.get("Segments")
        if isinstance(segments_list, list) and segments_list:  # Controlla se è una lista e non è vuota

            for segment in segments_list:  # Assume interesse per il primo segmento

                if isinstance(segment, dict):
                    points_list = segment.get("Points")
                    if isinstance(points_list, list):  # Points potrebbe essere una lista (anche vuota)
                        details_geometry.append(points_list)



    if info_code in ("-1", "-2", "-3", "-4", "-5"):
        details_vehicle = "metro"
    elif info_code == "-11":
        details_vehicle = "mela"
    else:
        details_vehicle = "surface"

    # --- 6. Parsa il tempo di attesa ---
    raw_waiting_time = line_data_item.get("WaitMessage")
    local_waiting_time = _parse_waiting_time(raw_waiting_time)





    # --- 7. Costruisce l'elemento processato finale ---
    # I commenti "Always empty as per requirement" sono stati rimossi/aggiornati
    # poiché l'obiettivo è estrarre il massimo dei dati disponibili.
    processed_item = {
        "info": {
            "code": info_code,
            "id": info_id,
            "direction": info_direction
        },
        "details": {
            "headCode": details_headcode,
            "startPoint": details_start,
            "endPoint": details_end,
            "desc": details_desc,  # Descrizione originale della linea
            "vehicle": details_vehicle,
            "stops": details_stops,  # Popolata se disponibile nell'input
            "geometry": details_geometry,  # Popolata se disponibile nell'input
        },
        "local" : {
            "waitingTime": local_waiting_time,
            "alerts": []
        }

    }
    return processed_item


def _parse_waiting_time(waitingtime):
    """Transforms the given data into the desired format."""
    local_waiting_time = create_local_waiting_time_json("none")




    if isinstance(waitingtime, str):
        raw_waiting_time = waitingtime.strip().lower()

    match waitingtime:


        case "ricalcolo":
            local_waiting_time = create_local_waiting_time_json("reloading")
        case "+30 min":
            local_waiting_time = create_local_waiting_time_json("plus30")
        case "serale":
            local_waiting_time = create_local_waiting_time_json("nightly")
        case "in arrivo":
            local_waiting_time = create_local_waiting_time_json("arriving")
        case "in coda":
            local_waiting_time = create_local_waiting_time_json("waiting")
        case "no serv.":
            local_waiting_time = create_local_waiting_time_json("no service")
        case "fermata\fsospesa":
            local_waiting_time = create_local_waiting_time_json("suspended")



    if isinstance(waitingtime, str):
        val = re.match(r"(\d*) min", waitingtime, re.IGNORECASE)
        if val:
            local_waiting_time = create_local_waiting_time_json("time", val.group(1))

    return  local_waiting_time
