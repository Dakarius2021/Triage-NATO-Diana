import streamlit as st
import pandas as pd
import time

# --- 1. CONFIGURARE INTERFAȚĂ ---
st.set_page_config(page_title="NATO DIANA - Triage 2.0", layout="wide")
st.title("🚁 P.A.C.E. - Predictive Analytics for Crash-state & Evacuation")
st.markdown("### Demonstrator TRL 4: Inteligență Artificială Predictivă & Auto-Dispatch MEDEVAC")

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
    st.sidebar.header("Misiune Activă: Comandă & Control")
    lista_pacienti = df['Patient_ID'].unique()
    pacient_selectat = st.sidebar.selectbox("Selectează Militarul (Ținta):", lista_pacienti)
    
    # reset_index ne asigură că putem naviga ușor rând cu rând pentru predicție
    date_pacient = df[df['Patient_ID'] == pacient_selectat].reset_index(drop=True)
    simuleaza = st.sidebar.button("▶ Start Simulare AI Predictiv")

    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Inovație NATO:** Sistemul nu așteaptă ca pacientul să intre în șoc. Analizează viteza de degradare și pre-alertează logistica de evacuare.")

    # --- LAYOUT DASHBOARD (2 Coloane) ---
    col_stanga, col_dreapta = st.columns([2, 1]) # Graficul e mai mare (2/3), Alertele în dreapta (1/3)

    metrice_placeholder = col_stanga.empty()
    grafic_placeholder = col_stanga.empty()
    
    predictie_placeholder = col_dreapta.empty()
    medevac_placeholder = col_dreapta.empty()

    if simuleaza:
        istoric_puls = []
        istoric_spo2 = []
        
        # Parcurgem secundă cu secundă
        for i in range(len(date_pacient)):
            rand = date_pacient.iloc[i]
            
            p_actual = rand['Puls'] if pd.notna(rand['Puls']) else 80
            s_actual = rand['SpO2'] if pd.notna(rand['SpO2']) else 98
            
            istoric_puls.append(p_actual)
            istoric_spo2.append(s_actual)
            
            # --- 3. MOTORUL AI PREDICTIV (Calculăm derivata din ultimele 10 secunde) ---
            if i >= 10:
                s_trecut = date_pacient.iloc[i-10]['SpO2']
                p_trecut = date_pacient.iloc[i-10]['Puls']
                
                delta_spo2 = s_actual - s_trecut # Viteza de cădere a oxigenului
                delta_puls = p_actual - p_trecut # Viteza de creștere a pulsului
            else:
                delta_spo2 = 0
                delta_puls = 0

            # Calculăm Scorul de Risc (EWS - Early Warning Score) 0-100%
            risc_baza = 0
            if s_actual < 95: risc_baza += 20
            if s_actual < 90: risc_baza += 40
            if p_actual > 110 or p_actual < 50: risc_baza += 20
            
            # Aici intervine Predictia: adăugăm risc MASIV dacă vedem că scade rapid
            if delta_spo2 < -1.5: risc_baza += 40 
            
            risc_total = min(100, max(0, risc_baza)) # Limităm între 0 și 100

            # Calculăm timpul estimat până la colaps (Intrare în T1) pe baza vitezei de cădere
            timp_ramas = "Stabil"
            if delta_spo2 < -0.5 and s_actual > 85:
                # Formula: Cât oxigen mai are până la 85% împărțit la viteza de scădere
                secunde_pana_la_colaps = int(abs((s_actual - 85) / (delta_spo2 / 10)))
                minute = secunde_pana_la_colaps // 60
                secunde = secunde_pana_la_colaps % 60
                timp_ramas = f"{minute} min {secunde} sec"
            elif risc_total >= 80:
                timp_ramas = "IMINENT (0 min)"

            # --- 4. AFIȘARE VIZUALĂ ÎN TIMP REAL ---
            with metrice_placeholder.container():
                st.markdown(f"<h4 style='color: gray;'>⏱️ Timp Misiune: {rand['Timp_Exact']}</h4>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                # Săgețile vor arăta cu cât a crescut/scăzut în ultimele 10 secunde
                c1.metric("Puls (BPM)", f"{p_actual:.0f}", f"{delta_puls:.1f} (Trend)", delta_color="inverse")
                c2.metric("SpO2 (%)", f"{s_actual:.0f}", f"{delta_spo2:.1f} (Trend)")
                c3.metric("Tensiune (mmHg)", f"{rand['Tensiune']:.0f}" if pd.notna(rand['Tensiune']) else "N/A")

            with grafic_placeholder.container():
                st.line_chart(pd.DataFrame({'SpO2 Real': istoric_spo2, 'Puls Real': istoric_puls}), height=350)

            # Modulul de Predicție a Viitorului
            with predictie_placeholder.container():
                st.subheader("🔮 Analiză Predictivă")
                if risc_total < 40:
                    st.success(f"Probabilitate Colaps (T1): {risc_total}%")
                    st.progress(risc_total / 100)
                    st.info(f"Timp până la degradare T1: {timp_ramas}")
                elif risc_total < 80:
                    st.warning(f"Probabilitate Colaps (T1): {risc_total}%")
                    st.progress(risc_total / 100)
                    st.warning(f"Timp până la degradare T1: {timp_ramas}")
                else:
                    st.error(f"Probabilitate Colaps (T1): {risc_total}% - CRITIC")
                    st.progress(risc_total / 100)
                    st.error(f"Timp până la degradare T1: {timp_ramas}")

            # Modulul Logistic (Auto-MEDEVAC) care va impresiona Juriul
            with medevac_placeholder.container():
                st.subheader("🚁 Auto-Dispatch C4ISR")
                if risc_total >= 80:
                    st.error("🚨 ALERTĂ PRE-CRASH (T1) DECLANȘATĂ!")
                    st.markdown("""
                    **Acțiuni Tactice Automate:**
                    * 📡 Semnal SOS prioritar trimis la Baza Centrală.
                    * 🚁 **Dronă MEDEVAC autonomă activată** (ETA: 4 min).
                    * 🩸 Rezervă sânge O-negativ blocată în inventar.
                    """)
                elif risc_total >= 40:
                    st.warning("⚠️ Risc T2 Detectat. Medic de pluton alertat automat pe stație.")
                    st.markdown("Vehiculele de extracție sunt în stand-by.")
                else:
                    st.success("✅ Pacient stabil. Nicio acțiune logistică necesară.")
            
            time.sleep(0.3) # Viteza de derulare a secundelor
