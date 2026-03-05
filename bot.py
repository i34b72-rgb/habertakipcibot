import feedparser
import asyncio
import os
import re
from telegram import Bot

# --- GÜVENLİK ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
MY_ID = 12345678  # Kendi ID'ni buraya yaz
HAFIZA_DOSYASI = "hafiza.txt"

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
    if 'media_content' in haber: return haber.media_content[0]['url']
    if 'links' in haber:
        for link in haber.links:
            if 'image' in link.get('type', ''): return link.get('href')
    if 'summary' in haber:
        bulunan = re.search(r'<img [^>]*src="([^"]+)"', haber.summary)
        if bulunan: return bulunan.group(1)
    return None

async def haber_cek_ve_gonder(bot, ad, url, gonderilenler):
    """Tek bir kaynağı tarar ve yeni haber varsa gönderir."""
    try:
        # Haberi çekme işlemini hızlandırmak için döngüden çıkardık
        loop = asyncio.get_event_loop()
        besleme = await loop.run_in_executor(None, feedparser.parse, url)
        
        if not besleme.entries: return

        haber = besleme.entries[0]
        if haber.title not in gonderilenler:
            resim_url = resim_bul(haber)
            mesaj = (f"<b>📰 {ad} | SON DAKİKA</b>\n\n"
                     f"🔥 {haber.title}\n\n"
                     f"🔗 <a href='{haber.link}'>Haberin Devamı</a>")

            if resim_url:
                await bot.send_photo(chat_id=MY_ID, photo=resim_url, caption=mesaj, parse_mode='HTML')
            else:
                await bot.send_message(chat_id=MY_ID, text=f"✨ {mesaj}", parse_mode='HTML')
            
            return haber.title # Yeni gönderilen haberi geri döndür
    except Exception as e:
        print(f"Hata ({ad}): {e}")
    return None

async def botu_calistir():
    bot = Bot(token=TOKEN)
    
    # Hafızayı oku
    if os.path.exists(HAFIZA_DOSYASI):
        with open(HAFIZA_DOSYASI, "r", encoding="utf-8") as f:
            gonderilenler = f.read().splitlines()
    else:
        gonderilenler = []

    # --- PARALEL ÇALIŞMA MANTIĞI ---
    # Tüm kaynaklar için görevleri (tasks) oluşturuyoruz
    gorevler = [haber_cek_ve_gonder(bot, ad, url, gonderilenler) for ad, url in KAYNAKLAR.items()]
    
    # Tüm görevleri AYNI ANDA başlatıyoruz
    sonuclar = await asyncio.gather(*gorevler)

    # Yeni gönderilen haberleri listeye ekle
    yeni_haberler = [s for s in sonuclar if s is not None]
    gonderilenler.extend(yeni_haberler)

    # Hafızayı güncelle
    with open(HAFIZA_DOSYASI, "w", encoding="utf-8") as f:
        f.write("\n".join(gonderilenler[-100:]))

if __name__ == "__main__":
    asyncio.run(botu_calistir())

# Çalıştırma komutu
if __name__ == "__main__":
    asyncio.run(botu_calistir())
