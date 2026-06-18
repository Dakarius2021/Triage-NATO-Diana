import streamlit as st
import pandas as pd
import time
import numpy as np

# --- 1. CONFIGURARE INTERFAȚĂ C4ISR ---
st.set_page_config(page_title="NATO DIANA - P.A.C.E. C4ISR", layout="wide")
st.title("🚁 P.A.C.E. - Command & Control (C4ISR)")
st.markdown("### Demonstrator TRL 4: MASCAL, Edge AI, Sensor Fusion & Auto-Dispatch")

# --- 2. ÎNCĂRCAREA DATELOR ---
@st.cache_data
def incarca_date():
    try:
        return pd.read_csv("baza_date_curatata_nato.csv")
    except FileNotFoundError:
        st.error("Nu găsesc fișierul 'baza_date_curatata_nato.csv'.")
        return pd.DataFrame()

df = incarca_date()

if not df.empty:
    st.sidebar.header("🕹️ Parametri Misiune")
    simuleaza = st.sidebar.button("▶ START MISIUNE TACTICĂ", type="primary")
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Inovații Active:**
    * 🤫 **Edge AI:** Liniște radio până la detecția colapsului.
    * 🌐 **Sensor Fusion:** Diferențiere între efort și hemoragie.
    * 🚑 **MASCAL:** Rutare autonomă a resurselor (1 Dronă MEDEVAC la 4 soldați).
    """)

    # Selectăm 4 pacienți pentru pluton (Includem cazurile critice descoperite)
    lista_completa = df['Patient_ID'].unique().tolist()
    # Asigurăm că avem pacienții instabili pentru demonstrație, plus alții la întâmplare
    pacienti_tinta = [p for p in [3000866, 3000063, 3000282, lista_completa[0], lista_completa[1]] if p in lista_completa][:4]
    
    # Extragem datele pentru cei 4 soldați
    date_pluton = {pid: df[df['Patient_ID'] == pid].reset_index(drop=True) for pid in pacienti_tinta}
    # Găsim durata minimă ca să nu dea eroare bucla
    durata_minima = min([len(date_pluton[pid]) for pid in pacienti_tinta])

    # --- LAYOUT DASHBOARD ---
    st.markdown("---")
    header_mascal = st.empty() # Aici afișăm decizia AI-ului pentru dronă
    st.markdown("### 🪖 Status Pluton Alpha (Monitorizare Live)")
    
    # Creăm un grid 2x2 pentru cei 4 soldați
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    containere_soldati = [col1.empty(), col2.empty(), col3.empty(), col4.empty()]

    if simuleaza:
        for i in range(durata_minima):
            stari_soldati = []

            # 1. EVALUAREA TUTUROR CELOR 4 SOLDAȚI
            for idx, pid in enumerate(pacienti_tinta):
                rand = date_pluton[pid].iloc[i]
                
                p_actual = rand['Puls'] if pd.notna(rand['Puls']) else 80
                s_actual = rand['SpO2'] if pd.notna(rand['SpO2']) else 98
                
                # Derivata (Predicția viitorului)
                if i >= 10:
                    s_trecut = date_pluton[pid].iloc[i-10]['SpO2']
                    delta_spo2 = s_actual - s_trecut
                else:
                    delta_spo2 = 0

                # Calcul Risc Predictiv
                risc_baza = 0
                if s_actual < 95: risc_baza += 20
                if s_actual < 90: risc_baza += 40
                if p_actual > 110 or p_actual < 50: risc_baza += 20
                if delta_spo2 < -1.5: risc_baza += 40 
                risc_total = min(100, max(0, risc_baza))

                # TIMP RĂMAS PÂNĂ LA COLAPS
                timp_ramas_sec = 9999
                if delta_spo2 < -0.5 and s_actual > 85:
                    timp_ramas_sec = int(abs((s_actual - 85) / (delta_spo2 / 10)))
                elif risc_total >= 80:
                    timp_ramas_sec = 0

                # SENSOR FUSION SIMULAT (Efort vs Traumă)
                context = "Nespecificat"
                if p_actual > 120 and s_actual >= 95:
                    context = "🏃‍♂️ Efort Tactic (Combat Stress)"
                    risc_total = max(0, risc_total - 20) # Reducem riscul fals
                elif p_actual > 120 and s_actual < 92:
                    context = "💥 Traumă / Hemoragie masivă"
                elif s_actual < 95 and p_actual < 100:
                    context = "💨 Inhalare Fum / Problemă Căi Respiratorii"
                else:
                    context = "✅ Poziție Stabilă"

                stari_soldati.append({
                    'id': pid,
                    'puls': p_actual,
                    'spo2': s_actual,
                    'risc': risc_total,
                    'timp_sec': timp_ramas_sec,
                    'context': context,
                    'container': containere_soldati[idx],
                    'timp_exact': rand['Timp_Exact']
                })

            # 2. MOTORUL MASCAL (Prioritizarea Resurselor)
            # Sortăm soldații: primul e cel cu riscul cel mai mare și timpul cel mai scurt
            stari_sortate = sorted(stari_soldati, key=lambda x: (-x['risc'], x['timp_sec']))
            
            cel_mai_critic = stari_sortate[0]
            al_doilea_critic = stari_sortate[1]

            with header_mascal.container():
                if cel_mai_critic['risc'] >= 80:
                    st.error(f"🚨 **PROTOCOL MASCAL ACTIVAT** 🚨 | Drona MEDEVAC-1 a fost direcționată către **Soldatul {cel_mai_critic['id']}**. ETA: 3 min.")
                    if al_doilea_critic['risc'] >= 60:
                        st.warning(f"⚠️ Atenție: **Soldatul {al_doilea_critic['id']}** se deteriorează. Solicitare MEDEVAC-2 în așteptare.")
                else:
                    st.success("✅ Pluton Operațional. Drona MEDEVAC în stand-by la bază.")

            # 3. AFIȘAREA INDIVIDUALĂ A FIECĂRUI SOLDAT
            for soldat in stari_soldati:
                with soldat['container'].container():
                    # Setări vizuale în funcție de risc
                    if soldat['risc'] < 40:
                        culoare_bg = "#1e3d23" # Verde militar închis
                        stadiu = "T3 (VERDE)"
                        edge_ai = "🤫 LINIȘTE RADIO (Monitorizare Edge)"
                    elif soldat['risc'] < 80:
                        culoare_bg = "#8a631c" # Galben/Maro tactic
                        stadiu = "T2 (GALBEN)"
                        edge_ai = "📡 ALERTĂ PRE-CRASH (Transmisie activă)"
                    else:
                        culoare_bg = "#6e1616" # Roșu închis
                        stadiu = "T1 (ROȘU) - CRITIC"
                        edge_ai = "🆘 SOS MEDEVAC (Poziție transmisă)"

                    # Caseta soldatului
                    st.markdown(f"""
                    <div style='background-color: {culoare_bg}; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #555;'>
                        <h3 style='margin: 0; color: white;'>Soldat {soldat['id']} - {stadiu}</h3>
                        <p style='margin: 0; font-size: 14px; color: #aaa;'>⏱️ Timp sistem: {soldat['timp_exact']} | <b>{edge_ai}</b></p>
                        <hr style='margin: 10px 0; border-color: #555;'>
                        <p style='margin: 0; color: white;'><b>Puls:</b> {soldat['puls']:.0f} BPM | <b>SpO2:</b> {soldat['spo2']:.0f}%</p>
                        <p style='margin: 5px 0 0 0; color: #ddd;'><b>Fuziune Senzori:</b> {soldat['context']}</p>
                        <p style='margin: 5px 0 0 0; color: #ffb7b2;'><b>Risc Colaps:</b> {soldat['risc']}%</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            time.sleep(0.4) # Viteza animației
