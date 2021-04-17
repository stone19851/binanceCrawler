# binanceCrawler

Requirements:
- python3
- pip3

Usage:
- clone project
- cd binanceCrawler/crawler/crawler/spiders
- update file settings.txt:
  - mail_address_recipient: where do you want to send the mail to
  - mail_address_sender: from which mail do you want to send
  - mail_address_password: password for mail to send
  - api_key: gate.io api key
  - api_secret: gate.io api secret
- sudo pip3 install -r requirements.txt
- scrapy crawl binance -O newListings.json && python3 main.py
- before first run, make sure that oldListings.json is up do date. So you don't accidentally buy something, you don't want to buy