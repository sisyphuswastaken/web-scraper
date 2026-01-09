from trafilatura import fetch_url, extract

def scrapeWeb(url):
    # article_raw is the entire HTML file of the article. We will parse it to just get the article content
    article_raw = fetch_url(url)
    # extracts the article in md format
    article = extract(article_raw, output_format="markdown")
    



