import re
import json
import html

from html_to_markdown import convert_to_markdown


def _clean_html_to_markdown(html_content):
    """
    Cleans HTML content and converts it to Markdown, embedding emojis.
    """
    content = re.sub(r'&nbsp;', ' ', html_content)
    content  = html.unescape(content)


    content = re.sub(r"([^\s])<strong>\s*", r"\1 <strong>", content)

    content = re.sub(r"\s*</strong>(\S)", r"</strong> \1", content)

    content = re.sub(r"\s*<a", r"  <a", content)


    content = convert_to_markdown(content)

    content = re.sub(r"\\-\\-\\-", r"---", content)

    content = re.sub(r"\\", r"", content)
    content = re.sub(r"---\n\n", r"---\n", content)

    return content.strip()

def parse_surface_status(json_string):
    """
    Parses the surface status JSON string, cleans the HTML content,
    and returns it in a structured format.
    """
    data = json.loads(json_string)

    title = data.get("alert_title", "")
    html_content = data.get("alert_text", "")

    markdown_content = _clean_html_to_markdown(html_content)

    return {
        "title": title,
        "content": markdown_content
    }
