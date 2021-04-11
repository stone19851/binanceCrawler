import scrapy


class BinanceSpider(scrapy.Spider):
    name = 'binance'

    start_urls = ['https://www.binance.com/en/support/announcement/c-48']

    def parse(self, response):
        matchers = ['list', 'List']
        binance_page_links = response.css('.css-6f91y1 a')
        hit = []
        for elem in binance_page_links:
            a = elem.css('a::text').get()
            if any(x in a for x in matchers):
                hit.append(elem)
        yield from response.follow_all(hit, self.parse_binance)

    def parse_binance(self, response):
        def extract_with_css(query):
            return response.css(query).getall()

        heading = extract_with_css('.css-1lfxnnc .css-kxziuu::text')
        text = extract_with_css('.css-3fpgoh .css-1vsinja::text')
        yield {
            'heading': heading,
            'text': text,
        }

from scrapy import cmdline
cmdline.execute("scrapy crawl binance -O newListings.json".split())