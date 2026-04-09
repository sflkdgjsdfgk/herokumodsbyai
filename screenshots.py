# meta developer: @modsbyai
# meta telegram: @modsbyai

import asyncio
from herokutl.types import Message
from herokutl.tl import functions, types
from .. import loader, utils

@loader.tds
class ScrSpamMod(loader.Module):
    """Обновленная версия модуля спама скриншотами (оригинал от KeyZenD)"""
    
    strings = {
        "name": "ScrSpam",
        "forbidden": "❌ <b>В Избранном нельзя!</b>",
        "error": "❌ <b>Ошибка отправки.</b>",
        "stop": "🛑 <b>Спам остановлен.</b>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "delay", 0.1, "Задержка (сек)", 
                validator=loader.validators.Float(minimum=0.01)
            ),
            loader.ConfigValue(
                "remove", "after", 
                "Удаление команды: no, instant, after",
                validator=loader.validators.Choice(["no", "instant", "after"])
            )
        )
        self._active_spams = set()

    async def _send_ss(self, client, chat_id, message_id=None):
        """Максимально быстрый метод отправки"""
        try:
            peer = await client.get_input_entity(chat_id)
            # Проверка на Saved Messages
            me = await client.get_me()
            if hasattr(peer, 'user_id') and peer.user_id == me.id:
                return "forbidden"

            reply_to = types.InputReplyToMessage(reply_to_msg_id=message_id) if message_id else None
            await client(functions.messages.SendScreenshotNotificationRequest(peer=peer, reply_to=reply_to))
            return True
        except:
            try:
                await client(functions.messages.SendScreenshotNotificationRequest(
                    peer=await client.get_input_entity(chat_id),
                    reply_to=None
                ))
                return True
            except: return False

    @loader.command(ru_doc="[кол-во] - Запустить спам скриншотами")
    async def scrs(self, message: Message):
        """.scrs <количество>"""
        args = utils.get_args(message)
        
        # ЛОГИКА ТУРБО-ОТПРАВКИ (если без числа)
        is_single = not (args and args[0].isdigit())
        count = 1 if is_single else int(args[0])
        
        reply = await message.get_reply_message()
        msg_id = reply.id if reply else message.id
        chat_id = message.chat_id
        
        # Если одиночный вызов — удаляем сразу, не глядя в конфиг
        if is_single or self.config["remove"] == "instant":
            await message.delete()
        
        # Для спама регистрируем процесс
        if not is_single:
            self._active_spams.add(chat_id)
        
        success = False
        for i in range(count):
            if not is_single and chat_id not in self._active_spams:
                break
                
            res = await self._send_ss(message.client, chat_id, msg_id)
            
            if res == "forbidden":
                if not is_single or self.config["remove"] == "no":
                    await utils.answer(message, self.strings["forbidden"])
                self._active_spams.discard(chat_id)
                return
            
            if res is True: success = True
            
            if i < count - 1:
                await asyncio.sleep(self.config["delay"])

        if not is_single:
            self._active_spams.discard(chat_id)
            # Если был спам и режим after — удаляем в конце
            if self.config["remove"] == "after":
                try: await message.delete()
                except: pass
            elif self.config["remove"] == "no" and success:
                await utils.answer(message, "✅ <b>Готово!</b>")

    @loader.command(ru_doc="Остановить спам в текущем чате")
    async def scrstop(self, message: Message):
        """Остановить запущенный спам"""
        if message.chat_id in self._active_spams:
            self._active_spams.remove(message.chat_id)
            await utils.answer(message, self.strings["stop"])
        else:
            await message.delete()
