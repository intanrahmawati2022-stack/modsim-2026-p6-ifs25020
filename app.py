import streamlit as st
import simpy
import random
import pandas as pd
import numpy as np
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Simulasi Antrean IT Del", 
    page_icon="📊", 
    layout="wide"
)

# --- STYLE CSS CUSTOM ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE SIMULASI (LOGIKA BISNIS) ---
class UjianSystem:
    def __init__(self, env, capacity):
        self.env = env
        self.meja_pengajar = simpy.Resource(env, capacity=capacity)
        self.data_log = []

def mahasiswa_process(env, nama, system, min_d, max_d):
    t_datang = env.now
    
    with system.meja_pengajar.request() as request:
        yield request
        
        t_mulai = env.now
        waktu_tunggu = t_mulai - t_datang
        
        # Menggunakan distribusi uniform untuk durasi pelayanan
        durasi_pelayanan = random.uniform(min_d, max_d)
        yield env.timeout(durasi_pelayanan)
        
        t_selesai = env.now
        
        system.data_log.append({
            "Mahasiswa": nama,
            "Waktu Datang": round(t_datang, 2),
            "Mulai Dilayani": round(t_mulai, 2),
            "Lama Tunggu": round(waktu_tunggu, 2),
            "Durasi Pelayanan": round(durasi_pelayanan, 2),
            "Waktu Selesai": round(t_selesai, 2),
            "Resource": "Meja Pengajar"
        })

def run_simulation(N, min_d, max_d, seed, capacity):
    random.seed(seed)
    env = simpy.Environment()
    system = UjianSystem(env, capacity)
    
    for i in range(1, N + 1):
        env.process(mahasiswa_process(env, f"Mhs {i:02d}", system, min_d, max_d))
    
    env.run()
    return pd.DataFrame(system.data_log).sort_values("Mulai Dilayani")

# --- UI STREAMLIT ---
st.title("📊 Simulasi Antrean Pengambilan Lembar Jawaban")
st.info("Aplikasi ini memodelkan antrean satu jalur (Single Server Queue) menggunakan aturan FIFO.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Parameter Input")
    num_mahasiswa = st.number_input("Jumlah Mahasiswa (N)", min_value=1, value=30)
    
    st.subheader("⏱️ Durasi Pelayanan (Menit)")
    min_durasi = st.slider("Minimum", 0.1, 5.0, 1.0)
    max_durasi = st.slider("Maksimum", 1.0, 15.0, 3.0)
    
    if min_durasi > max_durasi:
        st.error("Error: Durasi Min tidak boleh > Max")
    
    st.subheader("🏫 Konfigurasi")
    kapasitas = st.selectbox("Jumlah Meja/Petugas", [1, 2, 3], index=0)
    random_seed = st.number_input("Random Seed", value=42)
    
    run_btn = st.button("🚀 Jalankan Simulasi", use_container_width=True)

# --- EKSEKUSI ---
if run_btn:
    df_hasil = run_simulation(num_mahasiswa, min_durasi, max_durasi, random_seed, kapasitas)
    
    # --- 1. METRIK UTAMA ---
    total_waktu = df_hasil["Waktu Selesai"].max()
    rata_tunggu = df_hasil["Lama Tunggu"].mean()
    utilisasi = (df_hasil["Durasi Pelayanan"].sum() / (total_waktu * kapasitas)) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Waktu Proses", f"{total_waktu:.2f} m")
    col2.metric("Rata-rata Antrean", f"{rata_tunggu:.2f} m")
    col3.metric("Utilisasi Meja", f"{utilisasi:.1f}%")

    # --- 2. VISUALISASI GANTT CHART ---
    st.subheader("⏳ Garis Waktu Pelayanan (Gantt Chart)")
    fig = px.timeline(
        df_hasil, 
        x_start="Mulai Dilayani", 
        x_end="Waktu Selesai", 
        y="Mahasiswa", 
        color="Durasi Pelayanan",
        hover_data=["Lama Tunggu"],
        color_continuous_scale="Viridis"
    )
    # Tweak untuk menampilkan angka (menit) di sumbu X alih-alih tanggal
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(xaxis_type='linear', xaxis_title="Waktu (Menit)")
    st.plotly_chart(fig, use_container_width=True)

    # --- 3. VALIDASI & VERIFIKASI ---
    tab1, tab2 = st.tabs(["🔍 Verifikasi Data", "🧪 Validasi Teoretis"])
    
    with tab1:
        st.dataframe(df_hasil, use_container_width=True)
        csv = df_hasil.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Hasil (CSV)", data=csv, file_name="hasil_simulasi.csv")
    with tab2:
        rata_durasi_teori = (min_durasi + max_durasi) / 2
        total_waktu_teori = (num_mahasiswa * rata_durasi_teori) / kapasitas
        akurasi = (1 - abs(total_waktu - total_waktu_teori) / total_waktu_teori) * 100
        
        v_col1, v_col2 = st.columns(2)
        v_col1.write("**Hasil Simulasi:**")
        v_col1.code(f"Rata-rata Pelayanan: {df_hasil['Durasi Pelayanan'].mean():.2f}\nTotal Waktu: {total_waktu:.2f}")
        
        v_col2.write("**Estimasi Teoretis:**")
        v_col2.code(f"Rata-rata Pelayanan: {rata_durasi_teori:.2f}\nTotal Waktu: {total_waktu_teori:.2f}")
        
        st.success(f"**Tingkat Kemiripan Model:** {akurasi:.2f}%")

else:
    st.warning("Gunakan panel di sebelah kiri untuk mengatur parameter dan tekan tombol 'Jalankan Simulasi'.")