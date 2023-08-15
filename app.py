# -*- coding: utf-8 -*-
import os
import sys
import random
import requests
import unicodedata
from bs4 import BeautifulSoup
from argparse import ArgumentParser
from imgurpython import ImgurClient
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, SourceGroup, SourceRoom, ImageSendMessage

app = Flask(__name__)

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

def meme_programmer():
    url = "https://programming-memes-images.p.rapidapi.com/v1/memes"
    headers = {
        "X-RapidAPI-Key": os.getenv("PRGM_KEY", None),
        "X-RapidAPI-Host": "programming-memes-images.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)
    api_return = response.json()
    
    client_id = os.getenv("IMGUR_ID", None)
    client_secret = os.getenv("IMGUR_SECRET", None)
    access_token = os.getenv("IMGUR_ACCESS", None)
    refresh_token = os.getenv("IMGUR_REFRESH", None)
    
    client = ImgurClient(client_id, client_secret, access_token, refresh_token)
    
    response = client.upload_from_url(api_return[0]['image'], config = None, anon = True)
    
    return  response['link']


def meme_reddit():
    url = "https://memes-from-reddit.p.rapidapi.com/memes"
    headers =  {
    	"X-RapidAPI-Key": os.getenv("REDDIT_KEY", None),
    	"X-RapidAPI-Host": "memes-from-reddit.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)
    api_return = response.json()['data']
    api_return = [i for i in api_return if '.jpg' in i['url']]
    jpg_link = random.choice(api_return)['url']
    return jpg_link

def shorten_url(url):
    api_url = f"http://tinyurl.com/api-create.php?url={url}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text
    else:
        return url

def recommend_food(search):
    city = ''
    distinct = ''
    cat = ''
    level = ''
    if  search.split('/')[0] != '':
        city = search.split('/')[0]+'/'
    
    if search.split('/')[1] != '':
        distinct = search.split('/')[1]+'/'
        
    if search.split('/')[2] != '':
        cat = '/'+search.split('/')[2]
    
    if search.split('/')[3] != '':
        price = int(search.split('/')[3])
        if price < 150:
            pb = '1'
        elif price <= 600:
            pb = '2'
        elif price <= 1200:
            pb = '3'
        else:
            pb = '4'
        level = '&priceLevel=' + pb

    url = 'https://ifoodie.tw/explore/' + city + distinct + 'list' + cat + '?sortby=popluar' + level
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    cards = soup.find_all(
           'div', {'class': 'jsx-1156793088 info-rows'}, limit=10)

    content = ""
    for card in cards:
        title_element = card.find("a", {"class": "jsx-1156793088 title-text"})
        title = getattr(title_element, 'getText', lambda: '')()
        
        stars_element = card.find("div", {"class": "jsx-2373119553 text"})
        stars = getattr(stars_element, 'getText', lambda: '')()
        
        avg_element = card.find("div", {"class": "jsx-1156793088 avg-price"})
        avg = getattr(avg_element, 'getText', lambda: '')()
        
        address_element = card.find("div", {"class": "jsx-1156793088 address-row"})
        address = getattr(address_element, 'getText', lambda: '')()
        
        description_element = card.find('a')
        description = 'https:/ifoodie.tw' + description_element['href'] if description_element else ''
        short_url = shorten_url(description)

        content += f"{title} ({stars}顆星{avg}) \n{address} \n{short_url}\n\n"
    
    return content

def get_weather(location):
    api_key = os.getenv("WTHR_KEY", None)
    weather_api_url = f"https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={api_key}&format=JSON&locationName={location}"
    response = requests.get(weather_api_url)
    data = response.json()
    
    try:
        records = data['records']['location'][0]['weatherElement']
        tod_des = records[0]['time'][0]['parameter']['parameterName']
        tod_drop = records[1]['time'][0]['parameter']['parameterName'] +'%'
        tod_low = records[2]['time'][0]['parameter']['parameterName'] + '度' 
        tod_high = records[4]['time'][0]['parameter']['parameterName'] + '度'
        tom_des = records[0]['time'][2]['parameter']['parameterName']
        tom_drop = records[1]['time'][2]['parameter']['parameterName'] +'%'
        tom_low = records[2]['time'][2]['parameter']['parameterName'] + '度'
        tom_high = records[4]['time'][2]['parameter']['parameterName'] + '度'
        
        content = f"今天{tod_des}，最低溫:{tod_low}/最高溫:{tod_high}，降雨機率:{tod_drop}\n明日{tom_des}，最低溫:{tom_low}/最高溫:{tom_high}，降雨機率:{tom_drop}"
    
    except KeyError:
        content = '未找到相關天氣數據'
    
    return content

@handler.add(MessageEvent, message=TextMessage)
def line_send_image(func, event):
    image_link = func
    try: 
        line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_link, preview_image_url=image_link))
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text= image_link + 'Sorry~故障囉！'))

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    reply_mess = ''
    inputs = unicodedata.normalize('NFKC', event.message.text.lower())
    if '重複:' in inputs :
        reply_mess = inputs.replace('重複:','')

    elif 'chatim掰' in inputs:
        if isinstance(event.source, SourceGroup):
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.leave_room(event.source.room_id)
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='抱歉，你只能繼續跟我1v1'))
            
    elif 'programmer' in inputs:
        line_send_image(meme_programmer(), event)
            
    elif 'reddit' in inputs:
        line_send_image(meme_reddit(), event)
    
    elif '本日運勢' in inputs:
        reply_mess = random.choice(['大凶', '凶', '末吉', '吉','小吉', '中吉','大吉'])

    elif '美食:' in inputs:
        search = inputs.replace('美食:', '')
        # reply_mess = recommend_food(search)
        try: 
            reply_mess = recommend_food(search)
        except:
            reply_mess = 'ㄅ欠~搜尋關鍵字有誤，請檢查格式或可能沒有該分類'
            
    elif '天氣:' in inputs:
        reply_mess = get_weather(inputs.replace('天氣:', '')
                                 
    elif 'function' in inputs:
        reply_mess = '''1. 重複:\n說明 : 重複別人說的話\n\n2. programmer\n說明 : 工程師meme\n\n3. reddit\n說明 : reddit meme\n\n4. 本日運勢\n說明 : BJ4\n\n5. 美食:\n說明 : 請按照以下格式依序填寫(其中一定要有城市，其餘可有可無)\nXX市/XX區/類型/期待均消(數值，不吃範圍)\nex.台北市/中山區/拉麵/300\n\n6. chatim掰\n說明 : 請chatim走人\n\nHave a nice day~
        '''
    else:
        None
        
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_mess)
    )


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)


'''
def imgur_authenticate():
    # Get client ID and secret from config.py
    client_id = 
    client_secret = 
    
    client = imgurpython.ImgurClient(client_id, client_secret)

    # Authorization flow, pin example (see docs for other auth types)
    authorization_url = client.get_auth_url('pin')

    print("Go to the following URL: {0}".format(authorization_url))

    # Read in the pin, handle Python 2 or 3 here.
    pin = 'XXXXX'
    # ... redirect user to `authorization_url`, obtain pin (or code or token) ...
    credentials = client.authorize(pin, 'pin')
    client.set_user_auth(credentials['access_token'], credentials['refresh_token'])

    print("Authentication successful! Here are the details:")
    print("   Access token:  {0}".format(credentials['access_token']))
    print("   Refresh token: {0}".format(credentials['refresh_token']))
    # access_token = 
    # refresh_token = 

    return client
'''
