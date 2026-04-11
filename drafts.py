# meta developer: @modsbyai

import datetime
from herokutl.types import Message
from .. import loader, utils


@loader.tds
class DraftMod(loader.Module):
    """Модуль для управления черновиками"""

    strings = {
        "name": "Draft",
        "saved": "<b>✅ Черновик сохранен:</b>\n<code>{}</code>",
        "no_text": "<b>❌ Что сохранять? Ответьте на сообщение или введите текст.</b>",
        "list_header": "<b>📝 Список ваших черновиков:</b>\n\n",
        "no_drafts": "<b>📭 Список черновиков пуст.</b>",
        "draft_item": "<code>{}</code>. <b>{}</b>\n",
        "not_found": "<b>❌ Черновик с таким номером не найден.</b>",
        "deleted": "<b>🗑 Черновик №{} удален.</b>",
        "cleared": "<b>🧹 Все черновики удалены.</b>",
        "usage": (
            "<b>ℹ️ Справка по модулю Draft:</b>\n"
            "<code>{0}draft save [имя]</code> — сохранить (реплаем или текст)\n"
            "<code>{0}draft list</code> — список всех черновиков\n"
            "<code>{0}draft get [номер]</code> — получить текст черновика\n"
            "<code>{0}draft del [номер]</code> — удалить черновик\n"
            "<code>{0}draft clear</code> — очистить всё"
        ),
    }

    strings_ru = {
        "saved": "<b>✅ Черновик сохранен:</b>\n<code>{}</code>",
        "no_text": "<b>❌ Что сохранять? Ответьте на сообщение или введите текст.</b>",
        "list_header": "<b>📝 Список ваших черновиков:</b>\n\n",
        "no_drafts": "<b>📭 Список черновиков пуст.</b>",
        "draft_item": "<code>{}</code>. <b>{}</b>\n",
        "not_found": "<b>❌ Черновик с таким номером не найден.</b>",
        "deleted": "<b>🗑 Черновик №{} удален.</b>",
        "cleared": "<b>🧹 Все черновики удалены.</b>",
        "usage": (
            "<b>ℹ️ Справка по модулю Draft:</b>\n"
            "<code>{0}draft save [имя]</code> — сохранить (реплаем или текст)\n"
            "<code>{0}draft list</code> — список всех черновиков\n"
            "<code>{0}draft get [номер]</code> — получить текст черновика\n"
            "<code>{0}draft del [номер]</code> — удалить черновик\n"
            "<code>{0}draft clear</code> — очистить всё"
        ),
    }

    async def client_ready(self, client, db):
        self.db = db

    @loader.command(
        ru_doc="[save|list|get|del|clear] — Управление черновиками. Если аргумент отсутствует будет показана справка.",
    )
    async def draft(self, message: Message):
        """[save|list|get|del|clear] — Manage your drafts. Use .draft help for more info."""
        args = utils.get_args_raw(message)
        drafts = self.db.get("DraftMod", "drafts", [])
        
        # Получаем префикс из системы
        try:
            prefixes = await self.get_prefixes()
            prefix = prefixes[0] if prefixes else "."
        except Exception:
            prefix = "."

        if not args or args.lower() == "help":
            await utils.answer(message, self.strings["usage"].format(prefix))
            return

        parts = args.split(maxsplit=1)
        cmd = parts[0].lower()
        content = parts[1] if len(parts) > 1 else ""

        if cmd == "save":
            reply = await message.get_reply_message()
            text_to_save = ""
            
            if reply and reply.text:
                text_to_save = reply.text
                user_name = content
            else:
                text_to_save = content
                user_name = ""

            if not text_to_save:
                await utils.answer(message, self.strings["no_text"])
                return

            if user_name:
                draft_name = f"[{user_name}]"
            else:
                now = datetime.datetime.now().strftime("%d.%m/%H:%M")
                chat = await message.get_chat()
                chat_title = getattr(chat, "title", "Private")
                if len(chat_title) > 15:
                    chat_title = chat_title[:12] + "..."
                draft_name = f"{now} | {chat_title} #{len(drafts) + 1}"
            
            drafts.append({"name": draft_name, "text": text_to_save})
            self.db.set("DraftMod", "drafts", drafts)
            await utils.answer(message, self.strings["saved"].format(draft_name))

        elif cmd == "list":
            if not drafts:
                await utils.answer(message, self.strings["no_drafts"])
                return
            
            res = self.strings["list_header"]
            for i, d in enumerate(drafts, 1):
                res += self.strings["draft_item"].format(i, d["name"])
            await utils.answer(message, res)

        elif cmd == "get":
            if not content.isdigit():
                await utils.answer(message, self.strings["usage"].format(prefix))
                return
            
            idx = int(content) - 1
            if 0 <= idx < len(drafts):
                await utils.answer(message, drafts[idx]["text"])
            else:
                await utils.answer(message, self.strings["not_found"])

        elif cmd == "del":
            if not content.isdigit():
                await utils.answer(message, self.strings["usage"].format(prefix))
                return
            
            idx = int(content) - 1
            if 0 <= idx < len(drafts):
                drafts.pop(idx)
                self.db.set("DraftMod", "drafts", drafts)
                await utils.answer(message, self.strings["deleted"].format(idx + 1))
            else:
                await utils.answer(message, self.strings["not_found"])

        elif cmd == "clear":
            self.db.set("DraftMod", "drafts", [])
            await utils.answer(message, self.strings["cleared"])

        else:
            await utils.answer(message, self.strings["usage"].format(prefix))