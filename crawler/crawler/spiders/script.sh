#!/bin/sh
cd /opt/binanceCrawler/crawler/crawler/spiders/
PATH=$PATH:/usr/local/bin
export PATH
scrapy crawl binance -O newListings.json && python3 main.py