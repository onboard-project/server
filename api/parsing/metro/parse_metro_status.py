from bs4 import BeautifulSoup
import re

def parse_metro_status(html_content):
    """
    Parses the HTML content of the ATM status page to extract metro line statuses.
    """ 
    soup = BeautifulSoup(html_content, 'html.parser')

    rows = soup.select('#StatusLinee tr')

    status_list = []
    for row in rows:
        line_img = row.select_one('.StatusLinee_Linea img')
        if not line_img:
            continue
        line = line_img.get('alt', 'N/A')

        status_element = row.select_one('.StatusLinee_StatoScritta')
        status_text = status_element.text.strip() if status_element else "N/A"

        if line != 'N/A':
            status_list.append({
                "line": line,
                "status": status_text
            })

    message_element = soup.select_one('.StatusLinee_Mex_Testo')
    message = message_element.text.strip() if message_element else ""

    return {
        "lines": status_list,
        "message": message
    }
