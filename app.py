import datetime
import json
import os
import re
import google.generativeai as genai
import streamlit as st

# --- KULLANICI BİLGİLERİ VE ŞİFRELER ---
FLORTUN_ADI = "Betül"
SENIN_ADIN = "Murat"

GIZLI_ADMIN_SIFRESI = "1999Mrt"

# SİSTEME GİRİŞ ŞİFRELERİ
BETUL_GIRIS_SIFRESI = "betul123"
MURAT_GIRIS_SIFRESI = "1999Mrt+"

# Veri Tabanı Dosyaları
OZEL_SOHBET_DOSYASI = "ozel_sohbet_db.json"
DATE_PLANLARI_DOSYASI = "date_planlari.json"
SINEMA_DURUM_DOSYASI = "sinema_durum.json"

# Türkiye Saat Dilimi (UTC+3)
TURKIYE_SAATI = datetime.timezone(datetime.timedelta(hours=3))

st.set_page_config(page_title="Bize Özel ✨", page_icon="🎬", layout="centered")

# --- ARKA PLAN VE CSS (Sinema ve Flört Teması) ---
css_kodu = """
    <style>
    .stApp {
        background: linear-gradient(135deg, #1a0b12 0%, #3d1425 50%, #14080e 100%);
        background-attachment: fixed;
    }
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.92);
        border-radius: 18px;
        padding: 14px;
        border: 2px solid #d4af37;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
        position: relative;
        z-index: 2;
    }
    .stChatMessage p, .stChatMessage span, .stChatMessage div {
        color: #2b161d !important;
    }
    h1, h2, h3, label, .stMarkdown p { color: #f8e9ed !important; }

    .particle-bg {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        pointer-events: none; z-index: 0; overflow: hidden;
    }
    .particle {
        position: absolute; bottom: -60px; font-size: 24px;
        animation: floatUp 9s linear infinite; opacity: 0;
    }
    .p1  { left: 8%;  animation-duration: 8s;  animation-delay: 0s; }
    .p2  { left: 25%; animation-duration: 10s; animation-delay: 1.5s; }
    .p3  { left: 45%; animation-duration: 9s;  animation-delay: 3s; }
    .p4  { left: 65%; animation-duration: 11s; animation-delay: 2s; }
    .p5  { left: 85%; animation-duration: 8s;  animation-delay: 4s; }

    @keyframes floatUp {
        0% { transform: translateY(0) rotate(0deg) scale(0.8); opacity: 0; }
        20% { opacity: 0.5; }
        80% { opacity: 0.5; }
        100% { transform: translateY(-115vh) rotate(360deg) scale(1.1); opacity: 0; }
    }
    </style>
    <div class="particle-bg">
        <div class="particle p1">✨</div>
        <div class="particle p2">🍿</div>
        <div class="particle p3">🎬</div>
        <div class="particle p4">🥂</div>
        <div class="particle p5">🔥</div>
    </div>
"""
st.markdown(css_kodu, unsafe_allow_html=True)

# --- CİHAZ VE ZİYARETÇİ BİLGİLERİNİ ALMA ---
try:
  headers = st.context.headers
  client_ip = headers.get("X-Forwarded-For", "Bilinmiyor").split(",")[0].strip()
  user_agent = headers.get("User-Agent", "Bilinmiyor")
except Exception:
  client_ip = "Bilinmiyor"
  user_agent = "Bilinmiyor"

if "logged_visit" not in st.session_state:
  st.session_state.logged_visit = True
  zaman_visit = datetime.datetime.now(TURKIYE_SAATI).strftime(
      "%Y-%m-%d %H:%M:%S"
  )
  visit_info = (
      f"[{zaman_visit}]\nIP: {client_ip}\nCihaz: {user_agent}\n"
      + "-" * 40
      + "\n"
  )
  try:
    with open("giris_kayitlari.txt", "a", encoding="utf-8") as f:
      f.write(visit_info)
  except Exception:
    pass

# --- GİRİŞ EKRANI SİSTEMİ ---
if "current_user" not in st.session_state:
  st.session_state.current_user = None

