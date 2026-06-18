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
if 'timp_critic' not in st.session_state:
    st.session_state.timp_critic = {}
if 'last_sec' not in st.session_state:
    st.session_state.last_sec = -1

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
        st.session_state.last_sec = -1
        st.session_state.timp_critic = {pid: 0 for pid in lista_completa} # Resetăm cronometrele la start
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
        * Risc > 80%. Șoc iminent. Necesită confirmare 30s.

        **⬛ T4 (NEGRU) - Decedat (KIA)**
        * Pierderea a cel puțin 3 parametri vitali. Protocol de extragere anulat, resurse realocate.
        
        ---
        **🧠 Inovații (Deep Tech):**
        * **Filtru Anti-Falsificare (30s):** Pentru a evita trimiterea eronată a elicopterelor din cauza unor senzori deplasați, MEDEVAC este activat DOAR dacă starea critică se menține neîntrerupt timp de 30 de secunde.
        * **Edge AI:** Păstrează „Liniștea Radio” când pacientul este stabil.
        * **Sensor Fusion:** Diferențiază efortul fizic de o rană reală. Reconstruiește istoric un senzor căzut.
        * **Protocol TCCC:** Asistență automată de prim ajutor pentru camarazi.
        """)

    # --- 5. FUNCȚII DE INTELIGENȚĂ ARTIFICIALĂ ---
    def evalueaza_soldat(pid, secunda):
        rand = date_toti[pid].iloc[secunda]
        
        def is_zero_or_nan(val):
            return pd.isna(val) or val == 0

        valori_brute = [rand['Puls'], rand['SpO2'], rand['Tensiune'], rand['Respiratie']]
        zeros_count = sum([1 for v in valori_brute if is_zero_or_nan(v)])

        if zeros_count >= 3:
            return {
                'id': pid, 'puls': 0, 'spo2': 0, 'tensiune': 0, 'respiratie': 0,
                'delta_puls': 0, 'delta_spo2': 0, 'risc': 100, 'timp_sec': 0,
                'context': "💀 KIA (Fără semne vitale)", 'timp_exact': rand['Timp_Exact'],
                'is_kia': True
            }

        istoric = date_toti[pid].iloc[:secunda]
        
        def preia_istoric(col, default_val):
            val_curenta = rand[col]
            if is_zero_or_nan(val_curenta):
                valori_bune = istoric[istoric[col] > 0][col]
                if not valori_bune.empty:
                    return valori_bune.iloc[-1]
                return default_val
            return val_curenta

        p_act = preia_istoric('Puls', 80)
        s_act = preia_istoric('SpO2', 98)
        t_act = preia_istoric('Tensiune', 120)
        r_act = preia_istoric('Respiratie', 16)

        d_spo2 = 0
        d_puls = 0
        if secunda >= 10:
            s_trecut = preia_istoric('SpO2', 98)
            p_trecut = preia_istoric('Puls', 80)
            if not is_zero_or_nan(date_toti[pid].iloc[secunda-10]['SpO2']):
                s_trecut = date_toti[pid].iloc[secunda-10]['SpO2']
            if not is_zero_or_nan(date_toti[pid].iloc[secunda-10]['Puls']):
                p_trecut = date_toti[pid].iloc[secunda-10]['Puls']
            
            d_spo2 = s_act - s_trecut
            d_puls = p_act - p_trecut

        risc = 0
        if s_act < 95: risc += 20
        if s_act < 90: risc += 40
        if p_act > 110 or p_act < 50: risc += 20
        if t_act < 90: risc += 40 
        
        if d_spo2 < -1.5: risc += 40 
        risc = min(100, max(0, risc))

        timp_sec = 9999
        if d_spo2 < -0.5 and s_act > 85:
            timp_sec = int(abs((s_act - 85) / (d_spo2 / 10)))
        elif risc >= 80:
            timp_sec = 0

        context = "✅ Stabil"
        if p_act > 120 and s_act >= 94 and t_act >= 100:
            context = "🏃 Efort Tactic"
            risc = max(0, risc - 20)
        elif p_act > 120 and (s_act < 92 or t_act < 90):
            context = "💥 Traumă/Hemoragie"

        return {
            'id': pid, 'puls': p_act, 'spo2': s_act, 'tensiune': t_act, 'respiratie': r_act,
            'delta_puls': d_puls, 'delta_spo2': d_spo2, 'risc': risc, 'timp_sec': timp_sec,
            'context': context, 'timp_exact': rand['Timp_Exact'], 'is_kia': False
        }

    def genereaza_protocol_tccc(soldat):
        if soldat.get('is_kia', False):
            return "💀 **DECES CONSTATAT (T4 - NEGRU).**\n\n* Fără semne vitale.\n* Se suspendă protocolul de resuscitare conform regulilor de triaj tactic MASCAL.\n* Protejați corpul și echipamentul (Echipa Mortuary Affairs)."

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

    # --- 6. PROCESARE BATCH & CRONOMETRU 30 SECUNDE ---
    # Evaluăm toți soldații pentru a menține sincronizarea (indiferent de ecran)
    toti_evaluati = [evalueaza_soldat(pid, timp_curent) for pid in lista_completa]
    
    # Inițializare memorie cronometre la prima rulare
    if not st.session_state.timp_critic:
        st.session_state.timp_critic = {pid: 0 for pid in lista_completa}

    # Actualizăm timpul de "șoc iminent" DOAR când avansează ceasul (evităm actualizări la apăsări de butoane)
    if timp_curent > st.session_state.last_sec:
        for s in toti_evaluati:
            if s['risc'] >= 80 and not s.get('is_kia', False):
                st.session_state.timp_critic[s['id']] += 1
            else:
                st.session_state.timp_critic[s['id']] = 0 # Se resetează dacă pacientul își revine!
        st.session_state.last_sec = timp_curent

    # Atașăm detaliile MEDEVAC direct fiecărui profil de soldat
    for s in toti_evaluati:
        s['secunde_critice'] = st.session_state.timp_critic.get(s['id'], 0)
        s['medevac_trimis'] = s['secunde_critice'] >= 30

    # Sortare: 1. Risc (Mare -> Mic), 2. Timp în stare critică (Mare -> Mic), 3. SpO2 (Mic -> Mare)
    stari_sortate = sorted(toti_evaluati, key=lambda x: (-x['risc'], -x['secunde_critice'], x['spo2']))
    top_5 = stari_sortate[:5]

    # ==========================================
    # ECRAN 1: RADAR DINAMIC (TOP 5)
    # ==========================================
    if st.session_state.mod_vizualizare == 'pluton':
        status_misiune = "🔴 SCANEAZĂ..." if st.session_state.simulare_activa else "⏸ PAUZĂ SCANARE"
        st.markdown(f"<h2>📡 Radar Triaj | Batalion complet (100 Soldați) | {status_misiune}</h2>", unsafe_allow_html=True)
        st.markdown(f"**⏱️ Secunda Misiunii: {timp_curent}** (Viteză: 1 rând/sec)")
        
        # Logica de direcționare MEDEVAC care exclude pacienții KIA
        vii = [s for s in stari_sortate if not s.get('is_kia', False)]
        numar_kia = len([s for s in stari_sortate if s.get('is_kia', False)])
        mesaj_kia = f" | {numar_kia} Decese înregistrate (KIA)" if numar_kia > 0 else ""

        if vii:
            cel_mai_critic_viu = vii[0]
            if cel_mai_critic_viu['risc'] >= 80:
                if cel_mai_critic_viu['medevac_trimis']:
                    st.error(f"🚨 **ALERTĂ MASCAL CONFIRMATĂ:** MEDEVAC alocat automat Soldatului ({cel_mai_critic_viu['id']}).{mesaj_kia}")
                else:
                    sec_ramase = 30 - cel_mai_critic_viu['secunde_critice']
                    st.warning(f"⏳ **VERIFICARE RISC:** Așteptare confirmare T1 pentru Soldat {cel_mai_critic_viu['id']}... Filtru MEDEVAC: {sec_ramase}s.{mesaj_kia}")
            elif cel_mai_critic_viu['risc'] >= 40:
                st.warning(f"⚠️ Batalionul raportează răniți. Triaj T2 în desfășurare.{mesaj_kia}")
            else:
                if numar_kia > 0:
                    st.warning(f"⚠️ Batalion operațional. Pierderi: {numar_kia} KIA.")
                else:
                    st.success("✅ Tot batalionul este operațional.")
        else:
            st.error("⬛ BATALION COMPROMIS. FĂRĂ SUPRAVIEȚUITORI DETECTAȚI.")

        st.markdown("---")
        
        def deseneaza_card(soldat, dimensiune_titlu="h3"):
            if soldat.get('is_kia', False):
                culoare_bg = "#000000"; stadiu = "T4 (NEGRU - KIA)"; edge_ai = "⬛ SENZORI OFFLINE (DECEDAT)"
            elif soldat['risc'] < 40:
                culoare_bg = "#1e3d23"; stadiu = "T3 (VERDE)"; edge_ai = "🤫 LINIȘTE RADIO"
            elif soldat['risc'] < 80:
                culoare_bg = "#8a631c"; stadiu = "T2 (GALBEN)"; edge_ai = "📡 ALERTĂ PRE-CRASH"
            else:
                culoare_bg = "#6e1616"; stadiu = "T1 (ROȘU)"
                if soldat['medevac_trimis']:
                    edge_ai = "🆘 SOS MEDEVAC CONFIRMAT"
                else:
                    edge_ai = f"⏳ VERIFICARE ALARMĂ ({30 - soldat['secunde_critice']}s)"

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

        st.markdown("### 🥇 ȚINTĂ PRIORITARĂ (Cel mai grav caz)")
        deseneaza_card(top_5[0], dimensiune_titlu="h2")
        
        st.markdown("### ⚠️ Restul topului (Următorii 4)")
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        coloane_top4 = [c1, c2, c3, c4]
        
        for idx in range(1, 5):
            if idx < len(top_5):
                with coloane_top4[idx-1]:
                    deseneaza_card(top_5[idx])

    # ==========================================
    # ECRAN 2: VEDEREA DETALIATĂ (ZOOM DIRECT PE GRAFIC)
    # ==========================================
    elif st.session_state.mod_vizualizare == 'detaliu':
        pid = st.session_state.soldat_selectat
        
        # Luăm direct obiectul evaluat ca să păstrăm datele de cronometru calculate mai sus
        soldat = next(s for s in toti_evaluati if s['id'] == pid)
        
        status_misiune = "<span style='color:red;'>🔴 LIVE REC</span>" if st.session_state.simulare_activa else "<span style='color:gray;'>⏸ PAUZĂ</span>"
        
        st.markdown(f"<h2>🔍 Dosar Tactic: {pid} | {status_misiune}</h2>", unsafe_allow_html=True)
        st.markdown(f"**⏱️ Secunda: {timp_curent} | ORA: {soldat['timp_exact']}**")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Puls (BPM)", f"{soldat['puls']:.0f}", f"{soldat['delta_puls']:.1f}" if not soldat.get('is_kia') else "0.0", delta_color="inverse")
        c2.metric("SpO2 (%)", f"{soldat['spo2']:.0f}", f"{soldat['delta_spo2']:.1f}" if not soldat.get('is_kia') else "0.0")
        c3.metric("Tensiune (mmHg)", f"{soldat['tensiune']:.0f}" if pd.notna(soldat['tensiune']) else "N/A")
        c4.metric("Respirație", f"{soldat['respiratie']:.0f}" if pd.notna(soldat['respiratie']) else "N/A")

        st.markdown("### 📊 Monitorizare Multi-Senzor")
        date_istoric = date_toti[pid].iloc[:timp_curent+1].copy()
        
        zero_mask = (date_istoric[['Puls', 'SpO2', 'Tensiune', 'Respiratie']] == 0) | date_istoric[['Puls', 'SpO2', 'Tensiune', 'Respiratie']].isna()
        kia_mask = zero_mask.sum(axis=1) >= 3
        
        for col in ['Puls', 'SpO2', 'Tensiune', 'Respiratie']:
            date_istoric[col] = date_istoric[col].replace(0, pd.NA)
        date_istoric[['Puls', 'SpO2', 'Tensiune', 'Respiratie']] = date_istoric[['Puls', 'SpO2', 'Tensiune', 'Respiratie']].ffill()
        
        date_istoric.loc[kia_mask, ['Puls', 'SpO2', 'Tensiune', 'Respiratie']] = 0

        grafic_df = pd.DataFrame({
            'SpO2 (%)': date_istoric['SpO2'].fillna(98),
            'Puls (BPM)': date_istoric['Puls'].fillna(80),
            'Tensiune (mmHg)': date_istoric['Tensiune'].fillna(120),
            'Respirație (RPM)': date_istoric['Respiratie'].fillna(16)
        })
        st.line_chart(grafic_df, height=450)

        protocol_activ = genereaza_protocol_tccc(soldat)
        
        st.markdown("---")
        if soldat.get('is_kia', False):
            st.error("### ⬛ PROTOCOL ACȚIUNE IMEDIATĂ (TCCC)")
            st.markdown(f"<div style='font-size: 18px; padding: 10px; background-color: #000000; border-radius: 5px; color: white;'>{protocol_activ}</div>", unsafe_allow_html=True)
        elif soldat['risc'] >= 40:
            st.error("### ⚠️ PROTOCOL ACȚIUNE IMEDIATĂ (TCCC)")
            st.markdown(f"<div style='font-size: 18px; padding: 10px; background-color: #521818; border-radius: 5px; color: white;'>{protocol_activ}</div>", unsafe_allow_html=True)
        else:
            st.success("### ✅ PROTOCOL ACȚIUNE (TCCC)")
            st.markdown(f"<div style='font-size: 18px; padding: 10px; background-color: #1e3d23; border-radius: 5px; color: white;'>{protocol_activ}</div>", unsafe_allow_html=True)
        st.markdown("---")

        c_pred, c_med = st.columns(2)
        
        with c_pred:
            st.subheader("🔮 AI Predictiv P.A.C.E.")
            if soldat.get('is_kia', False):
                st.error("Probabilitate Colaps: 100% (DECES)")
                st.progress(1.0)
                st.error("Timp până la șoc: N/A")
            else:
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
            if soldat.get('is_kia', False):
                st.error("⬛ ALERTĂ T4 (NEGRU)!\n* Extracție medicală MEDEVAC anulată.\n* Echipa de recuperare (Mortuary Affairs) a fost notificată.")
            elif soldat['risc'] >= 80:
                if soldat['medevac_trimis']:
                    st.error("🚨 ALERTĂ T1 CONFIRMATĂ!\n* Stare critică stabilă (>30s).\n* Semnal SOS prioritar trimis.\n* Dronă activată.\n* ETA: 3 min.")
                else:
                    sec_ramase = 30 - soldat['secunde_critice']
                    st.warning(f"⏳ ALERTĂ T1 ÎN AȘTEPTARE...\n* Se așteaptă confirmarea riscului (evitare alarmă falsă).\n* Trimitere MEDEVAC în {sec_ramase} secunde.")
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
