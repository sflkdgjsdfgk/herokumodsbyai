# meta developer: @modsbyai

from herokutl.types import Message #[span_2](start_span)[span_2](end_span)
from .. import loader, utils #[span_3](start_span)[span_3](end_span)

@loader.tds #[span_4](start_span)[span_4](end_span)
class MuteModule(loader.Module):
    """Модуль для управления мутом собеседника и обхода бизнес-ботов."""
    
    strings = { #[span_5](start_span)[span_5](end_span)
        "name": "Mute",
        "no_reply": "❌ Ответьте на сообщение пользователя или используйте команду в ЛС.",
        "self_mute": "❌ Нельзя замутить самого себя.",
        "dmute_on": "🤫 Пользователь ограничен. Его сообщения в этом чате будут удаляться.",
        "dmute_off": "✅ Пользователь успешно размучен.",
        "dnomute_on": "✅ Тоггл dnomute ВКЛЮЧЕН в этом чате.",
        "dnomute_off": "❌ Тоггл dnomute ВЫКЛЮЧЕН в этом чате."
    }
    
    async def client_ready(self, client, db):
        self.client = client
        self._db = db
        self.me = await client.get_me()
        self.tg_id = self.me.id
    
    @loader.command(ru_doc="Замутить пользователя (ответом или в ЛС)") #[span_6](start_span)[span_6](end_span)
    async def dmute(self, message: Message):
        reply = await message.get_reply_message()
        target_id = None
        
        if reply:
            target_id = reply.sender_id
        elif message.is_private:
            target_id = message.chat_id
        else:
            await utils.answer(message, self.strings["no_reply"]) #[span_7](start_span)[span_7](end_span)
            return
            
        if target_id == self.tg_id:
            await utils.answer(message, self.strings["self_mute"]) #[span_8](start_span)[span_8](end_span)
            return
            
        # Прямое обращение к БД с указанием владельца (owner)[span_9](start_span)[span_9](end_span)
        muted_users = self._db.get(self.strings["name"], f"muted_{message.chat_id}", []) or [] #[span_10](start_span)[span_10](end_span)
        if target_id not in muted_users:
            muted_users.append(target_id)
            self._db.set(self.strings["name"], f"muted_{message.chat_id}", muted_users) #[span_11](start_span)[span_11](end_span)
            
        await self.inline.form(
            text=self.strings["dmute_on"],
            message=message,
            reply_markup=[
                [{"text": "🔓 Размутить", "callback": self.inline_unmute, "args": (target_id, message.chat_id)}]
            ]
        )
        
    @loader.command(ru_doc="Размутить пользователя (ответом или в ЛС)") #[span_12](start_span)[span_12](end_span)
    async def dunmute(self, message: Message):
        reply = await message.get_reply_message()
        target_id = None
        
        if reply:
            target_id = reply.sender_id
        elif message.is_private:
            target_id = message.chat_id
        else:
            await utils.answer(message, self.strings["no_reply"]) #[span_13](start_span)[span_13](end_span)
            return
            
        muted_users = self._db.get(self.strings["name"], f"muted_{message.chat_id}", []) or [] #[span_14](start_span)[span_14](end_span)
        if target_id in muted_users:
            muted_users.remove(target_id)
            self._db.set(self.strings["name"], f"muted_{message.chat_id}", muted_users) #[span_15](start_span)[span_15](end_span)
            
        await utils.answer(message, self.strings["dmute_off"]) #[span_16](start_span)[span_16](end_span)
        
    async def inline_unmute(self, call, target_id, chat_id):
        """Коллбэк для инлайн-кнопки размута."""
        
        # Безопасное извлечение ID для обёртки Pydantic
        clicker_id = getattr(call, "from_id", getattr(call, "user_id", getattr(call, "sender_id", None)))
        
        if clicker_id and clicker_id != target_id and clicker_id != self.tg_id:
            await call.answer("Вы не можете использовать эту кнопку!", show_alert=True)
            return
            
        muted_users = self._db.get(self.strings["name"], f"muted_{chat_id}", []) or [] #[span_17](start_span)[span_17](end_span)
        if target_id in muted_users:
            muted_users.remove(target_id)
            self._db.set(self.strings["name"], f"muted_{chat_id}", muted_users) #[span_18](start_span)[span_18](end_span)
            
        await call.edit(self.strings["dmute_off"])
        
    @loader.command(ru_doc="Тоггл обхода бизнес-ботов в текущем чате") #[span_19](start_span)[span_19](end_span)
    async def dnomute(self, message: Message):
        nomute_chats = self._db.get(self.strings["name"], "nomute_chats", []) or [] #[span_20](start_span)[span_20](end_span)
        chat_id = message.chat_id
        
        if chat_id in nomute_chats:
            nomute_chats.remove(chat_id)
            self._db.set(self.strings["name"], "nomute_chats", nomute_chats) #[span_21](start_span)[span_21](end_span)
            await utils.answer(message, self.strings["dnomute_off"]) #[span_22](start_span)[span_22](end_span)
        else:
            nomute_chats.append(chat_id)
            self._db.set(self.strings["name"], "nomute_chats", nomute_chats) #[span_23](start_span)[span_23](end_span)
            await utils.answer(message, self.strings["dnomute_on"]) #[span_24](start_span)[span_24](end_span)
            
    # Используем тег only_messages для перехвата только сообщений[span_25](start_span)[span_25](end_span)
    @loader.watcher(only_messages=True) #[span_26](start_span)[span_26](end_span)
    async def watcher(self, message: Message):
        """Отлавливает сообщения для dmute и dnomute."""
        if getattr(message, "chat_id", None) is None:
            return
            
        if getattr(message, "out", False):
            nomute_chats = self._db.get(self.strings["name"], "nomute_chats", []) or [] #[span_27](start_span)[span_27](end_span)
            if message.chat_id in nomute_chats and getattr(message, "text", None):
                if message.text.startswith("."):
                    return
                if message.text.endswith("\u200b"):
                    return
                    
                text_to_send = message.text + "\u200b"
                
                try:
                    await message.delete()
                    msg1 = await message.client.send_message(message.chat_id, text_to_send)
                    await message.client.send_message(message.chat_id, text_to_send)
                    await msg1.delete()
                except Exception:
                    pass
            return

        if not getattr(message, "out", False):
            muted_users = self._db.get(self.strings["name"], f"muted_{message.chat_id}", []) or [] #[span_28](start_span)[span_28](end_span)
            sender_id = getattr(message, "sender_id", None)
            
            if sender_id and sender_id in muted_users:
                try:
                    await message.delete()
                except Exception:
                    pass
