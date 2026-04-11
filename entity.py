# █▀▀ █▄░█ ▀█▀ █ ▀█▀ █▄█
# ██▄ █░▀█ ░█░ █ ░█░ ░█░
# Professional OSINT & Entity analysis tool.
# meta developer: @modsbyai

import time
import io
import re
import asyncio
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import User
from .. import loader, utils

@loader.tds
class EntityMod(loader.Module):
    """Мощный и лаконичный инструмент для сбора исчерпывающей информации о пользователе."""
    
    strings = {"name": "Entity"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            "agreed", False, "Согласие с правилами использования модуля",
            "dump_beta", False, "Включить экспериментальную функцию дампа"
        )
        self.timers = {}
        self.cache = {}

    async def client_ready(self, client, db):
        self.client = client

    # ==========================================
    #             УТИЛИТЫ И HTML
    # ==========================================
    
    def clean(self, text):
        """Экранирование символов для защиты форматирования"""
        if text is None: return ""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def get_tabs_keyboard(self, user_id, current_tab="main", has_phone=False):
        """Генерация клавиатуры вкладок"""
        kb = []
        row1 = [
            {"text": "👤 Главная" if current_tab != "main" else "· 👤 Главная ·", "callback": self.inline_tab, "args": [user_id, "main"]},
            {"text": "💎 Премиум" if current_tab != "prem" else "· 💎 Премиум ·", "callback": self.inline_tab, "args": [user_id, "prem"]},
        ]
        
        row2 = [{"text": "🚫 Отсутствует" if current_tab != "none" else "· 🚫 Отсутствует ·", "callback": self.inline_tab, "args": [user_id, "none"]}]
        
        if self.config["dump_beta"]:
            row2.append({"text": "📄 Дамп (Beta)", "callback": self.inline_dump, "args": [user_id]})
            
        kb.append(row1)
        kb.append(row2)
        
        if current_tab == "main" and has_phone:
            kb.append([{"text": "📞 Показать скрытый номер", "callback": self.inline_show_phone, "args": [user_id]}])
            
        return kb

    # ==========================================
    #             ОНБОРДИНГ (Its-legal?)
    # ==========================================

    async def start_onboarding(self, message, target_args):
        """Запуск 3-шагового онбординга"""
        user_id = int(message.sender_id) # Фикс PeerUser
        self.timers[user_id] = time.time() + 5
        
        text = (
            "⚖️ <b>Entity | Инициализация [Шаг 1/3]</b>\n\n"
            "Перед использованием модуля необходимо ознакомиться с правилами.\n\n"
            "<b>Легальность:</b> Данный модуль не использует сторонние базы данных. "
            "Вся информация получается исключительно легальным путём через официальный API Telegram (Telethon)."
        )
        
        await self.inline.form(
            text=text,
            message=message,
            reply_markup=[[{"text": "Продолжить ➡️", "callback": self.ob_step_2, "args": [target_args]}]]
        )

    async def ob_step_2(self, call, target_args):
        user_id = int(call.from_user.id)
        if time.time() < self.timers.get(user_id, 0):
            remain = int(self.timers[user_id] - time.time())
            return await call.answer(f"⏳ Пожалуйста, прочтите текст. Осталось: {remain} сек.", alert=False)
            
        self.timers[user_id] = time.time() + 5
        text = (
            "⚠️ <b>Entity | Ответственность [Шаг 2/3]</b>\n\n"
            "Автор модуля не несет ответственности за то, как вы распоряжаетесь полученной информацией.\n\n"
            "🚫 Писать в комментарии канала разработчика по поводу «доксинга» категорически запрещено."
        )
        await call.edit(
            text=text,
            reply_markup=[[{"text": "Продолжить ➡️", "callback": self.ob_step_3, "args": [target_args]}]]
        )

    async def ob_step_3(self, call, target_args):
        user_id = int(call.from_user.id)
        if time.time() < self.timers.get(user_id, 0):
            remain = int(self.timers[user_id] - time.time())
            return await call.answer(f"⏳ Пожалуйста, прочтите текст. Осталось: {remain} сек.", alert=False)
            
        text = (
            "✅ <b>Entity | Готово [Шаг 3/3]</b>\n\n"
            "Это уведомление больше не будет показываться.\n\n"
            "Нажмите «ОК 🆗», чтобы начать работу."
        )
        await call.edit(
            text=text,
            reply_markup=[[{"text": "ОК 🆗", "callback": self.ob_finish, "args": [target_args]}]]
        )

    async def ob_finish(self, call, target_args):
        self.config["agreed"] = True
        await call.answer("🚀 Модуль активирован!", alert=False)
        await self.process_entity(call, target_args, is_inline=True)

    # ==========================================
    #             ОСНОВНАЯ ЛОГИКА
    # ==========================================

    @loader.command(ru_doc="<@user/id/reply> - Собрать информацию об Entity")
    async def entitycmd(self, message):
        """Сбор информации о сущности"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        target = args if args else (reply.sender_id if reply else None)

        if not target:
            return await utils.answer(message, "❗️ <b>Укажите юзернейм, ID или ответьте на сообщение.</b>")

        target_str = str(target)

        if not self.config["agreed"]:
            msg = await utils.answer(message, "⏳ <b>Проверка прав доступа...</b>")
            await asyncio.sleep(1.2)
            await msg.delete()
            return await self.start_onboarding(message, target_str)

        await self.process_entity(message, target_str, is_inline=False)

    async def process_entity(self, context, target_str, is_inline=False):
        """Ядро сбора информации"""
        target = int(target_str) if str(target_str).lstrip('-').isdigit() else target_str
        
        loading_text = "🔍 <b>Анализ Entity...</b> ⠋"
        if is_inline:
            await context.edit(loading_text)
            msg = None
        else:
            msg = await utils.answer(context, loading_text)
        
        try:
            entity = await self.client.get_entity(target)
        except Exception:
            err = "❌ <b>Entity не найдена.</b>"
            if is_inline: return await context.edit(err)
            else: return await utils.answer(msg, err)

        if not isinstance(entity, User):
            err = "❌ <b>Это не пользователь.</b>"
            if is_inline: return await context.edit(err)
            else: return await utils.answer(msg, err)

        # Анимация загрузки
        for frame in ["⠙", "⠼", "⠧", "⠏"]:
            text = f"🔍 <b>Сбор данных...</b> {frame}"
            if is_inline: await context.edit(text)
            else: await utils.answer(msg, text)
            await asyncio.sleep(0.1)

        full_user = await self.client(GetFullUserRequest(entity))
        u = full_user.users[0]
        f = full_user.full_user

        data = {
            "id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "username": u.username,
            "phone": u.phone,
            "bio": f.about,
            "bot": u.bot,
            "scam": u.scam,
            "fake": getattr(u, 'fake', False),
            "verified": u.verified,
            "restricted": u.restricted,
            "contact": u.contact,
            "mutual_contact": u.mutual_contact,
            "premium": u.premium,
            "deleted": u.deleted,
            "dc_id": getattr(u.photo, 'dc_id', None) if u.photo else None,
            "profile_color": getattr(u, 'color', None),
            "profile_bg_emoji": getattr(u, 'profile_color', getattr(u, 'background_emoji_id', None)),
            "common_chats": f.common_chats_count,
            "premium_since": getattr(f, 'premium_since', None),
            "emoji_status": getattr(u, 'emoji_status', None),
            "heroku_protected": False,
            "hidden_phone": False
        }

        if data["phone"]:
            if not re.match(r'^\+?[0-9\(\)\s\-]+$', data["phone"]):
                data["heroku_protected"] = True
                data["phone"] = None
            else:
                data["hidden_phone"] = True

        self.cache[u.id] = data
        text = self.format_main_tab(data)
        kb = self.get_tabs_keyboard(u.id, "main", data["hidden_phone"])

        if is_inline:
            await context.edit(text=text, reply_markup=kb)
        else:
            await self.inline.form(text=text, message=context, reply_markup=kb)
            if msg: await msg.delete()

    # ==========================================
    #             ФОРМАТИРОВАНИЕ
    # ==========================================

    def format_main_tab(self, data):
        t = ""
        if data.get('phone') and not data.get('hidden_phone', True):
            t += f"📞 <b>Найден номер:</b> <code>+{data['phone']}</code>\n\n"
            
        t += f"🔢 <b>Entity ID:</b> <code>{data['id']}</code>\n\n"
        t += f"👤 <b>Имя:</b> <code>{self.clean(data['first_name']) or '—'}</code>\n"
        if data['last_name']: t += f"👥 <b>Фамилия:</b> <code>{self.clean(data['last_name'])}</code>\n"
        if data['username']: t += f"🔗 <b>Юзернейм:</b> @{self.clean(data['username'])}\n"
        
        bio = self.clean(data['bio'])
        t += f"\n📝 <b>О себе:</b> \n<code>{bio or '—'}</code>\n\n"
        
        t += f"📡 <b>DC ID:</b> <code>{data['dc_id'] or '—'}</code>\n"
        t += f"🎨 <b>Цвет профиля:</b> <code>{data['profile_color'] or '—'}</code>\n"
        t += f"💬 <b>Общих чатов:</b> <code>{data['common_chats']}</code>\n\n"
        
        badges = []
        if data['bot']: badges.append("🤖 Бот")
        if data['scam']: badges.append("⚠️ SCAM")
        if data['fake']: badges.append("🤥 FAKE")
        if data['verified']: badges.append("✅ Верифицирован")
        if data['contact']: badges.append("📒 В контактах")
        if data['mutual_contact']: badges.append("🤝 Взаимный контакт")
        if badges:
            t += "<b>Статусы:</b>\n" + " | ".join(badges)
        return t

    def format_prem_tab(self, data):
        t = f"💎 <b>Premium данные ID:</b> <code>{data['id']}</code>\n\n"
        if data['premium']:
            t += "🌟 <b>Статус:</b> <code>Активен</code>\n"
            t += f"📅 <b>Premium с:</b> <code>{data['premium_since'] or 'Неизвестно'}</code>\n"
            t += f"🎭 <b>Эмодзи статус:</b> <code>{data['emoji_status'] or 'Нет'}</code>\n"
            t += f"🖼 <b>Фон профиля:</b> <code>{data['profile_bg_emoji'] or 'Нет'}</code>\n"
        else:
            t += "<i>Пользователь не имеет подписки Telegram Premium.</i>"
        return t

    def format_none_tab(self, data):
        t = f"🚫 <b>Отсутствующие данные ID:</b> <code>{data['id']}</code>\n\n"
        missing = []
        if not data['last_name']: missing.append("Фамилия")
        if not data['username']: missing.append("Юзернейм")
        if not data['bio']: missing.append("О себе (Bio)")
        if not data['dc_id']: missing.append("Фото профиля (DC ID)")
        if not data['phone'] and not data['hidden_phone']: missing.append("Номер телефона")
        
        if data['heroku_protected']:
            t += "🛡 <b>ВНИМАНИЕ:</b> Сработала защита Heroku/Session. Номер был обфусцирован.\n\n"

        if missing:
            t += "<b>Список отсутствующего:</b>\n• " + "\n• ".join(missing)
        else:
            t += "<i>У этого пользователя заполнено всё инфо.</i>"
        return t

    # ==========================================
    #             ОБРАБОТЧИКИ
    # ==========================================

    async def inline_tab(self, call, user_id, tab):
        data = self.cache.get(int(user_id))
        if not data: return await call.answer("❌ Кэш устарел.", alert=True)

        if tab == "main": text = self.format_main_tab(data)
        elif tab == "prem": text = self.format_prem_tab(data)
        elif tab == "none": text = self.format_none_tab(data)

        kb = self.get_tabs_keyboard(int(user_id), tab, data.get("hidden_phone", False))
        await call.edit(text=text, reply_markup=kb)

    async def inline_show_phone(self, call, user_id):
        data = self.cache.get(int(user_id))
        if not data: return await call.answer("❌ Кэш устарел.", alert=True)
        
        data["hidden_phone"] = False
        self.cache[int(user_id)] = data
        
        text = self.format_main_tab(data)
        kb = self.get_tabs_keyboard(int(user_id), "main", False)
        await call.edit(text=text, reply_markup=kb)
        await call.answer("Номер открыт!", alert=False)

    async def inline_dump(self, call, user_id):
        if not self.config["dump_beta"]:
            return await call.answer("🚫 Функция дампа отключена.", alert=True)
        
        data = self.cache.get(int(user_id))
        if not data: return await call.answer("❌ Кэш устарел.", alert=True)

        await call.answer("Сборка дампа...", alert=False)
        dump_text = f"ENTITY DUMP | ID: {data['id']}\n"
        for key, value in data.items():
            dump_text += f"{key.upper()}: {value}\n"

        file = io.BytesIO(dump_text.encode("utf-8"))
        file.name = f"dump_{data['id']}.txt"

        try:
            # Универсальный хак для получения ID чата в инлайне
            target_chat = call.message.chat.id if hasattr(call, 'message') else call.from_user.id
            await self.client.send_file(target_chat, file, caption=f"📄 Дамп {data['id']}")
            await call.answer("✅ Дамп отправлен!", alert=False)
        except Exception as e:
            await call.answer(f"❌ Ошибка: {str(e)}", alert=True)