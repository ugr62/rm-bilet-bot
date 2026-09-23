import os
import threading
import logging
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    ContextTypes, 
    filters
)

# =========================================================
# BİLGİLERİNİZİ BURAYA GİRİN
# =========================================================
TELEGRAM_TOKEN = "8811575691:AAHWtPi7hYLrYQ6CufX81HPxI9YGgIQ_YMI"
CHAT_ID = "-5356646775"

REAL_MADRID_TICKETS_URL = "https://www.realmadrid.com/en-US/tickets"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Active")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def check_tickets_status():
    """Bilet durumunu kontrol eder ve (mesaj, bilet_satista_mi) döndürür."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(REAL_MADRID_TICKETS_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()
        
        if "villarreal" in page_text:
            if "buy tickets" in page_text or "tickets available" in page_text:
                msg = (
                    "🚨 **MÜJDE! Real Madrid - Villarreal Biletleri Satışta!** 🚨\n\n"
                    f"Hemen satın almak için tıkla:\n{REAL_MADRID_TICKETS_URL}"
                )
                return msg, True
            else:
                return "ℹ️ Real Madrid - Villarreal maçı bilet listesinde görünüyor ancak genel satış henüz açılmadı.", False
        else:
            return "ℹ️ Villarreal maçı bilet listesinde henüz aktif olarak yayınlanmadı.", False
            
    except Exception as e:
        return f"❌ Sayfa kontrol edilirken bir hata oluştu: {e}", False

async def periyodik_bilet_kontrolu(context: ContextTypes.DEFAULT_TYPE):
    """Saatlik kontroller"""
    mesaj, bilet_bulundu = check_tickets_status()
    
    if bilet_bulundu:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=mesaj,
            parse_mode="Markdown",
            disable_notification=False
        )
    else:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"⏰ **Saatlik Otomatik Kontrol**\n\n{mesaj}",
            parse_mode="Markdown",
            disable_notification=True
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Real Madrid Bilet Takip Botu Aktif!**\n\n"
        "Komutlar veya Kelimeler:\n"
        "▫️ `/kontrol` veya grupta **kontrol** yazarak anlık sorgulayabilirsiniz."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def manuel_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hem /kontrol komutuna hem de içinde 'kontrol' geçen mesajlara yanıt verir"""
    await update.message.reply_text("🔍 Bilet durumu kontrol ediliyor, lütfen bekleyin...")
    durum_mesaji, _ = check_tickets_status()
    await update.message.reply_text(durum_mesaji, parse_mode="Markdown")

async def kelime_dinleyici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grupta 'kontrol', 'bilet' veya 'durum' yazılırsa otomatik yanıt verir"""
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    if any(k in text for k in ["kontrol", "bilet", "durum"]):
        await manuel_kontrol(update, context)

if __name__ == '__main__':
    threading.Thread(target=run_http_server, daemon=True).start()
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    job_queue = app.job_queue
    job_queue.run_repeating(periyodik_bilet_kontrolu, interval=3600, first=10)

    # Komut Dinleyiciler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kontrol", manuel_kontrol))
    
    # Metin Dinleyici (Grupta 'kontrol', 'bilet' vb. yazılınca çalışır)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), kelime_dinleyici))

    print("Bot ve saatlik zamanlayıcı çalışmaya başladı...")
    app.run_polling(drop_pending_updates=True)
