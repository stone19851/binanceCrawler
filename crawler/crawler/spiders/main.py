import collections
import time
import hashlib
import hmac
import requests
import re
import json
import os
import yagmail
import configparser
from datetime import datetime

file1 = open("binanceCrawler.txt","a")

config = configparser.ConfigParser()
config.read_file(open(r'settings.txt'))
settings_mail_address_recipient = config.get('settings', 'mail_address_recipient')
settings_mail_address_sender = config.get('settings', 'mail_address_sender')
settings_mail_address_password = config.get('settings', 'mail_address_password')
settings_api_key = config.get('settings', 'api_key')
settings_api_secret = config.get('settings', 'api_secret')

mail_address = settings_mail_address_recipient

# Spot/margin trade Read and write
# wallet Read only
api_key = settings_api_key
api_secret = settings_api_secret

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

yag = yagmail.SMTP(settings_mail_address_sender, settings_mail_address_password)

def gen_sign(method, url, query_string=None, payload_string=None):
    key = api_key
    secret = api_secret

    t = time.time()
    m = hashlib.sha512()
    m.update((payload_string or "").encode('utf-8'))
    hashed_payload = m.hexdigest()
    s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
    sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}

def get_ticker(pair):
    url = '/spot/tickers'
    query_param = 'currency_pair=' + pair
    r = requests.request('GET', host + prefix + url + '?' + query_param, headers=headers)
    last_price = r.json()[0]['last']
    file1.write("{0} -- last_price: {1}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M"), last_price))
    last_price = float(last_price)
    last_price = last_price + last_price / 100 * 5
    file1.write("{0} -- last_price + 5%: {1}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M"), str(last_price)))
    return str(last_price)


def get_balance(last_price):
    last_price_float = float(last_price)
    url = '/wallet/sub_account_balances'
    query_param = ''
    sign_headers = gen_sign('GET', prefix + url, query_param)
    headers.update(sign_headers)
    r = requests.request('GET', host + prefix + url, headers=headers)
    amount = 0
    if r.text != '[]':
        usdt_amount = float(r[0]['available']['USDT'])
        file1.write("{0} -- USDT available on wallet: {1}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M"), usdt_amount))
        amount = round(usdt_amount / last_price_float, 5)
        file1.write("{0} -- How much coins can be bougth: {1}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M"), amount))
    return amount


def place_order(pair, amount, last_price):
    url = '/spot/orders'
    query_param = ''
    body = '{"currency_pair":"'+pair+'","type":"limit","account":"spot","side":"buy","amount":"'+str(amount)+'","price":"'+last_price+'","time_in_force":"gtc"}'
    sign_headers = gen_sign('POST', prefix + url, query_param, body)
    headers.update(sign_headers)
    r = requests.request('POST', host + prefix + url, headers=headers, data=body)
    if r.status_code == 200:
        # send mail here
        mail_text = 'Erfolgreich gekauft'
        yag.send(mail_address, mail_text, mail_text)
    else:
        # send mail here
        mail_text = 'Fehler beim Kauf'
        yag.send(mail_address, mail_text, mail_text)

    file1.write("{0} -- Status code: {1}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M"), str(r.status_code)))
    file1.write("{0} -- Content: {1}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M"), str(r.content)))


def apply_regex(txt):
    pattern = '\(([A-Z]{2,})\)'
    return re.findall(pattern, txt)


def read_json():
    # Opening JSON file
    f = open('newListings.json', )
    g = open('oldListings.json', )

    # returns JSON object as a dictionary
    data1 = json.load(f)
    data2 = json.load(g)
    diff = [x for x in data1 if x not in data2]
    if diff:
        file1.write("{0} -- New entry in listings: ".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
        file1.write(str(diff) + "\n")

        # delete data2
        os.rename('oldListings.json', 'save.json')

        # rename data to data2
        os.rename('newListings.json', 'oldListings.json')

        os.rename('save.json', 'newListings.json')

    # Closing file
    f.close()
    g.close()

    if not diff:
        return []

    return diff[0]['heading'][0]

def keep_last_n_and_return_first_of_last_n(filename, n):
    with open(filename, "r") as inp:
         lines = collections.deque(inp, maxlen=n)
    with open(filename, "w") as out:
         out.writelines(lines)
    return lines[0]

if __name__ == "__main__":
    entry = read_json()

    if entry:
        matches = apply_regex(entry)
        #get first match
        if matches:
            for match in matches:
                mail_text = match + ' is now on binance'
                # sending mail here
                yag.send(mail_address, mail_text, mail_text)

                #iterate over all matches
                #for match in matches:
                pair = match + '_USDT'
                file1.write("{0} -- Trading pair: {1}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M"), pair))
                last_price = get_ticker(pair)
                amount = get_balance(last_price)
                place_order(pair, amount, last_price)
                if amount != 0:
                    place_order(pair, amount, last_price)
                else:
                    file1.write("{0} -- No money on wallet\n".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
        else:
            file1.write("{0} -- No new listing found\n".format(datetime.now().strftime("%Y-%m-%d %H:%M")))

    else:
        file1.write("{0} -- No new entry on binance\n".format(datetime.now().strftime("%Y-%m-%d %H:%M")))

    file1.close()
    keep_last_n_and_return_first_of_last_n('binanceCrawler.txt', 10000)
