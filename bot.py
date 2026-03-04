import feedparser
import asyncio
import os
import re
from telegram import Bot

# --- GÜVENLİK VE AYARLAR ---
# GitHub'a yüklerken bunları 'Secrets' kısmına taşıyacağız. 
# Şimdilik test için buraya yazabilirsin.
TOKEN = os.environ.get('TELEGRAM_TOKEN')
MY_ID = 12345678 # Kendi ID numaranı yaz
HAFIZA_DOSYASI = "hafiza.txt"

# Kaynak Listesi (Hepsini tek bir standartta topladık)
KAYNAKLAR = {
    "BBC TÜRKÇE": "https://feeds.bbci.co.uk/turkce/rss.xml",
    "GOOGLE SON DAKİKA": "https://news.google.com/rss/search?q=when:1d&hl=tr&gl=TR&ceid=TR:tr",
    "TRT HABER": "https://www.trthaber.com/xml_haberler.rss",
    "CNN TÜRK": "https://www.cnnturk.com/feed/rss/all/news",
    "HÜRRİYET": "https://www.hurriyet.com.tr/rss/anasayfa",
    "MİLLİYET": "https://www.milliyet.com.tr/rss/rss-liste/son-dakika-haberleri/",
    "RESMİ GAZETE": "https://www.resmigazete.gov.tr/rss/resmigazete.xml"
}

def resim_bul(haber):
    """Farklı sitelerden en kaliteli resmi bulur."""
    resim = None
    # 1. Standart medya etiketi
    if 'media_content' in haber:
        resim = haber.media_content[0]['url']
    # 2. Linkler içindeki resim tipi
    elif 'links' in haber:
        for link in haber.links:
            if 'image' in link.get('type', ''):
                resim = link.get('href')
    # 3. Metin içindeki gizli img etiketi (Regex ile)
    if not resim and 'summary' in haber:
        bulunan = re.search(r'<img [^>]*src="([^"]+)"', haber.summary)
        if bulunan:
            resim = bulunan.group(1)
    return resim

async def botu_calistir():
    bot = Bot(token=TOKEN)
    
    # Hafızayı oku
    if os.path.exists(HAFIZA_DOSYASI):
        with open(HAFIZA_DOSYASI, "r", encoding="utf-8") as f:
            gonderilenler = f.read().splitlines()
    else:
        gonderilenler = []

    print("🚀 Tarama başlatıldı...")

    for ad, url in KAYNAKLAR.items():
        try:
            besleme = feedparser.parse(url)
            # Her kaynaktan sadece en yeni haberi kontrol et (Hız ve temizlik için)
            if not besleme.entries: continue
            
            haber = besleme.entries[0]
            
            # Eğer haber daha önce gönderilmediyse
            if haber.title not in gonderilenler:
                resim_url = resim_bul(haber)
                mesaj = (f"<b>📰 {ad} | SON DAKİKA</b>\n\n"
                         f"🔥 {haber.title}\n\n"
                         f"🔗 <a href='{haber.link}'>Haberin Devamı</a>")

                try:
                    if resim_url:
                        await bot.send_photo(chat_id=MY_ID, photo=resim_url, caption=mesaj, parse_mode='HTML')
                    else:
                        await bot.send_message(chat_id=MY_ID, text=f"✨ {mesaj}", parse_mode='HTML')
                    
                    gonderilenler.append(haber.title)
                    print(f"✅ Gönderildi: {ad}")
                except Exception as e:
                    print(f"⚠️ Mesaj hatası ({ad}): {e}")
                
                await asyncio.sleep(2) # Telegram engeline takılmamak için bekleme

        except Exception as e:
            print(f"❌ Kaynak hatası ({ad}): {e}")

    # Hafızayı güncelle (Son 50 haberi tut)
    with open(HAFIZA_DOSYASI, "w", encoding="utf-8") as f:
        f.write("\n".join(gonderilenler[-50:]))
    
    print("🏁 İşlem tamamlandı.")

# Çalıştırma komutu
await botu_calistir()