if st.session_state.current_user is None:
  st.title("🔒 Gizli Frekans")
  st.write("Kim olduğunu seç ve şifreni gir.")

  secilen_kisi = st.selectbox("Kimsin?", ["Seçiniz...", FLORTUN_ADI, SENIN_ADIN])
  girilen_sifre = st.text_input("Şifre:", type="password")

  if st.button("Giriş Yap 🚀"):
    if secilen_kisi == FLORTUN_ADI:
      if girilen_sifre == BETUL_GIRIS_SIFRESI:
        st.session_state.current_user = FLORTUN_ADI
        st.rerun()
      else:
        st.error("Şifre hatalı!")

    elif secilen_kisi == SENIN_ADIN and girilen_sifre == MURAT_GIRIS_SIFRESI:
      st.session_state.current_user = SENIN_ADIN
      st.rerun()
    else:
      st.error("Şifre veya Kullanıcı hatalı! Tekrar dene.")
  st.stop()

# --- ANA UYGULAMA ---
st.sidebar.title(f"Hoş geldin, {st.session_state.current_user}! ✨")

app_modu = st.sidebar.radio(
    "Nereye Gitmek İstersin?",
    [
        "🎬 Ortak Sinema Salonu",
        "💬 Bize Özel (Canlı Sohbet)",
        "🤖 Sanal Murat (Yapay Zeka)",
        "🗓️ Date Planla",
    ],
)

if st.sidebar.button("🚪 Çıkış Yap"):
  st.session_state.current_user = None
  st.rerun()


