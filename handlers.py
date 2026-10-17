import io
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart
from claude_service import claude_service
from erp_service import erp_service

logger = logging.getLogger(__name__)
router = Router()

def format_stock_response(stock: dict) -> str:
    if stock.get("in_stock"):
        return (
            f"✅ **Тканина в наявності:**\n\n"
            f"🏷 **Позиція:** `{stock['name']}`\n"
            f"📦 **Вільний залишок:** `{stock['balance_meters']} м`\n"
            f"📍 **Склад:** {stock['warehouse']}\n"
            f"💰 **Ціна:** `{stock['price_per_meter_uah']} грн/м`\n\n"
            f"ℹ️ _Дані синхронізовано з 1С:Підприємство в реальному часі._"
        )
    else:
        return (
            f"⚠️ **Тканини тимчасово немає в наявності:**\n\n"
            f"🏷 **Позиція:** `{stock['name']}`\n"
            f"📦 **Залишок на складах:** `0.0 м`\n"
            f"🔄 Зверніться до менеджера для оформлення передзамовлення на фабрику."
        )

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(
        "👋 Вітаю! Я AI-асистент з обліку тканин та текстилю.\n\n"
        "Я вмію:\n"
        "• Розпізнавати запити наявності у тексті (наприклад: *«Чи є Siena 05-Birch?»*)\n"
        "• Зчитувати назви тканин з фото етикеток та зразків (Anthropic Claude Vision)\n"
        "• Перевіряти залишки в 1С у реальному часі\n\n"
        "Надішліть фото зразка або текст із запитом!"
    )

@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_bytes = io.BytesIO()
    await bot.download_file(file_info.file_path, destination=file_bytes)
    
    status_msg = await message.reply("🔍 _AI аналізує фотографію етикетки через Claude Vision..._")
    
    intent = await claude_service.analyze_image_sample(
        image_bytes=file_bytes.getvalue(),
        caption=message.caption
    )
    
    if intent and intent.get("article"):
        stock = await erp_service.check_stock(intent["article"], intent.get("shade"))
        reply_text = format_stock_response(stock)
        await status_msg.edit_text(reply_text)
    else:
        await status_msg.edit_text("ℹ️ Не вдалося чітко розпізнати етикетку тканини на фото. Спробуйте надіслати ближче або напишіть назву текстом.")

@router.message(F.text)
async def handle_text(message: Message):
    text = message.text.strip()
    if text.startswith("/"):
        return
        
    intent = await claude_service.analyze_text_query(text)
    if intent and intent.get("article"):
        stock = await erp_service.check_stock(intent["article"], intent.get("shade"))
        reply_text = format_stock_response(stock)
        await message.reply(reply_text)
