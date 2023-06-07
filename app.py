# -*- coding: utf-8 -*-
import os
import sys
import requests
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
        "X-RapidAPI-Key": "2eb4ae18demsha492b3b31ae7229p11a89ajsn374987e29bb9",
        "X-RapidAPI-Host": "programming-memes-images.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)
    api_return = response.json()
   
    # res_img = requests.get(api_return[0]['image'])
    # image = res_img.content
    # from PIL import Image
    # import io
    # stream = io.BytesIO(image)    
    # image2 = Image.open(stream)
    
    client_id = '911cca3455d90f1'
    client_secret = '6abd7b8943b34f18ba0500836812171a0a687725'
    access_token = '2e57b37c2f63e005904008e26fa3374a4af92ac3'
    refresh_token = '10808e6a470f8b172a8188d151d11c6a343d2242'
    
    client = ImgurClient(client_id, client_secret, access_token, refresh_token)
    
    response = client.upload_from_url(api_return[0]['image'], config = None, anon = True)
    
    return  response['link']

# def meme_reddit():
#     url = "https://random-stuff-api.p.rapidapi.com/reddit/RandomMeme"
#     querystring = {"searchType":"hot"}
#     headers = {
#     	"Authorization": "chrnMsqPx8Ww",
#     	"X-RapidAPI-Key": "2eb4ae18demsha492b3b31ae7229p11a89ajsn374987e29bb9",
#     	"X-RapidAPI-Host": "random-stuff-api.p.rapidapi.com"
#     }
#     response = requests.get(url, headers=headers, params=querystring)

#     api_return = response.json()
    
#     return api_return['thumbnail']

def meme_reddit2(cat):
    url = 'https://reddit-meme.p.rapidapi.com/memes/' + cat
    headers = {
    	"X-RapidAPI-Key": "2eb4ae18demsha492b3b31ae7229p11a89ajsn374987e29bb9",
    	"X-RapidAPI-Host": "reddit-meme.p.rapidapi.com"
    }
    
    response = requests.get(url, headers=headers)

    api_return = response.json()
    api_return_filter = [i for i in api_return if '.gif' in i['url'] or '.jpeg' in i['url'] or '.png' in i['url'] or '.jpg' in i['url']]
    
    return api_return_filter[0]['url']


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
    if '重複' in event.message.text:
        reply_mess = event.message.text.replace('重複','')
        
#     elif 'FATZ' in str.upper(event.message.text):
#         reply_mess = '喔不!!'
#     elif '噗鼠' in event.message.text:
#         reply_mess = 'MD'

    elif 'chatim掰' in event.message.text:
        if isinstance(event.source, SourceGroup):
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.leave_room(event.source.room_id)
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='抱歉，你只能繼續跟我1v1'))
            
    elif 'programmer' in event.message.text:
        line_send_image(meme_programmer(), event)
            
    elif 'reddit' in event.message.text:
        line_send_image(meme_reddit2('trending'), event)
        
    else:
        return
        
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
