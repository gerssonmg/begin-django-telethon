import threading
from telethon import TelegramClient


api_id = 7647546
api_hash = 'c2f716ab581c86a4f3158c5529d51d8d'

print("BEGIN class thread out")
class BotScrapingTelegramThread(threading.Thread):
    print("BEGIN class thread insider")
    def __init__(self, total):
        print(total)
        threading.Thread.__init__(self)

    def run(self):
        print("BEGIN RUN")
        try:
            client = TelegramClient('session_name', api_id, api_hash)
            client.start()
            print('Begin Thread')
            me = client.get_me()
            print(me.stringify())
            print("Carol")
            for i in range(0,10000):
                if i == 1000 or i == 6000:
                    print('AQUI')
        except Exception as e:
            print("DEU RUIM")
            print(e)


# api_id = 7647546
# api_hash = 'c2f716ab581c86a4f3158c5529d51d8d'
# #
# # client = TelegramClient('session_name', api_id, api_hash)
# #
# #
# # async def get_message_telegram():
# #     # These example values won't work. You must get your own api_id and
# #     # api_hash from https://my.telegram.org, under API Development.
# #
# #     me = await client.get_me()
# #
# #     print(me.stringify())
# #
# #
# # async def _get_messages():
# #     diego = await client.get_messages(-1001323428126, 1)
# #     print(diego)
# #
# #
# # with client:
# #     client.loop.run_until_complete(get_message_telegram())
# #
#
# # with client:
# #     client.loop.run_until_complete(_get_messages())
