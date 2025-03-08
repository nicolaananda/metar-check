import streamlit as st
from metar_data import MetarData

# Setup dasar aplikasi
st.set_page_config(page_title="METAR Viewer App", page_icon="🌦️", layout="centered")
st.title("🌦️ Aplikasi Pengecekan METAR")
st.write("Masukkan kode stasiun ICAO (pisahkan dengan koma untuk beberapa stasiun, contoh: WARR,WIHH) untuk melihat laporan METAR terbaru!")

# Input kode stasiun
station_input = st.text_input("Kode Stasiun ICAO:", "WADD", help="Contoh: WARR,WIHH").upper()

# Tombol untuk memicu pengambilan data
if st.button("🔍 Cek METAR"):
    # Memisahkan input stasiun menjadi list
    stations = [station.strip() for station in station_input.split(",")]

    # Validasi setiap kode stasiun
    valid = True
    for station in stations:
        if len(station) != 4:
            st.error(f"Kode stasiun '{station}' harus terdiri dari 4 huruf!")
            valid = False
            break

    if valid:
        # Warna berbeda untuk setiap stasiun (max 5 warna untuk contoh)
        colors = ["#FF4500", "#4682B4", "#32CD32", "#FFD700", "#800080"] 
        color_index = 0

        # Mengambil data untuk setiap stasiun
        with st.spinner("Mengambil data METAR..."):
            st.subheader("📊 Data METAR")
            for station in stations:
                metar = MetarData(station)
                metar.fetch_data()
                result = metar.get_data()

                if result["error"]:
                    st.error(result["error"])
                else:
                    # Menampilkan waktu pengamatan dan laporan METAR dengan warna berbeda
                    st.write(f"**Waktu Pengamatan ({station}):** {result['timestamp']}")
                    color = colors[color_index % len(colors)]  # Menggunakan warna secara berulang jika lebih dari 5 stasiun
                    st.markdown(f"**Laporan METAR ({station}):** <span style='color:{color}'>{result['report']}</span>", unsafe_allow_html=True)

                    # Parsing lebih detail dengan penjelasan singkatan dalam button expand
                    with st.expander(f"🔧 Lihat Detail Parsing ({station})"):
                        parsed_data = result["parsed"]
                        if parsed_data["wind"]["value"]:
                            st.write(f"🌬️ Angin: {parsed_data['wind']['value']} ({parsed_data['wind']['description']})")
                        if parsed_data["visibility"]["value"]:
                            st.write(f"👓 Visibilitas: {parsed_data['visibility']['value']} ({parsed_data['visibility']['description']})")
                        if parsed_data["weather"]["value"]:
                            st.write(f"☁️ Kondisi Cuaca: {parsed_data['weather']['value']} ({parsed_data['weather']['description']})")
                        if parsed_data["clouds"]["value"]:
                            st.write(f"⛅ Awan: {', '.join(parsed_data['clouds']['value'])} ({', '.join(parsed_data['clouds']['description'])})")
                        else:
                            st.write("⛅ Awan: Tidak ada informasi awan yang dilaporkan.")
                        if parsed_data["temperature"]["value"]:
                            st.write(f"🌡️ Suhu: {parsed_data['temperature']['value']} ({parsed_data['temperature']['description']})")
                        if parsed_data["dew_point"]["value"]:
                            st.write(f"💧 Titik Embun: {parsed_data['dew_point']['value']} ({parsed_data['dew_point']['description']})")
                        if parsed_data["pressure"]["value"]:
                            st.write(f"📏 Tekanan: {parsed_data['pressure']['value']} ({parsed_data['pressure']['description']})")
                        if parsed_data["remarks"]["value"]:
                            st.write(f"💬 Keterangan: {parsed_data['remarks']['value']} ({parsed_data['remarks']['description']})")

                    color_index += 1 

# Penjelasan tentang METAR dalam expander
with st.expander("ℹ️ Apa itu METAR?"):
    st.write("""
        METAR (Meteorological Aerodrome Report) adalah laporan cuaca standar internasional yang digunakan di bandara. 
        Laporan ini memberikan informasi tentang kondisi cuaca saat ini seperti suhu, angin, tekanan udara, visibilitas, kondisi cuaca, dan lapisan awan.
        Formatnya singkat dan menggunakan kode tertentu, biasanya diperbarui setiap jam.
    """)
    st.write("**Contoh:** `WADD 081330Z 19004KT 9999 FEW017 29/28 Q1009 NOSIG`")

# Footer
st.write("---")
st.write("Data diambil dari server NOAA (http://tgftp.nws.noaa.gov).")