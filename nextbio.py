from herokutl.types import Message
from telethon import functions, errors
from .. import loader, utils
import datetime
import asyncio
import httpx
import pytz
import os
import psutil
import random
import re

# meta developer: @modsbyai

@loader.tds
class NextAutoBioModule(loader.Module):
    """Автоматизация био нового поколения."""
    
    strings = {
        "name": "NextBio",
        "enabled": "<b>[NextAutoBio]</b> Статус: <code>Включен</code> ✅\n\n⚙️ <b>Настройка:</b> <code>{}cfg NextBio</code>",
        "disabled": "<b>[NextAutoBio]</b> Статус: <code>Выключен</code> ❌\n<i>Оригинальное био восстановлено.</i>",
        "force_update": "<b>[NextAutoBio]</b> Био обновлено! ⚡️",
        "error": "<b>[NextAutoBio]</b> Ошибка: <code>{}</code>",
        "flood_wait": "<b>[NextAutoBio]</b> ⚠️ Лимит Telegram! Подождите {} сек.",
        "prefix_err": "\n⚠️ <i>Произошла ошибка при получении вашего префикса, использован стандартный (<code>.</code>)</i>",
        "cfg_bios": (
            "СПИСОК ВАШИХ БИО (каждое с новой строки).\n"
            "ПЕРЕМЕННЫЕ: {time}, {date}, {weather}, {crypto}, {rub}, {usd}, {eur}, {quote}, "
            "{uptime}, {cpu}, {ram}, {ping}, {users}, {chats}, {msgs}, {day_progress}, {year_progress}.\n\n"
            "⚠️ ЛИМИТ: 70 символов. (140 для Premium).\n"
            "❗ Некоторые переменные возвращают длинные значения, не пытайтесь вставить всё сразу.\n"
            "❗ Следите за опечатками! Один неверный символ может сломать вам всё био!\n"
            "❗ К сожалению из-за большого количества запросов некоторые переменные могут не работать"
        ),
        "cfg_api_key": "⚠️ КЛЮЧ OpenWeatherMap. Без него {weather} вернет 'NoKey'"
    }

    TAG = "\ufe0f"

    QUOTES = [
        "Code is poetry.", "Stay hungry, stay foolish.", "Do it now.", 
        "Keep it simple.", "Focus on the goal.", "Think different.",
        "Be water, my friend.", "Work hard, dream big.", "Enjoy the moment."
    ]

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("status", False, "Включить авто-обновление", validator=loader.validators.Boolean()),
            loader.ConfigValue("city", "Moscow", "Город для погоды"),
            loader.ConfigValue("api_key", "", self.strings["cfg_api_key"], validator=loader.validators.Hidden()),
            loader.ConfigValue("timezone", "Europe/Moscow", "Часовой пояс"),
            loader.ConfigValue("bios", ["{time} | {weather} | {quote}"], self.strings["cfg_bios"], validator=loader.validators.Series()),
            loader.ConfigValue("interval", 60, "Интервал (сек)", validator=loader.validators.Integer(minimum=30)),
            loader.ConfigValue("start_hour", 0, "Начало (0-23)"),
            loader.ConfigValue("end_hour", 23, "Конец (0-23)"),
            loader.ConfigValue("crypto", "bitcoin,ethereum", "ID монет (coingecko)")
        )
        self._current_index = 0
        self._is_premium = None
        self._start_time = datetime.datetime.now()
        self._last_set_bio = ""
        self._cache = {"weather": "N/A", "crypto": "N/A", "fiat": "N/A", "last_call": 0}
        self._task = None 

    def _get_progress_bar(self, percent):
        filled = int(percent / 10)
        return "█" * filled + "░" * (10 - filled)

    def _safe_format(self, text, mapping):
        def replace(match):
            key = match.group(1)
            return str(mapping.get(key, match.group(0)))
        return re.sub(r"{(.*?)}", replace, text)

    async def _fetch_api_data(self):
        now_ts = datetime.datetime.now().timestamp()
        if now_ts - self._cache["last_call"] > 300:
            async with httpx.AsyncClient(timeout=5.0) as c:
                if self.config["api_key"]:
                    try:
                        r = await c.get(f"http://api.openweathermap.org/data/2.5/weather?q={self.config['city']}&appid={self.config['api_key']}&units=metric")
                        self._cache["weather"] = f"{round(r.json()['main']['temp'])}°C" if r.status_code == 200 else "Err"
                    except: self._cache["weather"] = "Offline"
                try:
                    r = await c.get(f"https://api.coingecko.com/api/v3/simple/price?ids={self.config['crypto'].lower()}&vs_currencies=usd")
                    if r.status_code == 200:
                        res = r.json()
                        self._cache["crypto"] = " | ".join([f"{k[:3].upper()}: ${v['usd']}" for k, v in res.items()])
                except: pass
                try:
                    r = await c.get("https://www.cbr-xml-daily.ru/daily_json.js")
                    if r.status_code == 200: self._cache["fiat"] = r.json()["Valute"]
                except: pass
            self._cache["last_call"] = now_ts

    async def _get_data(self, template):
        await self._fetch_api_data()
        tz = pytz.timezone(self.config["timezone"])
        dt = datetime.datetime.now(tz)
        up = datetime.datetime.now() - self._start_time
        day_pct = (dt.hour * 3600 + dt.minute * 60 + dt.second) / 86400 * 100
        year_start = datetime.datetime(dt.year, 1, 1, tzinfo=tz)
        year_end = datetime.datetime(dt.year + 1, 1, 1, tzinfo=tz)
        year_pct = (dt - year_start) / (year_end - year_start) * 100

        data = {
            "time": dt.strftime("%H:%M"), "date": dt.strftime("%d/%m"),
            "weather": self._cache["weather"], "crypto": self._cache["crypto"],
            "uptime": f"{up.seconds // 3600}h {(up.seconds // 60) % 60}m",
            "cpu": f"{psutil.cpu_percent()}%", "ram": f"{round(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024)}MB",
            "quote": random.choice(self.QUOTES),
            "day_progress": self._get_progress_bar(day_pct),
            "year_progress": f"{round(year_pct, 1)}%", "week": dt.isocalendar()[1]
        }
        if self._cache["fiat"] != "N/A":
            usd_to_rub = self._cache['fiat']['USD']['Value']
            data["rub"] = f"{round(usd_to_rub, 1)}₽" # Цена доллара в рублях
            data["usd"] = f"${round(1 / usd_to_rub, 4)}" # Цена рубля в долларах
            data["eur"] = f"{round(self._cache['fiat']['EUR']['Value'], 1)}₽"

        if "{ping}" in template:
            try:
                s_p = datetime.datetime.now()
                await self._client(functions.PingRequest(ping_id=0))
                data["ping"] = f"{round((datetime.datetime.now() - s_p).microseconds / 1000)}ms"
            except: data["ping"] = "Err"
        
        if any(x in template for x in ["{users}", "{chats}", "{msgs}"]):
            dialogs = await self._client.get_dialogs()
            data["users"] = str(len([d for d in dialogs if d.is_user]))
            data["chats"] = str(len([d for d in dialogs if d.is_group or d.is_channel]))
            data["msgs"] = str(sum([getattr(d, 'unread_count', 0) for d in dialogs]))
        return data

    async def _update_bio_logic(self, is_init=False):
        try:
            full = await self._client(functions.users.GetFullUserRequest(id='me'))
            current_bio = getattr(full.full_user, 'about', "") or ""
            if self.TAG not in current_bio and current_bio != self._last_set_bio:
                self.db.set("NextBio", "fallback", current_bio)
            if is_init: return 

            self._is_premium = getattr(full.users[0], 'premium', False)
            valid_bios = [b for b in self.config["bios"] if b.strip()]
            if not valid_bios: return None
            
            raw_bio = valid_bios[self._current_index % len(valid_bios)]
            vals = await self._get_data(raw_bio)
            limit = 140 if self._is_premium else 70
            final_bio = self._safe_format(raw_bio, vals)
            final_bio = (final_bio[:limit-1] if len(final_bio) >= limit else final_bio) + self.TAG
            
            await self._client(functions.account.UpdateProfileRequest(about=final_bio))
            self._last_set_bio = final_bio
            self._current_index += 1
            return {"bio": final_bio, "template": raw_bio}
        except errors.FloodWaitError as e: return {"flood": e.seconds}
        except Exception: return None

    async def _bio_loop(self):
        while True:
            if not self.config["status"]:
                await asyncio.sleep(5)
                continue
            try:
                tz = pytz.timezone(self.config["timezone"])
                now = datetime.datetime.now(tz)
                if self.config["start_hour"] <= now.hour <= self.config["end_hour"]:
                    res = await self._update_bio_logic()
                    if res and "flood" in res:
                        await asyncio.sleep(res["flood"] + 5); continue
                    if res and "{time}" in res.get("template", ""):
                        await asyncio.sleep(max(60 - datetime.datetime.now().second, 1)); continue
            except: pass
            await asyncio.sleep(self.config["interval"])

    @loader.command()
    async def ntogglebio(self, message: Message):
        """Вкл/Выкл авто-био."""
        self.config["status"] = not self.config["status"]
        if self.config["status"]:
            prefix, suffix = ".", ""
            try:
                main_cfg = self.db.get("main.main", {})
                prefix = main_cfg.get("prefix", ".") if isinstance(main_cfg, dict) else "."
            except: suffix = self.strings["prefix_err"]
            await utils.answer(message, self.strings["enabled"].format(prefix) + suffix)
            await self._update_bio_logic()
        else:
            fallback = self.db.get("NextBio", "fallback", "Автоматизация био нового поколения.")
            await self._client(functions.account.UpdateProfileRequest(about=fallback))
            self._last_set_bio = fallback
            await utils.answer(message, self.strings["disabled"])

    @loader.command()
    async def nbioforce(self, message: Message):
        """Обновить био немедленно."""
        res = await self._update_bio_logic()
        if res and "flood" in res:
            await utils.answer(message, self.strings["flood_wait"].format(res["flood"]))
        else:
            await utils.answer(message, self.strings["force_update"])

    async def client_ready(self, client, db):
        self._client, self.db = client, db
        if self._task: self._task.cancel()
        if not self.config["status"]: await self._update_bio_logic(is_init=True)
        self._task = asyncio.create_task(self._bio_loop())

    async def on_unload(self):
        if self._task: self._task.cancel()

