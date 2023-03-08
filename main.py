import sys

import scrapy
from scrapy.crawler import CrawlerProcess


class ImageInDepth(scrapy.Spider):
    name = 'image_in_depth'
    custom_settings = {
        # Saves the results in a csv file automatically
        'FEED_URI': 'results.json',
        'FEED_FORMAT': 'json',
        'ROBOTSTXT_OBEY': True, # If the spider should obey the robots.txt file (with false it will ignore it)
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36', # User agent to use
        'FEED_EXPORT_ENCODING': 'utf-8' # Encoding to use
    }

    def __init__(self, url: str, depth: int):
        self.start_urls = [url]
        self.__depth = depth
        self.__actual_depth = 0
        self.__urls_seen = list()

    def parse_images_in_depth(self, response, **kwargs):
        """Get images and links from a page and go to the next page inside

        Args:
            response: scrapy response object

        Yields:
            dict: dictionary with the image urls, the source urls and the depths in a list
        """        
        self.__actual_depth += 1

        results: list = list()
        if kwargs:
            results = kwargs['results']

        # Get data from page
        crawl_data = dict(
            imageUrl = response.xpath('//img/@src').getall()[0],
            sourceUrl = response.url,
            depth = self.__actual_depth
        )

        # Add data to results
        results.append(crawl_data)

        # Add url to seen urls
        self.__urls_seen.append(response.url)

        # Get new next link
        next_page_links = response.xpath('//a/@href').getall()
        # Validate next link is not already seen
        link_index = 0
        while link_index < len(next_page_links) and (next_page_links[link_index] in ['#', '/'] or next_page_links[link_index] in self.__urls_seen):
            link_index += 1

        if next_page_links[link_index] and self.__actual_depth < self.__depth:
            yield response.follow(
                next_page_links[link_index], 
                callback=self.parse_images_in_depth, 
                cb_kwargs={'results': results}, 
                dont_filter=True # Allows to go to the same page again
            )
        else:
            yield {
                'results': results
            }


    def parse(self, response):
        yield response.follow(self.start_urls[0], callback=self.parse_images_in_depth)


def scrape_page(url: str, depth: int):
    """Sets up the crawler process and starts it

    Args:
        url (str): url where to start the crawling
        depth (int): depth of the crawling
    """    
    process = CrawlerProcess()

    process.crawl(ImageInDepth, url = url, depth = depth)
    process.start() # the script will block here until the crawling is finished


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        raise Exception('No URL provided')
    
    page_url: str = sys.argv[1]

    if len(sys.argv) <= 2:
        raise Exception('No depth provided')

    depth: int = int(sys.argv[2])
    
    scrape_page(page_url, depth)