import io
import httpx
import re
import asyncio
from herokutl.types import Message
from .. import loader, utils
# meta developer: @modsbyai

@loader.tds
class OCRModule(loader.Module):
    """Простое распознавание текста с картинки/стикера, поэтому и быстрое."""
    
    strings = {
        "name": "QOCR",
        "loading": "<b>[OCR]</b> Распознаю...",
        "no_reply": "<b>[OCR]</b> Ответьте на медиа!",
        "no_text": "<b>[OCR]</b> Текст не найден.",
        "error": "<b>[OCR]</b> Ошибка: <code>{}</code>",
        "result": "<b>[OCR] Результат:</b>\n\n<code>{}</code>"
    }

    async def _lens(self, p: bytes):
        try:
            async with httpx.AsyncClient(follow_redirects=True) as c:
                res = await c.post("https://lens.google.com/v3/upload", files={'encoded_image': ('i.jpg', p, 'image/jpeg')}, params={"hl": "ru"}, timeout=10)
                return " ".join(re.findall(r'\["([^"]+)",null,null,null,null,null,null,null,null,null,null,\[\]\]', res.text)).strip()
        except: return ""

    async def _space(self, p: bytes):
        try:
            async with httpx.AsyncClient() as c:
                res = await c.post("https://api.ocr.space/parse/image", files={"f": ("i.jpg", p, "image/jpeg")}, data={"apikey": "helloworld", "language": "rus", "OCREngine": 2}, timeout=10)
                return res.json()["ParsedResults"][0]["ParsedText"].strip()
        except: return ""

    async def _api_ext(self, p: bytes, url: str):
        try:
            async with httpx.AsyncClient() as c:
                res = await c.post(url, files={"file": p}, timeout=10)
                return res.json().get("text", "").strip()
        except: return ""

    async def _local(self, p: bytes):
        try:
            import pytesseract
            from PIL import Image
            return pytesseract.image_to_string(Image.open(io.BytesIO(p)), lang="rus+eng").strip()
        except: return ""

    @loader.command(ru_doc="Распознать текст.")
    async def ocr(self, message: Message):
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            return await utils.answer(message, self.strings["no_reply"])

        message = await utils.answer(message, self.strings["loading"])
        photo = await reply.download_media(bytes) # Скачивание в RAM [cite: 20]
        
        try:
            tasks = [
                self._lens(photo), 
                self._space(photo), 
                self._local(photo),
                self._api_ext(photo, "https://api.v-ocr.com/v1/get_text"),
                self._api_ext(photo, "https://ocr-api.com/v1/parse")
            ]
            results = await asyncio.gather(*tasks)
            text = max(results, key=len) # Выбор самого полного результата

            if not text:
                await utils.answer(message, self.strings["no_text"])
            else:
                await utils.answer(message, self.strings["result"].format(text))
        except Exception as e:
            await utils.answer(message, self.strings["error"].format(str(e)))
        finally:
            if photo: del photo # Очистка памяти [cite: 20]
