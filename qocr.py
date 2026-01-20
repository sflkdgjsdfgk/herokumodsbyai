import io
import httpx
from herokutl.types import Message
from .. import loader, utils
# meta developer: @modsbyai

@loader.tds
class OCRModule(loader.Module):
    """Простое распознавание текста с картинки/стикера, поэтому и быстрое."""
    
    strings = {
        "name": "QOCR",
        "loading": "<b>[OCR]</b> Считываю текст...",
        "no_reply": "<b>[OCR]</b> Ответьте на фото/стикер!",
        "no_text": "<b>[OCR]</b> Текст не найден.",
        "error": "<b>[OCR]</b> Ошибка: <code>{}</code>",
        "result": "<b>[OCR] Результат:</b>\n\n<code>{}</code>"
    }

    @loader.command(ru_doc="Распознать текст на фото (через Google Lens)")
    async def ocr(self, message: Message):
        """Recognize text from image using Lens"""
        reply = await message.get_reply_message()
        
        if not reply or not reply.media:
            await utils.answer(message, self.strings["no_reply"])
            return

        message = await utils.answer(message, self.strings["loading"])
        
        try:
            # Скачиваем в память
            photo = await reply.download_media(bytes)
            
            # Используем Google Lens API (через прокси-запрос или прямой парсинг)
            # Это намного надежнее ocr.space для Telegram стикеров и фото
            async with httpx.AsyncClient() as client:
                # Отправляем файл как multipart/form-data 
                files = {'encoded_image': ('image.jpg', photo, 'image/jpeg')}
                res = await client.post(
                    "https://lens.google.com/v3/upload",
                    files=files,
                    params={"hl": "ru"},
                    follow_redirects=True,
                    timeout=20
                )
            
            # Извлекаем текст из ответа (упрощенный поиск в теле ответа Lens)
            import re
            content = res.text
            # Регулярка для поиска текстовых блоков в JSON-подобной структуре Lens
            text_parts = re.findall(r'\["([^"]+)",null,null,null,null,null,null,null,null,null,null,\[\]\]', content)
            
            if not text_parts:
                # Если Lens не сработал, пробуем ваш исходный ocr.space с фиксом заголовков
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        "https://api.ocr.space/parse/image",
                        files={"file": ("image.jpg", photo, "image/jpeg")},
                        data={"apikey": "helloworld", "language": "rus", "OCREngine": 2}
                    )
                    data = res.json()
                    text = data["ParsedResults"][0]["ParsedText"] if data.get("OCRExitCode") == 1 else ""
            else:
                text = " ".join(text_parts)

            if not text or not text.strip():
                await utils.answer(message, self.strings["no_text"])
            else:
                await utils.answer(message, self.strings["result"].format(text))

        except Exception as e:
            await utils.answer(message, self.strings["error"].format(str(e)))

