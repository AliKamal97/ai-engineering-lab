from bs4 import BeautifulSoup
import requests
from urllib.parse import urlsplit


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    if urlsplit(url).scheme not in {"http", "https"}:
        raise ValueError("Use an HTTP or HTTPS website URL.")
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser", from_encoding=response.encoding)
    title = soup.title.get_text(strip=True) if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input", "nav", "footer"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """Return the href values from links on a webpage."""
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
