import streamlit as st
import pandas as pd
import time

# --- 1. CONFIGURARE INTERFAȚĂ ---
st.set_page_config(page_title="NATO DIANA - Triage Dinamic", layout="wide")

# --- 2. INIȚIALIZARE MEMORIE (SESSION STATE) ---
if 'mod_vizualizare' not in st.session_state:
    st.session_state.mod_vizualizare = 'pluton'
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
    lista_completa = df['Patient_ID'].unique().tolist()
    date_toti = {pid: df[df['Patient_ID'] == pid].reset_index(drop=True) for pid in lista_completa}
    durata_minima = min([len(v) for v in date_toti.values()])

    # --- 4. PANOU LATERAL (MENIU & LEGENDĂ) ---
    st.sidebar.header("🕹️ Comandament Tactic")
    
    if st.sidebar.button("▶ START SCANARE (LIVE)", type="primary"):
        st.session_state.simulare_activa = True
        st.session_state.timp_curent = 0
        st.session_state.mod_vizualizare = 'pluton'
        st.rerun()
        
    if st.sidebar.button("⏸ PAUZĂ"):
        st.session_state.simulare_activa = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 Căutare Manuală")
    index_default = 0
    if st.session_state.soldat_selectat in lista_completa:
        index_default = lista_completa.index(st.session_state.soldat_selectat)
        
    soldat_manual = st.sidebar.selectbox("Caută ID Soldat:", lista_completa, index=index_default)
    
    if st.sidebar.button("Vezi Dosar Selectat"):
        st.session_state.mod_vizualizare = 'detaliu'
        st.session_state.soldat_selectat = soldat_manual
        st.rerun()

    if st.session_state.mod_vizualizare == 'detaliu':
        st.sidebar.markdown("---")
        if st.sidebar.button("🔙 ÎNAPOI LA RADAR", type="secondary"):
            st.session_state.mod_vizualizare = 'pluton'
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info("📡 **Radar Tactic:** Sistemul scanează 100 de soldați simultan.")

    with st.sidebar.expander("📖 LEGENDĂ & GLOSAR TACTIC", expanded=False):
        st.markdown("""
        **🟩 T3 (VERDE) - Operațional**
        * Risc < 40%. Pacient stabil.
        
        **🟨 T2 (GALBEN) - Alertă Tactică**
        * Risc 40-79%. Deteriorare detectată.
        
        **🟥 T1 (ROȘU) - Colaps Critic**
        * Risc > 80%. Șoc iminent. Solicitare MEDEVAC imediată.
        
        ---
        **🧠 Inovații (Deep Tech):**
        * **Edge AI:** Păstrează „Liniștea Radio” când pacientul este stabil.
        * **Sensor Fusion:** Diferențiază efortul fizic de o rană reală.
        * **Protocol TCCC:** Asistență automată de prim ajutor pentru camarazi.
        """)

    # --- 5. FUNCȚII DE INTELIGENȚĂ ARTIFICIALĂ ---
    def evalueaza_soldat(pid, secunda):
        rand = date_toti[pid].iloc[secunda]
        p_act = rand['Puls'] if pd.notna(rand['Puls']) else 80
        s_act = rand['SpO2'] if pd.notna(rand['SpO2']) else 98
        t_act = rand['Tensiune'] if pd.notna(rand['Tensiune']) else 120
        r_act = rand['Respiratie'] if pd.notna(rand['Respiratie']) else 16

        d_spo2 = 0
        d_puls = 0
        if secunda >= 10:
            d_spo2 = s_act - date_toti[pid].iloc[secunda-10]['SpO2']
            d_puls = p_act - date_toti[pid].iloc[secunda-10]['Puls']

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

    # Asistentul Digital TCCC (Ghidaj de Prim Ajutor)
    def genereaza_protocol_tccc(soldat):
        if soldat['risc'] < 40:
            return "✅ **Nicio acțiune medicală necesară.** Soldat combatant."
        
        instructiuni = []
        if soldat['puls'] > 120 and soldat['tensiune'] < 90:
            instructiuni.append("🩸 **RISC HEMORAGIE MASIVĂ!** Caută sursa sângerării. Dacă e pe membre, **APLICĂ GAROU (TOURNIQUET)** sus și strâns!")
        if soldat['spo2'] < 90 and soldat['respiratie'] > 25:
            instructiuni.append("🫁 **INSUFICIENȚĂ RESPIRATORIE!** Verifică toracele pentru plăgi împușcate. Aplică **Chest Seal (Pansament Ocluziv)** dacă e necesar.")
        if soldat['spo2'] < 85 and soldat['respiratie'] < 8:
            instructiuni.append("⚠️ **COLAPS CĂI AERIENE!** Ridică bărbia. Eliberează căile respiratorii. Pregătește suport ventilator.")
        
        if not instructiuni:
            instructiuni.append("🚑 **DETERIORARE FIZIOLOGICĂ.** Monitorizează funcțiile vitale și pregătește trusa de traumă.")
            
        return "\n\n".join(instructiuni)

    timp_curent = min(st.session_state.timp_curent, durata_minima - 1)

    # ==========================================
    # ECRAN 1: RADAR DINAMIC (TOP 5)
    # ==========================================
    if st.session_state.mod_vizualizare == 'pluton':
        status_misiune = "🔴 SCANEAZĂ..." if st.session_state.simulare_activa else "⏸ PAUZĂ SCANARE"
        st.markdown(f"<h2>📡 Radar Triaj | Batalion complet (100 Soldați) | {status_misiune}</h2>", unsafe_allow_html=True)
        st.markdown(f"**⏱️ Secunda Misiunii: {timp_curent}** (Viteză: 1 rând/sec)")

        toti_evaluati = [evalueaza_soldat(pid, timp_curent) for pid in lista_completa]
        stari_sortate = sorted(toti_evaluati, key=lambda x: (-x['risc'], x['spo2']))
        
        top_5 = stari_sortate[:5]
        cel_mai_critic = top_5[0]

        if cel_mai_critic['risc'] >= 80:
            st.error(f"🚨 **ALERTĂ MASCAL:** MEDEVAC alocat automat Țintei Principale (Soldat {cel_mai_critic['id']}).")
        elif cel_mai_critic['risc'] >= 40:
            st.warning("⚠️ Batalionul raportează răniți. Triaj T2 în desfășurare.")
        else:
            st.success("✅ Tot batalionul este operațional.")

        st.markdown("---")
        
        def deseneaza_card(soldat, dimensiune_titlu="h3"):
            if soldat['risc'] < 40:
                culoare_bg = "#1e3d23"; stadiu = "T3 (VERDE)"; edge_ai = "🤫 LINIȘTE RADIO"
            elif soldat['risc'] < 80:
                culoare_bg = "#8a631c"; stadiu = "T2 (GALBEN)"; edge_ai = "📡 ALERTĂ PRE-CRASH"
            else:
                culoare_bg = "#6e1616"; stadiu = "T1 (ROȘU)"; edge_ai = "🆘 SOS MEDEVAC"

            st.markdown(f"""
            <div style='background-color: {culoare_bg}; padding: 15px; border-radius: 10px; border: 1px solid #555; margin-bottom: 10px;'>
                <{dimensiune_titlu} style='margin: 0; color: white;'>Soldat {soldat['id']} - {stadiu}</{dimensiune_titlu}>
                <p style='margin: 0; font-size: 14px; color: #ddd;'><b>{edge_ai}</b></p>
                <hr style='margin: 10px 0; border-color: #555;'>
                <p style='color: white; font-size: 18px;'><b>Puls:</b> {soldat['puls']:.0f} | <b>SpO2:</b> {soldat['spo2']:.0f}%</p>
                <p style='color: #ffb7b2;'><b>Risc Colaps:</b> {soldat['risc']}% | {soldat['context']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🔍 Investighează Soldat {soldat['id']}", key=f"btn_{soldat['id']}", use_container_width=True):
                st.session_state.mod_vizualizare = 'detaliu'
                st.session_state.soldat_selectat = soldat['id']
                st.rerun()

        st.markdown("### 🥇 ȚINTĂ PRIORITARĂ (Cel mai grav rănit)")
        deseneaza_card(top_5[0], dimensiune_titlu="h2")
        
        st.markdown("### ⚠️ Restul topului (Următorii 4)")
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        coloane_top4 = [c1, c2, c3, c4]
        
        for idx in range(1, 5):
            with coloane_top4[idx-1]:
                deseneaza_card(top_5[idx])

    # ==========================================
    # ECRAN 2: VEDEREA DETALIATĂ (ZOOM DIRECT PE GRAFIC)
    # ==========================================
    elif st.session_state.mod_vizualizare == 'detaliu':
        pid = st.session_state.soldat_selectat
        soldat = evalueaza_soldat(pid, timp_curent)
        
        status_misiune = "<span style='color:red;'>🔴 LIVE REC</span>" if st.session_state.simulare_activa else "<span style='color:gray;'>⏸ PAUZĂ</span>"
        
        st.markdown(f"<h2>🔍 Dosar Tactic: {pid} | {status_misiune}</h2>", unsafe_allow_html=True)
        st.markdown(f"**⏱️ Secunda: {timp_curent} | ORA: {soldat['timp_exact']}**")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Puls (BPM)", f"{soldat['puls']:.0f}", f"{soldat['delta_puls']:.1f}", delta_color="inverse")
        c2.metric("SpO2 (%)", f"{soldat['spo2']:.0f}", f"{soldat['delta_spo2']:.1f}")
        c3.metric("Tensiune (mmHg)", f"{soldat['tensiune']:.0f}" if pd.notna(soldat['tensiune']) else "N/A")
        c4.metric("Respirație", f"{soldat['respiratie']:.0f}" if pd.notna(soldat['respiratie']) else "N/A")

        st.markdown("### 📊 Monitorizare Multi-Senzor")
        date_istoric = date_toti[pid].iloc[:timp_curent+1]
        
        grafic_df = pd.DataFrame({
            'SpO2 (%)': date_istoric['SpO2'].ffill().fillna(98),
            'Puls (BPM)': date_istoric['Puls'].ffill().fillna(80),
            'Tensiune (mmHg)': date_istoric['Tensiune'].ffill().fillna(120),
            'Respirație (RPM)': date_istoric['Respiratie'].ffill().fillna(16)
        })
        st.line_chart(grafic_df, height=450)

        # --- NOU: ASISTENTUL TACTIC DE PRIM AJUTOR ---
        protocol_activ = genereaza_protocol_tccc(soldat)
        
        st.markdown("---")
        if soldat['risc'] >= 40:
            st.error("### ⚠️ PROTOCOL ACȚIUNE IMEDIATĂ (TCCC)")
            st.markdown(f"<div style='font-size: 18px; padding: 10px; background-color: #521818; border-radius: 5px; color: white;'>{protocol_activ}</div>", unsafe_allow_html=True)
        else:
            st.success("### ✅ PROTOCOL ACȚIUNE (TCCC)")
            st.markdown(f"<div style='font-size: 18px; padding: 10px; background-color: #1e3d23; border-radius: 5px; color: white;'>{protocol_activ}</div>", unsafe_allow_html=True)
        st.markdown("---")

        c_pred, c_med = st.columns(2)
        
        with c_pred:
            st.subheader("🔮 AI Predictiv P.A.C.E.")
            risc = soldat['risc']
            timp_text = "Stabil" if soldat['timp_sec'] == 9999 else ("IMINENT (0 min)" if soldat['timp_sec'] == 0 else f"{soldat['timp_sec']//60} min {soldat['timp_sec']%60} sec")

            if risc < 40:
                st.success(f"Probabilitate Colaps: {risc}%"); st.progress(risc / 100); st.info(f"Timp până la șoc: {timp_text}")
            elif risc < 80:
                st.warning(f"Probabilitate Colaps: {risc}%"); st.progress(risc / 100); st.warning(f"Timp până la șoc: {timp_text}")
            else:
                st.error(f"Probabilitate Colaps: {risc}%"); st.progress(risc / 100); st.error(f"Timp până la șoc: {timp_text}")
        
        with c_med:
            st.subheader("🚁 Auto-Dispatch MEDEVAC")
            if risc >= 80:
                st.error("🚨 ALERTĂ T1 DECLANȘATĂ!\n* Semnal SOS prioritar trimis.\n* Dronă activată.\n* ETA: 3 min.")
            else:
                st.success("✅ MEDEVAC în Stand-by.")

    # ==========================================
    # MOTORUL TIMPULUI CONTINUU
    # ==========================================
    if st.session_state.simulare_activa and timp_curent < durata_minima - 1:
        time.sleep(1.0) 
        st.session_state.timp_curent += 1 
        st.rerun() 
    elif st.session_state.simulare_activa and timp_curent >= durata_minima - 1:
        st.info("🏁 Misiune finalizată (Batalion retras).")
        st.session_state.simulare_activa = False
