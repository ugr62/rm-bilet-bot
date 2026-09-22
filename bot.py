import os
import threading
import logging
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================================================
# BİLGİLERİNİZİ BURAYA GİRİN
# =========================================================
TELEGRAM_TOKEN = "8811575691:AAHWtPi7hYLrYQ6CufX81HPxI9YGgIQ_YMI"
# Otomatik bildirimlerin atılacağı Telegram Grup Chat ID'si (Eksi işaretiyle başlar, Örn: "-100123456789")
CHAT_ID = "-5356646775" 

REAL_MADRID_TICKETS_URL = "https://www.realmadrid.com/en-US/tickets"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Render'ın uykuda kalmaması ve ayakta tutulması için basit HTTP sunucusu
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
    """Bilet durumunu kontrol eder."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(REAL_MADRID_TICKETS_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()
        
        if "villarreal" in page_text:
            if "buy tickets" in page_text or "tickets available" in page_text:
                return (
                    "🚨 **MÜJDE! Real Madrid - Villarreal Biletleri Satışta!** 🚨\n\n"
                    f"Hemen satın almak için tıkla:\n{REAL_MADRID_TICKETS_URL}"
                )
            else:
                return "ℹ️ Real Madrid - Villarreal maçı bilet listesinde görünüyor ancak genel satış henüz açılmadı."
        else:
            return "ℹ️ Villarreal maçı bilet listesinde henüz aktif olarak yayınlanmadı."
            
    except Exception as e:
        return f"❌ Sayfa kontrol edilirken bir hata oluştu: {e}"

# --- SAAT BAŞI OTOMATİK KONTROL GÖREVİ ---
async def periyodik_bilet_kontrolu(context: ContextTypes.DEFAULT_TYPE):
    """Her saat başı otomatik olarak çalışır ve gruba bilgi verir."""
    mesaj = check_tickets_status()
    
    # Sadece biletler satışa çıktığında bildirim atmak isterseniz bu koşul kalabilir.
    # Her saat başı durum ne olursa olsun gruba yazsın isterseniz aşağıdaki if mantığını kaldırıp doğrudan send_message yapabilirsiniz.
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"⏰ **Saatlik Otomatik Kontrol**\n\n{mesaj}",
        parse_mode="Markdown"
    )

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Real Madrid Bilet Takip Botu Aktif!**\n\n"
        "Bot her saat başı otomatik kontrol yapıp gruba bilgi geçecektir.\n"
        "İstediğiniz an manuel kontrol için:\n"
        "▫️ `/kontrol` - Anlık durumu sorgular\n"
        "▫️ `/yardim` - Bilgi verir"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Bilet durumu kontrol ediliyor, lütfen bekleyin...")
    durum_mesaji = check_tickets_status()
    await update.message.reply_text(durum_mesaji, parse_mode="Markdown")

async def yardim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Bu bot Real Madrid - Villarreal maçının bilet satış durumunu her saat başı otomatik kontrol eder. "
        "Ayrıca `/kontrol` yazarak istediğiniz an sorgulama yapabilirsiniz."
    )
    await update.message.reply_text(help_text)

if __name__ == '__main__':
    # Web sunucusunu başlat
    threading.Thread(target=run_http_server, daemon=True).start()
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Zamanlayıcıyı (JobQueue) Başlatma: Her 3600 saniyede bir (1 saat) çalışır
    job_queue = app.job_queue
    job_queue.run_repeating(periyodik_bilet_kontrolu, interval=3600, first=10) # Başladıktan 10sn sonra ilk kontrolü yapar

    # Komut Dinleyicileri
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kontrol", kontrol))
    app.add_handler(CommandHandler("yardim", yardim))

    print("Bot ve saatlik zamanlayıcı çalışmaya başladı...")
    app.run_polling()
