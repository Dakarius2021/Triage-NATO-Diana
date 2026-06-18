import streamlit as st
import pandas as pd
import time

# --- 1. CONFIGURARE INTERFAȚĂ ---
st.set_page_config(page_title="NATO DIANA - P.A.C.E. C4ISR", layout="wide")

# --- 2. INIȚIALIZARE MEMORIE (SESSION STATE) ---
# Aici aplicația "ține minte" unde ești și în ce secundă a misiunii te afli
if 'mod_vizualizare' not in st.session_state:
    st.session_state.mod_vizualizare = 'pluton' # Poate fi 'pluton' sau 'detaliu'
if 'soldat_selectat' not in st.session_state:
    st.session_state.soldat_selectat = None
if 'timp_curent' not in st.session_state:
    st.session_state.timp_curent = 0
if 'simulare_activa' not in st.session_state:
    st.session_state.simulare_activa = False

# --- 3. ÎNCĂRCAREA DATELOR ---
@st.cache_data
def incarca_date():
    try:
        return pd.read_csv("baza_date_curatata_nato.csv")
    except FileNotFoundError:
        st.error("Nu găsesc fișierul 'baza_date_curatata_nato.csv'.")
        return pd.DataFrame()

df = incarca_date()

if not df.empty:
    # Selectăm cei 4 soldați (Plutonul Alpha)
    lista_completa = df['Patient_ID'].unique().tolist()
    pacienti_tinta = [p for p in [3000866, 3000063, 3000282, lista_completa[0], lista_completa[1]] if p in lista_completa][:4]
    
    date_pluton = {pid: df[df['Patient_ID'] == pid].reset_index(drop=True) for pid in pacienti_tinta}
    durata_minima = min([len(date_pluton[pid]) for pid in pacienti_tinta])

    # --- 4. PANOU LATERAL (MENIU) ---
    st.sidebar.header("🕹️ Comandă Misiune")
    
    if st.sidebar.button("▶ START MISIUNE", type="primary"):
        st.session_state.simulare_activa = True
        st.session_state.timp_curent = 0 # Resetăm ceasul
        st.rerun() # Reîmprospătăm ecranul instant
        
    if st.sidebar.button("⏸ PAUZĂ MISIUNE"):
        st.session_state.simulare_activa = False
        st.rerun()

    # Dacă suntem în modul "zoom", arătăm butonul de întoarcere
    if st.session_state.mod_vizualizare == 'detaliu':
        st.sidebar.markdown("---")
        if st.sidebar.button("🔙 ÎNAPOI LA PLUTON", type="secondary"):
            st.session_state.mod_vizualizare = 'pluton'
            st.rerun()

    # --- 5. FUNCȚIA DE INTELIGENȚĂ ARTIFICIALĂ (P.A.C.E.) ---
    # Procesează semnele vitale pentru un soldat la secunda X
    def evalueaza_soldat(pid, secunda):
        rand = date_pluton[pid].iloc[secunda]
        p_act = rand['Puls'] if pd.notna(rand['Puls']) else 80
        s_act = rand['SpO2'] if pd.notna(rand['SpO2']) else 98
        t_act = rand['Tensiune'] if pd.notna(rand['Tensiune']) else None
        r_act = rand['Respiratie'] if pd.notna(rand['Respiratie']) else None

        d_spo2 = 0
        d_puls = 0
        if secunda >= 10:
            d_spo2 = s_act - date_pluton[pid].iloc[secunda-10]['SpO2']
            d_puls = p_act - date_pluton[pid].iloc[secunda-10]['Puls']

        risc = 0
        if s_act < 95: risc += 20
        if s_act < 90: risc += 40
        if p_act > 110 or p_act < 50: risc += 20
        if d_spo2 < -1.5: risc += 40 
        risc = min(100, max(0, risc))

        timp_sec = 9999
        if d_spo2 < -0.5 and s_act > 85:
            timp_sec = int(abs((s_act - 85) / (d_spo2 / 10)))
        elif risc >= 80:
            timp_sec = 0

        context = "✅ Stabil"
        if p_act > 120 and s_act >= 95:
            context = "🏃 Efort Tactic"
            risc = max(0, risc - 20)
        elif p_act > 120 and s_act < 92:
            context = "💥 Traumă/Hemoragie"

        return {
            'id': pid, 'puls': p_act, 'spo2': s_act, 'tensiune': t_act, 'respiratie': r_act,
            'delta_puls': d_puls, 'delta_spo2': d_spo2, 'risc': risc, 'timp_sec': timp_sec,
            'context': context, 'timp_exact': rand['Timp_Exact']
        }

    # Asigurăm că nu depășim baza de date
    timp_curent = min(st.session_state.timp_curent, durata_minima - 1)

    # ==========================================
    # ECRAN 1: VEDEREA DE ANSAMBLU (PLUTON)
    # ==========================================
    if st.session_state.mod_vizualizare == 'pluton':
        st.title("🚁 P.A.C.E. - Command & Control (C4ISR)")
        st.markdown("### 🪖 Status Pluton Alpha")

        stari_soldati = [evalueaza_soldat(pid, timp_curent) for pid in pacienti_tinta]
        stari_sortate = sorted(stari_soldati, key=lambda x: (-x['risc'], x['timp_sec']))
        cel_mai_critic = stari_sortate[0]

        if cel_mai_critic['risc'] >= 80:
            st.error(f"🚨 **PROTOCOL MASCAL ACTIVAT** | Drona MEDEVAC direcționată către **Soldatul {cel_mai_critic['id']}**.")
        else:
            st.success("✅ Pluton Operațional. Drona MEDEVAC în stand-by la bază.")

        # Generăm 2 rânduri cu 2 coloane
        rand1 = st.columns(2)
        rand2 = st.columns(2)
        coloane_grid = [rand1[0], rand1[1], rand2[0], rand2[1]]

        for idx, soldat in enumerate(stari_soldati):
            with coloane_grid[idx]:
                if soldat['risc'] < 40:
                    culoare_bg = "#1e3d23"; stadiu = "T3 (VERDE)"
                elif soldat['risc'] < 80:
                    culoare_bg = "#8a631c"; stadiu = "T2 (GALBEN)"
                else:
                    culoare_bg = "#6e1616"; stadiu = "T1 (ROȘU)"

                # Interfața soldatului
                st.markdown(f"""
                <div style='background-color: {culoare_bg}; padding: 15px; border-radius: 10px; border: 1px solid #555;'>
                    <h3 style='margin: 0; color: white;'>Soldat {soldat['id']} - {stadiu}</h3>
                    <p style='margin: 0; color: #aaa;'>⏱️ Timp: {soldat['timp_exact']}</p>
                    <hr style='margin: 10px 0; border-color: #555;'>
                    <p style='color: white;'><b>Puls:</b> {soldat['puls']:.0f} | <b>SpO2:</b> {soldat['spo2']:.0f}%</p>
                    <p style='color: #ffb7b2;'><b>Risc Colaps:</b> {soldat['risc']}% | {soldat['context']}</p>
                </div>
                """, unsafe_allow_html=True)

                # BUTONUL MAGIC: Trece în modul Detaliu
                if st.button(f"🔍 Vezi Detalii Soldat {soldat['id']}", key=f"btn_{soldat['id']}", use_container_width=True):
                    st.session_state.mod_vizualizare = 'detaliu'
                    st.session_state.soldat_selectat = soldat['id']
                    st.rerun()

    # ==========================================
    # ECRAN 2: VEDEREA DETALIATĂ (INDIVIDUALĂ)
    # ==========================================
    elif st.session_state.mod_vizualizare == 'detaliu':
        pid = st.session_state.soldat_selectat
        soldat = evalueaza_soldat(pid, timp_curent)
        
        st.title(f"🔍 Dosar Tactic: Soldatul {pid}")
        st.markdown(f"**Urmărire live pentru semnalul MEDEVAC. Te afli la secunda: {timp_curent} din misiune.**")

        col_stanga, col_dreapta = st.columns([2, 1])

        with col_stanga:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Puls (BPM)", f"{soldat['puls']:.0f}", f"{soldat['delta_puls']:.1f}", delta_color="inverse")
            c2.metric("SpO2 (%)", f"{soldat['spo2']:.0f}", f"{soldat['delta_spo2']:.1f}")
            c3.metric("Tensiune", f"{soldat['tensiune']:.0f}" if pd.notna(soldat['tensiune']) else "N/A")
            c4.metric("Respirație", f"{soldat['respiratie']:.0f}" if pd.notna(soldat['respiratie']) else "N/A")

            # Aici desenăm istoricul PÂNĂ la secunda curentă
            date_istoric = date_pluton[pid].iloc[:timp_curent+1]
            grafic_df = pd.DataFrame({
                'SpO2 (%)': date_istoric['SpO2'].ffill().fillna(98),
                'Puls (BPM)': date_istoric['Puls'].ffill().fillna(80),
                'Tensiune (mmHg)': date_istoric['Tensiune'].ffill().fillna(120),
                'Respirație (RPM)': date_istoric['Respiratie'].ffill().fillna(16)
            })
            st.line_chart(grafic_df, height=350)

        with col_dreapta:
            st.subheader("🔮 Inteligență Artificială")
            risc = soldat['risc']
            timp = "Stabil" if soldat['timp_sec'] == 9999 else ("IMINENT" if soldat['timp_sec'] == 0 else f"{soldat['timp_sec']//60}m {soldat['timp_sec']%60}s")

            if risc < 40:
                st.success(f"Probabilitate Colaps: {risc}%")
                st.progress(risc / 100)
                st.info(f"Timp până la șoc: {timp}")
            elif risc < 80:
                st.warning(f"Probabilitate Colaps: {risc}%")
                st.progress(risc / 100)
                st.warning(f"Timp până la șoc: {timp}")
            else:
                st.error(f"Probabilitate Colaps: {risc}%")
                st.progress(risc / 100)
                st.error(f"Timp până la șoc: {timp}")
            
            st.markdown("---")
            st.subheader("🚁 Extracție Autonomă")
            if risc >= 80:
                st.error("🚨 ALERTĂ T1 DECLANȘATĂ!\n\n* Semnal SOS prioritar trimis.\n* Dronă în tranzit.\n* Sânge O-negativ rezervat.")
            elif risc >= 40:
                st.warning("⚠️ Risc T2 Detectat. Monitorizare sporită.")
            else:
                st.success("✅ Pacient stabil.")

    # ==========================================
    # MOTORUL TIMPULUI (Rulează constant în fundal)
    # ==========================================
    if st.session_state.simulare_activa and timp_curent < durata_minima - 1:
        time.sleep(0.4) # Așteptăm puțin
        st.session_state.timp_curent += 1 # Avansăm timpul cu o secundă
        st.rerun() # Redesenăm interfața automat
    elif st.session_state.simulare_activa and timp_curent >= durata_minima - 1:
        st.success("🏁 Misiune finalizată (Sfârșitul datelor).")
        st.session_state.simulare_activa = False
