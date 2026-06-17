import streamlit as st
import pandas as pd
import time

# --- CONFIGURARE INTERFAȚĂ ---
st.set_page_config(page_title="Sistem Triaj NATO DIANA", layout="wide")
st.title("🩺 Sistem Inteligent de Triaj Militar (T1-T4)")
st.markdown("Demonstrator TRL 4 - Monitorizare Multi-Senzor în Dinamică")

# --- ÎNCĂRCAREA DATELOR ---
@st.cache_data
def incarca_date():
    try:
        return pd.read_csv("baza_date_curatata_nato.csv")
    except FileNotFoundError:
        st.error("Nu găsesc fișierul 'baza_date_curatata_nato.csv'.")
        return pd.DataFrame()

df = incarca_date()

if not df.empty:
    # --- ALGORITMUL DE TRIAJ NATO ---
    def evalueaza_triaj(puls, spo2, tensiune):
        # Protecție anti-erori pentru datele lipsă
        t = tensiune if pd.notna(tensiune) else 120
        p = puls if pd.notna(puls) else 80
        s = spo2 if pd.notna(spo2) else 98

        if p < 10 or t < 30:
            return "T4 (NEGRU) - Resurse Redirecționate", "black"
        elif s < 90 or p > 130 or p < 50 or t < 90:
            return "T1 (ROȘU) - Evacuare MEDEVAC Imediată", "red"
        elif s < 95 or p > 100 or t < 100:
            return "T2 (GALBEN) - Intervenție Medicală Necesară", "orange"
        else:
            return "T3 (VERDE) - Pacient Stabil, Monitorizare", "green"

    # --- PANOU DE CONTROL ---
    st.sidebar.header("Misiune Activă")
    lista_pacienti = df['Patient_ID'].unique()
    pacient_selectat = st.sidebar.selectbox("Selectează Militarul:", lista_pacienti)

    date_pacient = df[df['Patient_ID'] == pacient_selectat].copy()
    simuleaza = st.sidebar.button("▶ Simulează Dinamica (Live)")

    # --- AFIȘARE DASHBOARD ---
    placeholder_timp = st.empty()
    placeholder_valori = st.empty()
    placeholder_grafic = st.empty()

    if simuleaza:
        # LISTE PENTRU GRAFIC: Acum urmărim toți cei 4 parametri
        istoric_puls = []
        istoric_spo2 = []
        istoric_tensiune = []
        istoric_respiratie = []
        
        for index, rand in date_pacient.iterrows():
            stadiu_text, culoare = evalueaza_triaj(rand['Puls'], rand['SpO2'], rand['Tensiune'])
            
            # Adăugăm datele noi în liste la fiecare secundă
            istoric_puls.append(rand['Puls'])
            istoric_spo2.append(rand['SpO2'])
            istoric_tensiune.append(rand['Tensiune'])
            istoric_respiratie.append(rand['Respiratie'])

            # Afișare Timp
            cuvant_timp = f"<h3 style='color: gray;'>⏱️ Timp Misiune: {rand['Timp_Exact']}</h3>"
            placeholder_timp.markdown(cuvant_timp, unsafe_allow_html=True)

            # Afișare Valori și Culoare Triaj
            with placeholder_valori.container():
                st.markdown(f"<h1 style='text-align: center; background-color: {culoare}; color: white; border-radius: 10px; padding: 10px;'>{stadiu_text}</h1>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Puls (BPM)", f"{rand['Puls']:.0f}" if pd.notna(rand['Puls']) else "N/A")
                col2.metric("SpO2 (%)", f"{rand['SpO2']:.0f}" if pd.notna(rand['SpO2']) else "N/A")
                col3.metric("Tensiune (mmHg)", f"{rand['Tensiune']:.0f}" if pd.notna(rand['Tensiune']) else "N/A")
                col4.metric("Respirații / min", f"{rand['Respiratie']:.0f}" if pd.notna(rand['Respiratie']) else "N/A")

            # Afișare Grafic cu TOATE cele 4 coloane
            with placeholder_grafic.container():
                grafic_df = pd.DataFrame({
                    'Puls (BPM)': istoric_puls, 
                    'SpO2 (%)': istoric_spo2,
                    'Tensiune (mmHg)': istoric_tensiune,
                    'Respirație (RPM)': istoric_respiratie
                })
                st.line_chart(grafic_df, height=350)
            
            time.sleep(0.3) # Viteza animației
    else:
        # Vizualizare statică înainte de a apăsa Play
        rand_initial = date_pacient.iloc[0]
        stadiu_text, culoare = evalueaza_triaj(rand_initial['Puls'], rand_initial['SpO2'], rand_initial['Tensiune'])
        
        placeholder_timp.markdown(f"<h3 style='color: gray;'>⏱️ Timp Misiune: {rand_initial['Timp_Exact']}</h3>", unsafe_allow_html=True)
        
        with placeholder_valori.container():
            st.markdown(f"<h1 style='text-align: center; background-color: {culoare}; color: white; border-radius: 10px; padding: 10px;'>{stadiu_text}</h1>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Puls (BPM)", f"{rand_initial['Puls']:.0f}" if pd.notna(rand_initial['Puls']) else "N/A")
            col2.metric("SpO2 (%)", f"{rand_initial['SpO2']:.0f}" if pd.notna(rand_initial['SpO2']) else "N/A")
            col3.metric("Tensiune (mmHg)", f"{rand_initial['Tensiune']:.0f}" if pd.notna(rand_initial['Tensiune']) else "N/A")
            col4.metric("Respirații / min", f"{rand_initial['Respiratie']:.0f}" if pd.notna(rand_initial['Respiratie']) else "N/A")
            
        st.info("Apasă pe '▶ Simulează Dinamica (Live)' în meniul din stânga pentru a urmări graficul multi-senzor.")