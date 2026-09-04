
import streamlit as st
import os
import re
import json
import math
import random
import hashlib
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()

_VERI_KLASORU      = "seyahat_verileri"
_GECMIS_DOSYASI    = os.path.join(_VERI_KLASORU, "seyahat_gecmisi.json")
_KULLANICI_DOSYASI = os.path.join(_VERI_KLASORU, "kullanicilar.json")
_MBTI_DOSYASI      = os.path.join(_VERI_KLASORU, "mbti_profiller.json")

def _kullanicilari_oku() -> dict:
    """Disk'teki kullanıcı kayıtlarını okur; dosya yoksa boş sözlük döner."""
    if not os.path.exists(_KULLANICI_DOSYASI):
        return {}
    try:
        with open(_KULLANICI_DOSYASI, "r", encoding="utf-8") as f:
            veri = json.load(f)
            return veri if isinstance(veri, dict) else {}
    except Exception:
        return {}

def _kullanicilari_kaydet(kullanicilar: dict) -> None:
    """Kullanıcı sözlüğünü JSON dosyasına yazar."""
    try:
        os.makedirs(_VERI_KLASORU, exist_ok=True)
        with open(_KULLANICI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(kullanicilar, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Kullanıcı kaydetme hatası: {e}")

import binascii as _binascii

def _sifre_hashle(sifre: str) -> str:
    """PBKDF2-SHA256 ile güvenli hash üretir (salt dahil)."""
    salt = os.urandom(32)
    key  = hashlib.pbkdf2_hmac('sha256', sifre.encode('utf-8'), salt, 260_000)
    return "pbkdf2:" + _binascii.hexlify(salt).decode() + ":" + _binascii.hexlify(key).decode()

def _sifre_dogrula(sifre: str, stored: str) -> bool:
    """PBKDF2 ve eski SHA-256 formatlarını doğrular."""
    if stored.startswith("pbkdf2:"):
        parts = stored.split(":")
        if len(parts) != 3:
            return False
        salt = _binascii.unhexlify(parts[1])
        key  = hashlib.pbkdf2_hmac('sha256', sifre.encode('utf-8'), salt, 260_000)
        return _binascii.hexlify(key).decode() == parts[2]
    return hashlib.sha256(sifre.encode('utf-8')).hexdigest() == stored

def _mbti_profil_oku(username: str) -> dict:
    try:
        if not os.path.exists(_MBTI_DOSYASI):
            return {}
        with open(_MBTI_DOSYASI, "r", encoding="utf-8") as f:
            profiller = json.load(f)
            return profiller.get(username, {})
    except Exception:
        return {}

def _mbti_profil_kaydet(username: str, profil: dict) -> None:
    try:
        os.makedirs(_VERI_KLASORU, exist_ok=True)
        profiller = {}
        if os.path.exists(_MBTI_DOSYASI):
            with open(_MBTI_DOSYASI, "r", encoding="utf-8") as f:
                profiller = json.load(f)
        profiller[username] = profil
        with open(_MBTI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(profiller, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"MBTI profil kaydetme hatası: {e}")

def _gecmis_oku() -> list:
    """Disk'teki JSON geçmişini okur; dosya yoksa boş liste döner."""
    if not os.path.exists(_GECMIS_DOSYASI):
        return []
    try:
        with open(_GECMIS_DOSYASI, "r", encoding="utf-8") as f:
            veri = json.load(f)
            return veri if isinstance(veri, list) else []
    except Exception:
        return []

def _gecmis_kaydet(history: list) -> None:
    """Geçmiş listesini JSON dosyasına yazar."""
    try:
        os.makedirs(_VERI_KLASORU, exist_ok=True)
        kayitlar = []
        for item in history:
            if not isinstance(item, dict):
                continue
            kayit = {k: v for k, v in item.items() if k != "transport_details"}
            kayit["transport_details"] = str(item.get("transport_details", ""))[:4000]
            kayitlar.append(kayit)
        with open(_GECMIS_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(kayitlar, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Geçmiş kaydetme hatası: {e}")

def _gecmis_sil_index(history: list, idx: int) -> list:
    """Belirtilen indeksi listeden çıkarır ve diski günceller."""
    yeni = [h for i, h in enumerate(history) if i != idx]
    _gecmis_kaydet(yeni)
    return yeni

try:
    from agents.mbti     import MBTIAgent
    from agents.aco      import ACOAgent
    from agents.ulasım   import UlasimAgent
    from agents.plan     import PlanAgent
    from agents.restoran import RestaurantAgent
    from agents.maliyet  import MaliyetAgent, maliyet_gecmisi_oku
except ImportError as e:
    st.error(f"Eksik modül: {e}")
    st.stop()

st.set_page_config(
    page_title="TRAVEL PLANNER",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={}
)

st.markdown("""
<style>
:root {
  --c-primary:#4f46e5; --c-primary-dark:#4338ca; --c-green:#059669;
  --c-bg:#d6e8f0; --c-white:#ffffff; --c-border:#e5e7eb;
  --c-text:#111827; --c-muted:#6b7280;
  --sp-1:8px; --sp-2:16px; --sp-3:24px; --sp-4:32px;
  --fs-xs:11px; --fs-sm:12px; --fs-base:13px; --fs-md:15px;
  --fs-lg:18px; --fs-xl:22px; --fs-2xl:28px;
  --radius-sm:8px; --radius-md:12px; --radius-lg:16px; --radius-xl:20px;
  --shadow-sm:0 1px 3px rgba(0,0,0,0.08);
  --shadow-md:0 4px 12px rgba(0,0,0,0.10);
  --shadow-lg:0 8px 24px rgba(0,0,0,0.12);
}
@keyframes fadeInUp {
  from { opacity:0; transform:translateY(16px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes fadeIn {
  from { opacity:0; }
  to   { opacity:1; }
}
@keyframes shimmer {
  0%   { background-position:-800px 0; }
  100% { background-position:800px 0; }
}
@keyframes pulse-dot {
  0%,100% { opacity:1; } 50% { opacity:0.4; }
}
.animate-fadein  { animation:fadeIn 0.4s ease both; }
.animate-fadeup  { animation:fadeInUp 0.45s ease both; }
.skeleton {
  background:linear-gradient(90deg,#f0f0f0 25%,#e8e8e8 50%,#f0f0f0 75%);
  background-size:800px 100%;
  animation:shimmer 1.5s infinite;
  border-radius:6px;
}
[data-baseweb="tab-panel"] { animation:fadeIn 0.3s ease; }
.stProgress > div > div {
  background:linear-gradient(90deg,#4f46e5,#7c3aed) !important;
  border-radius:4px; transition:width 0.4s ease;
}
.stSelectbox > div > div:focus-within,
.stDateInput  > div > div:focus-within {
  box-shadow:0 0 0 3px rgba(79,70,229,0.12) !important;
  border-color:#4f46e5 !important;
}
@media (max-width:768px) {
  .block-container { padding:0 !important; }
  [data-baseweb="tab-list"] { overflow-x:auto; flex-wrap:nowrap !important; }
  .stTabs [data-baseweb="tab"] { font-size:11px !important; padding:4px 10px !important; }
}
[data-testid="stAppViewContainer"] {
    background: #d6e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; width: 0 !important; }
.css-1d391kg, .css-uf99v8 { display: none !important; }

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f1f1f1; }
::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 3px; }

.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border: none !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: #4f46e5 !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: #4338ca !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(79,70,229,0.3) !important;
}
.stButton > button[kind="secondary"] {
    background: white !important;
    color: #374151 !important;
    border: 1px solid #e5e7eb !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #f9fafb !important;
    border-color: #4f46e5 !important;
    color: #4f46e5 !important;
}

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
    background: white !important;
    font-size: 13px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.1) !important;
}

.stFormSubmitButton > button {
    background: #4f46e5 !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    width: 100% !important;
}
.stFormSubmitButton > button:hover {
    background: #4338ca !important;
}

[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px !important;
}

.streamlit-expanderHeader {
    background: white !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    color: #374151 !important;
}

.stAlert { border-radius: 10px !important; }

.stRadio > div { gap: 6px; }
.stRadio > div > label {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 8px 12px !important;
    cursor: pointer;
    transition: all 0.1s;
}
.stRadio > div > label:hover { border-color: #4f46e5; }

.stProgress > div > div { background: #4f46e5 !important; border-radius: 4px; }

hr { border-color: #e5e7eb !important; margin: 1rem 0 !important; }

/* ── Nude ton tab stili ── */
.stTabs [data-baseweb="tab-list"] {
    background: #bdd8e8 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #4a6a80 !important;
    border-radius: 7px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 6px 14px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #1a3a4a !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: white;
    border-radius: 0 12px 12px 12px;
    padding: 20px !important;
    margin-top: -2px;
}

/* ── Genel metin rengi ── */
.stMarkdown, .stText { color: #1e3a4a; }
.plan-container { background: white; border-radius: 12px; padding: 4px; }
</style>
""", unsafe_allow_html=True)

_defaults = {
    "logged_in":        False,
    "username":         "",
    "user_data":        {},
    "mbti_completed":   False,
    "mbti_report":      "",
    "mbti_archetype":   "",
    "travel_history":   [],
    "last_plan":        None,
    "last_aco":         None,
    "last_t_data":      None,
    "maliyet_result":       None,
    "last_rest_res":        None,
    "last_rest_schedule":   None,
    "current_tab":          0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.get("_gecmis_yuklendi"):
    disk_gecmis = _gecmis_oku()
    if disk_gecmis:
        st.session_state.travel_history = disk_gecmis
    st.session_state["_gecmis_yuklendi"] = True

params = st.query_params
if "tab" in params:
    try:
        t = int(params["tab"])
        if 0 <= t <= 4:
            st.session_state.current_tab = t
    except Exception:
        pass

def go_tab(idx: int):
    st.session_state.current_tab = idx
    st.query_params["tab"] = str(idx)


if not st.session_state.logged_in:
    st.markdown("""
    <div style="display:flex;justify-content:center;padding:60px 16px 0">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <div style="width:40px;height:40px;border-radius:10px;
                    background:linear-gradient(135deg,#4f46e5,#7c3aed);
                    display:flex;align-items:center;justify-content:center;
                    font-size:20px;box-shadow:0 2px 8px rgba(79,70,229,0.3)">✈️</div>
        <span style="font-size:22px;font-weight:800;color:#111827;letter-spacing:-0.4px">SmartTravel AI</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _login_col = st.columns([1, 1.2, 1])[1]
    with _login_col:
        giris_tab, kayit_tab = st.tabs(["Giriş Yap", "Kayıt Ol"])

        with giris_tab:
            with st.form("giris_form"):
                g_kullanici = st.text_input("Kullanıcı adı", key="g_kullanici")
                g_sifre     = st.text_input("Şifre", type="password", key="g_sifre")
                g_submit    = st.form_submit_button("Giriş Yap")
            if g_submit:
                kullanicilar = _kullanicilari_oku()
                kayit = kullanicilar.get(g_kullanici.strip())
                if kayit and _sifre_dogrula(g_sifre, kayit.get("sifre_hash", "")):
                    # Eski SHA-256 hash'ini otomatik PBKDF2'ye yükselt
                    if not kayit.get("sifre_hash", "").startswith("pbkdf2:"):
                        kullanicilar[g_kullanici.strip()]["sifre_hash"] = _sifre_hashle(g_sifre)
                        _kullanicilari_kaydet(kullanicilar)
                    st.session_state.logged_in = True
                    st.session_state.username  = g_kullanici.strip()
                    profil = _mbti_profil_oku(g_kullanici.strip())
                    if profil:
                        st.session_state.mbti_completed = True
                        st.session_state.mbti_report    = profil.get("description", "")
                        st.session_state.mbti_archetype = profil.get("archetype", "")
                        st.session_state.user_data      = st.session_state.get("user_data", {})
                        st.session_state.user_data["mbti_type"] = profil.get("mbti_type", "")
                        st.session_state.current_tab = 1  # profil varsa direkt Kimlik Profili sekmesi
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı.")

        with kayit_tab:
            with st.form("kayit_form"):
                k_kullanici = st.text_input("Kullanıcı adı", key="k_kullanici")
                k_sifre     = st.text_input("Şifre", type="password", key="k_sifre")
                k_sifre2    = st.text_input("Şifre (tekrar)", type="password", key="k_sifre2")
                k_submit    = st.form_submit_button("Kayıt Ol")
            if k_submit:
                k_kullanici_temiz = k_kullanici.strip()
                if not k_kullanici_temiz or not k_sifre:
                    st.error("Kullanıcı adı ve şifre boş olamaz.")
                elif k_sifre != k_sifre2:
                    st.error("Şifreler eşleşmiyor.")
                else:
                    kullanicilar = _kullanicilari_oku()
                    if k_kullanici_temiz in kullanicilar:
                        st.error("Bu kullanıcı adı zaten kayıtlı.")
                    else:
                        kullanicilar[k_kullanici_temiz] = {"sifre_hash": _sifre_hashle(k_sifre)}
                        _kullanicilari_kaydet(kullanicilar)
                        st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
    st.stop()


@st.cache_data(show_spinner=False, ttl=86400)
def _wiki_landmark_urls(sehir: str) -> list:
    try:
        import requests as _rq
        api  = "https://en.wikipedia.org/w/api.php"
        hdrs = {"User-Agent": "SmartTravelAI/1.0 (educational; ilaydanudak@icloud.com)"}
        key  = sehir.lower().replace("ı","i").replace("ş","s").replace("ğ","g").replace("ü","u").replace("ö","o").replace("ç","c")
        _landmark_db = {
            "istanbul":  ["Hagia Sophia","Topkapi Palace","Bosphorus","Grand Bazaar, Istanbul","Galata Tower","Blue Mosque","Dolmabahce Palace","Basilica Cistern"],
            "ankara":    ["Anıtkabir","Ankara Castle","Museum of Anatolian Civilizations","Kocatepe Mosque","Atatürk Forest Farm"],
            "izmir":     ["Ephesus","Kadifekale","Kordon, İzmir","Asansör, İzmir","Agora of Smyrna","Çeşme"],
            "antalya":   ["Perge","Aspendos","Kaleiçi","Düden Waterfalls","Hadrian's Gate"],
            "roma":      ["Colosseum","Trevi Fountain","Pantheon, Rome","Roman Forum","Vatican Museums","Piazza Navona","Spanish Steps","Castel Sant'Angelo"],
            "paris":     ["Eiffel Tower","Louvre Museum","Notre-Dame de Paris","Sacré-Cœur, Paris","Palace of Versailles","Musée d'Orsay","Arc de Triomphe","Seine"],
            "barcelona": ["Sagrada Família","Park Güell","La Rambla","Camp Nou","Gothic Quarter, Barcelona","Casa Batlló","Barceloneta Beach","Palau de la Música Catalana"],
            "amsterdam": ["Rijksmuseum","Anne Frank House","Van Gogh Museum","Vondelpark","Keukenhof","Heineken Experience","A'DAM Tower"],
            "prag":      ["Prague Castle","Charles Bridge","Old Town Square, Prague","Prague Astronomical Clock","Wenceslas Square","Petřín","Josefov"],
            "viyana":    ["Schönbrunn Palace","St. Stephen's Cathedral, Vienna","Belvedere, Vienna","Vienna State Opera","Hofburg","Prater","Kunsthistorisches Museum"],
            "londra":    ["Tower of London","Buckingham Palace","Big Ben","Tower Bridge","British Museum","Tate Modern","Hyde Park","Westminster Abbey"],
            "dubai":     ["Burj Khalifa","Palm Jumeirah","Dubai Mall","Dubai Frame","Burj Al Arab","Dubai Creek","Gold Souk, Dubai","Dubai Museum"],
            "tokyo":     ["Tokyo Tower","Senso-ji","Shibuya crossing","Shinjuku Gyoen","Tokyo Skytree","Meiji Shrine","Akihabara","teamLab Borderless"],
            "bangkok":   ["Grand Palace, Bangkok","Wat Pho","Wat Arun","Chatuchak Weekend Market","Khao San Road","Lumphini Park","Jim Thompson House"],
            "atina":     ["Acropolis of Athens","Parthenon","National Archaeological Museum, Athens","Plaka","Temple of Hephaestus","Monastiraki","Panathenaic Stadium"],
            "budapeste": ["Hungarian Parliament Building","Buda Castle","Chain Bridge, Budapest","Fisherman's Bastion","Széchenyi thermal bath","Matthias Church","Heroes' Square"],
            "tiflis":    ["Narikala","Tbilisi Old Town","Bridge of Peace, Tbilisi","Metekhi Church","Mtatsminda","Anchiskhati Basilica"],
            "new york":  ["Statue of Liberty","Empire State Building","Central Park","Times Square","Brooklyn Bridge","Metropolitan Museum of Art","High Line","One World Trade Center"],
            "singapur":  ["Marina Bay Sands","Gardens by the Bay","Merlion","Sentosa Island","Chinatown, Singapore","Clarke Quay","Singapore Botanic Gardens"],
            "marakes":   ["Jemaa el-Fna","Koutoubia","Bahia Palace","Medina of Marrakesh","Majorelle Garden","Saadian Tombs","Mouassine Fountain"],
        }
        titles = _landmark_db.get(key)
        urls = []
        seen = set()

        if titles:
            r = _rq.get(api, params={
                "action":"query","titles":"|".join(titles[:8]),
                "prop":"pageimages","pithumbsize":1200,"format":"json"
            }, headers=hdrs, timeout=7)
            title_map = {}
            for pg in r.json().get("query",{}).get("pages",{}).values():
                t = pg.get("thumbnail",{}).get("source","")
                if t:
                    title_map[pg.get("title","")] = t
            for ti in titles[:8]:
                u = title_map.get(ti,"")
                if u and u not in seen:
                    seen.add(u)
                    urls.append(u)

        if len(urls) < 6:
            for q in [sehir, f"{sehir} landmark", f"{sehir} skyline", f"{sehir} architecture"]:
                sr = _rq.get(api, params={
                    "action":"query","generator":"search",
                    "gsrsearch":q,"gsrlimit":8,
                    "prop":"pageimages","pithumbsize":1200,"format":"json"
                }, headers=hdrs, timeout=6)
                for pg in sr.json().get("query",{}).get("pages",{}).values():
                    t = pg.get("thumbnail",{}).get("source","")
                    if t and t not in seen:
                        seen.add(t)
                        urls.append(t)
                if len(urls) >= 6:
                    break

        return urls[:6]
    except Exception:
        return []

cur = st.session_state.current_tab

NAV_ITEMS = [
    ("Kimlik Testi",    True),
    ("Kimlik Profili",  st.session_state.mbti_completed),
    ("Rota Formu",      True),
    ("Plan Sonucu",     st.session_state.last_plan is not None),
    ("ACO & Maliyet",   st.session_state.last_aco is not None or st.session_state.maliyet_result is not None),
    ("Seyahat Geçmişi", True),
]

topbar_items = ""
for i, (label, done) in enumerate(NAV_ITEMS):
    if i == cur:
        span_style = ("background:#4f46e5;color:white;border-radius:20px;"
                      "font-weight:700;padding:5px 14px;font-size:12px;display:inline-block;")
    elif done:
        span_style = "color:#059669;font-weight:600;font-size:12px;padding:5px 14px;display:inline-block;"
    else:
        span_style = "color:#9ca3af;font-size:12px;padding:5px 14px;display:inline-block;"
    check = " ✓" if done and i != cur else ""
    topbar_items += (
        f'<a href="?tab={i}" target="_self" style="text-decoration:none;">'
        f'<span style="{span_style}">{label}{check}</span></a>'
    )

st.markdown(f"""
<div style="background:white;border-bottom:1px solid #e5e7eb;
            padding:0 32px;display:flex;align-items:center;
            justify-content:space-between;position:sticky;top:0;z-index:999;
            box-shadow:0 2px 8px rgba(0,0,0,0.06);height:56px">
  <div style="display:flex;align-items:center;gap:10px">
    <div style="width:32px;height:32px;border-radius:10px;
                background:linear-gradient(135deg,#4f46e5,#7c3aed);
                display:flex;align-items:center;justify-content:center;
                font-size:16px;box-shadow:0 2px 8px rgba(79,70,229,0.3);flex-shrink:0">✈️</div>
    <div style="display:flex;align-items:baseline;gap:0">
      <span style="font-size:15px;font-weight:800;color:#111827;letter-spacing:-0.4px">SmartTravel</span>
      <span style="font-size:15px;font-weight:800;color:#4f46e5;letter-spacing:-0.4px"> AI</span>
    </div>
    <span style="font-size:10px;color:#4f46e5;background:#ede9fe;
                 padding:2px 7px;border-radius:999px;font-weight:700;letter-spacing:0.3px">BETA</span>
  </div>
  <div style="display:flex;align-items:center;gap:2px">
    {topbar_items}
  </div>
</div>
""", unsafe_allow_html=True)

_topbar_user_col = st.columns([6, 1])[1]
with _topbar_user_col:
    _u1, _u2 = st.columns([2, 1])
    with _u1:
        st.caption(f"👤 {st.session_state.username}")
    with _u2:
        if st.button("Çıkış", key="_cikis_btn"):
            st.session_state.logged_in = False
            st.session_state.username  = ""
            st.rerun()

def page_header(title, subtitle=""):
    sub = f'<p style="color:#6b7280;font-size:14px;margin:4px 0 0">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="padding:28px 32px 0">
      <h1 style="font-size:22px;font-weight:700;color:#111827;margin:0">{title}</h1>
      {sub}
    </div>
    """, unsafe_allow_html=True)

def card(content_html, padding="20px"):
    st.markdown(f"""
    <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;
                padding:{padding};margin-bottom:12px">
      {content_html}
    </div>
    """, unsafe_allow_html=True)

def badge(text, color="#4f46e5"):
    return (f'<span style="background:{color}18;color:{color};font-size:11px;'
            f'font-weight:600;padding:2px 8px;border-radius:999px">{text}</span>')

def step_indicator(steps, current):
    items = ""
    for i, (label, done) in enumerate(steps):
        if done:
            dot = f'<div style="width:24px;height:24px;border-radius:50%;background:#059669;color:white;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700">✓</div>'
            txt_color = "#059669"
        elif i == current:
            dot = f'<div style="width:24px;height:24px;border-radius:50%;background:#4f46e5;color:white;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700">{i+1}</div>'
            txt_color = "#4f46e5"
        else:
            dot = f'<div style="width:24px;height:24px;border-radius:50%;background:#f3f4f6;color:#9ca3af;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600">{i+1}</div>'
            txt_color = "#9ca3af"
        line = '<div style="flex:1;height:1px;background:#e5e7eb;margin:0 6px"></div>' if i < len(steps)-1 else ""
        items += f'<div style="display:flex;align-items:center">{dot}<span style="font-size:11px;color:{txt_color};font-weight:500;margin-left:6px;white-space:nowrap">{label}</span></div>{line}'
    st.markdown(f'<div style="display:flex;align-items:center;padding:16px 32px;background:white;border-bottom:1px solid #f3f4f6">{items}</div>', unsafe_allow_html=True)

def nav_arrows(ileri_label, ileri_idx, geri_label=None, geri_idx=None):
    st.markdown("""
    <style>
    .nav-arrow-btn > button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #4f46e5 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 6px 0 !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 2px !important;
        min-height: unset !important;
    }
    .nav-arrow-btn > button:hover {
        color: #4338ca !important;
        background: transparent !important;
        transform: none !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="border-top:1px solid #f3f4f6;margin-top:32px;'
        'padding:16px 32px;display:flex;justify-content:space-between;align-items:center">',
        unsafe_allow_html=True
    )

    left_col, spacer, right_col = st.columns([2, 6, 2])

    with left_col:
        if geri_label and geri_idx is not None:
            st.markdown(
                f'<div style="display:flex;flex-direction:column;align-items:flex-start;gap:2px">'
                f'<span style="font-size:18px;color:#9ca3af;line-height:1">←</span>'
                f'<span style="font-size:11px;color:#6b7280">{geri_label}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown('<div class="nav-arrow-btn" style="margin-top:-52px">', unsafe_allow_html=True)
            if st.button("←  " + geri_label, key=f"geri_{geri_idx}_{ileri_idx}", use_container_width=False):
                go_tab(geri_idx)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown(
            f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px">'
            f'<span style="font-size:11px;color:#6b7280;text-align:right">{ileri_label}</span>'
            f'<span style="font-size:18px;color:#4f46e5;line-height:1;text-align:right">→</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown('<div class="nav-arrow-btn" style="margin-top:-52px;text-align:right">', unsafe_allow_html=True)
        if st.button(ileri_label + "  →", key=f"ileri_{ileri_idx}_{geri_idx}", use_container_width=False):
            go_tab(ileri_idx)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def aco_optimized_route(aco_res: dict) -> list:
    """
    ACO ajanı 'optimized_route' veya 'locations' veya başka bir anahtar
    döndürebilir. Her durumda liste döndürür; boş liste asla hata vermez.
    """
    if not aco_res:
        return []
    route = aco_res.get("optimized_route")
    if route and isinstance(route, list):
        return route
    locs = aco_res.get("locations")
    if locs and isinstance(locs, list):
        return locs
    for v in aco_res.values():
        if isinstance(v, list) and v:
            return v
    return []


if cur == 0:
    step_indicator(NAV_ITEMS, 0)

    if st.session_state.mbti_completed:
        mbti = st.session_state.user_data.get("mbti_type", "")
        arch = st.session_state.mbti_archetype
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#ede9fe,#f0fdf4);
                    border:1px solid #c4b5fd;border-radius:14px;
                    padding:18px 24px;margin:16px 32px 8px;
                    display:flex;align-items:center;gap:16px">
          <div style="font-size:28px">🧬</div>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:800;color:#4f46e5;margin-bottom:4px">
              {arch} · {mbti}</div>
            <div style="font-size:12px;color:#6b7280;line-height:1.6">
              Kişilik profiliniz oluşturuldu. Detaylı analizi ve destinasyon önerilerini görmek için
              <strong>Kimlik Profili</strong> sekmesine tıklayın.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        _c1p, _c2p = st.columns([2, 1])
        with _c1p:
            if st.button("🧬 Kimlik Profilimi Gör", key="go_profil_tab", type="primary",
                         use_container_width=True):
                go_tab(1); st.rerun()
        with _c2p:
            if st.button("Yeniden Çöz", key="redo_from_test_tab", use_container_width=True):
                st.session_state.mbti_completed = False
                st.rerun()
        st.stop()

        # --- TAB 1'E TAŞINDI: aşağıdaki kod artık Kimlik Profili sekmesinde çalışır ---
        MBTI_SEYAHAT = {
            "INTJ": {"tercih": "Derin planlama, tarihi alanlar, soliter kültür turları", "kac": "Kalabalık gruplar, spontane değişiklikler, gövde gösterisi turları", "ideal": "Japonya çay seremonisi, Roma müzeleri, Edinburgh kalesi", "renk": "#6d28d9"},
            "INTP": {"tercih": "Bilim müzesi, arkeoloji, sessiz doğal alanlar, kütüphaneler", "kac": "Plaj partileri, yüksek sesli mekanlar, kalabalık alışveriş", "ideal": "Atina Akropolü, Krakow tarihi merkez, İzlanda fiyortları", "renk": "#7c3aed"},
            "ENTJ": {"tercih": "Verimli rota, business sınıf, lüks otel, liderlik turları", "kac": "Organizasyonsuz geziler, hostel, uzun bekleme", "ideal": "Singapur, Zürih, Tokyo iş merkezi", "renk": "#4338ca"},
            "ENTP": {"tercih": "Yeni fikirler, tartışma kafeleri, startup sahnesi, farklı kültürler", "kac": "Rutin turist rotaları, tur rehberi, kısıtlayıcı programlar", "ideal": "Berlin sanat sahnesi, İstanbul agorası, Amsterdam", "renk": "#2563eb"},
            "INFJ": {"tercih": "Anlamlı deneyimler, yerel halk ile tanışma, manevi mekanlar", "kac": "Yüzeysel turist noktaları, kalabalık, gürültü", "ideal": "Hindistan ashram, Kyoto tapınakları, Fas medina", "renk": "#0891b2"},
            "INFP": {"tercih": "Romantik şehirler, edebiyat turları, doğal ortamlar, sanat", "kac": "Kalabalık turistik mekanlar, zaman baskısı, katı program", "ideal": "Edinburgh, Prag, Yeni Zelanda doğası", "renk": "#0d9488"},
            "ENFJ": {"tercih": "Kültür takası, topluluk deneyimleri, rehberli turlar, insanlarla bağlanma", "kac": "Yalnız uzlet, kuvvetli tur programı, doğal afetler", "ideal": "Brezilya karnavalı, Hindistan kültür turları, Gana", "renk": "#059669"},
            "ENFP": {"tercih": "Spontane keşifler, festival, yerel pazar, yeni insanlar", "kac": "Katı programlar, standart otel, tekrar eden rotalar", "ideal": "Tayland festivalleri, Marakeş meydanı, Barselona", "renk": "#65a30d"},
            "ISTJ": {"tercih": "Planlı ve organize, tarihi mekanlar, müzeler, güvenilir ulaşım", "kac": "Son dakika değişiklikler, belirsizlik, hostel kaos", "ideal": "Viyana, Londra müze turu, Japonya trenleri", "renk": "#ca8a04"},
            "ISFJ": {"tercih": "Güvenli, rahat, aile dostu mekanlar, geleneksel yemekler", "kac": "Riskli maceralar, bilinmezlik, kalabalık gece hayatı", "ideal": "Provence Fransa, Toskana köyü, Yeni Zelanda", "renk": "#d97706"},
            "ESTJ": {"tercih": "Verimli program, lüks otel, organize turlar, önem verilen mekanlar", "kac": "Kaos ve plansızlık, kirli mekanlar, zaman kaybı", "ideal": "Viyana opera, Londra iş merkezi, Singapur", "renk": "#dc2626"},
            "ESFJ": {"tercih": "Aile tatilleri, sosyal aktiviteler, hoş restoranlar, fotoğraflık noktalar", "kac": "Yalnızlık, sert koşullar, soğuk mekanlar", "ideal": "Paris romantik turu, Bali tatil köyü, Santorini", "renk": "#e11d48"},
            "ISTP": {"tercih": "Macera sporları, mekanik teknik turlar, dağ, doğa kampı", "kac": "Kalabalık şehir merkezleri, organize turlar, sosyal zorunluluk", "ideal": "Norveç dağ trekkingi, Moğolistan step, Patagonya", "renk": "#0284c7"},
            "ISFP": {"tercih": "Sanat galerileri, doğada yürüyüş, yerel el sanatları, sessiz kafeler", "kac": "Soğuk konferans tarzı turlar, kalabalık alışveriş merkezleri", "ideal": "Floransa sanat turu, Bali Ubud, Oaxaca Meksika", "renk": "#7c3aed"},
            "ESTP": {"tercih": "Aksiyon sporları, gece hayatı, hızlı şehir keşifleri, macera parkları", "kac": "Müze saatleri, yavaş tempolu turlar, kültürel zorunluluklar", "ideal": "Dubai, Las Vegas, Bangkok gece hayatı", "renk": "#ea580c"},
            "ESFP": {"tercih": "Festival, plaj, sosyal etkinlikler, dans, canlı müzik", "kac": "Sakin ve izole mekanlar, uzun müze turları, yalnız gezi", "ideal": "Rio karnavalı, İbiza, Bali festivalleri", "renk": "#db2777"},
        }
        profil_detay = MBTI_SEYAHAT.get(mbti, {
            "tercih": "Kişisel keşifler ve özgün deneyimler",
            "kac": "Standart turist rotaları",
            "ideal": "Size özel destinasyonlar",
            "renk": "#4f46e5"
        })

        _renk = profil_detay["renk"]

        _dim_labels = [
            ("E","I","Dışavurumcu","İçedönük"),
            ("N","S","Sezgisel","Gözlemci"),
            ("T","F","Mantıksal","Duygusal"),
            ("J","P","Planlayıcı","Esnek"),
        ]
        _dim_vals = []
        for _di, (_a, _b, _la, _lb) in enumerate(_dim_labels):
            _letter = mbti[_di] if _di < len(mbti) else _a
            _is_a   = (_letter == _a)
            _dim_vals.append((_is_a, _la if _is_a else _lb))

        _MBTI_BLOG_P = {
            "INTJ":"INTJ'ler seyahat ederken her ayrıntıyı önceden planlar. Antik kentleri, felsefi müzeleri ve sessiz doğa rotalarını tercih ederler.",
            "INTP":"INTP'ler seyahati çözülmesi gereken bir bilim projesi gibi görürler. Arkeolojik alanlar ve kütüphaneler onları büyüler.",
            "ENTJ":"ENTJ'ler tatilde bile verimlilik ararlar. Prestijli destinasyonları ve lüks otelleri seçerler.",
            "ENTP":"ENTP'ler rutin rotaları reddeden vizyon avcılarıdır. Startup sahnesi ve alternatif galeriler tam onlara göredir.",
            "INFJ":"INFJ'ler için seyahat içsel bir yolculuktur. Yerel halkla tanışabilecekleri otantik mekanları severler.",
            "INFP":"INFP'ler her şehirde bir masalın izini sürer. Tarihi kafeler, eski kitapçılar ve bohem mahalleler onlar için cennettir.",
            "ENFJ":"ENFJ'ler her destinasyonda insanları bir araya getiren rehberlerdir. Kültür takasına dayalı festivaller onları besler.",
            "ENFP":"ENFP'ler için seyahat tüm planları yırtıp spontane hareket etmek demektir. Renkli pazarlar ve festivaller tam onlara göredir.",
            "ISTJ":"ISTJ'ler için mükemmel seyahat milimetrik düzen ve önceden test edilmiş bir programa bağlıdır.",
            "ISFJ":"ISFJ'ler güvenli, sıcak ve aile dostu ortamlar ararlar. Nostaljik kasabaları ve el sanatları pazarlarını severler.",
            "ESTJ":"ESTJ'ler seyahatin her anında tam kontrol sağlamak isteyen organizatörlerdir.",
            "ESFJ":"ESFJ'ler seyahati sosyal paylaşım ve kolektif eğlence aracı olarak görürler.",
            "ISTP":"ISTP'ler fiziksel aksiyonu ve doğanın zorluklarıyla mücadeleyi seven kaşiflerdir.",
            "ISFP":"ISFP'ler dünyayı gözleri ve kalpleriyle hisseden estetik duyarlılığı yüksek sanatçı gezginlerdir.",
            "ESTP":"ESTP'ler için durağan bir tatil kabustur. Adrenalin sporları ve gece hayatı onların kan grubudur.",
            "ESFP":"ESFP'ler ayak bastıkları her destinasyonu eğlence sahnesine dönüştüren hayat dolu turistlerdir.",
        }
        _blog_txt = _MBTI_BLOG_P.get(mbti, "Seyahat tarzınız tamamen kendinize özgü.")

        _trait_map_p = {
            "INTJ":["Stratejik","Bağımsız","Analitik","Kararlı","Öngörülü"],
            "INTP":["Meraklı","Nesnel","Yenilikçi","Analitik","Sessiz"],
            "ENTJ":["Lider","Verimli","Güçlü","Stratejik","Kararlı"],
            "ENTP":["Yaratıcı","Tartışmacı","Vizyoner","Hızlı","Esnek"],
            "INFJ":["Empatik","Anlayışlı","İçgörülü","İdealci","Sakin"],
            "INFP":["Romantik","Yaratıcı","Özgün","Duyarlı","Hayalperest"],
            "ENFJ":["Karizmatik","İlham Veren","Empatik","Sosyal","Yardımsever"],
            "ENFP":["Enerjik","Özgür","Coşkulu","Meraklı","Spontane"],
            "ISTJ":["Güvenilir","Düzenli","Sorumlu","Kararlı","Pratik"],
            "ISFJ":["Sıcak","Koruyucu","Sadık","Sabırlı","Özenli"],
            "ESTJ":["Organizatör","Güçlü","Net","Sorumlu","Verimli"],
            "ESFJ":["Sosyal","Sevgi Dolu","Fedakâr","Uyumlu","Cana Yakın"],
            "ISTP":["Pratik","Mekanik","Cesur","Sessiz","Bağımsız"],
            "ISFP":["Sanatçı","Hassas","Uysal","Anlık","Estetik"],
            "ESTP":["Maceracı","Hızlı","Pratik","Sosyal","Cesur"],
            "ESFP":["Neşeli","Spontane","Eğlenceli","Sosyal","Coşkulu"],
        }
        _traits_p = _trait_map_p.get(mbti, ["Özgün","Keşifçi","Meraklı","Bağımsız","Esnek"])

        _trait_chips_dark = "".join(
            f'<span style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.18);'
            f'border-radius:99px;padding:4px 12px;font-size:11px;font-weight:600;'
            f'color:rgba(255,255,255,0.88);display:inline-block;margin:3px 2px">{t}</span>'
            for t in _traits_p
        )

        def _dim_bar_p(letter_a, letter_b, label_a, label_b, is_a):
            _fill = 72 if is_a else 28
            return f"""
<div style="margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
    <span style="font-size:11px;font-weight:{'800' if is_a else '500'};
                 color:{'#111827' if is_a else '#9ca3af'}">{label_a} ({letter_a})</span>
    <span style="font-size:11px;font-weight:{'800' if not is_a else '500'};
                 color:{'#111827' if not is_a else '#9ca3af'}">{label_b} ({letter_b})</span>
  </div>
  <div style="background:#f3f4f6;border-radius:99px;height:7px;overflow:hidden">
    <div style="height:100%;width:{_fill}%;background:linear-gradient(90deg,{_renk},{_renk}99);
                border-radius:99px;{'margin-left:auto' if not is_a else ''}"></div>
  </div>
</div>"""

        _boyut_html = "".join(
            _dim_bar_p(_dim_labels[i][0], _dim_labels[i][1],
                       _dim_labels[i][2], _dim_labels[i][3],
                       _dim_vals[i][0])
            for i in range(4)
        )

        st.markdown(f"""
<div style="padding:20px 32px 0">
  <!-- Hero Banner -->
  <div style="background:linear-gradient(135deg,#1e1b4b 0%,#3730a3 50%,#4f46e5 100%);
              border-radius:20px;padding:32px 36px;margin-bottom:16px;
              position:relative;overflow:hidden">
    <div style="position:absolute;right:-40px;top:-40px;width:220px;height:220px;
                border-radius:50%;background:rgba(255,255,255,0.04)"></div>
    <div style="position:absolute;right:50px;bottom:-70px;width:160px;height:160px;
                border-radius:50%;background:{_renk}22"></div>
    <div style="position:relative;display:flex;align-items:flex-start;gap:36px;flex-wrap:wrap">
      <div style="min-width:140px">
        <div style="font-size:10px;font-weight:700;letter-spacing:2.5px;
                    color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:8px">
          Gezgin Tipin</div>
        <div style="font-size:72px;font-weight:900;letter-spacing:-5px;line-height:0.9;
                    color:white">{mbti}</div>
        <div style="margin-top:14px;display:inline-block;background:{_renk}44;
                    border:1px solid {_renk}88;border-radius:8px;
                    padding:5px 14px;font-size:13px;font-weight:700;color:white;
                    letter-spacing:0.3px">{arch}</div>
      </div>
      <div style="flex:1;min-width:200px;padding-top:4px">
        <div style="font-size:10px;font-weight:700;color:rgba(255,255,255,0.38);
                    letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px">
          Kişilik Özelliklerin</div>
        <div style="line-height:1.4">{_trait_chips_dark}</div>
        <div style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.08);
                    font-size:11.5px;color:rgba(255,255,255,0.45);display:flex;align-items:center;gap:8px">
          <span style="width:6px;height:6px;border-radius:50%;background:#9eaa8f;
                       display:inline-block;flex-shrink:0"></span>
          Rota, restoran ve maliyet ajanları bu profile göre çalışıyor
        </div>
      </div>
    </div>
  </div>

  <!-- Boyutlar + Blog -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px">
    <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;padding:20px 22px">
      <div style="font-size:10px;font-weight:700;color:#6b7280;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:14px">Kişilik Boyutları</div>
      {_boyut_html}
    </div>
    <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;padding:20px 22px">
      <div style="font-size:10px;font-weight:700;color:#6b7280;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:10px">Seyahat Tarzın</div>
      <div style="font-size:13px;color:#374151;line-height:1.8">{_blog_txt}</div>
    </div>
  </div>

  <!-- Sevdikleri / Kaçındıkları / İdeal -->
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
    <div style="background:white;border:1px solid #e5e7eb;border-radius:14px;padding:16px 18px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:15px;color:#059669">✦</span>
        <span style="font-size:9px;font-weight:700;color:#059669;text-transform:uppercase;
                     letter-spacing:0.9px">Sevdiklerin</span>
      </div>
      <div style="font-size:12.5px;color:#374151;line-height:1.7">{profil_detay['tercih']}</div>
    </div>
    <div style="background:white;border:1px solid #e5e7eb;border-radius:14px;padding:16px 18px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:15px;color:#dc2626">✕</span>
        <span style="font-size:9px;font-weight:700;color:#dc2626;text-transform:uppercase;
                     letter-spacing:0.9px">Kaçındıkların</span>
      </div>
      <div style="font-size:12.5px;color:#374151;line-height:1.7">{profil_detay['kac']}</div>
    </div>
    <div style="background:linear-gradient(150deg,#f0f9ff,#e0f2fe);border:1px solid #bae6fd;
                border-radius:14px;padding:16px 18px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:15px;color:#0284c7">◈</span>
        <span style="font-size:9px;font-weight:700;color:#0284c7;text-transform:uppercase;
                     letter-spacing:0.9px">İdeal Destinasyon</span>
      </div>
      <div style="font-size:12.5px;color:#374151;line-height:1.7">{profil_detay['ideal']}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        MBTI_DESTINASYONLAR = {
            "INTJ": {
                "ozet": "INTJ'ler için ideal seyahat, derin hazırlık ve stratejik bir bakış açısı gerektirir. Kalabalıktan uzak, entelektüel uyarım sağlayan, tarihin ve mimarinin bir arada hissedildiği destinasyonlar bu tipin ruhuna en çok hitap eder. Aşağıdaki öneriler; INTJ'nin yalnızlık ihtiyacını, analitik bakışını ve kaliteli deneyim arayışını merkeze alarak seçilmiştir.",
                "sehirler": [
                    {"isim": "Kyoto, Japonya", "neden": "Kyoto, yüzyıllar boyu Japon imparatorluğunun merkezi olmuş, geleneksel Japon mimarisini ve budist felsefesini iç içe sunan bir şehirdir. INTJ'ler için Fushimi Inari tapınak yolunun sabah erken saatlerinde ıssız gezilmesi, Ryoanji'nin kum bahçesinde sessiz bir meditasyon anı geçirilmesi ya da Arashiyama bambu ormanında tek başına yürünmesi mükemmel birer deneyimdir. Şehrin katmanlı tarihi, her köşede bir anlam barındıran sembolleri ve wabi-sabi estetiği INTJ'nin analitik zihnini besler. Geisha kültürünü, çay seremonisini ve Zen bahçelerini derinlemesine araştırmak bu profil için tatmin edici bir entelektüel uğraştır."},
                    {"isim": "Edinburgh, İskoçya", "neden": "Edinburgh; karanlık ortaçağ tarihi, volkanik kayalıklar üzerinde yükselen kalesi, dar taş sokakları ve dünyanın en büyük edebiyat festivali ile INTJ'lerin ruhuna derinden dokunan bir şehirdir. Arthur's Seat zirvesine yapılan solo yürüyüş, şehrin bütününe hâkim bir bakış açısı sunar. Ulusal Müzesi İskoçya'nın jeolojik ve kültürel katmanlarını birlikte anlatır. Tarihi Old Town ile modern New Town arasındaki mimari gerilim bile bu tipin zihninde ilgi çekici bir analiz konusuna dönüşür. Whisky distillery turları, coğrafi köken ve iklim bilgisiyle birleşince sıradan bir tatil aktivitesinin çok ötesine geçer."},
                    {"isim": "Viyana, Avusturya", "neden": "Viyana'nın entelektüel ağırlığı eşsizdir: Freud'un muayenehanesi, Klimt'in altın yaprakları, Beethoven'ın son dönem semfonilerinin yazıldığı odalar ve Habsburg hanedanlığının hesap soran arşivleri aynı şehirdedir. INTJ'ler için Kunsthistorisches Museum bir günü dolduracak kadar zengindir. Kafeler Viyana'da yüzyıllık bir entelektüel gelenek taşır; bir köşeye çekilip saatlerce kitap okumak sosyal açıdan tamamen kabul görür. Klasik müzik konserleri, burada sadece bir gösteri değil, şehrin günlük yaşamının parçasıdır. Planlı bir INTJ için Viyana'nın metro sistemi, müze kartları ve rezervasyon kültürü kusursuz bir lojistik zemin sunar."},
                    {"isim": "Reykjavik, İzlanda", "neden": "İzlanda, INTJ'nin doğaya duyduğu derin merakı ve yalnızlık ihtiyacını aynı anda karşılar. Reykjavik, küçük ve işlevsel bir başkent olarak sürtünmesiz bir üs noktası işlevi görür. Ancak asıl çekim, şehrin dışındadır: jeotermal alanlar, buzullar, volkanik ova ve aurora borealis. Bu doğal fenomenleri derinlemesine anlamak için bilimsel arka plan araştırmak, INTJ için seyahatin ta kendisidir. Haftalarca önceden planlanan gece fotoğrafçılığı oturumları, jeoloji turları ve dağ yürüyüşleri bu profil için idealdir. Üstelik İzlanda'nın küçük nüfusu ve sessiz sosyal kültürü, sosyal enerji tüketimini minimumda tutar."},
                    {"isim": "Prag, Çek Cumhuriyeti", "neden": "Prag'ın Orta Avrupa gotik mimarisi, Kafka'nın labirentimsi sokaklara yansıyan varoluşsal estetiği ve Bohemya'nın felsefi tarihi INTJ'leri büyüler. Şehir, savaşlardan görece korunmuş olması sayesinde binlerce yıllık mimari katmanı hâlâ taşır. Josefov (tarihi Yahudi mahallesi), Old Town meydanının astronomik saati ve Vyšehrad kalesi tek tek ele alındığında bile günler süren bir araştırma programı oluşturur. INTJ'ler için Prag aynı zamanda bütçe dostudur; bu da kalite–maliyet dengesine önem veren bu tip için bir artı puandır."},
                ],
            },
            "INTP": {
                "ozet": "INTP'ler seyahati bir bilgi toplama süreci olarak yaşar. Keşfedilmemiş köşeler, bilimsel fenomenler, arkeolojik derinlik ve kütüphane büyüklüğündeki müzeler bu tipin enerji kaynağıdır. Sosyal performans beklentisinin düşük, entelektüel uyarımın yüksek olduğu destinasyonlar önerilmiştir.",
                "sehirler": [
                    {"isim": "Atina, Yunanistan", "neden": "Batı uygarlığının felsefi temelleri Atina'da somut biçimde yaşar. Akropolis'in sabah açılışında kalabalık olmadan gezilmesi, Stoa Attalos'un kolonlarında Sokrates'in öğrencileriyle yürüdüğü agora'yı hayal ederek dolaşmak INTP için soyut düşünceleri mekâna bağlayan bir deneyimdir. Ulusal Arkeoloji Müzesi, tek bir günde tükenilemeyecek kadar zengindir. Plaka mahallesi, geceleri akademik sohbetlerin döndüğü küçük meyhaneleriyle INTP'lerin spontane fikir alışverişine girdiği anlara zemin hazırlar."},
                    {"isim": "Krakow, Polonya", "neden": "Krakow; Orta Avrupa'nın en iyi korunmuş ortaçağ şehir merkezine, güçlü bir Yahudi kültürel mirasına ve yakınındaki Wieliczka tuz madenine ev sahipliği yapar. INTP'ler için tuz madeninin 700 yıllık mühendislik tarihi, Wawel kalesi'nin çok katmanlı mimarisi ve Jagiellonian Üniversitesi'nin kütüphaneleri büyüleyicidir. Şehrin üniversite kenti enerjisi, ucuz kahve fiyatları ve kalabalık olmayan müzeleri bu tipin bütçe bilincini ve merakını aynı anda tatmin eder."},
                    {"isim": "İzlanda Hinterland", "neden": "İzlanda'nın iç kesimleri INTP için adeta canlı bir bilim laboratuvarıdır. Jeotermal sistemler, volkanik oluşumlar, buzul göllerarasındaki renk geçişleri ve aurora fiziksel olaylar olarak incelenebilir. Ring Road üzerinde kendi hızınızda ilerleyen bir solo sürüş, her noktada durma ve araştırma özgürlüğü sunar. Bilimsel bağlam olmadan bakıldığında güzel olan bu manzaralar, arka plan bilgisiyle bakıldığında akıl almaz derinlikte bir anlam kazanır."},
                    {"isim": "Singapur", "neden": "Singapur, INTP'nin sistem odaklı düşüncesine hitap eden nadir kentsel destinasyonlardan biridir. Şehrin lojistik mükemmeliyeti, çok katmanlı etnik yapısı ve Gardens by the Bay'in biyo-mühendislik harikası 'Supertree'leri bu tipi büyüler. Aynı anda Çin, Hint, Malay ve İngiliz kültürel katmanlarını taşıyan bir şehirde her saat farklı bir bağlamda gezinmek, INTP'nin sentez yapma yeteneğini sürekli aktif tutar."},
                    {"isim": "Berlin, Almanya", "neden": "Berlin, 20. yüzyılın en ağır tarihsel travmalarını en dürüst biçimde yüzleşen şehirdir. Holocaust Anıtı, Stasi Müzesi, Checkpoint Charlie ve Topography of Terror, acımasız bir tarihsel şeffaflıkla sunulur. INTP'ler için bu yüzleşme kültürü derin bir entelektüel saygınlık taşır. Şehrin kesintisiz gelişen sanat ve teknoloji sahnesi, Bauhaus mirası ve güçlü tekno müzik kültürü ise farklı sistemlerin bir arada nasıl işleyebildiğini gösteren canlı bir deney alanıdır."},
                ],
            },
            "ENTJ": {
                "ozet": "ENTJ'ler için seyahat, prestij, verimlilik ve güçlü bir anlatı gerektirir. Liderlik tarihinin iz bıraktığı şehirler, iş dünyasının kalbi olan metropoller ve dünya standartlarında hizmet sunan destinasyonlar bu tip için idealdir. Her gün maksimum değer üretecek şekilde planlanmış bir program ENTJ'yi tatmin eder.",
                "sehirler": [
                    {"isim": "Singapur", "neden": "Singapur, bir şehir devletinin nasıl global bir ekonomik güç merkezi hâline gelebildiğini somutlaştıran en çarpıcı örnektir. Lee Kuan Yew'in vizyon liderliğiyle inşa edilen bu şehir, ENTJ'nin liderlik ve strateji merakını besler. Marina Bay Sands, finansal bölge gökdelenleri ve Changi Havalimanı'nın kusursuz lojistiği ENTJ için ilham kaynağıdır. Şehrin Michelin yıldızlı restoranları, business sınıf bağlantıları ve uluslararası konferans altyapısı bu tipin beklentilerini karşılar."},
                    {"isim": "Tokyo, Japonya", "neden": "Tokyo'nun ölçeği, organizasyonu ve mükemmeliyetçi hizmet kültürü ENTJ'leri etkiler. Şehrin metro sistemi dünyada bir efsanedir; dakikası dakikasına çalışan trenler ENTJ'nin verimliliğe duyduğu hayranlıkla örtüşür. Shibuya'nın küresel reklam bombardımanı, Akihabara'nın teknoloji yoğunluğu ve Ginza'nın lüks alışveriş deneyimi bu tipin yüksek enerji ihtiyacını karşılar. İş dünyası odaklı turlar, şirket ziyaretleri ve Japon yönetim felsefesine dair müzeler ENTJ için değer katar."},
                    {"isim": "Zürih, İsviçre", "neden": "Zürih; küresel finans, saat mühendisliği ve temiz, düzenli kentsel yaşamın simgesidir. ENTJ'ler için bu şehir hem estetik hem işlevsel mükemmeliyeti bir arada sunar. Bahnhofstrasse'deki lüks mağazalar, Kunsthaus'un Avrupa'nın en değerli koleksiyonlarından biri, Uetliberg tepesinden şehrin panoramik görünümü ve İsviçre finansal sistemini anlatan müze bu tip için zengin bir program oluşturur. Şehrin pahalı olması ENTJ için caydırıcı değil, aksine seçici bir ayrıcalık işareti olarak okunur."},
                    {"isim": "New York, ABD", "neden": "New York, ENTJ'nin hırsını ve enerji yoğunluğunu karşılayan dünyanın belki de tek şehridir. Wall Street'in tarihsel anlatısı, Broadway'in profesyonellik standartları, Met'in koleksiyon derinliği ve Central Park'ın planlı doğallığı bu tipin farklı boyutlarına hitap eder. Şehrin 'ya büyürsün ya da çekilirsin' felsefesi ENTJ'nin rekabetçi doğasıyla rezonans kurar. Üst düzey iş yemekleri, rooftop barlar ve power networking etkinlikleri bu şehrin günlük dokusunun parçasıdır."},
                    {"isim": "Dubai, BAE", "neden": "Dubai, kısa sürede imkânsızı mümkün kılan bir kentsel dönüşüm hikâyesidir — ENTJ'nin vizyon ve hız sevgisiyle birebir örtüşür. Burj Khalifa'nın zirvesinden şehre bakmak, Palm Jumeirah'ın mühendislik cüretini görmek, Dubai Mall'un ölçeğiyle yüzleşmek bu tipin büyüklüğe duyduğu ilgiyi karşılar. Şehrin 0'dan inşa edilmiş lüks otel kültürü, business sınıf erişimi ve uluslararası bağlantısı ENTJ için ideal bir üs noktası oluşturur."},
                ],
            },
            "ENTP": {
                "ozet": "ENTP'ler rutin rotaları reddeder, fikir ateşleyen ortamlar arar. Startup sahnesi, alternatif sanat, farklı kültürlerin çarpıştığı şehirler ve tartışmayı kışkırtacak mekânlar bu tipin seyahat enerjisini canlı tutar. Öngörülemeyen keşifler ENTP için plan değil, hedefin ta kendisidir.",
                "sehirler": [
                    {"isim": "Berlin, Almanya", "neden": "Berlin, ENTP'nin kural tanımaz yaratıcılığına en çok yer açan Avrupa şehridir. Kreuzberg ve Neukölln'deki bağımsız galeriler, sokak sanatı müzeleri ve geç saate kadar açık felsefe kafeleri bu tip için doğal habitat sayılır. Şehrin startup ekosistemi Avrupa'nın en dinamiklerinden biridir; birkaç gün içinde dünyanın dört bir yanından girişimciyle tanışmak mümkündür. ENTP'lerin içgüdüsel olarak girdiği tartışmalar burada entelektüel bir para birimi olarak işlev görür."},
                    {"isim": "İstanbul, Türkiye", "neden": "İstanbul, iki kıtanın arasındaki bu benzersiz konum sayesinde ENTP'nin sentez yapma tutkusunu besler. Bir çay bahçesinde oturup Asya'ya baktığınızda Avrupa arkanızdadır; bu dualite başlı başına felsefi bir provokasyondur. Kapalıçarşı'nın kaotik müzakere kültürü, Beyoğlu'nun eklektik bar sahnesi ve Boğaz'ın kültürel geçirgenliği ENTP için bitmeyen bir uyarım kaynağıdır. Şehrin eski ile yeniyi aynı anda barındıran çelişkili enerjisi bu tipin çelişkilere duyduğu zevkle mükemmel uyum içindedir."},
                    {"isim": "Barselona, İspanya", "neden": "Barselona, ENTP'nin estetik zevki ve entelektüel merakını bir arada tatmin eder. Gaudí'nin Sagrada Família'sı, doğrusal mimari mantığını tamamen yıkan bir yapıdır ve ENTP bu tür paradigma kırıcı örneklerden derin tatmin alır. El Born mahallesi bağımsız tasarım mağazaları ve deneysel restoranlarıyla doludur. Barceloneta plajı sabah saatlerinde yerel sörfçülere, öğleden sonra dünyadan gelen genç girişimcilere ev sahipliği yapar. Katalon kimliğinin İspanya ile gerilimi ise ENTP için canlı bir siyasi tartışma laboratuvarıdır."},
                    {"isim": "Amsterdam, Hollanda", "neden": "Amsterdam'ın liberal sosyal yapısı, bisiklet ölçekli şehir tasarımı ve düşünce özgürlüğüne verdiği tarihin derinliklerine uzanan önem ENTP'yi çeker. Rijksmuseum ve Van Gogh Müzesi klasik başlangıç noktalarıdır; ancak ENTP'nin asıl ilgi alanı Jordaan mahallesinin küçük galerileri, FOAM fotoğraf müzesi ve EYE sinema müzesidir. Kanal turları sırasında her köşede farklı bir mimari dönem beliriyor olması bu tipin 'şimdi bir bağlantı kurdum' anlık heyecanını sürekli besler."},
                    {"isim": "Lizbon, Portekiz", "neden": "Lizbon, Avrupa'nın en ucuz ve en az tüketilmiş büyük başkentlerinden biridir; bu da ENTP'nin 'henüz kimse bilmiyor' estetiğine hitap eder. LX Factory'nin endüstriyel dönüşüm kompleksi, Mouraria'nın fado barları ve Belem'in denizcilik tarihi ENTP'nin çok katmanlı ilgisini dengeli biçimde dağıtır. Portekizlilerin yabancılarla kolayca sohbet kurduğu sıcak kültür bu tip için günde onlarca tesadüfi fikir alışverişi anı yaratır."},
                ],
            },
            "INFJ": {
                "ozet": "INFJ'ler seyahatte anlam ve dönüşüm arar. Yüzeysel turizmden uzak, ruhsal derinliği olan, yerel halkla gerçek bağ kurulabilen ve içsel bir yolculuğu tetikleyecek destinasyonlar bu tip için idealdir.",
                "sehirler": [
                    {"isim": "Kyoto, Japonya", "neden": "Kyoto'nun wabi-sabi felsefesi — kusursuzluğu değil, eskimenin güzelliğini kucaklayan bu Japon estetiği — INFJ'nin derinlik arayışıyla mükemmel rezonans kurar. Kinkaku-ji'nin altın rengi sabah ışığında, Philosopher's Path boyunca kiraz çiçeklerinin altında yürümek ve Nishiki Pazar'ında yerel satıcılarla kısa ama gerçek sohbetler kurmak bu tip için derin tatmin kaynağıdır. Zen tapınaklarının meditasyon programlarına katılmak INFJ'nin içsel yolculuk ihtiyacını doğrudan karşılar."},
                    {"isim": "Varanasi, Hindistan", "neden": "Varanasi, dünyanın sürekli kesintisiz iskân edilen en eski şehirlerinden biridir ve Ganj kıyısında ölüm ile yaşamın her gün iç içe ritüelleştiği bir yer olarak INFJ'nin varoluşsal meraklarına doğrudan hitap eder. Sabah aarti törenini şafak vakti bir kayıktan izlemek, Ganj'ın kıyısındaki ateşin önünde saatlerce oturmak ve dar sokaklarda yürürken yüzyıllık bir yaşam ritmine tanıklık etmek bu tipin ruhunu besler."},
                    {"isim": "Fes, Fas", "neden": "Fes'in medina'sı dünyanın en büyük yayaya kapalı kentsel dokusudur ve 9. yüzyıldan bu yana değişmeden işleyen bir şehir içinde kaybolmak INFJ için dönüştürücü bir deneyimdir. Yerel ailelerle birlikte konaklama (riad), geleneksel boyahaneleri uzaktan izlemek ve Kairaouine'nin kütüphanesinde dakikalar geçirmek bu tipin anlam ve köklülük arayışını doyurur."},
                    {"isim": "Kopenhag, Danimarka", "neden": "Kopenhag, sosyal adalet, tasarım etiği ve çevre bilincini günlük yaşama entegre etmiş bir şehir olarak INFJ'nin değer sistemiyle uyumludur. Nørrebro'nun çok kültürlü mahalle dokusu, Christiania'nın alternatif topluluk deneyi ve Danish Design Museum'un insan odaklı tasarım felsefesi bu tip için hem ilham hem yansıma zemini sunar."},
                    {"isim": "Tbilisi, Gürcistan", "neden": "Tbilisi, Doğu ile Batı'nın sessizce kaynaştığı, turistleşmeden önce keşfedilmeyi hak eden bir şehirdir. Eski şehrin sul'hu (geleneksel ağırlama kültürü) INFJ'nin insanlık bağına duyduğu özlemi karşılar. Kükürt hamamları, balkon mimarisi ve polyphonic Gürcü müziği bu tipin estetik ve manevi katmanlarını aynı anda besler."},
                ],
            },
            "INFP": {
                "ozet": "INFP'ler için her seyahat içsel bir hikâyedir. Romantik şehirler, edebiyat mirası, doğal güzellik ve insanî sıcaklık bu tipin seyahat ruhunu besler. Kalabalıktan uzak, anın içinde kalınabilen destinasyonlar idealdir.",
                "sehirler": [
                    {"isim": "Edinburgh, İskoçya", "neden": "Edinburgh, dünya edebiyatına J.K. Rowling, Robert Louis Stevenson ve Walter Scott gibi isimleri armağan etmiştir. Şehrin sis ve granit atmosferi, gotik kuleler ve dar taş sokakları INFP'nin hayal dünyasını besler. The Elephant Café'de oturmak, Greyfriars Kirkyard'da dolaşmak ve Edinburgh Uluslararası Kitap Festivali'ne katılmak bu tip için derin anlam taşır."},
                    {"isim": "Prag, Çek Cumhuriyeti", "neden": "Prag'ın kıvrımlı köprüleri, barok kiliseler ve gaz lambası sokakları adeta gerçeklikle masalın sınırında bir şehir yaratır. Kafka'nın evine gitmek, Josefov'da saatlerce yürümek ve Vltava kıyısında akşam karanlığında oturmak INFP'nin romantik içe dönüklüğüne mükemmel bir zemin hazırlar."},
                    {"isim": "Yeni Zelanda — Güney Adası", "neden": "Queenstown ve Fiordland'ın dramatik doğası INFP'nin doğayla kuruduğu derin bağı besler. Milford Sound'un sisli fiyortları, Mount Cook'un karla kaplı zirvesi ve hobbit köylerinin masalsı atmosferi bu tipin gerçeklikten soyutlanma ihtiyacına cevap verir."},
                    {"isim": "Porto, Portekiz", "neden": "Porto'nun azulejos (çini) kaplı eski binaları, fado'nun melankolik tınısı ve Douro Vadisi'nin şarap terisleri INFP için hem görsel hem duygusal bir şölen sunar. Livraria Lello kitabevinin görkemli merdivenlerinde durmak, tek başına Ribeira'da akşamı izlemek ve yerel halkın saudade duygusunu paylaşmak bu tip için unutulmaz anlar yaratır."},
                    {"isim": "Oaxaca, Meksika", "neden": "Oaxaca'nın canlı renkleri, yerli el sanatları ve Día de los Muertos geleneğinin ölüme bakışındaki şiirsel derinlik INFP'nin duygusal ve estetik dünyasıyla rezonans kurar. Pazarlarda yerel sanatçılarla tanışmak, mezcal yapımını öğrenmek ve Monte Albán'ın antik kalıntılarında yalnız dolaşmak bu tipin anlamlı yalnızlık ihtiyacını karşılar."},
                ],
            },
            "ENFJ": {
                "ozet": "ENFJ'ler için seyahat, insanlarla derin bağ kurma ve kültürel köprüler inşa etme sürecidir. Topluluk odaklı etkinlikler, paylaşım kültürü güçlü destinasyonlar ve kolektif deneyimler bu tipin seyahat enerjisini besler.",
                "sehirler": [
                    {"isim": "Barselona, İspanya", "neden": "Barselona'nın açık hava kültürü, paylaşım sofraları ve festival takvimi ENFJ'nin sosyal enerjisiyle örtüşür. La Boqueria pazarında sabah alışverişi yapmak, La Mercè festivali sırasında şehrin kolektif coşkusunu yaşamak ve yerel ailelerle tapas paylaşmak bu tipin insanlara dokunan anılar biriktirme ihtiyacını karşılar."},
                    {"isim": "Bali, Endonezya", "neden": "Bali'nin kolektif ruhani pratiği — her gün sunulan çiçekli sesajen, köy meydanlarındaki gamelan müziği ve Nyepi'nin toplumsal sessizlik ritüeli — ENFJ'nin insanlık bağına ve anlama duyduğu özlemi karşılar. Ubud'da yoga ve meditasyon retreatlarına katılmak, yerel sanatçıların atölyelerini ziyaret etmek ve Balili bir aile ile birlikte yemek pişirmek bu tip için dönüştürücü deneyimlerdir."},
                    {"isim": "Nairobi & Masai Mara, Kenya", "neden": "Kenya'nın topluluk temelli safari deneyimleri ENFJ'nin hem doğa hem insan bağını aynı anda tatmin eder. Masai köylerini ziyaret etmek, yerel rehberlerle kurduğu güçlü bağ ve savanada büyük göç izlemek bu tipin empati ve anlam repertuarını genişletir."},
                    {"isim": "Medellín, Kolombiya", "neden": "Medellín, dünyanın en dikkat çekici kentsel dönüşüm hikâyelerinden birini yaşayan şehirdir. ENFJ'ler için şehrin sosyal inovasyon kültürü, Comunas'ın duvar resimleri ve yerel halkın dönüşüm gururunu paylaşma isteği son derece ilham vericidir. Salsa müziğinin canlı olduğu geceleri kolektif dans enerjisiyle yaşamak ise bu tip için doğal bir varış noktasıdır."},
                    {"isim": "Seul, Güney Kore", "neden": "Seul'ün K-kültür etkisi, kolektif yaşam alanları ve son derece gelişmiş misafirperver kültürü ENFJ'nin sosyal enerji ihtiyacını karşılar. Insadong'un geleneksel el sanatları çarşısı, Gwangjang Pazarı'nda yerel halkla omuz omuza yemek yemek ve jimjilbang (geleneksel hamam) kültürüne dahil olmak bu tipin paylaşım ve bağ kurma ihtiyacını doyurur."},
                ],
            },
            "ENFP": {
                "ozet": "ENFP'ler için seyahat, planları yırtıp spontane akmak demektir. Renkli festivaller, sokak kültürü, yeni insanlar ve anlık kararların mümkün olduğu destinasyonlar bu tipin ruhunu besler.",
                "sehirler": [
                    {"isim": "Marakeş, Fas", "neden": "Marakeş'in Djemaa el-Fna meydanı dünyanın en kaotik ve en büyüleyici kamusal alanlarından biridir. ENFP'ler için bu meydan — yılan oynatıcıları, hikaye anlatıcıları, taze portakal suyu satıcıları ve dans eden kalabalıklar — sonsuz bir spontane keşif sahnesine dönüşür. Medina'nın sokak labirenti içinde kaybolmak, bir riad'ın avlusunda rastlantısal sohbetlere dalmak ve souk'larda renkli kumaşlar arasında dolaşmak bu tipin özgür ruhuna tam anlamıyla hitap eder."},
                    {"isim": "Tayland — Chiang Mai", "neden": "Chiang Mai'nin festival kültürü — Yi Peng'in binlerce fener uçurulan gece şenliği, Songkran'ın su festivali — ENFP'nin kolektif sevinç ihtiyacını en üst düzeyde karşılar. Pazar labirentleri, muay thai dersleri, sülük ve fil sığınakları ENFP'nin yeni deneyim eklektisizmine mükemmel uyar. Şehrin düşük maliyeti uzun süreli konaklamaya izin verir; bu da ENFP'nin plan yapmadan akma hakkını artırır."},
                    {"isim": "Meksika City", "neden": "Meksika City'nin sanat, sokak yemeği ve canlılık yoğunluğu ENFP için enerji kaynağıdır. Frida Kahlo Müzesi, Coyoacán mahallesinin pazar atmosferi ve Roma Norte'nin hipster kafelerinden oluşan eklektik karma bu tipin estetik kaosunu besler. Sabahları Teotihuacan piramitlerinde izbe, öğleyin tacos al pastor kuyruğunda yerel halkla, akşam rooftop terasta uluslararası kalabalıkla — bir günde üç farklı dünya."},
                    {"isim": "Lizbon, Portekiz", "neden": "Lizbon'un tram 28 hattında rastlantısal duraklar yapmak, Alfama'da fado sesi takip etmek ve LX Factory'nin haftasonu pazarında keşfetmek ENFP'nin spontane enerjisiyle tam uyum içindedir. Şehrin küçük ölçeği yürüyerek keşfetmeye izin verirken her köşede yeni bir insan hikâyesiyle karşılaşmak kaçınılmazdır."},
                    {"isim": "Buenos Aires, Arjantin", "neden": "Buenos Aires'in tango kültürü ENFP için seyahat değil, hayat felsefesidir. Milonga'ya katılmak, Palermo'nun açık hava pazar festivallerinde dolaşmak ve Arjantinlilerin geç saate kadar süren akşam yemeklerinin sohbet kültürüne dahil olmak bu tipin uzun, derin ve canlı sosyal bağ kurma ihtiyacını karşılar."},
                ],
            },
            "ISTJ": {
                "ozet": "ISTJ'ler için seyahat, dikkatli araştırma ve kanıtlanmış kaliteye dayanır. Tarihi belgeli şehirler, güvenilir ulaşım ve önceden test edilmiş programlar bu tipin seyahat konforunu sağlar.",
                "sehirler": [
                    {"isim": "Viyana, Avusturya", "neden": "Viyana'nın mükemmel kamu ulaşımı, müze rezervasyon sistemi ve saatlik programa bağlı kalmayı kolaylaştıran şehir yapısı ISTJ için ideal bir çerçeve oluşturur. Habsburg tarihi derinlemesine araştırılmış ve belgelenmiştir; bu da bilgi güvenilirliğine önem veren ISTJ'yi memnun eder."},
                    {"isim": "Kyoto, Japonya", "neden": "Japon dakikliği ve protokol kültürü ISTJ'nin değer sistemiyle örtüşür. Tapınak saatleri kesindir, rezervasyon sistemleri güvenilirdir ve şehrin harita okunaklılığı mükemmeldir. Tarihin belgelenmiş katmanları ISTJ için güvenilir bir bilgi zemini sunar."},
                    {"isim": "Londra, İngiltere", "neden": "Londra'nın British Museum, National Gallery ve Imperial War Museum gibi kuruluşları dünyanın en kapsamlı ve en sistematik biçimde belgelenmiş koleksiyonlarını barındırır. ISTJ için bu kurumlar, güvenilir birincil kaynaklara doğrudan erişim imkânı sunar. Şehrin Oyster kartıyla yönetilen ulaşım sistemi ve kesin tren tarifeleri bu tipin organizasyon ihtiyacını karşılar."},
                    {"isim": "Singapur", "neden": "Singapur'un hukuk düzeni, ultra temiz sokakları ve lojistik mükemmeliyeti ISTJ'nin seyahatte aradığı güven ve öngörülebilirliği maksimize eder. Her şey çalışır, her şey zamanındadır, her şey kurallara uygundur."},
                    {"isim": "Washington D.C., ABD", "neden": "Smithsonian Müzeler Kompleksi'nin tamamı ücretsizdir ve birkaç gün boyunca sistematik biçimde gezilebilir. ISTJ için bu müzeler — Doğa Tarihi, Amerikan Tarihi, Uzay ve Havacılık — her biri derinlemesine araştırılmış, güvenilir kaynaklara dayanan koleksiyonlardır. Şehrin grid düzenli cadde yapısı yönlenmeyi kolaylaştırır."},
                ],
            },
            "ISFJ": {
                "ozet": "ISFJ'ler güvenli, sıcak ve aile dostu ortamlarda en mutlu gezginlerdir. Nostaljik şehirler, yerel gelenekler ve ev sıcaklığı sunan konaklamalar bu tip için idealdir.",
                "sehirler": [
                    {"isim": "Floransa, İtalya", "neden": "Floransa'nın insan ölçeğindeki şehir yapısı, dünyanın en iyi erişilebilir müzeleri ve her köşede bir trattoria'nın ev yemeği sıcaklığı ISFJ için mükemmel bir ortam yaratır. Boboli Bahçeleri'nde sakin bir öğleden sonra, Oltrarno'da yerel bir fırının ekmeğini almak ve Arno nehri kenarında oturmak bu tipin seyahat anılarının en değerli katmanlarını oluşturur."},
                    {"isim": "Provence, Fransa", "neden": "Provence'ın lavanta tarlaları, küçük taş kasabaları ve köklü bir Fransız mutfak geleneği ISFJ'nin güzelliğe ve huzura duyduğu özlemi karşılar. Aix-en-Provence'da pazar gezmek, Gordes köyünde bir butik otelde birkaç gece kalmak ve şarap turları yapmak bu tipin seyahat dilini oluşturur."},
                    {"isim": "Salzburg, Avusturya", "neden": "Salzburg'un masalsı silueti, Mozart mirası ve Avusturya'nın ev sıcaklığını yansıtan yemek kültürü ISFJ için güvenli ve anlamlı bir destinasyon oluşturur. Şehrin kompakt yapısı yürüyerek keşfedilmeye uygundur; kaybolma korkusu minimaldir."},
                    {"isim": "Yeni Zelanda — Kuzey Adası", "neden": "Rotorua'nın jeotermal doğası, Maori kültürel deneyimleri ve kamp dostu parklar ISFJ için hem güvenli hem doğaya yakın bir seçenek sunar. Yerel halkın sıcak misafirperverliği ve Yeni Zelanda'nın güvenlik imajı bu tipin endişelerini en aza indirir."},
                    {"isim": "Toskana, İtalya", "neden": "Toskana'nın kırsal yaşam ritmi — sabah zeytin bahçelerinde yürümek, öğlen farm-to-table yemek, akşam köy piazzasında oturmak — ISFJ'nin huzur ve sürdürülebilirlik değerleriyle örtüşür. Agriturismo konaklaması bu tip için ideal: özel ama yalnız değil, doğayla iç içe ama konforlu."},
                ],
            },
            "ESTJ": {
                "ozet": "ESTJ'ler her seyahati verimli, önceden planlanmış ve kontrol altında tutmayı tercih eder. Prestijli şehirler, tanınmış müzeler, güvenilir ulaşım ve organize turlar bu tipin seyahat programını oluşturur. Lojistik mükemmeliyeti ve saygın destinasyonlar ESTJ için önceliklidir.",
                "sehirler": [
                    {"isim": "Londra, İngiltere", "neden": "Londra, ESTJ'nin düzen, prestij ve verimlilik beklentilerini aynı anda karşılayan bir dünya başkentidir. Buckingham Sarayı, Westminster, British Museum ve Tower of London gibi simgeler önceden araştırılmış, güvenilir ve saygın destinasyonlardır. Şehrin Oyster kart tabanlı metro sistemi dakika dakika planlamaya izin verir. Michelin yıldızlı restoranlar, resmi öğle yemekleri ve iş toplantılarının doğal uzantısı olan sosyal ortamlar ESTJ'nin hem tatil hem networking ihtiyacını karşılar. Harrod's gibi prestijli mağazalar, Savile Row ve City of London finans bölgesi bu tipin kalite standartlarını karşılar."},
                    {"isim": "Tokyo, Japonya", "neden": "Tokyo'nun disiplinli kamu kültürü — dakikası dakikasına çalışan trenler, son derece temiz sokaklar, hata kabul etmeyen hizmet standardı — ESTJ'nin değer sisteminin dışa yansımış halidir. Şehrin Michelin yıldızlı restoran yoğunluğu dünyada birincil konumdadır; bu da ESTJ'nin kalite ve statüye yönelik yemek deneyimi için eşsiz bir ortam sunar. Imperial Saray bahçeleri, Meiji Tapınağı ve Akihabara'nın teknoloji disiplini ESTJ için güçlü birer referans noktasıdır. JR Pass ile bütün Japonya sistematik biçimde keşfedilebilir; bu planlama kolaylığı ESTJ'yi memnun eder."},
                    {"isim": "Singapur", "neden": "Singapur, bir şehrin nasıl kusursuz biçimde işletilebileceğini gösteren global bir örnek vakadır; bu da ESTJ'nin yönetim ve verimlilik hayranlığını doğrudan besler. Changi Havalimanı'nın dünyanın en iyi havalimanı ünvanını yıllardır koruması, metro sisteminin hatasız çalışması ve yasal düzenin görünür varlığı ESTJ için hem estetik hem pratik bir tatmin kaynağıdır. Marina Bay'deki iş kulelerinin silüeti, şehrin finansal ağırlığını görselleştirir. Gardens by the Bay'in planlı mükemmeliyeti ve resmi restoran kültürü bu tipin programına kolayca entegre olur."},
                    {"isim": "Viyana, Avusturya", "neden": "Viyana'nın Habsburg mirası, opera evleri, saray müzeleri ve resmi kahve evi kültürü ESTJ için hem entelektüel hem sosyal bir prestij çerçevesi sunar. Schönbrunn Sarayı turu önceden rezervasyonla mükemmel biçimde planlanabilir; saray mimarisi ve bahçe düzeni ESTJ'nin simetri ve düzen estetiğiyle örtüşür. Wiener Staatsoper'de bir temsil izlemek bu tipin sosyal statü göstergesine katkı sağlar. Viyana'nın toplu taşıma sistemi ve otel kalitesi tartışmasızdır."},
                    {"isim": "Zürih, İsviçre", "neden": "Zürih, ESTJ'nin kalite, düzen ve güvenilirlik beklentilerini eksiksiz karşılayan bir destinasyondur. İsviçre'nin saat hassasiyetindeki tren ağı, şehrin ultra temiz caddeleri ve Bahnhofstrasse'nin prestijli mağazaları ESTJ için ideal bir kentsel zemin oluşturur. Zürih'in finans merkezi kimliği bu tipin iş dünyasına olan bağlılığıyla rezonans kurar. Kunsthaus koleksiyonu planlı biçimde gezilebilir; Rüegg's zürcher geschnetzeltes gibi ikonik İsviçre yemekleri saygın restoranlarda titizlikle sunulur. Şehrin yüksek maliyeti ESTJ için caydırıcı değil, seçici bir prestij işaretidir."},
                ],
            },
            "ESFJ": {
                "ozet": "ESFJ'ler seyahati sevdikleriyle paylaşmak için yaşar. Fotojenik mekânlar, sosyal aktiviteler, sıcak yerel kültür ve herkesin keyif alacağı ortamlar bu tipin seyahat anlayışını oluşturur.",
                "sehirler": [
                    {"isim": "Paris, Fransa", "neden": "Paris, ESFJ'nin estetik ve sosyal beklentilerini birleştiren klasik destinasyondur. Eiffel Kulesi'nden manzara, Montmartre'da sabah kahvesi, Seine kıyısında akşam yemeği ve Versailles bahçeleri fotoğraflanabilir anılar üretir. Şehrin kafe kültürü uzun, keyifli sohbetler için biçilmiş kaftandır."},
                    {"isim": "Santorini, Yunanistan", "neden": "Santorini'nin mavi kubbeli kiliseleri ve beyaz badanalı duvarları dünyanın en çok fotoğraflanan manzaralarından birini oluşturur; bu da ESFJ'nin sosyal medya ve anı paylaşma ihtiyacını doğrudan karşılar. Oia'da gün batımı izlemek grup dinamiği için kusursuz bir etkinliktir."},
                    {"isim": "Bali, Endonezya", "neden": "Bali'nin resort kültürü, spa deneyimleri ve kolektif yoga retreatları ESFJ'nin hem sosyal hem dinlendirici seyahat ihtiyacına cevap verir. Ubud'un pirinç tarası yürüyüşleri ve ateş dansı gösterileri grup seyahati için mükemmel aktivitelerdir."},
                    {"isim": "Dubrovnik, Hırvatistan", "neden": "Dubrovnik'in surlarla çevrili tarihi merkezi, Adriyatik'e bakan restoranları ve gün batımında kırmızıya dönen taş dokusu ESFJ için görsel ve sosyal açıdan zengin bir deneyim sunar. Şehrin kompakt yapısı grup seyahatini kolaylaştırır."},
                    {"isim": "Barselona, İspanya", "neden": "Barselona'nın açık hava kültürü, paylaşım sofraları ve gece hayatı ESFJ'nin sosyal enerjisiyle örtüşür. Tapas kültürü bu tipin paylaşımlı yemek sevgisini doğrudan karşılar; Gaudí yapıları grup fotoğrafları için ikonik arka planlar sunar."},
                ],
            },
            "ISTP": {
                "ozet": "ISTP'ler hareketi, fiziksel zorluğu ve pratik beceriyi ödüllendiren destinasyonlar ister. Doğa, dağ, mekanik kültür ve spontane macera bu tipin seyahat enerjisini şarj eder.",
                "sehirler": [
                    {"isim": "Norveç Fiyortları", "neden": "Preikestolen ve Trolltunga gibi trekking rotaları ISTP'nin fiziksel zorluğa ve saf doğaya duyduğu açlığı karşılar. Kayıkla fiyort gezmek, kamp kurmak ve sert hava koşullarıyla başa çıkmak bu tipin pragmatik beka becerilerini aktive eder."},
                    {"isim": "Moğolistan Stepi", "neden": "Ulaanbaatar dışına çıkıp stepte at binmek, ger çadırında kalmak ve Gobi Çölü'nde motosiklet sürmek ISTP için dünyanın sunabileceği en saf macera deneyimlerinden biridir. Modernliğin sıfırlandığı bu ortamda temel beceriler öne çıkar."},
                    {"isim": "Patagonya, Arjantin/Şili", "neden": "Torres del Paine'in zorlu yürüyüş parkurları, Perito Moreno buzulunun çatlamaları ve Tierra del Fuego'nun uçsuz bucaksız alanı ISTP'nin limitlerini test etme isteğini tatmin eder."},
                    {"isim": "Japonya — Hokkaido", "neden": "Hokkaido'nun kış sporları kültürü, Niseko'nun dünyaca ünlü kayak yamaçları ve açık doğa onsen deneyimleri ISTP'nin pratik macera anlayışına hitap eder. Motosikletle Hokkaido'nun kuzeyini dolaşmak bu tip için ideal bir solo seyahat senaryosudur."},
                    {"isim": "Yeni Zelanda — Güney Adası", "neden": "Queenstown bungee jumping, skydiving ve jet boat gibi adrenalin sporlarının başkentidir. Milford Track ve Routeburn Track zorlu trekking programları sunar. Şehrin macera kültürü ISTP'nin eylem odaklı tatil anlayışıyla birebir örtüşür."},
                ],
            },
            "ISFP": {
                "ozet": "ISFP'ler dünyayı estetik bir deneyim olarak yaşar. Sanat, el sanatları, doğanın güzelliği ve sessiz keşifler bu tipin seyahat ruhunu besler. Aceleye getirilmemiş, izlenebilecek anların bol olduğu destinasyonlar idealdir.",
                "sehirler": [
                    {"isim": "Floransa, İtalya", "neden": "Uffizi'nin Botticelli salonunda saatlerce durmak, San Miniato al Monte'nin bahçesinde Arno vadisini izlemek ve Oltrarno'da küçük bir çerçeveci atölyesine adım atmak ISFP için seyahatin özüdür. Floransa, sanatı müzeye hapsetmez; sokaklar, köprüler ve kahve barları da birer galeri köşesine dönüşür."},
                    {"isim": "Bali — Ubud", "neden": "Ubud'un pirinç tarası manzaraları, geleneksel dans gösterileri ve el sanatları atölyeleri ISFP'nin estetik duyarlılığını besler. Gün batımında Tegalalang teras fotoğrafları çekmek, bir batik boyama kursuna katılmak ya da sabah sessizliğinde yoga yapmak bu tipin anları yoğun hissetme ihtiyacıyla örtüşür."},
                    {"isim": "Oaxaca, Meksika", "neden": "Oaxaca'nın canlı renkleri, yerli dokuma gelenekleri ve çömlek atölyeleri ISFP için görsel ve dokunsal bir cennet yaratır. Küçük bir atölyede ustadan boyama öğrenmek ya da Monte Albán'ın sessizliğinde oturmak bu tipin içsel ritmine uyum sağlar."},
                    {"isim": "Kyoto, Japonya", "neden": "Kyoto'nun çiçek döneminde kiraz ağaçlarının altında durmak, Nishiki'nin renkli tezgahları arasında yavaşça ilerlemek ve Gion mahallesinde akşam ışığını beklemek ISFP'nin anlık güzelliğe duyduğu derin duyarlılığa hitap eder."},
                    {"isim": "Kopenhag, Danimarka", "neden": "Kopenhag'ın İskandinav tasarım felsefesi — işlevsellikle estetiği birleştiren minimalist yaklaşım — ISFP'nin görsel dünyasını zenginleştirir. Designmuseum Denmark, Nørrebro'nun vintage mağazaları ve Reffen street food marketinin renk cümbüşü bu tip için keyifli bir estetik rotadır."},
                ],
            },
            "ESTP": {
                "ozet": "ESTP'ler için seyahat maksimum hız ve aksiyon demektir. Gece hayatı, adrenalin sporları, hızlı şehir keşifleri ve anlık kararların serbestçe alındığı ortamlar bu tipin seyahat ateşini tutuşturur.",
                "sehirler": [
                    {"isim": "Dubai, BAE", "neden": "Dubai'nin Burj Khalifa'sından base jumping, Ski Dubai'de kayak, Formula E parkurunda araba deneyimi ve Atlantis'in su parkı ESTP'nin adrenalin ihtiyacını şehir konforunu koruyarak karşılar. Gece hayatı ise küresel DJ'lerle, rooftop barlarla ve 7 gün 7 gece devam eden bir eğlence makinesiyle gelir."},
                    {"isim": "Las Vegas, ABD", "neden": "Las Vegas, ESTP'nin hazırda var olan her şeyi anında tüketme enerjisi için tasarlanmış gibidir. Poker masası, gece kulübü, açık büfe ve motorsports arena aynı oteldedir. Strip'in ışıkları, sürekli değişen uyarım ortamı ve 'ne olur?' beklentisi bu tipin doğasına birebir uyar."},
                    {"isim": "Bangkok, Tayland", "neden": "Bangkok'un gece pazarları, muay thai kulüpleri, scooter kiralayarak trafik labirentinde ilerlemek ve Chao Phraya'da hızlı tekne turları ESTP için ideal bir aksiyon programı oluşturur. Şehrin kaotik enerjisi ve sürekli değişen sahnesi bu tipin sıkılma eşiğini asla tetiklemez."},
                    {"isim": "Queenstown, Yeni Zelanda", "neden": "Queenstown, Dünya'nın macera sporları başkentidir: bungee jumping, skydiving, canyon swing, jet boat. ESTP için bu şehir sadece bir destinasyon değil, fiziksel limitlerini test etmek için özelleşmiş bir platform gibidir."},
                    {"isim": "İbiza, İspanya", "neden": "İbiza'nın gece kulübü kültürü ESTP'nin topluluk enerjisiyle dans etme, anlık bağlantılar kurma ve adrenalini sosyal ortamda hissetme ihtiyacını maksimize eder. Gündüzleri plaj sporları, geceleri Pacha veya Amnesia — ritim hiç kesintisiz akar."},
                ],
            },
            "ESFP": {
                "ozet": "ESFP'ler her destinasyonu bir sahneye dönüştürür. Müzik, dans, kalabalık ve canlı sosyal ortamlar bu tipin seyahat enerjisinin kaynağıdır. Fotoğraflanabilir anlar, yeni arkadaşlıklar ve sürekli uyarım bu tipin beklentisidir.",
                "sehirler": [
                    {"isim": "Rio de Janeiro, Brezilya", "neden": "Rio'nun karnaval enerjisi ESFP'nin hayat felsefesiyle örtüşür. Copacabana'da sahil voleybolu, Cristo Redentor'dan panoramik selfie, samba okulu provalerında dans etmek ve boteco'larda caipirinha içmek bu tipin seyahat anılarının tam merkezini oluşturur."},
                    {"isim": "İbiza, İspanya", "neden": "İbiza'nın gündüz plaj partileri ve gece kulüp kültürü ESFP için mükemmel bir sahne sunar. Yeni insanlarla tanışmak, dans pistinde saatler geçirmek ve sabah denize girerek geceyi kapatmak bu tipin ritmine doğal olarak uyar."},
                    {"isim": "Bali, Endonezya", "neden": "Bali'nin Seminyak ve Kuta plajlarının gün batımı bar kültürü, pool party sahnesi ve sosyal yoga retreatları ESFP'nin hem eğlence hem bağ kurma ihtiyacını dengeler. Her gün yeni insanlarla tanışmak burada otomatik bir sonuç haline gelir."},
                    {"isim": "Barselona, İspanya", "neden": "Barselona'nın plaj, kulüp ve festivalin iç içe geçtiği yapısı ESFP için ideal bir karma sunar. Barceloneta sahilinde öğlen, Gaudí fotoğrafları için Las Ramblas'ta akşam öncesi, Opium veya Pacha'da gece — bu ritim bu tip için mükemmeldir."},
                    {"isim": "Seul, Güney Kore", "neden": "Seul'ün K-pop kültürü, canlı sokak yeme-içme sahnesi ve Hongdae'nin geç saatlere kadar açık müzik barları ESFP için her gece yeni bir keşif vaat eder. BTS gibi ikonların doğduğu kültürü yerinde yaşamak bu tipin pop kültürü enerjisiyle rezonans kurar."},
                ],
            },
        }

        mbti_dest = MBTI_DESTINASYONLAR.get(mbti, None)

        st.markdown('<div style="padding:0 32px">', unsafe_allow_html=True)

        st.markdown(f"""
<style>
.mbti-rapor h2 {{
    font-size:16px;font-weight:800;color:#2c1810;
    margin:18px 0 8px;padding-bottom:6px;
    border-bottom:1px solid #f0ebe3;
}}
.mbti-rapor h3 {{
    font-size:13px;font-weight:700;color:#4a3828;margin:12px 0 5px;
}}
.mbti-rapor p {{
    font-size:13px;color:#374151;line-height:1.85;margin:0 0 10px;
}}
.mbti-rapor ul {{
    margin:6px 0 12px 16px;padding:0;
}}
.mbti-rapor li {{
    font-size:12.5px;color:#4b5563;line-height:1.75;margin-bottom:4px;
}}
</style>
<div style="background:#fffefb;border-radius:16px;
            border-left:4px solid;
            border-image:linear-gradient(to bottom,#d4976a,#9eaa8f) 1;
            border-top:1px solid #e8e0d4;border-right:1px solid #e8e0d4;
            border-bottom:1px solid #e8e0d4;
            padding:24px 28px;margin-bottom:16px">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;
              padding-bottom:14px;border-bottom:1px solid #f0ebe3">
    <div style="width:32px;height:32px;border-radius:8px;flex-shrink:0;
                background:linear-gradient(135deg,#d4976a,#9eaa8f);
                display:flex;align-items:center;justify-content:center;
                font-size:14px">🧠</div>
    <div>
      <div style="font-size:12px;font-weight:800;color:#2c1810;letter-spacing:0.3px">
        AI Gezgin Profil Analizi</div>
      <div style="font-size:10px;color:#9ca3af;margin-top:1px">
        Kişiliğine göre kişiselleştirilmiş seyahat değerlendirmesi</div>
    </div>
  </div>
  <div class="mbti-rapor">
""", unsafe_allow_html=True)
        st.markdown(st.session_state.mbti_report, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        if mbti_dest:
            renk_dest = profil_detay['renk']

            sehir_html = ""
            for i, sehir in enumerate(mbti_dest['sehirler']):
                sehir_html += f"""
                <div style="background:#fafafa;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                    <div style="width:22px;height:22px;background:{renk_dest};border-radius:6px;
                                display:flex;align-items:center;justify-content:center;
                                font-size:10px;font-weight:800;color:white;flex-shrink:0">{i+1}</div>
                    <div style="font-size:13px;font-weight:700;color:#111827">{sehir['isim']}</div>
                  </div>
                  <div style="font-size:12px;color:#6b7280;line-height:1.65">{sehir['neden']}</div>
                </div>"""

            st.markdown(f"""
            <div style="background:white;border:1px solid #e5e7eb;border-radius:14px;
                        padding:20px 24px;margin-bottom:16px">
              <div style="display:flex;align-items:center;justify-content:space-between;
                          margin-bottom:12px">
                <div style="font-size:10px;font-weight:700;color:{renk_dest};text-transform:uppercase;
                            letter-spacing:0.6px">{mbti} için Destinasyon Önerileri</div>
                <div style="font-size:11px;color:#9ca3af">{len(mbti_dest['sehirler'])} şehir</div>
              </div>
              <div style="font-size:12px;color:#6b7280;line-height:1.6;margin-bottom:16px;
                          padding-bottom:14px;border-bottom:1px solid #f3f4f6">
                {mbti_dest['ozet']}
              </div>
              <div style="display:flex;flex-direction:column;gap:10px">
                {sehir_html}
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        col_btn, col_redo = st.columns([5, 1])
        with col_btn:
            nav_arrows("Rota Oluşturmaya Geç", 1)
        with col_redo:
            st.markdown('<div style="padding-top:24px">', unsafe_allow_html=True)
            if st.button("Yeniden Çöz", key="redo_mbti"):
                st.session_state.mbti_completed = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="animate-fadeup" style="background:linear-gradient(135deg,#1e1b4b 0%,#3730a3 50%,#4f46e5 100%);
                    border-radius:20px;padding:48px 40px;margin:24px 32px 0;
                    position:relative;overflow:hidden;text-align:center">
          <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;
                      border-radius:50%;background:rgba(255,255,255,0.05)"></div>
          <div style="position:absolute;bottom:-60px;left:-30px;width:240px;height:240px;
                      border-radius:50%;background:rgba(255,255,255,0.04)"></div>
          <div style="position:relative;z-index:1">
            <div style="font-size:40px;margin-bottom:12px">✈️</div>
            <h1 style="font-size:30px;font-weight:900;color:white;margin:0 0 12px;
                       letter-spacing:-1px;line-height:1.15">
              Seyahat Planınız<br>
              <span style="color:#a5b4fc">Yapay Zeka ile</span> Hazır
            </h1>
            <p style="font-size:14px;color:rgba(255,255,255,0.75);margin:0 auto 28px;
                      max-width:480px;line-height:1.7">
              MBTI profilinize göre kişiselleştirilmiş rota, restoran önerileri
              ve gerçekçi 2026 maliyet analizi — tek tıkla.
            </p>
            <div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-bottom:24px">
              <div style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);
                          border-radius:12px;padding:12px 20px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:900;color:white">16</div>
                <div style="font-size:11px;color:rgba(255,255,255,0.65);margin-top:2px">MBTI Profili</div>
              </div>
              <div style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);
                          border-radius:12px;padding:12px 20px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:900;color:white">AI</div>
                <div style="font-size:11px;color:rgba(255,255,255,0.65);margin-top:2px">Plan Motoru</div>
              </div>
              <div style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);
                          border-radius:12px;padding:12px 20px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:900;color:white">TL</div>
                <div style="font-size:11px;color:rgba(255,255,255,0.65);margin-top:2px">2026 Fiyat</div>
              </div>
            </div>
            <div style="font-size:12px;color:rgba(255,255,255,0.55)">
              Başlamak için aşağıdaki kişilik testini doldurun ↓
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        page_header("Gezgin Kimlik Testi",
                    "20 soruyla turizm kimliğinizi ve kişilik profilinizi belirliyoruz")

        st.markdown('<div style="padding:20px 32px">', unsafe_allow_html=True)

        st.markdown("""
        <div style="background:white;border:1px solid #e5e7eb;border-radius:14px;
                    padding:20px 24px;margin-bottom:20px;
                    display:flex;align-items:center;gap:20px">
          <div style="flex:1">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span style="font-size:12px;font-weight:600;color:#374151">Test İlerlemesi</span>
              <span style="font-size:11px;color:#9ca3af">20 soru · ~4 dakika</span>
            </div>
            <div style="background:#f3f4f6;border-radius:999px;height:6px">
              <div style="background:linear-gradient(90deg,#4f46e5,#818cf8);
                          border-radius:999px;height:6px;width:0%;
                          transition:width 0.3s ease"></div>
            </div>
          </div>
          <div style="display:flex;gap:8px">
            <div style="background:#eef2ff;border-radius:10px;padding:10px 16px;text-align:center">
              <div style="font-size:20px;font-weight:800;color:#4f46e5">20</div>
              <div style="font-size:10px;color:#6b7280;font-weight:500">Soru</div>
            </div>
            <div style="background:#f0fdf4;border-radius:10px;padding:10px 16px;text-align:center">
              <div style="font-size:20px;font-weight:800;color:#059669">16</div>
              <div style="font-size:10px;color:#6b7280;font-weight:500">Profil</div>
            </div>
            <div style="background:#fff7ed;border-radius:10px;padding:10px 16px;text-align:center">
              <div style="font-size:20px;font-weight:800;color:#ea580c">4</div>
              <div style="font-size:10px;color:#6b7280;font-weight:500">Boyut</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("mbti_form"):
            c1, c2 = st.columns(2, gap="large")
            with c1:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#eef2ff,#e0e7ff);
                            border-radius:12px;padding:14px 18px;margin-bottom:16px;
                            border:1px solid #c7d2fe">
                  <div style="font-size:10px;font-weight:700;color:#4f46e5;
                              text-transform:uppercase;letter-spacing:0.6px;margin-bottom:2px">
                    Bölüm 1 / 2
                  </div>
                  <div style="font-size:14px;font-weight:700;color:#1e1b4b">Turizm Kimliği &amp; Sosyal Tarz</div>
                  <div style="font-size:12px;color:#6b7280;margin-top:2px">Sorular 1 – 10</div>
                </div>
                """, unsafe_allow_html=True)
                q1 = st.radio(
                    "1. Tatilde insanlarla zaman geçirmek size ne hissettiriyor?",
                    ["A) Enerji doldurucu — yeni insanlar tanımak beni besler",
                     "B) Güzel — sosyal ortamlar seyahatimi zenginleştirir",
                     "C) Keyifli ama sınırlı — biraz yalnız zaman da gerek",
                     "D) Yorucu — tek başıma ya da küçük grupla daha rahatım"]
                )
                q2 = st.radio(
                    "2. Bir müzeyi gezerken dikkatinizi çeken ne olur?",
                    ["A) Somut eserler, tarihi belgeler ve gerçek nesneler",
                     "B) Kanıtlanmış tarihsel bilgiler ve kronolojik sıralama",
                     "C) Dönemler arasındaki örüntüler ve kültürel bağlantılar",
                     "D) Tarihin bana hissettirdiği anlam ve büyük resim"]
                )
                q3 = st.radio(
                    "3. Seyahatte beklenmedik bir aksaklıkla karşılaşırsanız?",
                    ["A) Alternatifleri hızlıca analiz eder, en mantıklı çözümü uygularım",
                     "B) Nesnel verilere bakarak hızlıca plan B üretirim",
                     "C) Grubun moralini öncelerim, herkesin hissini sorarım",
                     "D) Duygusal atmosferi düzelterek birlikte çözüm bulmaya çalışırım"]
                )
                q4 = st.radio(
                    "4. Tatil hazırlığınız nasıl?",
                    ["A) Günler öncesinden saatlik program yapar, tüm rezervasyonları tamamlarım",
                     "B) Detaylı bir plan hazırlar, mümkün olanları önceden netleştiririm",
                     "C) Genel çerçeveyi belirler, detayları giderken hallederim",
                     "D) Minimum hazırlıkla çıkarım, sürprizleri seviyorum"]
                )
                q5 = st.radio(
                    "5. Bir destinasyona vardığınızda ilk adımınız ne olur?",
                    ["A) Hemen sosyal bir mekana gider, insanlarla tanışırım",
                     "B) Çevreyi gezerek insanlarla konuşmaya başlarım",
                     "C) Haritayı inceler, sessizce ortama alışırım",
                     "D) Konakladığım yerde dinlenerek şehri zihinsel olarak haritalandırırım"]
                )
                q6 = st.radio(
                    "6. Destinasyon seçerken önceliğiniz nedir?",
                    ["A) İnceleme puanı yüksek, güvenilir ve kanıtlanmış popüler yerler",
                     "B) Somut aktiviteleri ve görülmesi gereken yerleri önceden belirlemek",
                     "C) Az keşfedilmiş, özgün hikayesi olan, kalabalıktan uzak yerler",
                     "D) Bana anlam ifade eden, sezgisel olarak çeken destinasyonlar"]
                )
                q7 = st.radio(
                    "7. Bir restoran seçerken ne belirler?",
                    ["A) Fiyat/kalite analizi, puanlar ve objektif değerlendirmeler",
                     "B) Menüyü önceden araştırıp bilinçli karar veririm",
                     "C) Ortam sıcaklığı ve sezgisel his",
                     "D) Arkadaş tavsiyesi ve duygusal çekim"]
                )
                q8 = st.radio(
                    "8. Programda beklenmedik bir değişiklik olunca ne hissedersiniz?",
                    ["A) Rahatsız olurum — plan yapmak benim için çok önemli",
                     "B) Biraz gerilerim ama hızlıca yeni bir plan kurarım",
                     "C) Esnerim — spontane değişiklikler güzel sürprizler getirir",
                     "D) Sevinç duyarım — planın dışına çıkmak beni canlandırır"]
                )
                q9 = st.radio(
                    "9. Seyahatte en çok hangi anlar sizi canlandırır?",
                    ["A) Yeni tanışıklıklar, grup aktiviteleri, kalabalık ortamlar",
                     "B) Rehberli turlar ve organize sosyal etkinlikler",
                     "C) Kendi ritmiyle, yalnız ya da çok yakın biriyle yapılan keşifler",
                     "D) Sessiz müze köşeleri, kütüphaneler, yalnız yürüyüşler"]
                )
                q10 = st.radio(
                    "10. Tatil bütçenizi ve harcamalarınızı nasıl yönetirsiniz?",
                    ["A) Her adımı somut bilgiye dayandırır, kalem kalem takip ederim",
                     "B) Belirli başlıklar altında somut bütçe hedefleri koyarım",
                     "C) Genel bir çerçeve yeterli; detaylar sezgiyle dolar",
                     "D) Anın ruhuna göre harcarım, katı bütçeler beni kısıtlar"]
                )
            with c2:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);
                            border-radius:12px;padding:14px 18px;margin-bottom:16px;
                            border:1px solid #a7f3d0">
                  <div style="font-size:10px;font-weight:700;color:#059669;
                              text-transform:uppercase;letter-spacing:0.6px;margin-bottom:2px">
                    Bölüm 2 / 2
                  </div>
                  <div style="font-size:14px;font-weight:700;color:#064e3b">Karar Tarzı &amp; Deneyim Anlayışı</div>
                  <div style="font-size:12px;color:#6b7280;margin-top:2px">Sorular 11 – 20</div>
                </div>
                """, unsafe_allow_html=True)
                q11 = st.radio(
                    "11. Rota konusunda seyahat arkadaşınızla anlaşmazlık çıkarsa?",
                    ["A) Veriler, maliyet ve verimlilik argümanlarıyla savunurum",
                     "B) Mantıksal en iyi seçeneği bulmak için tartışmayı yürütürüm",
                     "C) Herkesin mutlu olacağı ortak bir nokta için ödün veririm",
                     "D) Grup uyumunu öncelirim, kendi tercihimden kolayca vazgeçebilirim"]
                )
                q12 = st.radio(
                    "12. Seyahat çantanızı hazırlarken yaklaşımınız?",
                    ["A) Detaylı liste yaparak, her olasılığa karşı sistematik hazırlanırım",
                     "B) Çantayı kategorilere bölerek düzenli ve planlı doldururum",
                     "C) Son anda ne aklıma gelirse koyarım",
                     "D) Sadece en temel eşyaları alır, minimalistim"]
                )
                q13 = st.radio(
                    "13. Sosyal bir mekanda mı yoksa kendi odanızda mı daha rahat hissedersiniz?",
                    ["A) Sosyal alanda — insan enerjisi beni dolduruyor",
                     "B) İkisinde de iyi hissedebilirim ama sosyal ortamı tercih ederim",
                     "C) Kendi odamda — sosyal alan uzun süre yorucu gelir",
                     "D) Kesinlikle yalnız — kalabalık beni tüketiyor"]
                )
                q14 = st.radio(
                    "14. Yerel bir yemek denerken düşünceniz ne olur?",
                    ["A) Malzemeleri ve hazırlama yöntemini merak eder, somut bilgi ararım",
                     "B) Bu yemeğin şehrin mutfağındaki yerini ve tarihini araştırırım",
                     "C) Yemeğin kültürel anlamını ve bana hissettirdiği ruhu yaşarım",
                     "D) Lezzeti bir metafor olarak görürüm; şehrin ruhunu tattığımı hissederim"]
                )
                q15 = st.radio(
                    "15. Ziyaret ettiğiniz mekanlarda öncelik nasıl belirlenir?",
                    ["A) En önemli ve en çok değerlendirilen noktaları öne alırım",
                     "B) Sistematik bir yaklaşımla her mekânı nesnel değerlendiririm",
                     "C) Anın ruhuna ve içgüdülerime göre yönlenirim",
                     "D) Mekânın bana olan duygusal çekimine göre karar veririm"]
                )
                q16 = st.radio(
                    "16. Tatil boyunca zamanı nasıl yönetirsiniz?",
                    ["A) Programa uyarım, gecikmelerden rahatsız olurum",
                     "B) Verimli kullanmak için zamanı takip eder, önceden planlarım",
                     "C) Güzel bir yerde olunca saatlerce kalabilir, programı esnetirim",
                     "D) Zamanı hiç takip etmem, an'da yaşarım"]
                )
                q17 = st.radio(
                    "17. Tatil dönüşünde deneyimlerinizi nasıl paylaşırsınız?",
                    ["A) Herkese anlatır, sosyal medyada paylaşır, geniş çevremi dahil ederim",
                     "B) Arkadaş ve aile çevremiyle aktif biçimde paylaşırım",
                     "C) Sadece en yakınlarımla paylaşır, çoğunu günlüğüme yazarım",
                     "D) Kendi içimde yaşarım; deneyimler benim için kişisel kalır"]
                )
                q18 = st.radio(
                    "18. Konaklama seçerken belirleyici olan nedir?",
                    ["A) Konum, tesisat, fiziksel konfor ve güvenilir incelemeler",
                     "B) Fotoğraflara ve somut özelliklere bakarak karar veririm",
                     "C) Yerin karakteri, ruhu ve beni farklı hissettirip hissettirmediği",
                     "D) Bir hikayesi olan, atmosferiyle öne çıkan özgün mekanlar"]
                )
                q19 = st.radio(
                    "19. Seyahat başarısını nasıl değerlendirirsiniz?",
                    ["A) Planı ne kadar uyguladım ve kaç hedefi tamamladım",
                     "B) Verimli zaman kullanımı ve hedeflere ulaşma oranı",
                     "C) Yaşadığım duygular ve kurduğum bağlantıların kalitesi",
                     "D) Kalbimde bıraktığı iz ve manevi tatmin"]
                )
                q20 = st.radio(
                    "20. Tatilden temel beklentiniz ne?",
                    ["A) Her şeyin planlandığı gibi gitmesi ve hedeflere ulaşmak",
                     "B) Organize bir tatil sayesinde maksimum verim almak",
                     "C) Sürprize açık olmak ve planın ötesine geçen anlar yaşamak",
                     "D) Tamamen özgür kalmak, ne yaşarsam yaşayayım"]
                )

            extra = st.text_area(
                "Opsiyonel Not",
                placeholder="Örnek: Vejetaryenim, fotoğraf çekmekten hoşlanıyorum...",
            )

            if st.form_submit_button("Profil Oluştur", type="primary"):
                ans = {f"q{i}": v for i, v in enumerate(
                    [q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,
                     q11,q12,q13,q14,q15,q16,q17,q18,q19,q20], start=1)}
                ans["extra"] = extra
                with st.spinner("Profiliniz oluşturuluyor..."):
                    try:
                        res = MBTIAgent().analyze(ans)
                        st.session_state.mbti_report    = res.get("description", "")
                        st.session_state.user_data["mbti_type"] = res.get("mbti_type", "ENFP")
                        st.session_state.mbti_archetype = res.get("archetype", "Gezgin")
                        st.session_state.mbti_completed = True
                        _mbti_profil_kaydet(st.session_state.username, {
                            "mbti_type":   res.get("mbti_type", "ENFP"),
                            "archetype":   res.get("archetype", "Gezgin"),
                            "description": res.get("description", ""),
                        })
                        go_tab(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

elif cur == 1:
    step_indicator(NAV_ITEMS, 1)
    page_header("Kimlik Profili", "Kişiliğine özel seyahat analizi ve destinasyon önerileri")

    if not st.session_state.mbti_completed:
        st.markdown('<div style="padding:40px 32px;text-align:center">', unsafe_allow_html=True)
        st.info("Kimlik profilinizi görmek için önce Kimlik Testini tamamlayın.")
        _cp = st.columns([3, 2, 3])
        with _cp[1]:
            if st.button("Kimlik Testine Git", key="goto_test_p", use_container_width=True):
                go_tab(0); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        mbti = st.session_state.user_data.get("mbti_type", "")
        arch = st.session_state.mbti_archetype

        _MBTI_SEYAHAT_P = {
            "INTJ": {"tercih": "Derin planlama, tarihi alanlar, soliter kültür turları", "kac": "Kalabalık gruplar, spontane değişiklikler, gövde gösterisi turları", "ideal": "Japonya çay seremonisi, Roma müzeleri, Edinburgh kalesi", "renk": "#6d28d9"},
            "INTP": {"tercih": "Bilim müzesi, arkeoloji, sessiz doğal alanlar, kütüphaneler", "kac": "Plaj partileri, yüksek sesli mekanlar, kalabalık alışveriş", "ideal": "Atina Akropolü, Krakow tarihi merkez, İzlanda fiyortları", "renk": "#7c3aed"},
            "ENTJ": {"tercih": "Verimli rota, business sınıf, lüks otel, liderlik turları", "kac": "Organizasyonsuz geziler, hostel, uzun bekleme", "ideal": "Singapur, Zürih, Tokyo iş merkezi", "renk": "#4338ca"},
            "ENTP": {"tercih": "Yeni fikirler, tartışma kafeleri, startup sahnesi, farklı kültürler", "kac": "Rutin turist rotaları, tur rehberi, kısıtlayıcı programlar", "ideal": "Berlin sanat sahnesi, İstanbul agorası, Amsterdam", "renk": "#2563eb"},
            "INFJ": {"tercih": "Anlamlı deneyimler, yerel halk ile tanışma, manevi mekanlar", "kac": "Yüzeysel turist noktaları, kalabalık, gürültü", "ideal": "Hindistan ashram, Kyoto tapınakları, Fas medina", "renk": "#0891b2"},
            "INFP": {"tercih": "Romantik şehirler, edebiyat turları, doğal ortamlar, sanat", "kac": "Kalabalık turistik mekanlar, zaman baskısı, katı program", "ideal": "Edinburgh, Prag, Yeni Zelanda doğası", "renk": "#0d9488"},
            "ENFJ": {"tercih": "Kültür takası, topluluk deneyimleri, rehberli turlar, insanlarla bağlanma", "kac": "Yalnız uzlet, kuvvetli tur programı, doğal afetler", "ideal": "Brezilya karnavalı, Hindistan kültür turları, Gana", "renk": "#059669"},
            "ENFP": {"tercih": "Spontane keşifler, festival, yerel pazar, yeni insanlar", "kac": "Katı programlar, standart otel, tekrar eden rotalar", "ideal": "Tayland festivalleri, Marakeş meydanı, Barselona", "renk": "#65a30d"},
            "ISTJ": {"tercih": "Planlı ve organize, tarihi mekanlar, müzeler, güvenilir ulaşım", "kac": "Son dakika değişiklikler, belirsizlik, hostel kaos", "ideal": "Viyana, Londra müze turu, Japonya trenleri", "renk": "#ca8a04"},
            "ISFJ": {"tercih": "Güvenli, rahat, aile dostu mekanlar, geleneksel yemekler", "kac": "Riskli maceralar, bilinmezlik, kalabalık gece hayatı", "ideal": "Provence Fransa, Toskana köyü, Yeni Zelanda", "renk": "#d97706"},
            "ESTJ": {"tercih": "Verimli program, lüks otel, organize turlar, önem verilen mekanlar", "kac": "Kaos ve plansızlık, kirli mekanlar, zaman kaybı", "ideal": "Viyana opera, Londra iş merkezi, Singapur", "renk": "#dc2626"},
            "ESFJ": {"tercih": "Aile tatilleri, sosyal aktiviteler, hoş restoranlar, fotoğraflık noktalar", "kac": "Yalnızlık, sert koşullar, soğuk mekanlar", "ideal": "Paris romantik turu, Bali tatil köyü, Santorini", "renk": "#e11d48"},
            "ISTP": {"tercih": "Macera sporları, mekanik teknik turlar, dağ, doğa kampı", "kac": "Kalabalık şehir merkezleri, organize turlar, sosyal zorunluluk", "ideal": "Norveç dağ trekkingi, Moğolistan step, Patagonya", "renk": "#0284c7"},
            "ISFP": {"tercih": "Sanat galerileri, doğada yürüyüş, yerel el sanatları, sessiz kafeler", "kac": "Soğuk konferans tarzı turlar, kalabalık alışveriş merkezleri", "ideal": "Floransa sanat turu, Bali Ubud, Oaxaca Meksika", "renk": "#7c3aed"},
            "ESTP": {"tercih": "Aksiyon sporları, gece hayatı, hızlı şehir keşifleri, macera parkları", "kac": "Müze saatleri, yavaş tempolu turlar, kültürel zorunluluklar", "ideal": "Dubai, Las Vegas, Bangkok gece hayatı", "renk": "#ea580c"},
            "ESFP": {"tercih": "Festival, plaj, sosyal etkinlikler, dans, canlı müzik", "kac": "Sakin ve izole mekanlar, uzun müze turları, yalnız gezi", "ideal": "Rio karnavalı, İbiza, Bali festivalleri", "renk": "#db2777"},
        }
        _pd = _MBTI_SEYAHAT_P.get(mbti, {"tercih": "Kişisel keşifler", "kac": "Standart turlar", "ideal": "Size özel destinasyonlar", "renk": "#4f46e5"})
        _renk = _pd["renk"]

        _TRAIT_MAP_P = {
            "INTJ":["Stratejik","Bağımsız","Analitik","Kararlı","Öngörülü"],
            "INTP":["Meraklı","Nesnel","Yenilikçi","Analitik","Sessiz"],
            "ENTJ":["Lider","Verimli","Güçlü","Stratejik","Kararlı"],
            "ENTP":["Yaratıcı","Tartışmacı","Vizyoner","Hızlı","Esnek"],
            "INFJ":["Empatik","Anlayışlı","İçgörülü","İdealci","Sakin"],
            "INFP":["Romantik","Yaratıcı","Özgün","Duyarlı","Hayalperest"],
            "ENFJ":["Karizmatik","İlham Veren","Empatik","Sosyal","Yardımsever"],
            "ENFP":["Enerjik","Özgür","Coşkulu","Meraklı","Spontane"],
            "ISTJ":["Güvenilir","Düzenli","Sorumlu","Kararlı","Pratik"],
            "ISFJ":["Sıcak","Koruyucu","Sadık","Sabırlı","Özenli"],
            "ESTJ":["Organizatör","Güçlü","Net","Sorumlu","Verimli"],
            "ESFJ":["Sosyal","Sevgi Dolu","Fedakâr","Uyumlu","Cana Yakın"],
            "ISTP":["Pratik","Mekanik","Cesur","Sessiz","Bağımsız"],
            "ISFP":["Sanatçı","Hassas","Uysal","Anlık","Estetik"],
            "ESTP":["Maceracı","Hızlı","Pratik","Sosyal","Cesur"],
            "ESFP":["Neşeli","Spontane","Eğlenceli","Sosyal","Coşkulu"],
        }
        _traits = _TRAIT_MAP_P.get(mbti, ["Özgün","Keşifçi","Meraklı","Bağımsız","Esnek"])

        _trait_chips = "".join(
            f'<span style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.18);'
            f'border-radius:99px;padding:4px 12px;font-size:11px;font-weight:600;'
            f'color:rgba(255,255,255,0.88);display:inline-block;margin:3px 2px">{t}</span>'
            for t in _traits
        )

        _dim_labels = [("E","I","Dışavurumcu","İçedönük"),("N","S","Sezgisel","Gözlemci"),
                       ("T","F","Mantıksal","Duygusal"),("J","P","Planlayıcı","Esnek")]
        _dim_vals = []
        for _di, (_a, _b, _la, _lb) in enumerate(_dim_labels):
            _letter = mbti[_di] if _di < len(mbti) else _a
            _is_a   = (_letter == _a)
            _dim_vals.append((_is_a, _la if _is_a else _lb))

        def _dim_bar(la, lb, letter_a, letter_b, is_a):
            _fill = 72 if is_a else 28
            return f"""<div style="margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
    <span style="font-size:11px;font-weight:{'800' if is_a else '500'};color:{'#111827' if is_a else '#9ca3af'}">{la} ({letter_a})</span>
    <span style="font-size:11px;font-weight:{'800' if not is_a else '500'};color:{'#111827' if not is_a else '#9ca3af'}">{lb} ({letter_b})</span>
  </div>
  <div style="background:#f3f4f6;border-radius:99px;height:7px;overflow:hidden">
    <div style="height:100%;width:{_fill}%;background:linear-gradient(90deg,{_renk},{_renk}99);
                border-radius:99px;{'margin-left:auto' if not is_a else ''}"></div>
  </div>
</div>"""

        _boyut_html = "".join(
            _dim_bar(_dim_labels[i][2], _dim_labels[i][3], _dim_labels[i][0], _dim_labels[i][1], _dim_vals[i][0])
            for i in range(4)
        )

        _BLOG_P = {
            "INTJ":"INTJ'ler seyahat ederken her ayrıntıyı önceden planlar. Antik kentleri, felsefi müzeleri ve sessiz doğa rotalarını tercih ederler.",
            "INTP":"INTP'ler seyahati çözülmesi gereken bir bilim projesi gibi görürler. Arkeolojik alanlar ve kütüphaneler onları büyüler.",
            "ENTJ":"ENTJ'ler tatilde bile verimlilik ararlar. Prestijli destinasyonları ve lüks otelleri seçerler.",
            "ENTP":"ENTP'ler rutin rotaları reddeden vizyon avcılarıdır. Startup sahnesi ve alternatif galeriler tam onlara göredir.",
            "INFJ":"INFJ'ler için seyahat içsel bir yolculuktur. Yerel halkla tanışabilecekleri otantik mekanları severler.",
            "INFP":"INFP'ler her şehirde bir masalın izini sürer. Tarihi kafeler, eski kitapçılar ve bohem mahalleler onlar için cennettir.",
            "ENFJ":"ENFJ'ler her destinasyonda insanları bir araya getiren rehberlerdir. Kültür takasına dayalı festivaller onları besler.",
            "ENFP":"ENFP'ler için seyahat tüm planları yırtıp spontane hareket etmek demektir. Renkli pazarlar ve festivaller tam onlara göredir.",
            "ISTJ":"ISTJ'ler için mükemmel seyahat milimetrik düzen ve önceden test edilmiş bir programa bağlıdır.",
            "ISFJ":"ISFJ'ler güvenli, sıcak ve aile dostu ortamlar ararlar. Nostaljik kasabaları ve el sanatları pazarlarını severler.",
            "ESTJ":"ESTJ'ler seyahatin her anında tam kontrol sağlamak isteyen organizatörlerdir.",
            "ESFJ":"ESFJ'ler seyahati sosyal paylaşım ve kolektif eğlence aracı olarak görürler.",
            "ISTP":"ISTP'ler fiziksel aksiyonu ve doğanın zorluklarıyla mücadeleyi seven kaşiflerdir.",
            "ISFP":"ISFP'ler dünyayı gözleri ve kalpleriyle hisseden estetik duyarlılığı yüksek sanatçı gezginlerdir.",
            "ESTP":"ESTP'ler için durağan bir tatil kabustur. Adrenalin sporları ve gece hayatı onların kan grubudur.",
            "ESFP":"ESFP'ler ayak bastıkları her destinasyonu eğlence sahnesine dönüştüren hayat dolu turistlerdir.",
        }
        _blog_txt = _BLOG_P.get(mbti, "Seyahat tarzınız tamamen kendinize özgü.")

        _DEST_P = {
            "INTJ":  ["Kyoto, Japonya","Edinburgh, İskoçya","Viyana, Avusturya","Reykjavik, İzlanda","Prag, Çek Cumhuriyeti"],
            "INTP":  ["Atina, Yunanistan","Krakow, Polonya","İzlanda Hinterland","Singapur","Berlin, Almanya"],
            "ENTJ":  ["Singapur","Tokyo, Japonya","Zürih, İsviçre","New York, ABD","Dubai, BAE"],
            "ENTP":  ["Berlin, Almanya","İstanbul, Türkiye","Barselona, İspanya","Amsterdam, Hollanda","Lizbon, Portekiz"],
            "INFJ":  ["Kyoto, Japonya","Varanasi, Hindistan","Fes, Fas","Kopenhag, Danimarka","Tbilisi, Gürcistan"],
            "INFP":  ["Edinburgh, İskoçya","Prag, Çek Cumhuriyeti","Yeni Zelanda — Güney Adası","Porto, Portekiz","Oaxaca, Meksika"],
            "ENFJ":  ["Barselona, İspanya","Bali, Endonezya","Nairobi & Masai Mara","Medellín, Kolombiya","Seul, Güney Kore"],
            "ENFP":  ["Marakeş, Fas","Tayland — Chiang Mai","Meksika City","Lizbon, Portekiz","Buenos Aires, Arjantin"],
            "ISTJ":  ["Viyana, Avusturya","Kyoto, Japonya","Londra, İngiltere","Singapur","Washington D.C., ABD"],
            "ISFJ":  ["Floransa, İtalya","Provence, Fransa","Salzburg, Avusturya","Yeni Zelanda — Kuzey Adası","Toskana, İtalya"],
            "ESTJ":  ["Londra, İngiltere","Tokyo, Japonya","Singapur","Viyana, Avusturya","Zürih, İsviçre"],
            "ESFJ":  ["Paris, Fransa","Santorini, Yunanistan","Bali, Endonezya","Dubrovnik, Hırvatistan","Barselona, İspanya"],
            "ISTP":  ["Norveç Fiyortları","Moğolistan Stepi","Patagonya","Japonya — Hokkaido","Yeni Zelanda — Güney Adası"],
            "ISFP":  ["Floransa, İtalya","Bali — Ubud","Oaxaca, Meksika","Kyoto, Japonya","Kopenhag, Danimarka"],
            "ESTP":  ["Dubai, BAE","Las Vegas, ABD","Bangkok, Tayland","Queenstown, Yeni Zelanda","İbiza, İspanya"],
            "ESFP":  ["Rio de Janeiro, Brezilya","İbiza, İspanya","Bali, Endonezya","Barselona, İspanya","Seul, Güney Kore"],
        }
        _dest_list = _DEST_P.get(mbti, [])

        st.markdown(f"""
<div style="padding:20px 32px 0">
  <div style="background:linear-gradient(135deg,#1e1b4b 0%,#3730a3 50%,#4f46e5 100%);
              border-radius:20px;padding:32px 36px;margin-bottom:16px;
              position:relative;overflow:hidden">
    <div style="position:absolute;right:-40px;top:-40px;width:220px;height:220px;
                border-radius:50%;background:rgba(255,255,255,0.04)"></div>
    <div style="position:relative;display:flex;align-items:flex-start;gap:36px;flex-wrap:wrap">
      <div style="min-width:140px">
        <div style="font-size:10px;font-weight:700;letter-spacing:2.5px;
                    color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:8px">Gezgin Tipin</div>
        <div style="font-size:72px;font-weight:900;letter-spacing:-5px;line-height:0.9;color:white">{mbti}</div>
        <div style="margin-top:14px;display:inline-block;background:{_renk}44;
                    border:1px solid {_renk}88;border-radius:8px;
                    padding:5px 14px;font-size:13px;font-weight:700;color:white">{arch}</div>
      </div>
      <div style="flex:1;min-width:200px;padding-top:4px">
        <div style="font-size:10px;font-weight:700;color:rgba(255,255,255,0.38);
                    letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px">Kişilik Özelliklerin</div>
        <div style="line-height:1.4">{_trait_chips}</div>
        <div style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.08);
                    font-size:11.5px;color:rgba(255,255,255,0.45);display:flex;align-items:center;gap:8px">
          <span style="width:6px;height:6px;border-radius:50%;background:#9eaa8f;
                       display:inline-block;flex-shrink:0"></span>
          Rota, restoran ve maliyet ajanları bu profile göre çalışıyor
        </div>
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px">
    <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;padding:20px 22px">
      <div style="font-size:10px;font-weight:700;color:#6b7280;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:14px">Kişilik Boyutları</div>
      {_boyut_html}
    </div>
    <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;padding:20px 22px">
      <div style="font-size:10px;font-weight:700;color:#6b7280;text-transform:uppercase;
                  letter-spacing:1.2px;margin-bottom:10px">Seyahat Tarzın</div>
      <div style="font-size:13px;color:#374151;line-height:1.8">{_blog_txt}</div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
    <div style="background:white;border:1px solid #e5e7eb;border-radius:14px;padding:16px 18px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:15px;color:#059669">✦</span>
        <span style="font-size:9px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.9px">Sevdiklerin</span>
      </div>
      <div style="font-size:12.5px;color:#374151;line-height:1.7">{_pd['tercih']}</div>
    </div>
    <div style="background:white;border:1px solid #e5e7eb;border-radius:14px;padding:16px 18px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:15px;color:#dc2626">✕</span>
        <span style="font-size:9px;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:0.9px">Kaçındıkların</span>
      </div>
      <div style="font-size:12.5px;color:#374151;line-height:1.7">{_pd['kac']}</div>
    </div>
    <div style="background:linear-gradient(150deg,#f0f9ff,#e0f2fe);border:1px solid #bae6fd;
                border-radius:14px;padding:16px 18px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:15px;color:#0284c7">◈</span>
        <span style="font-size:9px;font-weight:700;color:#0284c7;text-transform:uppercase;letter-spacing:0.9px">İdeal Destinasyon</span>
      </div>
      <div style="font-size:12.5px;color:#374151;line-height:1.7">{_pd['ideal']}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div style="padding:0 32px">', unsafe_allow_html=True)

        if st.session_state.mbti_report:
            _rapor = st.session_state.mbti_report
            st.markdown("""
<style>
.mbti-rapor-p h2 {font-size:16px;font-weight:800;color:#2c1810;margin:18px 0 8px;
    padding-bottom:6px;border-bottom:1px solid #f0ebe3;}
.mbti-rapor-p h3 {font-size:13px;font-weight:700;color:#4a3828;margin:12px 0 5px;}
.mbti-rapor-p p {font-size:13px;color:#374151;line-height:1.85;margin:0 0 10px;}
.mbti-rapor-p ul {margin:6px 0 12px 16px;padding:0;}
.mbti-rapor-p li {font-size:12.5px;color:#4b5563;line-height:1.75;margin-bottom:4px;}
</style>
<div style="background:#fffefb;border-radius:16px;
            border-left:4px solid #d4976a;
            border-top:1px solid #e8e0d4;border-right:1px solid #e8e0d4;
            border-bottom:1px solid #e8e0d4;
            padding:24px 28px;margin-bottom:16px">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;
              padding-bottom:14px;border-bottom:1px solid #f0ebe3">
    <div style="width:32px;height:32px;border-radius:8px;flex-shrink:0;
                background:linear-gradient(135deg,#d4976a,#9eaa8f);
                display:flex;align-items:center;justify-content:center;font-size:14px">&#129504;</div>
    <div>
      <div style="font-size:12px;font-weight:800;color:#2c1810;letter-spacing:0.3px">AI Gezgin Profil Analizi</div>
      <div style="font-size:10px;color:#9ca3af;margin-top:1px">Kişiliğine göre kişiselleştirilmiş seyahat değerlendirmesi</div>
    </div>
  </div>
  <div class="mbti-rapor-p">
""", unsafe_allow_html=True)
            st.markdown(_rapor, unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

        if _dest_list:
            _dest_cards = "".join(
                f'<div style="background:#fafafa;border:1px solid #e5e7eb;border-radius:10px;'
                f'padding:10px 14px;display:flex;align-items:center;gap:10px">'
                f'<div style="width:22px;height:22px;background:{_renk};border-radius:6px;'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:10px;font-weight:800;color:white;flex-shrink:0">{i+1}</div>'
                f'<div style="font-size:13px;font-weight:600;color:#111827">{s}</div>'
                f'</div>'
                for i, s in enumerate(_dest_list)
            )
            st.markdown(f"""
<div style="background:white;border:1px solid #e5e7eb;border-radius:14px;
            padding:20px 24px;margin-bottom:16px">
  <div style="font-size:10px;font-weight:700;color:{_renk};text-transform:uppercase;
              letter-spacing:0.6px;margin-bottom:12px">{mbti} için Önerilen Destinasyonlar</div>
  <div style="display:flex;flex-direction:column;gap:8px">
    {_dest_cards}
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        _cp1, _cp2 = st.columns([5, 1])
        with _cp1:
            nav_arrows("Rota Oluşturmaya Geç", 2)
        with _cp2:
            st.markdown('<div style="padding-top:24px">', unsafe_allow_html=True)
            if st.button("Yeniden Çöz", key="redo_mbti_profil"):
                st.session_state.mbti_completed = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

elif cur == 2:
    step_indicator(NAV_ITEMS, 2)

    if not st.session_state.mbti_completed:
        st.markdown('<div style="padding:40px 32px;text-align:center">', unsafe_allow_html=True)
        st.warning("Devam etmek için önce Kimlik Testini tamamlayın.")
        c = st.columns([3, 2, 3])
        with c[1]:
            if st.button("Kimlik Testine Git", use_container_width=True):
                go_tab(0); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    left, right = st.columns([3, 2], gap="large")

    with left:
        page_header("Seyahat Planını Oluştur",
                    "Rotanızı ve tercihlerinizi girin, yapay zeka sizin için planlasın")
        st.markdown("""
        <div style="padding:16px 32px">
        <div class="animate-fadeup" style="background:white;border:1px solid #e5e7eb;
                    border-radius:20px;padding:28px 28px 20px;margin-bottom:16px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.06)">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;
                      padding-bottom:16px;border-bottom:1px solid #f3f4f6">
            <div style="width:40px;height:40px;border-radius:12px;flex-shrink:0;
                        background:linear-gradient(135deg,#4f46e5,#7c3aed);
                        display:flex;align-items:center;justify-content:center;
                        font-size:20px;box-shadow:0 2px 8px rgba(79,70,229,0.25)">🗺️</div>
            <div>
              <div style="font-size:15px;font-weight:800;color:#111827">Seyahat Rotanızı Oluşturun</div>
              <div style="font-size:12px;color:#6b7280;margin-top:1px">
                Bilgileri girin, AI kişiselleştirilmiş planınızı hazırlasın
              </div>
            </div>
          </div>
        </div></div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="padding:0 32px">', unsafe_allow_html=True)
        with st.form("travel_form"):

            st.markdown("""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
              <div style="width:8px;height:8px;background:#4f46e5;border-radius:50%"></div>
              <span style="font-size:12px;font-weight:700;color:#374151;
                           text-transform:uppercase;letter-spacing:0.5px">Destinasyon</span>
            </div>
            """, unsafe_allow_html=True)
            hedef = st.text_input("Destinasyon", placeholder="Şehir girin — Örnek: Roma, Tiflis, Marakeş",
                                  label_visibility="collapsed")

            st.markdown("""
            <div style="display:flex;align-items:center;gap:8px;margin:16px 0 6px">
              <div style="width:8px;height:8px;background:#059669;border-radius:50%"></div>
              <span style="font-size:12px;font-weight:700;color:#374151;
                           text-transform:uppercase;letter-spacing:0.5px">Tarihler</span>
            </div>
            """, unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            bas = d1.date_input("Giriş", value=date.today())
            bit = d2.date_input("Çıkış", value=date.today())

            st.markdown("""
            <div style="display:flex;align-items:center;gap:8px;margin:16px 0 6px">
              <div style="width:8px;height:8px;background:#d97706;border-radius:50%"></div>
              <span style="font-size:12px;font-weight:700;color:#374151;
                           text-transform:uppercase;letter-spacing:0.5px">Seyahat Detayları</span>
            </div>
            """, unsafe_allow_html=True)
            r1, r2, r3 = st.columns(3)
            kisi       = r1.number_input("Kişi Sayısı", min_value=1, max_value=20, value=1)
            ulasim_sec = r2.selectbox("Ulaşım", ["Uçak", "Otobüs", "Tren", "Araba"])
            butce_kat  = r3.selectbox("Bütçe",
                            ["ekonomik", "orta", "luks"],
                            format_func=lambda x: {"ekonomik": "Ekonomik", "orta": "Orta", "luks": "Lüks"}[x])

            st.markdown("""
            <div style="display:flex;align-items:center;gap:8px;margin:16px 0 6px">
              <div style="width:8px;height:8px;background:#db2777;border-radius:50%"></div>
              <span style="font-size:12px;font-weight:700;color:#374151;
                           text-transform:uppercase;letter-spacing:0.5px">Bütçe &amp; Profil</span>
            </div>
            """, unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            butce         = b1.number_input("Toplam Bütçe (TL)", min_value=500, value=10_000, step=500)
            kullanici_adi = b2.text_input("Adınız", placeholder="Örnek: Ayşe")

            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button("Plan Oluştur", type="primary")

        if submitted:
            errors = []
            if not hedef.strip(): errors.append("Şehir adı boş bırakılamaz.")
            if bit < bas:         errors.append("Çıkış tarihi başlangıçtan önce olamaz.")
            for err in errors:
                st.error(err)

            if not errors:
                gun_farki = (bit - bas).days + 1
                t_data = {
                    "destination":      hedef.strip(),
                    "budget":           butce,
                    "transport":        ulasim_sec,
                    "group_size":       int(kisi),
                    "start_date":       str(bas),
                    "end_date":         str(bit),
                    "butce_kategorisi": butce_kat,
                    "kullanici_adi":    kullanici_adi.strip() or "kullanici",
                    "user_profile":     st.session_state.user_data,
                    "travel_history":   st.session_state.travel_history,
                }

                st.markdown("""
                <div class="animate-fadein" style="background:linear-gradient(135deg,#f5f3ff,#eff6ff);
                            border:1px solid #e0e7ff;border-radius:16px;padding:20px 24px;
                            margin-bottom:12px;display:flex;align-items:center;gap:16px">
                  <div style="font-size:32px;flex-shrink:0">🤖</div>
                  <div>
                    <div style="font-size:14px;font-weight:700;color:#3730a3;margin-bottom:3px">
                      AI Planınızı Hazırlıyor
                    </div>
                    <div style="font-size:12px;color:#6b7280">
                      Bu işlem 15–45 saniye sürebilir, lütfen sayfayı kapatmayın
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                progress = st.progress(0)
                status   = st.empty()

                try:
                    progress.progress(10)
                    status.caption("🐜 Karınca Koloni Algoritması rotayı optimize ediyor...")
                    aco_res = ACOAgent().optimize_route(t_data)

                    if "optimized_route" not in aco_res:
                        fallback_route = aco_optimized_route(aco_res)
                        aco_res["optimized_route"] = fallback_route

                    progress.progress(30)
                    status.caption("✈️ Ulaşım seçenekleri hesaplanıyor...")
                    ulas_res = UlasimAgent().get_transport_options(t_data, aco_res)

                    progress.progress(50)
                    status.caption("🍽️ Restoran önerileri hazırlanıyor...")
                    rest_res      = RestaurantAgent().get_recommendations(t_data, gun_farki)
                    rest_schedule = RestaurantAgent().create_restaurant_schedule(t_data, recommendations=rest_res)

                    progress.progress(65)
                    status.caption("💰 2026 maliyet analizi yapılıyor...")
                    mal_res = MaliyetAgent().analyze(t_data, aco_res.get("optimized_route", []))

                    progress.progress(80)
                    status.caption("📝 Yapay zeka seyahat planı yazılıyor...")
                    plan = PlanAgent().create_plan(t_data, aco_res, ulas_res, rest_schedule, mal_res)

                    progress.progress(100)
                    status.caption("✅ Plan hazır!")

                    plan["start_date"]       = t_data["start_date"]
                    plan["end_date"]         = t_data["end_date"]
                    plan["group_size"]       = t_data["group_size"]
                    plan["transport"]        = t_data["transport"]
                    plan["butce_kategorisi"] = t_data["butce_kategorisi"]
                    plan["destination"]      = t_data.get("destination", "")
                    plan["mbti"]             = t_data.get("user_profile", {}).get("mbti_type", "")

                    st.session_state.travel_history.append(plan)
                    _gecmis_kaydet(st.session_state.travel_history)  # diske yaz
                    st.session_state.last_plan         = plan
                    st.session_state.last_aco          = aco_res
                    st.session_state.last_t_data       = t_data
                    st.session_state.maliyet_result    = mal_res
                    st.session_state.last_rest_res      = rest_res
                    st.session_state.last_rest_schedule = rest_schedule

                    progress.empty()
                    status.empty()

                    go_tab(3)
                    st.rerun()

                except Exception as e:
                    progress.empty()
                    status.empty()
                    st.error(f"Hata: {e}")
                    import traceback
                    with st.expander("Teknik Detay"):
                        st.code(traceback.format_exc())

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div style="padding:28px 16px 0">', unsafe_allow_html=True)
        mbti_cur = st.session_state.user_data.get("mbti_type", "?")
        arch_cur = st.session_state.mbti_archetype

        MBTI_BLOG = {
            "INTJ": "INTJ'ler seyahat ederken her ayrıntıyı önceden planlar, kaostan nefret ederler. Popüler alışveriş mağazaları onlar için zaman kaybıdır; bunun yerine antik kentleri, felsefi derinliği olan müzeleri ve sessiz doğa rotalarını tercih ederler. Kalabalık turist gruplarından ve yapay eğlence merkezlerinden kesinlikle uzak dururlar. Yemekte kültürel bağlamı güçlü, arka planında bir hikaye barındıran yerel tatları keşfetmeyi severler.",
            "INTP": "INTP'ler seyahati çözülmesi gereken bir bilim projesi gibi görürler. Arkeolojik kazı alanları, bilim merkezleri, devasa kütüphaneler ve gözlemevleri onları büyüler. Katı seyahat planlarından nefret eder; haritada görünmeyen kuytu köşeleri keşfetmeyi severler. Yemekte sade, pratik ama otantik lezzetleri tercih ederler; aşırı abartılı lüks akşam yemeklerinden uzak dururlar.",
            "ENTJ": "ENTJ'ler tatilde bile verimlilik ve stratejik planlama ararlar. Prestijli destinasyonları, lüks otelleri ve dünya standartlarında hizmet veren mekanları seçerler. Tarihi liderlik ve güç perspektifinden incelemeyi severler. Yemekte şef imzalı, ödüllü ve prestijli restoranlarda akşam yemeği tam onlara göredir; kalitesiz servisten ve amatör işletmelerden tamamen uzak dururlar.",
            "ENTP": "ENTP'ler rutin tatil rotalarını reddeden vizyon avcılarıdır. Startup kültürünün yoğun olduğu şehirleri, entelektüel tartışma kafelerini ve alternatif sanat galerilerini tercih ederler. Her seyahat yeni bir fikir tetiklemelidir. Yemekte daha önce duymadıkları malzemelerin birleştiği avangart tatları dener; monoton menülerden ve geleneksel adı altında kendini yenilemeyen mekanlardan nefret ederler.",
            "INFJ": "INFJ'ler için seyahat, içsel ve ruhsal bir derinleşme yolculuğudur. Yerel halkın yaşamına karışabilecekleri otantik mahalleleri, mistik tarihi ibadethaneleri ve sessiz doğa köşelerini severler. Yüzeysel turistik mekanlardan nefret ederler. Yemekte o bölgenin insanının gerçekte ne yediğini merak ederler; kültürel mirası güçlü geleneksel yemekleri tatmayı tercih ederler.",
            "INFP": "INFP'ler her şehirde bir masalın izini süren romantik gezginlerdir. Ünlü yazarların vakit geçirdiği tarihi kafeler, eski kitapçılar ve bohem mahalleler onlar için cennettir. Modern plazalardan ve endüstriyel şehirlerden nefret ederler. Yemekte mekanın ruhu yemeğin kendisi kadar önemlidir; mum ışığıyla aydınlatılmış, vintage sunumlu ve organik mekanlara giderler.",
            "ENFJ": "ENFJ'ler her destinasyonda insanları bir araya getiren rehberlerdir. Kültür takasının yapıldığı festivaller, yerel halk dansları ve sokak tiyatroları onları besler. İzole tatillerden nefret ederler. Yemekte büyük masalarda paylaşımlı sofraları, şefin gelip hikayesini anlattığı sıcak mekanları seçerler; bireysel tüketime odaklı soğuk ortamlardan hoşlanmazlar.",
            "ENFP": "ENFP'ler için seyahat, tüm planları yırtıp spontane hareket etmek demektir. Sokak müzisyenleri, renkli lokal pazarlar ve enerjik festivaller tam onlara göredir. Her dakikası belirlenmiş turlardan nefret ederler. Gastronomide sokak lezzetlerini, gece pazarlarını ve festival yemeklerini tercih ederler; protokol kuralları olan lüks akşam yemeklerinden uzak dururlar.",
            "ISTJ": "ISTJ'ler için mükemmel seyahat, milimetrik düzen ve önceden test edilmiş bir programa bağlıdır. Tarihi mekanları ve belgelenmiş anıtları özenle araştırırlar. Son dakika sürprizlerinden ve plansız değişikliklerden nefret ederler. Yemekte ne yiyeceklerini önceden bilmek isterler; kalitesi kanıtlanmış, tanıdık yerel tatlar onların ana tercihidir.",
            "ISFJ": "ISFJ'ler güvenli, sıcak ve aile dostu ortamlar ararlar. Nostaljik eski kasabaları, el sanatları pazarlarını ve huzurlu sahil köylerini tercih ederler. Ekstrem sporlardan ve kaotik metropollerden nefret ederler. Yemekte ev yapımı sıcaklığını yansıtan, nesilden nesile aktarılan geleneksel tarifleri ve yerel aile işletmelerini seçerler.",
            "ESTJ": "ESTJ'ler seyahatin her anında tam kontrol sağlamak isteyen gerçek organizatörlerdir. Net şekilde organize şehir turlarını ve tarihi anıtları checklist mantığıyla gezerler. Zaman kaybına neden olan plansızlıktan nefret ederler. Yemekte saygınlığı yüksek, menüsü belirli standartlara oturtulmuş restoranlarda düzenli menüleri tercih ederler.",
            "ESFJ": "ESFJ'ler seyahati sosyal paylaşım ve kolektif eğlence aracı olarak görürler. Şehrin en canlı caddelerini, fotojenik meydanları ve eğlenceli turistik mekanları severler. Yalnız kalmaktan ve ıssız yerlerden nefret ederler. Yemekte sunumu şık, fotoğraflanmaya uygun ve herkesin ortaklaşa paylaştığı büyük tabakları (tapas, meze) tercih ederler.",
            "ISTP": "ISTP'ler fiziksel aksiyonu ve doğanın zorluklarıyla mücadeleyi seven özgür kaşiflerdir. Dağ trekkingi, kamp ve motosikletle bilinmeyen yollara sapmak tam onların tatil tanımıdır. Pasif otobüs turlarından ve alışveriş merkezlerinden nefret ederler. Yemekte faydacı ve pratiktirler; enerji verecek doyurucu lezzetleri seçer, sıra beklemekten hoşlanmazlar.",
            "ISFP": "ISFP'ler dünyayı gözleri ve kalpleriyle hisseden estetik duyarlılığı yüksek sanatçı gezginlerdir. Yerel sanat galerileri, el sanatları atölyeleri ve mimari estetiği olan eski sokaklar onları büyüler. Aceleye getirilmiş turlardan nefret ederler. Yemekte tabağın bir sanat eseri gibi tasarlandığı, renk uyumlu ve organik malzemelerin kullanıldığı butik kafeleri seçerler.",
            "ESTP": "ESTP'ler için durağan bir tatil tam anlamıyla bir kabustur. Adrenalin dolu macera sporları, sabaha kadar süren gece hayatı ve hızlı şehir keşifleri onların kan grubudur. Müze saatlerinden ve yavaş tempolu turlardan nefret ederler. Yemekte acılı, baharatlı ve enerji veren hızlı lezzetleri severler; açık mutfakta alevli gösteriler sunan restoranlar ilgilerini çeker.",
            "ESFP": "ESFP'ler ayak bastıkları her destinasyonu devasa bir eğlence sahnesine dönüştüren hayat dolu turistlerdir. Büyük müzik festivalleri, plaj partileri ve karnavallar onların seyahat dilidir. Kasvetli tarihi kalıntılardan ve yalnız rotalardan nefret ederler. Gastronomide renk, canlılık ve yüksek enerji ararlar; müzikli, neşeli ve arkadaşlarla paylaşılabilecek eğlenceli sofralar tam onlara göredir."
        }

        blog_text = MBTI_BLOG.get(mbti_cur,
            "Seyahat tarzınız tamamen kendinize özgü. "
            "Bu profil size en uygun destinasyonları belirlemek için kullanılacak.")

        renk_map = {
            "INTJ": "#6d28d9", "INTP": "#7c3aed", "ENTJ": "#4338ca", "ENTP": "#2563eb",
            "INFJ": "#0891b2", "INFP": "#0d9488", "ENFJ": "#059669", "ENFP": "#65a30d",
            "ISTJ": "#ca8a04", "ISFJ": "#d97706", "ESTJ": "#dc2626", "ESFJ": "#e11d48",
            "ISTP": "#0284c7", "ISFP": "#7c3aed", "ESTP": "#ea580c", "ESFP": "#db2777",
        }
        renk = renk_map.get(mbti_cur, "#4f46e5")

        st.markdown(f"""
        <div style="border-radius:16px;overflow:hidden;
                    box-shadow:0 4px 20px rgba(0,0,0,0.08)">
          <div style="background:linear-gradient(150deg,{renk} 0%,{renk}cc 60%,{renk}88 100%);
                      padding:24px;color:white;position:relative">
            <div style="position:absolute;top:0;right:0;width:120px;height:120px;
                        background:rgba(255,255,255,0.06);border-radius:50%;
                        transform:translate(30px,-30px)"></div>
            <div style="position:absolute;bottom:0;right:40px;width:70px;height:70px;
                        background:rgba(255,255,255,0.06);border-radius:50%;
                        transform:translateY(20px)"></div>
            <div style="font-size:10px;opacity:0.7;font-weight:700;letter-spacing:0.8px;
                        text-transform:uppercase;margin-bottom:8px">Aktif Profil</div>
            <div style="font-size:36px;font-weight:900;letter-spacing:-1px;line-height:1">{mbti_cur}</div>
            <div style="font-size:13px;opacity:0.88;margin-top:8px;font-weight:500;
                        padding-top:10px;border-top:1px solid rgba(255,255,255,0.2)">{arch_cur}</div>
          </div>
          <div style="background:white;border:1px solid #e5e7eb;border-top:none;
                      border-radius:0 0 16px 16px;padding:18px">
            <div style="font-size:10px;font-weight:700;color:{renk};text-transform:uppercase;
                        letter-spacing:0.6px;margin-bottom:10px;padding-bottom:8px;
                        border-bottom:1px solid #f3f4f6">Seyahat Tarzınız</div>
            <div style="font-size:13px;color:#374151;line-height:1.75">{blog_text}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif cur == 3:
    step_indicator(NAV_ITEMS, 3)

    if not st.session_state.last_plan:
        page_header("Plan Sonucu", "Henüz bir plan oluşturulmadı")
        st.markdown('<div style="padding:16px 32px">', unsafe_allow_html=True)
        st.markdown("""
        <div class="animate-fadein" style="text-align:center;padding:48px 24px">
          <div style="width:80px;height:80px;border-radius:24px;
                      background:linear-gradient(135deg,#ede9fe,#ddd6fe);
                      display:flex;align-items:center;justify-content:center;
                      font-size:36px;margin:0 auto 20px">🗺️</div>
          <h3 style="font-size:18px;font-weight:700;color:#111827;margin:0 0 8px">
            Henüz Plan Yok
          </h3>
          <p style="font-size:13px;color:#6b7280;margin:0 auto 24px;max-width:360px;line-height:1.7">
            Rota Formu sekmesinden destinasyonunuzu girerek yapay zeka destekli
            seyahat planınızı oluşturabilirsiniz.
          </p>
        </div>
        """, unsafe_allow_html=True)
        nav_arrows("Rota Formuna Git", 2)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        import re

        plan    = st.session_state.last_plan
        t_d2    = st.session_state.last_t_data or {}
        dest_up = t_d2.get("destination", "?").capitalize()
        bas2    = t_d2.get("start_date", "")
        bit2    = t_d2.get("end_date", "")
        kisi2   = t_d2.get("group_size", 1)
        trans2  = t_d2.get("transport", "")
        mbti2   = t_d2.get("user_profile", {}).get("mbti_type", "")
        days2   = plan.get("duration_days", 1)
        cost2   = float(plan.get("estimated_cost") or 0)
        gun_str = f"{days2} gün"

        def _clean_html(raw: str) -> str:
            c = raw.strip()
            if c.startswith("```"):
                c = c.split("\n", 1)[-1]
            if c.endswith("```"):
                c = c[:-3].rstrip()
            if c.lower().startswith("html\n"):
                c = c[5:]
            c = re.sub(r'^[\w\-]+\s*:\s*[^<\n]+\)\s*"?\s*>', '', c.strip(), flags=re.MULTILINE)
            return c.strip()

        import streamlit.components.v1 as _stcomp

        mbti_renk = {
            "INTJ":"#6d28d9","INTP":"#7c3aed","ENTJ":"#4338ca","ENTP":"#2563eb",
            "INFJ":"#0891b2","INFP":"#0d9488","ENFJ":"#059669","ENFP":"#65a30d",
            "ISTJ":"#ca8a04","ISFJ":"#d97706","ESTJ":"#dc2626","ESFJ":"#e11d48",
            "ISTP":"#0284c7","ISFP":"#7c3aed","ESTP":"#ea580c","ESFP":"#db2777",
        }.get(mbti2, "#4f46e5")

        dest_harf = dest_up[0].upper() if dest_up else "?"

        gun_noktalari = "".join([
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:4px">'
            f'<div style="width:10px;height:10px;border-radius:50%;'
            f'background:rgba(255,255,255,{round(0.4+0.12*min(i,4),2)});'
            f'border:2px solid rgba(255,255,255,0.6)"></div>'
            + (f'<div style="width:1px;height:18px;background:rgba(255,255,255,0.25)"></div>' if i < int(days2)-1 else '')
            + f'</div>'
            for i in range(min(int(days2), 7))
        ])

        mbti_chip = (f'<span style="background:{mbti_renk}44;border:1px solid {mbti_renk}88;'
                     f'border-radius:20px;padding:3px 11px;font-size:11px;font-weight:700;color:white">'
                     f'{mbti2}</span>') if mbti2 else ""

        header_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
body{{background:transparent;padding:20px 32px 0}}
.card{{background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 45%,#312e81 100%);
       border-radius:20px;overflow:hidden;box-shadow:0 8px 32px rgba(15,23,42,0.35);
       position:relative}}
.inner{{position:relative;padding:28px 32px;display:flex;
        justify-content:space-between;align-items:center;gap:20px}}
.avatar{{flex-shrink:0;width:72px;height:72px;border-radius:18px;
         background:linear-gradient(135deg,{mbti_renk},{mbti_renk}88);
         display:flex;align-items:center;justify-content:center;
         font-size:32px;font-weight:900;color:white;box-shadow:0 4px 16px {mbti_renk}66}}
.chip{{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);
       border-radius:20px;padding:3px 11px;font-size:11px;font-weight:600;color:white;
       display:inline-block;margin:2px}}
.cost-box{{background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);
           border-radius:16px;padding:18px 24px;text-align:right;flex-shrink:0}}
</style></head><body>
<div class="card">
  <svg style="position:absolute;top:0;left:0;width:100%;height:100%;opacity:0.06;pointer-events:none"
       viewBox="0 0 900 180" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
    <circle cx="750" cy="20" r="130" fill="white"/>
    <circle cx="800" cy="170" r="90" fill="white"/>
    <circle cx="60" cy="160" r="70" fill="white"/>
    <line x1="0" y1="90" x2="900" y2="90" stroke="white" stroke-width="0.6" stroke-dasharray="6 12"/>
  </svg>
  <div class="inner">
    <div style="display:flex;align-items:center;gap:24px;flex:1;min-width:0">
      <div class="avatar">{dest_harf}</div>
      <div style="min-width:0">
        <div style="font-size:10px;color:rgba(255,255,255,0.5);font-weight:700;
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Seyahat Planı</div>
        <div style="font-size:32px;font-weight:900;color:white;letter-spacing:-1px;
                    line-height:1;margin-bottom:12px;white-space:nowrap;
                    overflow:hidden;text-overflow:ellipsis">{dest_up}</div>
        <div>
          <span class="chip">{bas2} — {bit2}</span>
          <span class="chip">{gun_str}</span>
          <span class="chip">{trans2}</span>
          {mbti_chip}
        </div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:20px">
      <div style="display:flex;flex-direction:column;align-items:center;opacity:0.7">
        {gun_noktalari}
      </div>
      <div class="cost-box">
        <div style="font-size:10px;color:rgba(255,255,255,0.55);text-transform:uppercase;
                    letter-spacing:0.6px;margin-bottom:6px">Tahmini Maliyet</div>
        <div style="font-size:28px;font-weight:900;color:white;letter-spacing:-1px;line-height:1">
          {cost2:,.0f}</div>
        <div style="font-size:11px;color:rgba(255,255,255,0.5);margin-top:4px">TL · {kisi2} kişi</div>
      </div>
    </div>
  </div>
</div>
</body></html>"""
        _stcomp.html(header_html, height=200, scrolling=False)

        st.markdown('<div style="padding:0 32px">', unsafe_allow_html=True)

        report_raw = (plan.get("transport_details") or plan.get("description") or plan.get("plan") or "")
        clean_html = _clean_html(report_raw) if report_raw else ""

        gezi_count  = len(re.findall(r'data-type=["\']gezi["\']', clean_html))
        yemek_count = len(re.findall(r'data-type=["\']yemek["\']', clean_html))
        kart_count  = len(re.findall(r'class=["\']aktivite-kart["\']', clean_html))

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px">
          <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;
                      text-align:center;border-top:3px solid #4f46e5">
            <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Toplam Gün</div>
            <div style="font-size:28px;font-weight:900;color:#4f46e5;line-height:1">{days2}</div>
          </div>
          <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;
                      text-align:center;border-top:3px solid #059669">
            <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Gezi Durağı</div>
            <div style="font-size:28px;font-weight:900;color:#059669;line-height:1">{gezi_count or "—"}</div>
          </div>
          <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;
                      text-align:center;border-top:3px solid #ea580c">
            <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Yemek Durağı</div>
            <div style="font-size:28px;font-weight:900;color:#ea580c;line-height:1">{yemek_count or "—"}</div>
          </div>
          <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:16px;
                      text-align:center;border-top:3px solid #0891b2">
            <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Kişi Sayısı</div>
            <div style="font-size:28px;font-weight:900;color:#0891b2;line-height:1">{kisi2}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        DEST_BILGI = {
            "istanbul":  {"dil":"Türkçe","para":"TL (₺)","zaman":"UTC+3","hava":"Yazın sıcak, kışın ılık","vize":"Kimlik kartı yeterli"},
            "ankara":    {"dil":"Türkçe","para":"TL (₺)","zaman":"UTC+3","hava":"Karasal, 4 mevsim","vize":"Kimlik kartı yeterli"},
            "izmir":     {"dil":"Türkçe","para":"TL (₺)","zaman":"UTC+3","hava":"Akdeniz, yazın çok sıcak","vize":"Kimlik kartı yeterli"},
            "antalya":   {"dil":"Türkçe","para":"TL (₺)","zaman":"UTC+3","hava":"Akdeniz, yıl boyu sıcak","vize":"Kimlik kartı yeterli"},
            "roma":      {"dil":"İtalyanca","para":"Euro (€)","zaman":"UTC+1/+2","hava":"Akdeniz, yazın kuru sıcak","vize":"Pasaport (Schengen)"},
            "paris":     {"dil":"Fransızca","para":"Euro (€)","zaman":"UTC+1/+2","hava":"Ilıman, yaz sıcak kış soğuk","vize":"Pasaport (Schengen)"},
            "barcelona": {"dil":"İspanyolca/Katalanca","para":"Euro (€)","zaman":"UTC+1/+2","hava":"Akdeniz, yazın sıcak","vize":"Pasaport (Schengen)"},
            "amsterdam": {"dil":"Hollandaca","para":"Euro (€)","zaman":"UTC+1/+2","hava":"Serin ve yağışlı","vize":"Pasaport (Schengen)"},
            "prag":      {"dil":"Çekçe","para":"Çek Korunası","zaman":"UTC+1/+2","hava":"4 mevsim belirgin","vize":"Pasaport (Schengen)"},
            "viyana":    {"dil":"Almanca","para":"Euro (€)","zaman":"UTC+1/+2","hava":"4 mevsim belirgin","vize":"Pasaport (Schengen)"},
            "londra":    {"dil":"İngilizce","para":"Sterlin (£)","zaman":"UTC+0/+1","hava":"Serin ve yağışlı","vize":"Pasaport + ETA"},
            "dubai":     {"dil":"Arapça/İngilizce","para":"AED (د.إ)","zaman":"UTC+4","hava":"Çöl, yazın çok sıcak","vize":"30 gün vizesiz"},
            "tokyo":     {"dil":"Japonca","para":"Yen (¥)","zaman":"UTC+9","hava":"4 mevsim, yazın nemli","vize":"90 gün vizesiz"},
            "bangkok":   {"dil":"Tayca","para":"Baht (฿)","zaman":"UTC+7","hava":"Tropikal, yüksek nem","vize":"30 gün vizesiz"},
            "marakes":   {"dil":"Arapça/Fransızca","para":"Dirhem (MAD)","zaman":"UTC+1","hava":"Yarı-kurak, yazın çok sıcak","vize":"90 gün vizesiz"},
            "atina":     {"dil":"Yunanca","para":"Euro (€)","zaman":"UTC+2/+3","hava":"Akdeniz, yazın çok sıcak","vize":"Pasaport (Schengen)"},
            "budapeste": {"dil":"Macarca","para":"Forint (Ft)","zaman":"UTC+1/+2","hava":"4 mevsim belirgin","vize":"Pasaport (Schengen)"},
            "tiflis":    {"dil":"Gürcüce","para":"Lari (₾)","zaman":"UTC+4","hava":"Ilıman, 4 mevsim","vize":"365 gün vizesiz"},
            "new york":  {"dil":"İngilizce","para":"Dolar ($)","zaman":"UTC-5/-4","hava":"4 mevsim belirgin","vize":"ESTA zorunlu"},
            "singapur":  {"dil":"İngilizce/Çince","para":"SGD ($)","zaman":"UTC+8","hava":"Tropikal, sıcak ve nemli","vize":"30 gün vizesiz"},
        }
        dest_key2 = dest_up.lower().replace("ı","i").replace("ş","s").replace("ğ","g").replace("ü","u").replace("ö","o").replace("ç","c")
        bilgi = next((v for k,v in DEST_BILGI.items() if k in dest_key2 or dest_key2.startswith(k)), None)

        if bilgi:
            badges = "".join([
                f'<div style="background:#f8faff;border:1px solid #e0e7ff;border-radius:10px;'
                f'padding:10px 14px;display:flex;justify-content:space-between;align-items:center">'
                f'<span style="font-size:11px;color:#6b7280;font-weight:600">{k}</span>'
                f'<span style="font-size:12px;color:#111827;font-weight:500">{v}</span></div>'
                for k,v in [("Dil",bilgi["dil"]),("Para Birimi",bilgi["para"]),
                             ("Zaman Dilimi",bilgi["zaman"]),("İklim",bilgi["hava"])]
            ])
            st.markdown(f"""
            <div style="background:white;border:1px solid #e5e7eb;border-radius:14px;
                        padding:20px;margin-bottom:20px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
                <span style="font-size:13px;font-weight:700;color:#111827">{dest_up} Hakkında</span>
                <span style="background:#f0fdf4;color:#059669;font-size:11px;font-weight:700;
                             padding:3px 10px;border-radius:20px;border:1px solid #bbf7d0">
                  Vize: {bilgi["vize"]}
                </span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px">
                {badges}
              </div>
            </div>
            """, unsafe_allow_html=True)

        galeri_urls = _wiki_landmark_urls(dest_up)

        if galeri_urls:
            cid = "carousel_" + dest_up.lower().replace(" ","_")
            imgs_html = "".join([
                f'<div style="flex:0 0 auto;height:320px;width:480px;border-radius:12px;'
                f'overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.18)">'
                f'<img src="{u}" style="width:100%;height:100%;object-fit:cover;display:block;'
                f'filter:sepia(10%) saturate(92%) brightness(1.03);transition:transform .5s ease" '
                f'onmouseover="this.style.transform=\'scale(1.04)\'" '
                f'onmouseout="this.style.transform=\'scale(1)\'" '
                f'onerror="this.parentElement.style.display=\'none\'"/></div>'
                for u in galeri_urls
            ])
            st.markdown(f"""
            <div style="position:relative;margin-bottom:24px;user-select:none">
              <!-- Sol ok -->
              <button onclick="document.getElementById('{cid}').scrollBy({{left:-500,behavior:'smooth'}})"
                style="position:absolute;left:-16px;top:50%;transform:translateY(-50%);z-index:10;
                       width:40px;height:40px;border-radius:50%;border:none;cursor:pointer;
                       background:white;box-shadow:0 2px 10px rgba(0,0,0,0.18);
                       font-size:18px;color:#2d2420;display:flex;align-items:center;justify-content:center;
                       transition:box-shadow .2s"
                onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.28)'"
                onmouseout="this.style.boxShadow='0 2px 10px rgba(0,0,0,0.18)'">&#8249;</button>

              <!-- Carousel -->
              <div id="{cid}"
                style="display:flex;gap:10px;overflow-x:auto;scroll-behavior:smooth;
                       padding:4px 2px 8px;
                       scrollbar-width:none;-ms-overflow-style:none">
                {imgs_html}
              </div>
              <style>#{cid}::-webkit-scrollbar{{display:none}}</style>

              <!-- Sağ ok -->
              <button onclick="document.getElementById('{cid}').scrollBy({{left:500,behavior:'smooth'}})"
                style="position:absolute;right:-16px;top:50%;transform:translateY(-50%);z-index:10;
                       width:40px;height:40px;border-radius:50%;border:none;cursor:pointer;
                       background:white;box-shadow:0 2px 10px rgba(0,0,0,0.18);
                       font-size:18px;color:#2d2420;display:flex;align-items:center;justify-content:center;
                       transition:box-shadow .2s"
                onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.28)'"
                onmouseout="this.style.boxShadow='0 2px 10px rgba(0,0,0,0.18)'">&#8250;</button>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:20px'></div>", unsafe_allow_html=True)

        col_copy, _ = st.columns([1, 5])
        with col_copy:
            if st.button("Planı Kopyala", key="plan_kopyala", type="secondary"):
                plain = re.sub(r'<[^>]+>', ' ', clean_html)
                plain = re.sub(r' {3,}', '\n\n', plain).strip()
                st.session_state["_plan_copy_text"] = plain
                st.toast("Plan metni hazırlandı, aşağıdan kopyalayın.")

        if st.session_state.get("_plan_copy_text"):
            with st.expander("Plan metni (kopyalamak için tıkla)"):
                st.code(st.session_state["_plan_copy_text"], language=None)

        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

        if clean_html:
            style_m    = re.search(r'<style>.*?</style>', clean_html, re.DOTALL)
            style_block = style_m.group(0) if style_m else ""
            html_nosty = re.sub(r'<style>.*?</style>', '', clean_html, flags=re.DOTALL).strip()

            _RENK_MAP = {
                "gezi":      "#4f46e5",
                "yemek":     "#ea580c",
                "konaklama": "#059669",
                "genel":     "#0891b2",
            }
            for _tip, _renk in _RENK_MAP.items():
                for _q in (f'data-type="{_tip}"', f"data-type='{_tip}'"):
                    html_nosty = html_nosty.replace(
                        _q, f'data-type="{_tip}" style="border-left:4px solid {_renk}"'
                    )

            parcalar      = re.split(r'(?=<div[^>]*class=["\']gun-baslik["\'])', html_nosty)
            gun_icerikler = [p for p in parcalar if 'gun-baslik' in p]

            def _render_plan_html(body: str, style: str = "") -> None:
                st.html(f"{style}<style>body{{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}"
                        f"img{{max-width:100%;height:auto;display:block}}a{{color:#4f46e5}}</style>"
                        f"<div class='plan-container'>{body}</div>")

            if len(gun_icerikler) > 1:
                gun_isimleri = []
                for idx_g, gi in enumerate(gun_icerikler):
                    m2 = re.search(r'class=["\']gun-baslik["\'][^>]*>(.*?)</div>', gi, re.DOTALL)
                    raw_label = re.sub(r'<[^>]+>', '', m2.group(1)).strip() if m2 else ""
                    raw_label = raw_label[:25] or f"Gün {idx_g + 1}"
                    if raw_label in gun_isimleri:
                        raw_label = f"{raw_label} ({idx_g + 1})"
                    gun_isimleri.append(raw_label)

                tabs = st.tabs(gun_isimleri)
                for tab, icerik in zip(tabs, gun_icerikler):
                    with tab:
                        _render_plan_html(icerik, style_block)
            else:
                _render_plan_html(html_nosty, style_block)
        else:
            st.info("Plan içeriği henüz oluşturulmadı.")

        st.markdown('</div>', unsafe_allow_html=True)
        nav_arrows("ACO & Maliyet", 4, "Rota Formuna Dön", 2)

elif cur == 4:
    step_indicator(NAV_ITEMS, 4)
    page_header("ACO & Maliyet Analizi", "Rota optimizasyonu ve 2026 maliyet karşılaştırması")
    st.markdown('<div style="padding:16px 32px">', unsafe_allow_html=True)

    aco = st.session_state.last_aco
    mal = st.session_state.maliyet_result
    t_d = st.session_state.last_t_data or {}

    if not aco and not mal:
        st.markdown("""
        <div class="animate-fadein" style="text-align:center;padding:48px 24px">
          <div style="width:80px;height:80px;border-radius:24px;
                      background:linear-gradient(135deg,#ecfdf5,#d1fae5);
                      display:flex;align-items:center;justify-content:center;
                      font-size:36px;margin:0 auto 20px">📊</div>
          <h3 style="font-size:18px;font-weight:700;color:#111827;margin:0 0 8px">
            Analiz Hazır Değil
          </h3>
          <p style="font-size:13px;color:#6b7280;margin:0 auto 24px;max-width:360px;line-height:1.7">
            Önce Rota Formu sekmesinden bir seyahat planı oluşturun.
          </p>
        </div>
        """, unsafe_allow_html=True)
        nav_arrows("Rota Oluşturmaya Git", 2)
    else:
        dest = t_d.get("destination", "?").capitalize()
        locations = (
            (aco.get("optimized_route") or aco.get("locations") or
             [{"name": n} for n in aco.get("seyahat_rotasi_siralamasi", [])])
            if aco else []
        )
        opt_route = locations
        opt_path  = (aco.get("optimized_path",
                     [l.get("name","") if isinstance(l,dict) else str(l) for l in opt_route])
                     if aco else [])
        total_dist = float((aco.get("total_distance") or aco.get("tahmini_toplam_mesafe_km") or 0) if aco else 0)
        raw_score  = (aco.get("optimization_score") or aco.get("rota_uyumluluk_skoru","0")) if aco else 0
        try:
            score = float(str(raw_score).replace("%","")) / (100 if "%" in str(raw_score) else 1)
        except Exception:
            score = 0.0
        n = len(locations)
        mbti_p = t_d.get("user_profile", {}).get("mbti_type","?")

        col_aco, col_mal = st.columns([6, 4], gap="large")

        with col_aco:
            st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px">
  <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:14px;text-align:center;
              border-top:3px solid #4f46e5">
    <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Mekan</div>
    <div style="font-size:26px;font-weight:900;color:#4f46e5;line-height:1">{n}</div>
  </div>
  <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:14px;text-align:center;
              border-top:3px solid #0891b2">
    <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Mesafe</div>
    <div style="font-size:26px;font-weight:900;color:#0891b2;line-height:1">{total_dist:.0f}</div>
    <div style="font-size:10px;color:#9ca3af">km</div>
  </div>
  <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:14px;text-align:center;
              border-top:3px solid #059669">
    <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Skor</div>
    <div style="font-size:26px;font-weight:900;color:#059669;line-height:1">{int(score*100)}</div>
    <div style="font-size:10px;color:#9ca3af">/ 100</div>
  </div>
  <div style="background:linear-gradient(135deg,#4f46e5,#7c3aed);border-radius:12px;padding:14px;text-align:center">
    <div style="font-size:10px;color:rgba(255,255,255,0.7);margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">MBTI</div>
    <div style="font-size:20px;font-weight:900;color:white;line-height:1">{mbti_p}</div>
  </div>
</div>""", unsafe_allow_html=True)

            st.markdown(f"""
<div style="background:white;border:1px solid #e5e7eb;border-radius:12px 12px 0 0;
            padding:12px 16px;border-bottom:none">
  <div style="font-size:12px;font-weight:700;color:#111827;text-transform:uppercase;
              letter-spacing:0.4px">{dest} — Optimize Edilmiş Rota</div>
</div>""", unsafe_allow_html=True)
            if n > 0:
                rng = random.Random(sum(ord(c) for c in dest))
                svgW, svgH, pad = 480, 300, 50
                coords = []
                for i, loc in enumerate(locations):
                    angle = (2 * math.pi * i / n) + rng.uniform(-0.3, 0.3)
                    r     = rng.uniform(0.55, 0.85)
                    cx    = pad + (svgW - 2*pad) * (0.5 + r * math.cos(angle) * 0.42)
                    cy    = pad + (svgH - 2*pad) * (0.5 + r * math.sin(angle) * 0.38)
                    coords.append((cx, cy, loc.get("name","?")))

                route_idx = []
                for name in opt_path:
                    for i, loc in enumerate(locations):
                        if loc.get("name") == name:
                            route_idx.append(i); break
                if not route_idx:
                    route_idx = list(range(n))

                svg = [
                    f'<svg viewBox="0 0 {svgW} {svgH}" xmlns="http://www.w3.org/2000/svg" ',
                    f'style="width:100%;background:white;border-radius:0 0 12px 12px;border:1px solid #e5e7eb;border-top:none;margin-bottom:16px">',
                    '<defs><pattern id="gg" width="28" height="28" patternUnits="userSpaceOnUse">',
                    '<path d="M 28 0 L 0 0 0 28" fill="none" stroke="#f3f4f6" stroke-width="0.7"/>',
                    '</pattern></defs>',
                    f'<rect width="{svgW}" height="{svgH}" fill="url(#gg)"/>',
                ]
                for i in range(n):
                    for j in range(i+1, n):
                        x1,y1,_ = coords[i]; x2,y2,_ = coords[j]
                        svg.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#f0f0f0" stroke-width="1"/>')
                for k in range(len(route_idx)):
                    i1 = route_idx[k]; i2 = route_idx[(k+1)%len(route_idx)]
                    x1,y1,_ = coords[i1]; x2,y2,_ = coords[i2]
                    dx,dy = x2-x1,y2-y1; d = math.sqrt(dx**2+dy**2) or 1
                    ux,uy = dx/d,dy/d; mx=(x1+x2)/2-uy*12; my=(y1+y2)/2+ux*12
                    svg.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#4f46e5" stroke-width="2" opacity="0.75" stroke-dasharray="7,4"><animate attributeName="stroke-dashoffset" from="0" to="-22" dur="1.4s" repeatCount="indefinite"/></line>')
                    svg.append(f'<polygon points="{mx:.0f},{my:.0f} {mx-uy*5-ux*7:.0f},{my+ux*5-uy*7:.0f} {mx+uy*5-ux*7:.0f},{my-ux*5-uy*7:.0f}" fill="#4f46e5" opacity="0.65"/>')

                TIP_C = {"kultur":"#6b7280","doga":"#6b7280","alisveris":"#6b7280","sosyal":"#6b7280","genel":"#6b7280"}
                for idx2,(cx,cy,lname) in enumerate(coords):
                    lt   = locations[idx2].get("type","genel") if idx2<len(locations) else "genel"
                    rc   = TIP_C.get(lt,"#6b7280")
                    sira = route_idx.index(idx2)+1 if idx2 in route_idx else "-"
                    if route_idx and route_idx[0]==idx2:
                        svg.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="22" fill="none" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="4,2"/>')
                    svg.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="16" fill="white" stroke="#e5e7eb" stroke-width="2"/>')
                    svg.append(f'<text x="{cx:.0f}" y="{cy+4:.0f}" text-anchor="middle" fill="#374151" font-size="10" font-weight="700">{sira}</text>')
                    kisa = lname[:10]+"..." if len(lname)>10 else lname
                    ly   = cy+30 if cy<svgH-40 else cy-20
                    svg.append(f'<text x="{cx:.0f}" y="{ly:.0f}" text-anchor="middle" fill="#6b7280" font-size="8">{kisa}</text>')
                svg.append("</svg>")
                st.markdown("".join(svg), unsafe_allow_html=True)

            st.markdown('<div style="font-size:11px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:0.4px;margin:16px 0 8px">Sıralı Rota</div>', unsafe_allow_html=True)
            TIP_RENK = {"kultur":"#7c3aed","doga":"#059669","alisveris":"#d97706","sosyal":"#0891b2","genel":"#6b7280"}
            for step, name in enumerate(opt_path):
                lo   = next((l for l in locations if l.get("name")==name), {})
                cv   = lo.get("cost", 0)
                dv   = lo.get("duration", 2)
                lt   = lo.get("type", "genel")
                rc   = TIP_RENK.get(lt, "#6b7280")
                lbl  = "Başlangıç" if step == 0 else ("Son Durak" if step == len(opt_path)-1 else f"{step+1}. Durak")
                st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;background:white;
            border:1px solid #e5e7eb;border-left:3px solid {rc};
            border-radius:10px;padding:10px 14px;margin-bottom:6px">
  <div style="min-width:26px;height:26px;border-radius:50%;background:{rc};
              display:flex;align-items:center;justify-content:center;
              font-size:10px;font-weight:800;color:white;flex-shrink:0">
    {step+1}
  </div>
  <div style="flex:1">
    <div style="font-size:12px;font-weight:600;color:#111827">{name}</div>
    <div style="font-size:11px;color:#9ca3af;margin-top:1px">{lbl}</div>
  </div>
  <div style="text-align:right">
    <div style="font-size:11px;font-weight:600;color:#374151">{dv} sa</div>
    <div style="font-size:11px;color:#9ca3af;margin-top:1px">{"Ücretsiz" if cv==0 else str(cv)+" TL"}</div>
  </div>
</div>""", unsafe_allow_html=True)

            st.markdown('<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px">', unsafe_allow_html=True)
            for baslik, renk, satirlar in [
                ("ACO Parametreleri", "#4f46e5", [
                    ("Karınca Sayısı", "10"),
                    ("İterasyon",      "5"),
                    ("Buharlaşma",     "0.50"),
                    ("Feromon α",      "1.0"),
                    ("Mesafe β",       "2.0"),
                ]),
                ("Optimizasyon Sonuçları", "#059669", [
                    ("Toplam Mekan",   str(n)),
                    ("Toplam Mesafe",  f"{total_dist:.1f} km"),
                    ("Uyum Skoru",     f"{int(score*100)} / 100"),
                    ("MBTI Profili",   mbti_p),
                    ("Geçmiş Kayıt",   f"{len(t_d.get('travel_history',[]))} adet"),
                ]),
            ]:
                satirlar_html = "".join(
                    f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                    f'border-bottom:1px solid #f3f4f6">'
                    f'<span style="font-size:12px;color:#6b7280">{k}</span>'
                    f'<span style="font-size:12px;font-weight:700;color:#111827">{v}</span>'
                    f'</div>'
                    for k, v in satirlar
                )
                st.markdown(f"""
<div style="background:white;border:1px solid #e5e7eb;border-radius:12px;
            padding:16px;border-top:3px solid {renk}">
  <div style="font-size:10px;font-weight:700;color:{renk};margin-bottom:12px;
              text-transform:uppercase;letter-spacing:0.5px">{baslik}</div>
  {satirlar_html}
</div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_mal:
            if not mal:
                st.markdown("""
<div style="background:white;border:1px solid #e5e7eb;border-radius:12px;
            padding:32px;text-align:center;color:#9ca3af;font-size:13px">
  Maliyet verisi henüz yok.
</div>""", unsafe_allow_html=True)
            else:
                if mal.get("uyari"):
                    st.warning(mal["uyari"])

                std  = mal["standart_plan"]
                oz   = mal["ozel_plan"]
                tas  = mal["tasarruf_tl"]
                yuz  = mal["tasarruf_yuzde"]

                st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px">
  <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:14px;text-align:center;
              border-top:3px solid #9ca3af">
    <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Standart</div>
    <div style="font-size:15px;font-weight:800;color:#9ca3af;text-decoration:line-through">{std["toplam"]:,.0f}</div>
    <div style="font-size:10px;color:#9ca3af">TL</div>
  </div>
  <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:14px;text-align:center;
              border-top:3px solid #4f46e5">
    <div style="font-size:10px;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Kişisel</div>
    <div style="font-size:15px;font-weight:800;color:#111827">{oz["toplam"]:,.0f}</div>
    <div style="font-size:10px;color:#9ca3af">TL</div>
  </div>
  <div style="background:linear-gradient(135deg,#ecfdf5,#d1fae5);border:1px solid #6ee7b7;
              border-radius:12px;padding:14px;text-align:center">
    <div style="font-size:10px;color:#059669;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.4px">Tasarruf</div>
    <div style="font-size:15px;font-weight:800;color:#059669">%{yuz:.1f}</div>
    <div style="font-size:10px;color:#059669">{tas:,.0f} TL</div>
  </div>
</div>""", unsafe_allow_html=True)

                kalemler = [
                    ("Konaklama",        "konaklama"),
                    ("Yemek",            "yemek"),
                    ("Şehir İçi Ulaşım", "sehir_ulasim"),
                    ("Aktivite",         "aktivite"),
                    ("Şehirlerarası",    "sehirlerarasi"),
                ]
                BAR_RENKLER = {
                    "konaklama":    "#4f46e5",
                    "yemek":        "#0891b2",
                    "sehir_ulasim": "#d97706",
                    "aktivite":     "#7c3aed",
                    "sehirlerarasi":"#059669",
                }
                satirlar_html = ""
                for label, key in kalemler:
                    sv    = std.get(key, 0)
                    ov    = oz.get(key, 0)
                    bar_w = max(4, round(ov/sv*100)) if sv > 0 else 100
                    brenk = BAR_RENKLER.get(key, "#4f46e5")
                    satirlar_html += f"""
<div style="padding:10px 0;border-bottom:1px solid #f3f4f6">
  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
    <span style="font-size:12px;color:#374151;font-weight:500">{label}</span>
    <div style="text-align:right">
      <span style="font-size:11px;color:#9ca3af;text-decoration:line-through">{sv:,.0f}</span>
      <span style="font-size:12px;font-weight:700;color:#111827;margin-left:6px">{ov:,.0f} TL</span>
    </div>
  </div>
  <div style="background:#f3f4f6;border-radius:4px;height:5px">
    <div style="background:linear-gradient(90deg,{brenk},{brenk}99);border-radius:4px;height:5px;width:{bar_w}%"></div>
  </div>
</div>"""

                tot_html = f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:12px 0 0;margin-top:4px">
  <span style="font-size:13px;font-weight:700;color:#111827">Toplam</span>
  <div>
    <span style="font-size:12px;color:#9ca3af;text-decoration:line-through">{std["toplam"]:,.0f}</span>
    <span style="font-size:15px;font-weight:800;color:#111827;margin-left:8px">{oz["toplam"]:,.0f} TL</span>
  </div>
</div>"""

                st.markdown(f"""
<div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:18px;margin-bottom:14px">
  <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:4px;
              text-transform:uppercase;letter-spacing:0.4px">Maliyet Kalemleri</div>
  {satirlar_html}
  {tot_html}
</div>""", unsafe_allow_html=True)

                st.markdown(f"""
<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;
            padding:14px 18px;text-align:center;margin-bottom:14px">
  <div style="font-size:11px;color:#059669;font-weight:600;text-transform:uppercase;
              letter-spacing:0.4px;margin-bottom:4px">Toplam Tasarruf</div>
  <div style="font-size:22px;font-weight:800;color:#059669">{tas:,.0f} TL</div>
  <div style="font-size:12px;color:#6b7280;margin-top:2px">Standart plana göre %{yuz:.1f} daha ekonomik</div>
</div>""", unsafe_allow_html=True)

                detayli = mal.get("detayli_maliyet_analizi","")
                if detayli:
                    lines = [l.strip() for l in detayli.strip().splitlines() if l.strip()]
                    satirlar_d = ""
                    for line in lines:
                        if line.startswith("###"):
                            satirlar_d += f'<div style="font-size:12px;font-weight:700;color:#111827;margin:10px 0 4px">{line.lstrip("#").strip()}</div>'
                        elif line.startswith("##"):
                            pass  # ana başlık — zaten kart başlığında
                        elif line.startswith("-"):
                            txt = line.lstrip("- ").strip()
                            satirlar_d += f'<div style="font-size:12px;color:#374151;padding:3px 0;border-bottom:1px solid #f9fafb;display:flex;gap:6px"><span style="color:#9ca3af;flex-shrink:0">›</span><span>{txt}</span></div>'
                        elif ":" in line and not line.startswith("**"):
                            parts = line.split(":",1)
                            satirlar_d += f'<div style="font-size:12px;color:#374151;padding:3px 0;border-bottom:1px solid #f9fafb;display:flex;justify-content:space-between"><span style="color:#6b7280">{parts[0].strip()}</span><span style="font-weight:600">{parts[1].strip()}</span></div>'
                        else:
                            clean = line.replace("**","")
                            if clean:
                                satirlar_d += f'<div style="font-size:11px;color:#9ca3af;margin:4px 0">{clean}</div>'

                    st.markdown(f"""
<div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:18px">
  <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:10px;
              text-transform:uppercase;letter-spacing:0.4px">Detaylı Kalem Analizi</div>
  {satirlar_d}
</div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        _col_restart, _col_nav = st.columns([1, 3])
        with _col_restart:
            if st.button("🔄  Testi Yeniden Çöz", key="restart_test", use_container_width=True):
                st.session_state.mbti_completed  = False
                st.session_state.user_data["mbti_type"] = ""
                st.session_state.mbti_archetype  = ""
                st.session_state.mbti_report     = ""
                st.session_state.current_tab     = 0
                _mbti_profil_kaydet(st.session_state.username, {})
                st.rerun()
        nav_arrows("Seyahat Geçmişi", 5, "Plan Sonucuna Dön", 3)

    st.markdown('</div>', unsafe_allow_html=True)

elif cur == 5:
    step_indicator(NAV_ITEMS, 5)
    page_header("Seyahat Geçmişim", "Tüm planlanmış seyahatleriniz ve analizleriniz")

    gecmis = st.session_state.get("travel_history", [])

    if not gecmis:
        st.markdown("""
<div style="padding:60px 32px;text-align:center">
  <div style="font-size:48px;margin-bottom:16px">🗺️</div>
  <div style="font-size:18px;font-weight:700;color:#111827;margin-bottom:8px">Henüz seyahat kaydın yok</div>
  <div style="font-size:13px;color:#6b7280">İlk planını oluşturduğunda burada görünecek.</div>
</div>""", unsafe_allow_html=True)
    else:
        _mbti_h = st.session_state.user_data.get("mbti_type", "")
        _renk_h_map = {
            "INTJ":"#6d28d9","INTP":"#7c3aed","ENTJ":"#4338ca","ENTP":"#2563eb",
            "INFJ":"#0891b2","INFP":"#0d9488","ENFJ":"#059669","ENFP":"#65a30d",
            "ISTJ":"#ca8a04","ISFJ":"#d97706","ESTJ":"#dc2626","ESFJ":"#e11d48",
            "ISTP":"#0284c7","ISFP":"#7c3aed","ESTP":"#ea580c","ESFP":"#db2777",
        }
        _renk_h = _renk_h_map.get(_mbti_h, "#4f46e5")

        toplam_plan = len(gecmis)
        dest_set    = set(g.get("destination","").capitalize() for g in gecmis if g.get("destination"))
        _arch_h     = st.session_state.mbti_archetype or ""

        st.markdown(f"""
<div style="padding:0 32px 20px">
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:24px">
    <div style="background:linear-gradient(135deg,{_renk_h},{_renk_h}bb);border-radius:16px;
                padding:20px 24px;color:white;text-align:center">
      <div style="font-size:36px;font-weight:900;line-height:1">{toplam_plan}</div>
      <div style="font-size:11px;opacity:0.8;margin-top:6px;font-weight:600">Toplam Plan</div>
    </div>
    <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;
                padding:20px 24px;text-align:center">
      <div style="font-size:36px;font-weight:900;color:#111827;line-height:1">{len(dest_set)}</div>
      <div style="font-size:11px;color:#6b7280;margin-top:6px;font-weight:600">Farklı Destinasyon</div>
    </div>
    <div style="background:white;border:1px solid #e5e7eb;border-radius:16px;
                padding:20px 24px;text-align:center">
      <div style="font-size:22px;font-weight:800;color:#111827;line-height:1.2">{_mbti_h or "—"}</div>
      <div style="font-size:11px;color:#6b7280;margin-top:6px;font-weight:600">{_arch_h or "Gezgin Tipin"}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        for i, kayit in enumerate(reversed(gecmis)):
            _dest    = kayit.get("destination", "").capitalize()
            _bas     = kayit.get("start_date", "")
            _bit     = kayit.get("end_date", "")
            _gun     = kayit.get("duration_days", "")
            _kisi    = kayit.get("group_size", "")
            _trans   = kayit.get("transport", "")
            _butce_k = kayit.get("butce_kategorisi", "")
            _mbti_k  = kayit.get("mbti", "")
            _maliyet = float(kayit.get("estimated_cost") or 0)
            _harf    = _dest[0].upper() if _dest else str(toplam_plan - i)
            _baslik  = _dest if _dest else f"Seyahat #{toplam_plan - i}"
            _tarih_str = f"{_bas} — {_bit}" if _bas else ""

            _chip_s = '<div style="display:flex;flex-wrap:wrap;gap:6px">'
            if _mbti_k:
                _chip_s += f'<span style="background:{_renk_h}15;color:{_renk_h};border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700">{_mbti_k}</span>'
            if _gun:
                _chip_s += f'<span style="background:#f3f4f6;color:#6b7280;border-radius:6px;padding:2px 8px;font-size:10px;font-weight:600">{_gun} gün</span>'
            if _kisi:
                _chip_s += f'<span style="background:#f3f4f6;color:#6b7280;border-radius:6px;padding:2px 8px;font-size:10px;font-weight:600">{_kisi} kişi</span>'
            if _trans:
                _chip_s += f'<span style="background:#f3f4f6;color:#6b7280;border-radius:6px;padding:2px 8px;font-size:10px;font-weight:600">{_trans}</span>'
            if _butce_k:
                _chip_s += f'<span style="background:#f3f4f6;color:#6b7280;border-radius:6px;padding:2px 8px;font-size:10px;font-weight:600">{_butce_k}</span>'
            _chip_s += '</div>'

            _maliyet_html = ""
            if _maliyet:
                _maliyet_html = (
                    '<div style="text-align:right;flex-shrink:0">'
                    '<div style="font-size:11px;color:#9ca3af">Tahmini</div>'
                    f'<div style="font-size:18px;font-weight:800;color:#111827">{_maliyet:,.0f}</div>'
                    '<div style="font-size:10px;color:#9ca3af">TL</div></div>'
                )

            _kart = (
                '<div style="padding:0 32px;margin-bottom:12px">'
                '<div style="background:white;border:1px solid #e5e7eb;border-radius:16px;padding:18px 22px">'
                '<div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:10px">'
                '<div>'
                '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
                f'<div style="width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,{_renk_h},{_renk_h}88);display:flex;align-items:center;justify-content:center;font-size:14px;color:white;font-weight:800;flex-shrink:0">{_harf}</div>'
                '<div>'
                f'<div style="font-size:14px;font-weight:800;color:#111827">{_baslik}</div>'
                f'<div style="font-size:11px;color:#9ca3af;margin-top:1px">{_tarih_str}</div>'
                '</div></div>'
                + _chip_s +
                '</div>'
                + _maliyet_html +
                '</div></div></div>'
            )
            st.markdown(_kart, unsafe_allow_html=True)

    nav_arrows("Kimlik Testine Dön", 0, "ACO & Maliyet", 4)

st.markdown("""
<div style="background:white;border-top:1px solid #e5e7eb;margin-top:48px;padding:32px 32px 24px">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              flex-wrap:wrap;gap:24px;max-width:960px;margin:0 auto">
    <div style="min-width:200px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <div style="width:28px;height:28px;border-radius:8px;flex-shrink:0;
                    background:linear-gradient(135deg,#4f46e5,#7c3aed);
                    display:flex;align-items:center;justify-content:center;font-size:13px">✈️</div>
        <span style="font-size:14px;font-weight:800;color:#111827">SmartTravel
          <span style="color:#4f46e5">AI</span></span>
      </div>
      <p style="font-size:12px;color:#6b7280;margin:0;max-width:240px;line-height:1.65">
        MBTI tabanlı kişiselleştirilmiş seyahat planlayıcı.
        Google Gemini AI ile desteklenmektedir.
      </p>
    </div>
    <div style="display:flex;gap:40px;flex-wrap:wrap">
      <div>
        <div style="font-size:10px;font-weight:700;color:#374151;text-transform:uppercase;
                    letter-spacing:0.6px;margin-bottom:10px">Sekmeler</div>
        <div style="display:flex;flex-direction:column;gap:7px">
          <a href="?tab=0" style="font-size:12px;color:#6b7280;text-decoration:none">Kimlik Testi</a>
          <a href="?tab=1" style="font-size:12px;color:#6b7280;text-decoration:none">Rota Formu</a>
          <a href="?tab=2" style="font-size:12px;color:#6b7280;text-decoration:none">Plan Sonucu</a>
          <a href="?tab=3" style="font-size:12px;color:#6b7280;text-decoration:none">ACO &amp; Maliyet</a>
        </div>
      </div>
      <div>
        <div style="font-size:10px;font-weight:700;color:#374151;text-transform:uppercase;
                    letter-spacing:0.6px;margin-bottom:10px">Teknoloji</div>
        <div style="display:flex;flex-direction:column;gap:7px">
          <span style="font-size:12px;color:#6b7280">Google Gemini AI</span>
          <span style="font-size:12px;color:#6b7280">ACO Optimizasyon</span>
          <span style="font-size:12px;color:#6b7280">MBTI Profil Analizi</span>
          <span style="font-size:12px;color:#6b7280">2026 TL Fiyatlandırma</span>
          <span style="font-size:12px;color:#6b7280">Wikipedia Görseller</span>
        </div>
      </div>
    </div>
  </div>
  <div style="border-top:1px solid #f3f4f6;margin-top:24px;padding-top:16px;
              display:flex;justify-content:space-between;align-items:center;
              flex-wrap:wrap;gap:8px;max-width:960px;margin-left:auto;margin-right:auto">
    <span style="font-size:11px;color:#9ca3af">© 2026 SmartTravel AI — Tüm hakları saklıdır</span>
    <div style="display:flex;gap:12px;align-items:center">
      <span style="font-size:11px;color:#9ca3af">v2.0 Beta</span>
      <span style="font-size:11px;background:#f0fdf4;color:#059669;padding:2px 8px;
                  border-radius:999px;font-weight:600">● Çevrimiçi</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)