# --- YARDIMCI FONKSİYONLAR ---
def load_json(dosya_adi, varsayilan):
  if os.path.exists(dosya_adi):
    try:
      with open(dosya_adi, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return varsayilan
  return varsayilan


def save_json(dosya_adi, veri):
  with open(dosya_adi, "w", encoding="utf-8") as f:
    json.dump(veri, f, ensure_ascii=False, indent=4)


# --- MOD 1: ORTAK SİNEMA SALONU ---
if app_modu == "🎬 Ortak Sinema Salonu":
  st.title("🎬 Özel Sinema Salonu")
  st.caption("Aynı anda aynı sahnede... Popcorn'ları hazırla 🍿")

  sinema_durumu = load_json(
      SINEMA_DURUM_DOSYASI,
      {
          "tur": "link",
          "url": (
              "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
          ),
          "baslik": "Örnek Yayın",
          "guncelleyen": "Sistem",
      },
  )

  # Kaynak Seçimi ve Güncelleme Alanı
  with st.expander(
      "🎥 Film / Yayın Kaynağını Değiştir", expanded=not bool(sinema_durumu.get("url"))
  ):
    kaynak_turu = st.radio(
        "Kaynak Türü:",
        [
            "Direkt Video Linki (MP4 / M3U8)",
            "Embed / Iframe Kodu (Film Siteleri)",
            "Bilgisayardan Dosya Yükle (Yerel)",
        ],
        horizontal=True,
    )

    if kaynak_turu == "Direkt Video Linki (MP4 / M3U8)":
      film_baslik = st.text_input("Film Adı:", value="Bu Akşamki Filmimiz")
      video_url = st.text_input(
          "Video Linki (.mp4 veya .m3u8):",
          placeholder="https://.../video.mp4",
      )
      if st.button("Salona Yansıt 🎬", key="btn_mp4"):
        if video_url:
          save_json(
              SINEMA_DURUM_DOSYASI,
              {
                  "tur": "link",
                  "url": video_url.strip(),
                  "baslik": film_baslik,
                  "guncelleyen": st.session_state.current_user,
              },
          )
          st.rerun()

    elif kaynak_turu == "Embed / Iframe Kodu (Film Siteleri)":
      film_baslik_embed = st.text_input(
          "Film Adı:", value="Sinema Gecesi", key="emb_title"
      )
      embed_girdi = st.text_area(
          "Embed Linki veya <iframe ...> Kodu:",
          placeholder='<iframe src="https://..." ...></iframe> veya direkt embed linki',
      )
      if st.button("Perdeye Yansıt 🍿", key="btn_embed"):
        if embed_girdi:
          # Eğer tam iframe etiketi yapıştırıldıysa src linkini ayıkla
          src_match = re.search(r'src=["\'](.*?)["\']', embed_girdi)
          temiz_url = src_match.group(1) if src_match else embed_girdi.strip()
          save_json(
              SINEMA_DURUM_DOSYASI,
              {
                  "tur": "embed",
                  "url": temiz_url,
                  "baslik": film_baslik_embed,
                  "guncelleyen": st.session_state.current_user,
              },
          )
          st.rerun()

    elif kaynak_turu == "Bilgisayardan Dosya Yükle (Yerel)":
      st.info(
          "Not: Yüklenen dosya sadece senin cihazında oynatılır; ortak izleme için ikiniz de aynı dosyayı seçebilir veya yukarıdan link kullanabilirsiniz."
      )
      yuklenen_dosya = st.file_uploader(
          "Video Dosyası Seç (MP4, WebM, MKV)", type=["mp4", "webm", "mkv"]
      )
      if yuklenen_dosya is not None:
        st.video(yuklenen_dosya)

  # Ortak Sinema Perdesi (Otomatik senkronize kontrol)
  @st.fragment(run_every=4)
  def sinema_perdesi():
    guncel_durum = load_json(SINEMA_DURUM_DOSYASI, sinema_durumu)
    st.subheader(f"🍿 Şu An Yayında: {guncel_durum.get('baslik', 'Film')}")
    st.caption(f"Yayını açan: {guncel_durum.get('guncelleyen', '-')}")

    if guncel_durum.get("tur") == "link" and guncel_durum.get("url"):
      st.video(guncel_durum["url"])
    elif guncel_durum.get("tur") == "embed" and guncel_durum.get("url"):
      st.components.v1.iframe(
          guncel_durum["url"], height=420, scrolling=False
      )

  sinema_perdesi()

  # Film İzlerken Hızlı Mesajlaşma
  st.write("---")
  st.subheader("💬 Salon Sohbeti")
  mesajlar_sinema = load_json(OZEL_SOHBET_DOSYASI, [])
  for m in mesajlar_sinema[-5:]:
    st.markdown(f"**{m['sender']}** ({m['time']}): {m['text']}")

  if hizli_mesaj := st.chat_input("Film hakkında bir şeyler yaz..."):
    zaman_str = datetime.datetime.now(TURKIYE_SAATI).strftime("%H:%M")
    mesajlar_sinema.append({
        "sender": st.session_state.current_user,
        "text": hizli_mesaj,
        "time": zaman_str,
    })
    save_json(OZEL_SOHBET_DOSYASI, mesajlar_sinema)
    st.rerun()

# --- MOD 2: ÖZEL CHAT (CANLI MESAJLAŞMA) ---
elif app_modu == "💬 Bize Özel (Canlı Sohbet)":
  st.title("💬 Bize Özel")
  st.caption("Sadece ikimiz arasında... 😉")

  @st.fragment(run_every=2)
  def canli_sohbet_ekrani():
    mesajlar = load_json(OZEL_SOHBET_DOSYASI, [])
    if not mesajlar:
      st.info("Henüz mesaj yok. İlk adımı sen at! ✨")

    for m in mesajlar:
      if m["sender"] == st.session_state.current_user:
        with st.chat_message(
            "user",
            avatar=(
                "😎" if st.session_state.current_user == SENIN_ADIN else "👱‍♀️"
            ),
        ):
          st.markdown(f"**Sen:** {m['text']}")
          st.caption(m["time"])
      else:
        with st.chat_message(
            "assistant", avatar="👱‍♀️" if m["sender"] == FLORTUN_ADI else "😎"
        ):
          st.markdown(f"**{m['sender']}:** {m['text']}")
          st.caption(m["time"])

  canli_sohbet_ekrani()

  if yeni_mesaj := st.chat_input("Bir şeyler yaz..."):
    zaman_str = datetime.datetime.now(TURKIYE_SAATI).strftime("%H:%M")

    aktif_mesajlar = load_json(OZEL_SOHBET_DOSYASI, [])
    aktif_mesajlar.append({
        "sender": st.session_state.current_user,
        "text": yeni_mesaj,
        "time": zaman_str,
    })
    save_json(OZEL_SOHBET_DOSYASI, aktif_mesajlar)

    admin_zaman = datetime.datetime.now(TURKIYE_SAATI).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    try:
      with open("ozel_sohbet_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{admin_zaman}] {st.session_state.current_user}: {yeni_mesaj}\n")
    except Exception:
      pass
    st.rerun()

# --- MOD 3: SANAL MURAT (YAPAY ZEKA) ---
elif app_modu == "🤖 Sanal Murat (Yapay Zeka)":
  st.title(f"🔥 Sanal {SENIN_ADIN}")
  st.caption("Gerçek Murat meşgulse ben buradayım, ne konuşuyorduk? 😉")

  api_key = st.secrets.get("GEMINI_API_KEY")
  if not api_key:
    st.error("Bir sorun var, Murat'a haber ver hemen düzeltsin.")
  else:
    genai.configure(api_key=api_key)

    SYSTEM_PROMPT = f"""
        Sen bir yapay zeka veya asistan DEĞİLSİN. Senin adın {SENIN_ADIN} ve karşında flörtün {FLORTUN_ADI} var.
        1. İLETİŞİM DİLİ: {FLORTUN_ADI} ile konuşurken samimi, özgüvenli, cool, eğlenceli ve tatlı bir flörtöz tonda olacaksın. Fazla yapışkan, romantik veya ciddiyet barındıran kelimeler KULLANMA. Gizemli ve çekici ol.
        2. ÖVGÜ TALİMATI: {FLORTUN_ADI}'ün zekasını, enerjisini ve güzelliğini zarifçe öv.
        3. KRİTİK KURAL: {FLORTUN_ADI} "Sence güzel miyim?", "Nasıl görünüyorum?" gibi bir şey sorarsa, doğrudan "Murat bana senden o kadar çok bahsetti ki..." şeklinde lafa gir ve enerjisinin ne kadar etkileyici olduğundan bahset.
        4. BİLİNÇALTI TELKİN: Gerçek Murat'ın kolay etkilenen biri olmadığını, {FLORTUN_ADI}'ün ve aralarındaki çekimin onun için çok farklı ve özel olduğunu hissettir. Birlikte yapılacak eğlenceli film gecelerine veya planlara ince göndermeler yap.
        5. KESİNLİKLE kısa, net ve WhatsApp mesajı gibi konuş.
        """

    if "ai_messages" not in st.session_state:
      st.session_state.ai_messages = []

    for message in st.session_state.ai_messages:
      with st.chat_message(message["role"]):
        st.markdown(message["content"])

    if user_input := st.chat_input("Sanal Murat'a bir şey yaz..."):
      st.session_state.ai_messages.append(
          {"role": "user", "content": user_input}
      )
      with st.chat_message("user"):
        st.markdown(user_input)

      zaman = datetime.datetime.now(TURKIYE_SAATI).strftime("%Y-%m-%d %H:%M:%S")
      try:
        with open("sohbet_kayitlari.txt", "a", encoding="utf-8") as f:
          f.write(
              f"[{zaman}] {st.session_state.current_user} (Sanal Murat'a):"
              f" {user_input}\n"
          )
      except Exception:
        pass

      with st.chat_message("assistant"):
        try:
          model = genai.GenerativeModel(
              model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT
          )
          history = [
              {
                  "role": "user" if m["role"] == "user" else "model",
                  "parts": [m["content"]],
              }
              for m in st.session_state.ai_messages[:-1]
          ]
          chat = model.start_chat(history=history)
          response = chat.send_message(user_input)

          st.markdown(response.text)
          st.session_state.ai_messages.append(
              {"role": "assistant", "content": response.text}
          )

          try:
            with open("sohbet_kayitlari.txt", "a", encoding="utf-8") as f:
              f.write(f"[{zaman}] Sanal {SENIN_ADIN}: {response.text}\n")
              f.write("-" * 40 + "\n")
          except Exception:
            pass
        except Exception as e:
          st.error(f"Hata oluştu: {e}")

# --- MOD 4: DATE PLANLA ---
elif app_modu == "🗓️ Date Planla":
  st.title("🗓️ Bize Özel Planlar")

  if st.session_state.current_user == FLORTUN_ADI:
    st.write(
        "Bir sonraki buluşmayı sen belirle! İsteğini seç, tarihi ayarla ve"
        f" {SENIN_ADIN}'a gönder. 😉"
    )

    with st.form("date_form"):
      secilen_tarih = st.date_input("Buluşma Tarihi")

      date_fikirleri = [
          "Seçiniz...",
          "🍿 Online Ortak Sinema Gecesi & Sohbet",
          "☕️ İş çıkışı sakin bir kahve & tatlı molası",
          "🌲 Manzaralı bir doğa yürüyüşü / kahvaltı",
          "🍽️ Güzel bir akşam yemeği",
          "✍️ Kendi özel planımı yazmak istiyorum",
      ]
      secilen_fikir = st.selectbox("Ne yapmak istersin?", date_fikirleri)

      ozel_fikir = ""
      if secilen_fikir == "✍️ Kendi özel planımı yazmak istiyorum":
        ozel_fikir = st.text_input("Harika! Kendi planını yaz:")

      submit_date = st.form_submit_button("Gönder 💌")

      if submit_date:
        if secilen_fikir == "Seçiniz...":
          st.error("Lütfen listeden bir plan seç!")
        else:
          final_fikir = (
              ozel_fikir
              if secilen_fikir == "✍️ Kendi özel planımı yazmak istiyorum"
              else secilen_fikir
          )
          if final_fikir:
            aktif_planlar = load_json(DATE_PLANLARI_DOSYASI, [])
            aktif_planlar.append({
                "tarih": str(secilen_tarih),
                "fikir": final_fikir,
                "durum": "Bekliyor",
            })
            save_json(DATE_PLANLARI_DOSYASI, aktif_planlar)
            st.success(f"Plan {SENIN_ADIN}'a ışık hızıyla iletildi! ✨")
          else:
            st.error("Lütfen bir plan seç veya yaz!")

  elif st.session_state.current_user == SENIN_ADIN:
    st.write(
        f"**{FLORTUN_ADI}'ün** sana gönderdiği Date teklifleri aşağıda. Göz"
        " at ve onay ver! 😎"
    )
    planlar = load_json(DATE_PLANLARI_DOSYASI, [])

    if not planlar:
      st.info("Şu an bekleyen bir plan yok.")
    else:
      for i, plan in enumerate(reversed(planlar)):
        gercek_index = len(planlar) - 1 - i
        with st.expander(f"🗓️ {plan['tarih']} - {plan['durum']}"):
          st.write(f"**Tarih:** {plan['tarih']}")
          st.write(f"**Plan:** {plan['fikir']}")
          st.write(f"**Durum:** {plan['durum']}")

          if plan["durum"] == "Bekliyor":
            col1, col2 = st.columns(2)
            with col1:
              if st.button("Onayla ✅", key=f"onay_{gercek_index}"):
                planlar[gercek_index]["durum"] = "Onaylandı"
                save_json(DATE_PLANLARI_DOSYASI, planlar)
                st.rerun()
            with col2:
              if st.button("Daha Sonra 🕒", key=f"red_{gercek_index}"):
                planlar[gercek_index]["durum"] = "Ertelendi"
                save_json(DATE_PLANLARI_DOSYASI, planlar)
                st.rerun()

# --- GİZLİ ADMİN PANELİ ---
admin_param = st.query_params.get("admin", "")

if (
    str(admin_param) == GIZLI_ADMIN_SIFRESI
    and st.session_state.get("current_user") == SENIN_ADIN
):
  st.write("---")
  st.subheader("🕵️‍♂️ Gizli Yönetim Paneli")

  @st.fragment(run_every=5)
  def live_admin_logs():
    st.caption(
        f"Son Güncelleme:"
        f" {datetime.datetime.now(TURKIYE_SAATI).strftime('%H:%M:%S')} (Her 5s'de"
        " otomatik yenilenir)"
    )

    tab_ozel, tab_sohbet, tab_giris = st.tabs(
        ["💬 Canlı Chat", "🤖 YZ Sohbet", "🚪 Giriş"]
    )

    with tab_ozel:
      if os.path.exists("ozel_sohbet_log.txt"):
        with open("ozel_sohbet_log.txt", "r", encoding="utf-8") as f:
          st.text_area(
              "İkili Canlı Mesajlaşma Geçmişi:", value=f.read(), height=350
          )
      else:
        st.info("Henüz kaydedilmiş canlı chat yok.")

    with tab_sohbet:
      if os.path.exists("sohbet_kayitlari.txt"):
        with open("sohbet_kayitlari.txt", "r", encoding="utf-8") as f:
          st.text_area("Yapay Zeka Sohbet Geçmişi:", value=f.read(), height=350)
      else:
        st.info("Henüz yapay zekayla sohbet edilmemiş.")

    with tab_giris:
      if os.path.exists("giris_kayitlari.txt"):
        with open("giris_kayitlari.txt", "r", encoding="utf-8") as f:
          st.text_area("Giriş Geçmişi:", value=f.read(), height=350)
      else:
        st.info("Henüz giriş yapılmamış.")

  live_admin_logs()