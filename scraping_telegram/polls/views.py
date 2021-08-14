import time

from django.shortcuts import render
from django.http import HttpResponse
from telethon import TelegramClient

api_id = 7647546
api_hash = 'c2f716ab581c86a4f3158c5529d51d8d'

client = TelegramClient('session_name', api_id, api_hash)


async def get_message_telegram():
    # These example values won't work. You must get your own api_id and
    # api_hash from https://my.telegram.org, under API Development.

    me = await client.get_me()

    print(me.stringify())


async def _get_messages():
    while True:

        last_message_my_channel = await client.get_messages(-1001581627805, 1)
        diego = await client.get_messages(-1001323428126, 1)

        if last_message_my_channel[0].message != diego[0].message:
            print("NEW MSG")
            await client.send_message(-1001581627805, diego[0].message)
        time.sleep(0.5)


with client:
    client.loop.run_until_complete(get_message_telegram())


with client:
    client.loop.run_until_complete(_get_messages())


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
# Create your views here.
