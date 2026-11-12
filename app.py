# --- MOD 1: ORTAK SİNEMA SALONU ---
elif app_modu == "🎬 Ortak Sinema Salonu":
    # Sinema salonu özel CSS tasarımı
    st.markdown(
        """
        <style>
        .theater-container {
            background: radial-gradient(circle at center, #2b121a 0%, #0d0408 100%);
            border: 3px solid #d4af37;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.3), inset 0 0 20px rgba(0,0,0,0.8);
            margin-bottom: 25px;
        }
        .curtain-banner {
            text-align: center;
            font-family: 'Courier New', monospace;
            color: #d4af37;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-weight: bold;
            margin-bottom: 15px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.6);
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("🎬 VIP Ortak Sinema Salonu")
    st.caption("Işıklar kapandı, perde açılıyor... Mısırları hazırlayın, aynı anda aynı sahnedesiniz 🍿")

    sinema_durumu = load_json(
        SINEMA_DURUM_DOSYASI,
        {
            "tur": "link",
            "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "baslik": "Örnek Sinema Gecesi Yayını",
            "guncelleyen": "Sistem",
        },
    )

    # Kaynak Seçimi ve Güncelleme Alanı (Sinema Locası)
    with st.expander("🎥 Film / Yayın Perdesini Değiştir", expanded=not bool(sinema_durumu.get("url"))):
        kaynak_turu = st.radio(
            "Yayın Kaynağı Seçin:",
            [
                "Direkt Video Linki (MP4 / M3U8)",
                "Embed / Iframe Kodu (Film Siteleri)",
                "Bilgisayardan Dosya Yükle (Yerel)",
            ],
            horizontal=True,
        )

        if kaynak_turu == "Direkt Video Linki (MP4 / M3U8)":
            film_baslik = st.text_input("Film Adı:", value="Bu Akşamki Sinema Filmi")
            video_url = st.text_input("Video Linki (.mp4 veya .m3u8):", placeholder="https://.../video.mp4")
            if st.button("Perdeye Yansıt 🎬", key="btn_mp4"):
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
            film_baslik_embed = st.text_input("Film Adı:", value="Özel Sinema Gecesi", key="emb_title")
            embed_girdi = st.text_area(
                "Embed Linki veya <iframe ...> Kodu:",
                placeholder='<iframe src="https://..." ...></iframe> veya direkt embed linki',
            )
            if st.button("Salona Yansıt 🍿", key="btn_embed"):
                if embed_girdi:
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
            st.info("Not: Yüklenen dosya sadece senin cihazında oynatılır; ortak izleme için ikiniz de aynı dosyayı seçebilir veya yukarıdan link kullanabilirsiniz.")
            yuklenen_dosya = st.file_uploader("Video Dosyası Seç (MP4, WebM, MKV)", type=["mp4", "webm", "mkv"])
            if yuklenen_dosya is not None:
                st.video(yuklenen_dosya)

    # Sinema Salonu Çerçevesi İçinde Perde
    st.markdown('<div class="theater-container">', unsafe_allow_html=True)

    @st.fragment(run_every=4)
    def sinema_perdesi():
        guncel_durum = load_json(SINEMA_DURUM_DOSYASI, sinema_durumu)
        st.markdown(
            f'<div class="curtain-banner">⭐ Vizyonda:  {guncel_durum.get("baslik", "Film")} ⭐</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Salona yansıtan: {guncel_durum.get('guncelleyen', '-')}")

        if guncel_durum.get("tur") == "link" and guncel_durum.get("url"):
            st.video(guncel_durum["url"])
        elif guncel_durum.get("tur") == "embed" and guncel_durum.get("url"):
            st.components.v1.iframe(guncel_durum["url"], height=450, scrolling=False)

    sinema_perdesi()
    st.markdown("</div>", unsafe_allow_html=True)

    # Film İzlerken Hızlı Salon Sohbeti
    st.write("---")
    st.subheader("💬 Koltuk Sohbeti (Canlı)")

    if hizli_mesaj := st.chat_input("Sahne hakkında fısılda..."):
        zaman_str = datetime.datetime.now(TURKIYE_SAATI).strftime("%H:%M")
        mesajlar_sinema = load_json(OZEL_SOHBET_DOSYASI, [])
        mesajlar_sinema.append({
            "sender": st.session_state.current_user,
            "text": hizli_mesaj,
            "time": zaman_str,
        })
        save_json(OZEL_SOHBET_DOSYASI, mesajlar_sinema)
        st.rerun()

    @st.fragment(run_every=2)
    def sinema_sohbet_akisi():
        guncel_mesajlar = load_json(OZEL_SOHBET_DOSYASI, [])
        for m in guncel_mesajlar[-5:]:
            st.markdown(
                f"🍿 **{m['sender']}** <span style='font-size:12px; color:#aaa;'>({m['time']}):</span> {m['text']}",
                unsafe_allow_html=True,
            )

    sinema_sohbet_akisi()
