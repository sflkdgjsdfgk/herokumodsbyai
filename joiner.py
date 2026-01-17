from herokutl.types import Message
from .. import loader, utils
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
# meta developer: @isdistorted

@loader.tds
class SimpleJoiner(loader.Module):
    """Clean & Fast Joiner Module"""
    strings = {
        "name": "SimpleJoiner",
        "joining": "<b>🪐 Вхожу в орбиту...</b>",
        "success": "<b>✅ Доступ получен:</b> <code>{}</code>",
        "error": "<b>❌ Провал:</b> <code>{}</code>"
    }

    @loader.command(ru_doc="Вступить в чат по ссылке или ID")
    async def join(self, message: Message):
        """<link/ID/username>"""
        # Получаем аргументы или текст из реплая
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message) or (reply.text if reply else None)

        if not args:
            await utils.answer(message, "<b>ℹ️ Куда заходим?</b>")
            return

        message = await utils.answer(message, self.strings["joining"])

        try:
            if "t.me/+" in args or "joinchat/" in args:
                # Работа с приватными инвайтами
                hash_code = args.split("/")[-1].replace("+", "")
                await self._client(ImportChatInviteRequest(hash_code))
                target_display = "Приватный чат"
            else:
                # Работа с публичными чатами и ID
                target = int(args) if args.isdigit() or args.startswith("-100") else args
                await self._client(JoinChannelRequest(target))
                target_display = args
            
            # Финальный красивый ответ
            await utils.answer(message, self.strings["success"].format(target_display))
        
        except Exception as e:
            # Если защита все еще ругается, мы увидим причину
            await utils.answer(message, self.strings["error"].format(str(e)))
