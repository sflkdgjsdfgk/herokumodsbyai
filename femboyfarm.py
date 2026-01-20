from herokutl.types import Message
from .. import loader, utils
import asyncio
import datetime
# meta developer: @isdistorted, @isauthentic, @isvivid and gemini

@loader.tds
class FemboyAutoModule(loader.Module):
    """Автоматический фарм фембоев в @hikkahost_chat."""
    
    strings = {
        "name": "FemboyAuto",
        "status": "📊 Статус: {0}\n🕒 Последний раз (Минск): {1}",
        "force": "🚀 Отправлено!",
        "toggle": "🤖 Автофарм теперь <b>{0}</b>"
    }

    def __init__(self):
        # Добавлена настройка команды в конфиг
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled", False, "Статус авто-отправки",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "interval", 3600, "Интервал в секундах",
                validator=loader.validators.Integer(minimum=10)
            ),
            loader.ConfigValue(
                "command", "/fuckfemboy@femboykrutoibot", "Команда для отправки",
                validator=loader.validators.String()
            )
        )

    async def client_ready(self, client, db):
        self._client = client
        self.chat_id = -1001984640085
        self.thread_id = 146325
        
        if hasattr(self, "_loop_task"):
            self._loop_task.cancel()
        self._loop_task = asyncio.create_task(self._auto_fucker())

    def get_time(self):
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        return (utc_now + datetime.timedelta(hours=3)).strftime("%H:%M:%S")

    async def _auto_fucker(self):
        while True:
            if self.config["enabled"]:
                try:
                    await self._client.send_message(
                        self.chat_id, 
                        self.config["command"], 
                        reply_to=self.thread_id
                    )
                    # Используем встроенный обертку для базы данных
                    self.db.set("last_run", self.get_time())
                except Exception:
                    pass
            await asyncio.sleep(self.config["interval"])

    @loader.command(ru_doc="Логи фарма")
    async def femlogs(self, message: Message):
        """Show last farm time"""
        last_run = self.db.get("last_run", "Нет данных")
        status = "✅ Работает" if self.config["enabled"] else "❌ Выключен"
        await utils.answer(message, self.strings["status"].format(status, last_run))

    @loader.command(ru_doc="Принудительный фарм")
    async def femforcesend(self, message: Message):
        """Force farm now"""
        await self._client.send_message(self.chat_id, self.config["command"], reply_to=self.thread_id)
        await utils.answer(message, self.strings["force"])

    @loader.command(ru_doc="Вкл/Выкл", alias="tf")
    async def togglef(self, message: Message):
        """Toggle farming"""
        self.config["enabled"] = not self.config["enabled"]
        status = "ВКЛЮЧЕН" if self.config["enabled"] else "ВЫКЛЮЧЕН"
        await utils.answer(message, self.strings["toggle"].format(status))
