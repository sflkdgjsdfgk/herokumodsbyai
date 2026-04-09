# meta developer: @modsbyai

from herokutl.types import Message
from .. import loader, utils
import io

@loader.tds
class StickerManagerMod(loader.Module):
    """Удобное управление стикерами и получение информации о них"""
    # Автор: @modsbyai

    strings = {
        "name": "StickerManager",
        "info": "<b>🎨 Sticker Information:</b>\n\n"
                "<b>ID:</b> <code>{}</code>\n"
                "<b>Emoji:</b> {}\n"
                "<b>Pack:</b> <a href=\"https://t.me/addstickers/{}\">{}</a>",
        "no_sticker": "<b>❌ Reply to a sticker!</b>",
        "no_reply": "<b>ℹ️ You need to reply to a message with a sticker.</b>",
        "saving": "<b>📥 Downloading sticker as file...</b>"
    }

    strings_ru = {
        "info": "<b>🎨 Информация о стикере:</b>\n\n"
                "<b>ID:</b> <code>{}</code>\n"
                "<b>Эмодзи:</b> {}\n"
                "<b>Пак:</b> <a href=\"https://t.me/addstickers/{}\">{}</a>",
        "no_sticker": "<b>❌ Ответь на стикер!</b>",
        "no_reply": "<b>ℹ️ Нужно ответить на сообщение со стикером.</b>",
        "saving": "<b>📥 Скачиваю стикер в файл...</b>"
    }

    @loader.command(
        ru_doc="Узнать информацию о стикере через реплай"
    )
    async def stinfo(self, message: Message):
        """Get sticker info via reply"""
        reply = await message.get_reply_message()
        
        if not reply:
            await utils.answer(message, self.strings["no_reply"])
            return

        if not getattr(reply, "sticker", None):
            await utils.answer(message, self.strings["no_sticker"])
            return

        s = reply.sticker
        
        # Безопасно достаем данные, учитывая особенности Telethon Document
        sticker_id = getattr(s, 'id', 'Unknown')
        
        # Поиск эмодзи в атрибутах, если .emoji отсутствует
        emoji = "❓"
        if hasattr(s, 'attributes'):
            for attr in s.attributes:
                if hasattr(attr, 'alt'):
                    emoji = attr.alt
                    break
        
        pack_name = getattr(s, 'set_short_name', 'None')

        text = self.strings["info"].format(
            sticker_id,
            emoji,
            pack_name,
            pack_name
        )
        await utils.answer(message, text)

    @loader.command(
        ru_doc="Скачать стикер как документ (PNG/WEBP)"
    )
    async def stfile(self, message: Message):
        """Download sticker as a file"""
        reply = await message.get_reply_message()
        
        if not reply or not getattr(reply, "sticker", None):
            await utils.answer(message, self.strings["no_sticker"])
            return

        message = await utils.answer(message, self.strings["saving"])
        
        sticker_bytes = await reply.download_media(file=io.BytesIO())
        sticker_id = getattr(reply.sticker, 'id', 'sticker')
        sticker_bytes.name = f"{sticker_id}.webp"
        sticker_bytes.seek(0)

        await message.client.send_file(
            message.chat_id, 
            sticker_bytes, 
            reply_to=reply.id
        )
        await message.delete()
