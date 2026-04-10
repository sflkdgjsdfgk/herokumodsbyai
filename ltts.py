# meta developer: @modsbyai

import io
from herokutl.types import Message
from gtts import gTTS
from .. import loader, utils

@loader.tds
class LTTSMod(loader.Module):
    """Модуль локальной озвучки текста - LazyTTS"""
    strings = {
        "name": "LTTS",
        "no_text": "<b>[LTTS]</b> Введите текст или ответьте на сообщение!",
        "processing": "<b>[LTTS]</b> Озвучиваю...",
        "cfg_lang": "Язык озвучки (например: ru, en)",
        "cfg_speed": "Скорость озвучки (обычная, быстрая, медленная)"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "language",
                "ru",
                lambda: self.strings["cfg_lang"],
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "speed",
                "обычная",
                lambda: self.strings["cfg_speed"],
                validator=loader.validators.Choice(["обычная", "быстрая", "медленная"])
            ),
        )

    @loader.command(ru_doc="Озвучить текст (.tts <текст> или реплай)")
    async def tts(self, message: Message):
        """Озвучить текст через gTTS"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        text = args or (reply.text if reply else None)

        if not text:
            await utils.answer(message, self.strings["no_text"])
            return

        message = await utils.answer(message, self.strings["processing"])

        try:
            is_slow = self.config["speed"] == "медленная"
            
            tts = gTTS(
                text=text, 
                lang=self.config["language"], 
                slow=is_slow
            )
            
            audio_stream = io.BytesIO()
            tts.write_to_fp(audio_stream)
            audio_stream.seek(0)
            audio_stream.name = "voice.mp3"

            await message.client.send_file(
                message.chat_id, 
                audio_stream, 
                voice_note=True, 
                reply_to=reply.id if reply else None
            )
            
            await message.delete()
        except Exception as e:
            await utils.answer(message, f"<b>[LTTS] Ошибка:</b> <code>{str(e)}</code>")

    @loader.command(ru_doc="Список доступных языков")
    async def ttslangs(self, message: Message):
        """Показать список языков"""
        await utils.answer(message, "<b>Доступные языки:</b> ru, en, de, fr, es, it, ja, ko")
