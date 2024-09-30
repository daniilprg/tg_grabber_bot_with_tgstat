import os, platform, sys
import asyncio, threading

import aiohttp

from telethon import TelegramClient, events, sync
from telethon.errors import SessionPasswordNeededError

# Consts
HELP = (
    """Справочная информация о командах:
create <имя_связки> <канал>		Добавить связку по имени с идентификатором вашего канала
delete <имя_связки>			Удалить связку по имени
insert <имя_связки> <канал>		Добавить в связку канал по идентификатору
remove <имя связки> <канал>     	Удалить в связке канал по идентификатору
print <имя_связки>			Список каналов в связке
help					Сведения о командах
list					Список всех связок
clear					Очистить командную строку
exit					Выход из программы
"""
)


class GrabberBot:

    def __init__(self) -> None:
        self.list = {}
        self.stop_thread = False
        self.API_ID = 20419714
        self.API_HASH = "feee2b161028b2ce71cc92ede611e4ed"
        self.client = TelegramClient(session='my_account', api_id=self.API_ID, api_hash=self.API_HASH)
        self.is_auth = False

    async def telegram_client_create(self):
        await self.client.connect()

        if not await self.client.is_user_authorized():
            print("Сессия не найдена")
            print("\nАвторизация:")
            print("Введите номер телефона")

            phone_number = input('>>> ')

            await self.client.sign_in(phone_number)

            try:
                print("Введите отправленный код")
                await self.client.sign_in(code=input('>>> '))
            except SessionPasswordNeededError:
                print("Введите пароль")
                get_pass = input('>>> ')
                await self.client.sign_in(password=get_pass)
            print('Вы вошли в аккаунт\n')

        self.is_auth = True

        await self.grabber()

    async def grabber(self):
        """
        Grabber
        """
        @self.client.on(events.NewMessage)
        async def handler(event):
            for item in self.list.keys():
                for key, value in self.list[item].items():
                    if str(event.chat_id) in value:
                        await asyncio.sleep(240)
                        # sender = await event.get_sender()
                        # post_id = f't.me/{sender.username}/{event.message.id}'
                        async with aiohttp.ClientSession() as session:
                            async with session.get(url='https://api.tgstat.ru/posts/stat',
                                                   params={'token': '62fefd0c2643488f4022f918865cbcc5',
                                                           'postId': f't.me/c/{event.message.peer_id.channel_id}/{event.message.id}'
                                                           }
                                                   ) as response:
                                response = await response.json()

                                if response['status'] == 'ok':
                                    message_before_post = (f"<b>Ссылка на пост:</b>\n"
                                                           f"t.me/c/{event.message.peer_id.channel_id}/{event.message.id}\n\n"
                                                           f"<b>Статистика:</b>\n"
                                                           f"Кол-во просмотров: {response['response']['viewsCount']}\n"
                                                           f"Кол-во пересылок: {response['response']['sharesCount']}\n"
                                                           f"Кол-во комментариев: {response['response']['commentsCount']}\n"
                                                           f"Кол-во реакций: {response['response']['reactionsCount']}\n\n"
                                                           f"Доп. коэффициент: "
                                                           f"{round((int(response['response']['sharesCount']) / int(response['response']['viewsCount'])) * 100, 3)}%"
                                                           )

                                    post = await self.client.send_message(int(key), event.message)
                                    await self.client.send_message(int(key), message=message_before_post, reply_to=post.id, parse_mode='HTML')

        await self.client.run_until_disconnected()

    def start_telegram_client(self):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.telegram_client_create())

    async def telegram_session_disconnect(self):
        await self.client.disconnect()

    def list_management(self) -> None:
        """
        Case menu
        """

        while True:
            if self.is_auth:
                command = input('>>> ')

                if command.startswith('create '):
                    command = command.split()[1:3]

                    if command and not (command[0] in self.list) and len(command) == 2:
                        self.list[command[0]] = {command[1]: []}
                        print(f'Связка "{command[0]}" создана\n')
                    else:
                        print(f'Вы не ввели название связки или такая связка уже существует\n')

                elif command.startswith('delete '):
                    command = command.split()[1:2]

                    if command:
                        link_name = ''.join(command)

                        if link_name in self.list:
                            self.list.pop(link_name)
                            print(f'Связка "{link_name}" удалена\n')
                        else:
                            print(f'Связки "{link_name}" не существует\n')
                    else:
                        print(f'Вы не ввели название связки\n')

                elif command.startswith('insert '):
                    command = command.split()[1:3]

                    if len(command) == 2 and command[0] in self.list and not (command[1] in self.list[command[0]]):
                        for item in self.list[command[0]].keys():
                            self.list[command[0]][item].append(command[1])

                        print(f'Идентификатор "{command[1]}" канала добавлен в связку "{command[0]}"\n')
                    else:
                        print(
                            f'Вы не ввели название связки или идентификатор канала, которого нет в связке, или такой связки не существует\n')

                elif command.startswith('remove '):
                    command = command.split()[1:3]

                    if len(command) == 2 and command[0] in self.list:
                        for item in self.list[command[0]].keys():
                            if command[1] in self.list[command[0]][item]:
                                self.list[command[0]][item].remove(command[1])
                                print(f'Идентификатор "{command[1]}" канала удалён из связки "{command[0]}"\n')
                            else:
                                print(f'Вы не ввели название связки или идентификатор канала, или такой связки не существует\n')
                    else:
                        print(f'Вы не ввели название связки или идентификатор канала, или такой связки не существует\n')

                elif command.startswith('print '):
                    command = command.split()[1:2]

                    if command[0] in self.list:
                        print(
                            f'Список каналов в связке "{command[0]}" вашего канала "{[item for item in self.list[command[0]].keys()][0]}":')

                        for item in self.list[command[0]].keys():
                            for index in range(len(self.list[command[0]][item])):
                                print(f'{index + 1}.', self.list[command[0]][item][index])
                        print()
                    else:
                        print(f'Вы не ввели название связки или идентификатор канала, или такой связки не существует\n')

                elif command.startswith('list') and command.endswith('list'):
                    print('Список созданных связок:')

                    count = 1
                    for key in self.list.keys():
                        print(f'{count}.', key)
                        count += 1
                    print()

                elif command.startswith('help') and command.endswith('help'):
                    print(HELP)

                elif command.startswith('exit') and command.endswith('exit'):
                    print('Завершение процессов')
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.telegram_session_disconnect())
                    sys.exit(0)

                elif command.startswith('clear') and command.endswith('clear'):
                    if platform.system() == 'Windows':
                        os.system('cls')
                    else:
                        os.system('clear')
                else:
                    print(f'"{command}" не является командой или команда задана без параметров\n')


if __name__ == "__main__":
    print('Контакты разработчика: https://t.me/ar1hant\n\n' + HELP)

    obj = GrabberBot()

    task = threading.Thread(target=obj.start_telegram_client)
    task2 = threading.Thread(target=obj.list_management)
    task.start()
    task2.start()
    task.join()
    task2.join()
