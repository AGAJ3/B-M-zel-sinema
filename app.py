# Film İzlerken Hızlı Salon Sohbeti
    st.write("---")
    st.subheader("💬 Koltuk Sohbeti (Canlı)")


    # Mesaj gönderme alanı (En üste alıyoruz ki yazıp enter'a basınca anında kaydetsin)
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


    # Canlı Akış Alanı (Daha hızlı tetikleme için run_every=2 yapabiliriz)
    @st.fragment(run_every=2)
    def sinema_sohbet_akisi():
      guncel_mesajlar = load_json(OZEL_SOHBET_DOSYASI, [])
      for m in guncel_mesajlar[-5:]:
        st.markdown(
            f"🍿 **{m['sender']}** <span style='font-size:12px; color:#aaa;'>"
            f"({m['time']}):</span> {m['text']}",
            unsafe_allow_html=True,
        )


    sinema_sohbet_akisi()
