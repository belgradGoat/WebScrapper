import sys
import scrapy
from scrapy.crawler import CrawlerProcess

class SavePageSpider(scrapy.Spider):
    name = "save_page"

    def __init__(self, url: str, *args, **kwargs):
        """
        Parameters
        ----------
        url : str
            The web page you want to download.
        """
        super().__init__(*args, **kwargs)
        # Scrapy expects a list for start_urls
        self.start_urls = [url]

    def parse(self, response):
        """
        Write the raw response body to a text file.
        """
        filename = "page.txt"
        self.logger.info(f"Saving {response.url} to {filename}")
        with open(filename, "wb") as f:
            f.write(response.body)          # bytes → preserves encoding exactly
        yield {"saved_as": filename}        # lets Scrapy know we produced output


def main(target_url: str):
    """Run the SavePageSpider programmatically."""
    process = CrawlerProcess(settings={
        "LOG_LEVEL": "ERROR",   # keep console output clean
    })
    process.crawl(SavePageSpider, url=target_url)
    process.start()            # the script blocks here until crawling is finished


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python save_page.py <URL>")
        sys.exit(1)
    main(sys.argv[1])
