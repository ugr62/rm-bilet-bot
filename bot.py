import os
import threading
import logging
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = "BURAYA_BOT_TOKEN_GIRIN"
REAL_MADRID_TICKETS_URL = "https://www.realmadrid.com/en-US/tickets"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Render'ın Web Service için aradığı basit HTTP sunucusu
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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(REAL_MADRID_TICKETS_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()
        
        if "villarreal" in page_text:
            if "buy tickets" in page_text or "tickets available" in page_text:
                return f"🚨 **MÜJDE! Real Madrid - Villarreal biletleri satışta!** 🚨\n\nSatın almak için tıkla:\n{REAL_MADRID_TICKETS_URL}"
            else:
                return "ℹ️ Real Madrid - Villarreal maçı bilet listesinde görünüyor ancak genel satış henüz açılmadı."
        else:
            return "ℹ️ Villarreal maçı bilet listesinde henüz aktif olarak yayınlanmadı."
            
    except Exception as e:
        return f"❌ Sayfa kontrol edilirken bir hata oluştu: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Real Madrid Bilet Takip Botu Aktif!**\n\n"
        "Kullanabileceğiniz komutlar:\n"
        "▫️ `/kontrol` - Real Madrid - Villarreal bilet durumunu anlık sorgular\n"
        "▫️ `/yardim` - Bot kullanımı hakkında bilgi verir"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Bilet durumu kontrol ediliyor, lütfen bekleyin...")
    durum_mesaji = check_tickets_status()
    await update.message.reply_text(durum_mesaji, parse_mode="Markdown")

async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Bu bot, Real Madrid'in resmi web sitesini tarayarak Villarreal maçının "
        "bilet durumunu kontrol eder.\n\n"
        "İstediğiniz zaman `/kontrol` yazarak anlık durumu öğrenebilirsiniz."
    )
    await update.message.reply_text(help_text)

if __name__ == '__main__':
    # HTTP sunucusunu arka planda başlat
    threading.Thread(target=run_http_server, daemon=True).start()
    
    # Telegram Botunu Başlat
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kontrol", kontrol))
    app.add_handler(CommandHandler("yardim", yardim))
    print("Bot komutları dinlemeye başladı...")
    app.run_polling()
