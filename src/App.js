import React, { useState, useMemo, useEffect } from 'react';
import './index.css';
import * as XLSX from 'xlsx';

// ── SABİTLER VE YARDIMCI FONKSİYONLAR ──
const ASAMALAR = ['Teklif', 'Değerlendirme', 'Sözleşme', 'Kazanıldı', 'Kaybedildi'];
const DURUMLAR = ['Görüşülen', 'Bekleyen', 'Kazanılan', 'Kaybedilen'];
const LIMITLER = { Teklif: 3, Değerlendirme: 3, Sözleşme: 5 };
// Ortak ikon wrapper
const Icon = ({ children }) => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {children}
  </svg>
);

const SEKME_IKONLARI = {
  Dashboard: (
    <Icon>
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
      <path d="M9 22V12h6v10"/>
    </Icon>
  ),
  Müşteriler: (
    <Icon>
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </Icon>
  ),
  Takvim: (
    <Icon>
      <rect x="3" y="4" width="18" height="18" rx="2"/>
      <path d="M16 2v4M8 2v4M3 10h18"/>
    </Icon>
  ),
  Raporlar: (
    <Icon>
      <path d="M3 3v18h18"/>
      <rect x="7" y="12" width="3" height="6"/>
      <rect x="12" y="8" width="3" height="10"/>
      <rect x="17" y="5" width="3" height="13"/>
    </Icon>
  ),
  İşlemler: (
    <Icon>
      <rect x="2" y="5" width="20" height="14" rx="2"/>
      <path d="M2 10h20"/>
    </Icon>
  ),
  "Sanal POS": (
    <Icon>
      <path d="M3 21h18"/>
      <path d="M5 21V10M9 21V10M15 21V10M19 21V10"/>
      <path d="M2 10l10-6 10 6"/>
    </Icon>
  ),
  Kullanıcılar: (
    <Icon>
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </Icon>
  ),
};



const ODEME_KURULUSLARI = ['Qnbpay', 'İyzico', 'Payinall', 'Paynkolay', 'Lidio', 'ParatikaParam', 'PayTR', 'ZiraatPay', 'VakıfPay', 'MorPara', 'Moka', 'United', 'Tami'];
const BANKALAR = ['GarantiBBVA', 'Ziraat', 'TEB', 'VakıfBank', 'HalkBank', 'QNB', 'DenizBank', 'KuveytTürk', 'Türkiye İş Bankası', 'Akbank', 'Albaraka'];
const MUHASEBE_PROGRAMLARI = ['Logo', 'Netsis', 'Mikro', 'Paraşüt', 'Zirve', 'Bizim Hesap', 'Odoo', 'Nebim', 'ETA', 'Uyumsoft', 'Dia'];
const KART_SEMALARI = ['Visa', 'Mastercard', 'Troy', 'Amex'];


const API_BASE = 'http://localhost:5279';
const GOOGLE_CLIENT_ID = '711700948552-vorknte8alrnal606lnao1e6ubunmkb2.apps.googleusercontent.com';
const GOOGLE_SCOPE = 'https://www.googleapis.com/auth/calendar.events';

const HAFTA_GUNLERI = ['Pt', 'Sa', 'Ça', 'Pe', 'Cu', 'Ct', 'Pa'];
const tarihStr = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const ayGunleriOlustur = (yil, ay) => {
  const ilkGun = new Date(yil, ay, 1);
  const sonGun = new Date(yil, ay + 1, 0);
  const bosBaslangic = (ilkGun.getDay() + 6) % 7;
  const gunler = [];
  for (let i = 0; i < bosBaslangic; i++) gunler.push(null);
  for (let g = 1; g <= sonGun.getDate(); g++) gunler.push(new Date(yil, ay, g));
  return gunler;
};

const gunFarki = t => t ? Math.floor((new Date() - new Date(t)) / 86400000) : 0;
const durumHesapla = (m) => {
  if (m.asama === 'Kazanıldı') return 'Kazanılan';
  if (m.asama === 'Kaybedildi') return 'Kaybedilen';
  if (LIMITLER[m.asama] && gunFarki(m.asamaTarihi) >= LIMITLER[m.asama]) return 'Bekleyen';
  return 'Görüşülen';
};
const parseSayi = s => parseFloat(String(s || '').replace(/[^\d.,]/g, '').replace(',', '.')) || 0;
const formatPara = tutar => `${Number(tutar || 0).toLocaleString('tr-TR')} ₺`;

const hakedisHesapla = (ciro, oran) => {
  const c = parseSayi(ciro), o = parseSayi(oran);
  return (c && o) ? formatPara(Math.floor(c * (o / 100))) : '—';
};



const Bilgi = ({ etiketi, deger }) => (
  <div className="bilgi-row">
    <span>{etiketi}</span>
    <b>{deger || '—'}</b>
  </div>
);

const SimpleLineChart = ({ points = [], width = 600, height = 160, color = '#4f46e5' }) => {
  if (!points || points.length === 0) return <div style={{ height }} className="bos-mesaj">Veri yok</div>;
  const max = Math.max(...points.map(p => p.value), 1);
  const min = Math.min(...points.map(p => p.value), 0);
  const padding = { left: 40, right: 10, top: 10, bottom: 28 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const coords = points.map((p, i) => {
    const x = padding.left + (i / Math.max(1, points.length - 1)) * innerW;
    const y = padding.top + (1 - ((p.value - min) / Math.max(1, max - min))) * innerH;
    return { x, y };
  });
  const pointsAttr = coords.map(c => `${c.x},${c.y}`).join(' ');
  const tickCount = 4;
  const ticks = Array.from({ length: tickCount + 1 }, (_, i) => {
    const v = min + (i / tickCount) * (max - min);
    return v;
  }).reverse();
  const maxLabels = 6;
  const step = Math.max(1, Math.ceil(points.length / maxLabels));
  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
      {ticks.map((t, i) => {
        const y = padding.top + (1 - ((t - min) / Math.max(1, max - min))) * innerH;
        return (
          <g key={i}>
            <line x1={padding.left} x2={width - padding.right} y1={y} y2={y} stroke="#eee" strokeWidth="1" />
            <text x={padding.left - 8} y={y + 4} textAnchor="end" fontSize="11" fill="#374151">{formatPara(Math.round(t))}</text>
          </g>
        );
      })}
      <line x1={padding.left} x2={padding.left} y1={padding.top} y2={height - padding.bottom} stroke="#ddd" />
      <line x1={padding.left} x2={width - padding.right} y1={height - padding.bottom} y2={height - padding.bottom} stroke="#ddd" />
      <polyline fill="none" stroke={color} strokeWidth="2" points={pointsAttr} />
      {coords.map((c, i) => (
        <circle key={i} cx={c.x} cy={c.y} r="3" fill={color} />
      ))}
      {points.map((p, i) => {
        if (i % step !== 0 && i !== points.length - 1) return null;
        const c = coords[i];
        const label = p.label.slice(5);
        return <text key={i} x={c.x} y={height - 6} textAnchor="middle" fontSize="11" fill="#6b7280">{label}</text>;
      })}
    </svg>
  );
};

const CircleProgress = ({ percent = 0, value, label, size = 68, color = 'var(--primary)' }) => {
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(100, Math.max(0, percent)) / 100) * c;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth="6" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="6" strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" transform={`rotate(-90 ${size / 2} ${size / 2})`} />
        <text x="50%" y="50%" textAnchor="middle" dy="5" fontSize="15" fontWeight="700" fill="var(--text)">{value}</text>
      </svg>
      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</span>
    </div>
  );
};

// ── ANA BİLEŞEN ──
export default function App() {
  const [musteriler, setMusteriler] = useState([]);
  const [islemler, setIslemler] = useState([]);
  const [odemeler, setOdemeler] = useState([]);
  const [faturalar, setFaturalar] = useState([]);

const [googleToken, setGoogleToken] = useState(null);
const [googleEtkinlikler, setGoogleEtkinlikler] = useState([]);
const [takvimAy, setTakvimAy] = useState(new Date());
const [seciliGun, setSeciliGun] = useState(null);

  const [seciliId, setSeciliId] = useState(null);
  const [aktifSekme, setAktifSekme] = useState('Dashboard');
  const [formAcik, setFormAcik] = useState(false);
  const [hatirlatmaAcik, setHatirlatmaAcik] = useState(false);

  const [arama, setArama] = useState('');
  const [donemFiltre, setDonemFiltre] = useState('Bu Ay');
  const [secilenDurum, setSecilenDurum] = useState(null);
  const [posFiltre, setPosFiltre] = useState('Tümü');
  const [islemAltSekme, setIslemAltSekme] = useState('Tümü');
  const [posArama, setPosArama] = useState('');
  const [eklemeAcikBanka, setEklemeAcikBanka] = useState(null);
  const[eklemeMusteriId, setEklemeMusteriId] = useState('');
  const [eklemeGuvenli3D, setEklemeGuvenli3D] = useState('Kapalı');
  const [yeniFaturaForm, setYeniFaturaForm] = useState({ musteriId: '', faturaNo: '', tarih: '', tutar: '', valorTarihi: '', notlar: '' });
  
  const [yeniTarih, setYeniTarih] = useState('');
  const [yeniYorum, setYeniYorum] = useState('');

  const [yeniForm, setYeniForm] = useState({
    sirketUnvani: '', markaAdi: '', domain: '', email: '', telefon: '',sehir: '', semt: '', temsilci: ''
  });

  const [kullanici, setKullanici] = useState(() => {
  const kayitli = localStorage.getItem('kullanici');
  return kayitli ? JSON.parse(kayitli) : null;
});
const [girisForm, setGirisForm] = useState({ kullaniciAdi: '', sifre: '' });
const [girisHata, setGirisHata] = useState('');
const [kullanicilar, setKullanicilar] = useState([]);
const [kullaniciFormAcik, setKullaniciFormAcik] = useState(false);
const [yeniKullaniciForm, setYeniKullaniciForm] = useState({
  kullaniciAdi: '', adSoyad: '', sifre: '', kullaniciTipi: 'Portal', yetki: ''
});

const girisYap = () => {
  setGirisHata('');
  fetch(`${API_BASE}/Login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(girisForm)
  }).then(res => {
    if (!res.ok) throw new Error('Kullanıcı adı veya şifre hatalı');
    return res.json();
  }).then(veri => {
    localStorage.setItem('token', veri.token);
    localStorage.setItem('kullanici', JSON.stringify(veri.kullanici));
    setKullanici(veri.kullanici);
  }).catch(err => setGirisHata(err.message));
};

const cikisYap = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('kullanici');
  setKullanici(null);
};

const kullaniciEkle = () => {
  if (!yeniKullaniciForm.kullaniciAdi.trim() || !yeniKullaniciForm.sifre.trim()) return;
  fetch(`${API_BASE}/Kullanicilar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...yeniKullaniciForm, durum: 'Aktif' })
  })
    .then(res => res.json())
    .then(yeniKullanici => {
      setKullanicilar(eski => [...eski, yeniKullanici]);
      setYeniKullaniciForm({ kullaniciAdi: '', adSoyad: '', sifre: '', kullaniciTipi: 'Portal', yetki: 'Satış Temsilcisi' });
      setKullaniciFormAcik(false);
    })
    .catch(err => console.error('Kullanıcı eklenemedi:', err));
};

const kullaniciDurumDegistir = (k) => {
  const yeniDurum = k.durum === 'Aktif' ? 'Pasif' : 'Aktif';
  fetch(`${API_BASE}/Kullanicilar/${k.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kullaniciAdi: k.kullaniciAdi, adSoyad: k.adSoyad, kullaniciTipi: k.kullaniciTipi, yetki: k.yetki, durum: yeniDurum, sifre: '' })
  })
    .then(() => setKullanicilar(eski => eski.map(x => x.id === k.id ? { ...x, durum: yeniDurum } : x)))
    .catch(err => console.error('Durum güncellenemedi:', err));
};

const kullaniciSil = (id) => {
  if (!window.confirm('Bu kullanıcı silinsin mi?')) return;
  fetch(`${API_BASE}/Kullanicilar/${id}`, { method: 'DELETE' })
    .then(() => setKullanicilar(eski => eski.filter(x => x.id !== id)))
    .catch(err => console.error('Kullanıcı silinemedi:', err));
};

  

  // ── İLK YÜKLEME ──
  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/Islemler`).then(res => res.json()),
      fetch(`${API_BASE}/Musteri`).then(res => res.json()),
      fetch(`${API_BASE}/Odemeler`).then(res => res.json()),
      fetch(`${API_BASE}/Kullanicilar`).then(res => res.json()),
      fetch(`${API_BASE}/Faturalar`).then(res => res.json())
     
    ]).then(([islemlerVeri, musteriVeri, odemelerVeri, kullanicilarVeri, faturalarVeri]) => {
      setIslemler(islemlerVeri || []);
      setMusteriler(musteriVeri || []);
      setOdemeler(odemelerVeri || []);
      setKullanicilar(kullanicilarVeri || []);
      setFaturalar(faturalarVeri || []);
    }).catch(err => console.error('Veriler yüklenirken hata oluştu:', err));
  }, []);

  useEffect(() => {
  if (googleToken) googleEtkinlikleriGetir(googleToken);
}, [googleToken]);


useEffect(() => {
  if (!kullanici) return;
  fetch(`${API_BASE}/GoogleAuth/Token/${kullanici.id}`)
    .then(res => res.ok ? res.json() : null)
    .then(data => { if (data) setGoogleToken(data.accessToken); })
    .catch(() => {});
}, [kullanici]);

  // ── HESAPLANAN VERİLER & MEMO ──
const etkinliklerTarihe = useMemo(() => {
  const harita = {};
  googleEtkinlikler.forEach(e => {
    const t = e.start?.date || e.start?.dateTime?.slice(0, 10);
    if (!t) return;
    if (!harita[t]) harita[t] = [];
    harita[t].push(e.summary || '(başlıksız)');
  });
  return harita;
}, [googleEtkinlikler]);

  const musteriCirosu = (musteriId) => islemler.filter(i => i.musteriId === musteriId).reduce((t, i) => t + Number(i.tutar || 0), 0);
  const toplamCiro = useMemo(() => islemler.reduce((t, i) => t + Number(i.tutar || 0), 0), [islemler]);

  const seciliMusteri = useMemo(() => musteriler.find(m => m.id === seciliId) || null, [musteriler, seciliId]);
  const hatirlatmalar = useMemo(() => musteriler.filter(m => LIMITLER[m.asama] && gunFarki(m.asamaTarihi) >= LIMITLER[m.asama]), [musteriler]);
  const kazanilan = useMemo(() => musteriler.filter(m => m.asama === 'Kazanıldı').length, [musteriler]);

  const filtrelenmisMusteriler = useMemo(() => {
    return musteriler.filter(m => (m.sirketUnvani || '').toLowerCase().includes(arama.toLowerCase()));
  }, [musteriler, arama]);

  const aktifMusteriSayisi = useMemo(() => {
    const otuzGunOnce = new Date();
    otuzGunOnce.setDate(otuzGunOnce.getDate() - 30);
    return musteriler.filter(m => islemler.some(i => i.musteriId === m.id && new Date(i.tarih) >= otuzGunOnce)).length;
  }, [musteriler, islemler]);

  const bugununHatirlatmalari = useMemo(() => {
    const bugun = new Date().toISOString().slice(0, 10);
    return musteriler.filter(m => m.planTarihi === bugun);
  }, [musteriler]);

  const donemMetrikleri = useMemo(() => {
    const bugun = new Date();
    const bugunStr = bugun.toISOString().slice(0, 10);
    let baslangic = new Date(bugun.getFullYear(), bugun.getMonth(), 1).toISOString().slice(0, 10);

    if (donemFiltre === 'Bugün') baslangic = bugunStr;
    else if (donemFiltre === 'Dün') {
      const d = new Date(bugun); d.setDate(d.getDate() - 1);
      baslangic = d.toISOString().slice(0, 10);
    } else if (donemFiltre === 'Bu Hafta') {
      const d = new Date(bugun); d.setDate(d.getDate() - 7);
      baslangic = d.toISOString().slice(0, 10);
    }

    const suzulen = islemler.filter(i => i.tarih >= baslangic && i.tarih <= bugunStr);
    const ciro = suzulen.reduce((t, i) => t + Number(i.tutar || 0), 0);
    const hakedis = suzulen.reduce((t, i) => {
      const m = musteriler.find(x => x.id === i.musteriId);
      return t + Math.floor(Number(i.tutar || 0) * parseSayi(m?.teklifOrani) / 100);
    }, 0);

    return { ciro, hakedis, sayi: suzulen.length };
  }, [islemler, musteriler, donemFiltre]);

  
const donemSeries = useMemo(() => {
  const bugun = new Date();
  let bas = new Date(bugun.getFullYear(), bugun.getMonth(), 1);
  if (donemFiltre === 'Bugün') bas = new Date(bugun);
  else if (donemFiltre === 'Dün') { const d = new Date(bugun); d.setDate(d.getDate() - 1); bas = d; }
  else if (donemFiltre === 'Bu Hafta') { const d = new Date(bugun); d.setDate(d.getDate() - 7); bas = d; }
  const days = [];
  const cur = new Date(bas);
  const end = new Date(bugun);
  cur.setHours(0,0,0,0);
  end.setHours(0,0,0,0);
  while (cur <= end) {
    days.push(cur.toISOString().slice(0,10));
    cur.setDate(cur.getDate() + 1);
  }
  const map = {};
  days.forEach(d => map[d] = 0);
  const startStr = days[0];
  const endStr = days[days.length - 1];
  islemler.filter(i => i.tarih >= startStr && i.tarih <= endStr).forEach(i => {
    map[i.tarih] = (map[i.tarih] || 0) + Number(i.tutar || 0);
  });
  return days.map(d => ({ label: d, value: map[d] || 0 }));
}, [islemler, donemFiltre]);

  const [raporDonem, setRaporDonem] = useState('Son 7 Gün');

  
const isOrtaklari = useMemo(() => {
  const gruplar = {};
  musteriler.forEach(m => {
    const ortak = (m.yonlendiren || '').trim();
    if (!ortak) return;
    if (!gruplar[ortak]) gruplar[ortak] = [];
    gruplar[ortak].push(m);
  });
  return Object.entries(gruplar).map(([ad, musteriListesi]) => {
    const toplamHakedis = musteriListesi.reduce((t, m) => t + Math.floor(musteriCirosu(m.id) * parseSayi(m.gelirPayiOrani) / 100), 0);
    return { ad, musteriListesi, toplamHakedis };
  });
}, [musteriler, islemler]);

const hakedisOzeti = useMemo(() => {
  const toplamTutar = faturalar.reduce((t, f) => t + parseSayi(f.tutar), 0);
  const odenen = faturalar.reduce((t, f) => t + parseSayi(f.odenen), 0);
  const netBakiye = toplamTutar - odenen;

  const gruplar = {};
  faturalar.forEach(f => {
    if (!gruplar[f.musteriId]) gruplar[f.musteriId] = [];
    gruplar[f.musteriId].push(f);
  });
  const musteriOzeti = Object.entries(gruplar).map(([musteriId, liste]) => {
    const m = musteriler.find(x => x.id === Number(musteriId));
    const toplam = liste.reduce((t, f) => t + parseSayi(f.tutar), 0);
    const onaylanan = liste.reduce((t, f) => t + parseSayi(f.onaylanan), 0);
    const odenenM = liste.reduce((t, f) => t + parseSayi(f.odenen), 0);
    return { musteri: m?.sirketUnvani || '—', toplam, onaylanan, odenen: odenenM, netBakiye: toplam - odenenM };
  });

  return { toplamTutar, odenen, netBakiye, musteriOzeti };
}, [faturalar, musteriler]);

  const raporMetrikleri = useMemo(() => {
    const bugun = new Date();
    const bugunStr = bugun.toISOString().slice(0, 10);
    let baslangic = bugunStr;

    if (raporDonem === 'Son 7 Gün') {
      const d = new Date(bugun); d.setDate(d.getDate() - 7);
      baslangic = d.toISOString().slice(0, 10);
    } else if (raporDonem === 'Son 30 Gün') {
      const d = new Date(bugun); d.setDate(d.getDate() - 30);
      baslangic = d.toISOString().slice(0, 10);
    } else if (raporDonem === 'Bu Ay') {
      baslangic = new Date(bugun.getFullYear(), bugun.getMonth(), 1).toISOString().slice(0, 10);
    }

    const suzulen = odemeler.filter(o => o.tarih.slice(0, 10) >= baslangic && o.tarih.slice(0, 10) <= bugunStr);
    const basarili = suzulen.filter(o => o.durum === 'Başarılı');
    const basarisiz = suzulen.filter(o => o.durum === 'Başarısız');
    const oran = suzulen.length ? Math.round(basarili.length / suzulen.length * 100) : 0;
    const donemCiro = basarili.reduce((t, o) => t + Number(o.tutar || 0), 0);

    const bankaSayaci = {};
    suzulen.forEach(o => { bankaSayaci[o.banka] = (bankaSayaci[o.banka] || 0) + 1; });
    const enAktifBanka = Object.entries(bankaSayaci).sort((a, b) => b[1] - a[1])[0]?.[0] || '—';

    return { toplam: suzulen.length, basarili: basarili.length, basarisiz: basarisiz.length, oran, donemCiro, enAktifBanka };
  }, [odemeler, raporDonem]);

  const kayitliKartlar = useMemo(() => {
    const map = new Map();
    odemeler.forEach(o => {
      if (!map.has(o.kart)) {
        const m = musteriler.find(x => x.id === o.musteriId);
        map.set(o.kart, { kart: o.kart, kartBankasi: o.kartBankasi, kartTipi: o.kartTipi, musteri: m?.sirketUnvani || '—' });
      }
    });
    return Array.from(map.values());
  }, [odemeler, musteriler]);

  const ilkGorusmeTarihi = (musteriId) => {
    const tarihler = islemler.filter(i => i.musteriId === musteriId).map(i => i.tarih).sort();
    return tarihler[0] || '—';
  };

  const sonYorum = (musteriId) => {
    const kayitlar = islemler.filter(i => i.musteriId === musteriId && i.not).sort((a, b) => b.tarih.localeCompare(a.tarih));
    return kayitlar[0]?.not || '—';
  };

  // ── EYLEMLER / HANDLERS ──
  const musteriPut = (id, patch) => {
    const m = { ...musteriler.find(x => x.id === id), ...patch };
    return fetch(`${API_BASE}/Musteri/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(m)
    });
  };

const islemPost = (body, onSuccess) => {
  fetch(`${API_BASE}/Islemler`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
    .then(res => res.json())
    .then(yeniIslem => {
      setIslemler(eski => [...eski, yeniIslem]);
      if (googleToken && yeniIslem.tarih) {
        const musteriAdi = musteriler.find(m => m.id === yeniIslem.musteriId)?.sirketUnvani || '';
        fetch('https://www.googleapis.com/calendar/v3/calendars/primary/events', {
          method: 'POST',
          headers: { Authorization: `Bearer ${googleToken}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            summary: `${yeniIslem.tip} — ${musteriAdi}`,
            start: { date: yeniIslem.tarih },
            end: { date: yeniIslem.tarih },
          }),
        }).then(() => googleEtkinlikleriGetir(googleToken)).catch(err => console.error('Takvime eklenemedi:', err));
      }
      onSuccess?.();
    })
    .catch(err => console.error('İşlem eklenemedi:', err));
};

const faturaEkle = (dto) => {
  fetch(`${API_BASE}/Faturalar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dto)
  })
    .then(res => res.json())
    .then(yeni => setFaturalar(eski => [...eski, yeni]))
    .catch(err => console.error('Fatura eklenemedi:', err));
};

const faturaGuncelle = (fatura, patch) => {
  fetch(`${API_BASE}/Faturalar/${fatura.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ onaylanan: fatura.onaylanan, odenen: fatura.odenen, durum: fatura.durum, ...patch })
  })
    .then(() => setFaturalar(eski => eski.map(f => f.id === fatura.id ? { ...f, ...patch } : f)))
    .catch(err => console.error('Fatura güncellenemedi:', err));
};

const faturaOnayla = (fatura) => faturaGuncelle(fatura, { onaylanan: fatura.tutar, durum: 'Onaylandı' });
const faturaOde = (fatura) => faturaGuncelle(fatura, { odenen: fatura.tutar, durum: 'Ödendi' });

const faturaSil = (id) => {
  fetch(`${API_BASE}/Faturalar/${id}`, { method: 'DELETE' })
    .then(() => setFaturalar(eski => eski.filter(f => f.id !== id)))
    .catch(err => console.error('Fatura silinemedi:', err));
};

  const excelYaz = (veri, sayfaAdi, dosyaAdi) => {
    const sayfa = XLSX.utils.json_to_sheet(veri);
    const kitap = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(kitap, sayfa, sayfaAdi);
    XLSX.writeFile(kitap, dosyaAdi);
  };

  const excelIndir = () => {
    const veri = odemeler.map(o => {
      const m = musteriler.find(x => x.id === o.musteriId);
      return {
        'Müşteri': m?.sirketUnvani || '',
        'Banka': o.banka,
        'Sanal POS': o.sanalPos,
        'Sipariş No': o.siparisNo,
        'İşlem No': o.islemNo,
        'İşlem Tipi': o.islemTipi,
        'Durum': o.durum,
        'Tarih': o.tarih,
        'Tutar': o.tutar,
        'Para Birimi': o.paraBirimi,
        'E-posta': o.eposta,
        'Kart': o.kart,
        'Kart Bankası': o.kartBankasi,
        'Kart Tipi': o.kartTipi,
        '3D Güvenli': o.guvenli3D,
        'Sonuç': o.sonuc
      };
    });
    excelYaz(veri, 'İşlemler', 'islemler.xlsx');
  };

  const isOrtaklariExcelIndir = () => {
    const veri = isOrtaklari.flatMap(o => o.musteriListesi.map(m => ({
      'İş Ortağı': o.ad,
      'Müşteri': m.sirketUnvani,
      'Ciro': musteriCirosu(m.id),
      'Gelir Payı Oranı': m.gelirPayiOrani || '',
      'Hakediş': Math.floor(musteriCirosu(m.id) * parseSayi(m.gelirPayiOrani) / 100)
    })));
    excelYaz(veri, 'İş Ortakları', 'is-ortaklari.xlsx');
  };

  const hakedisExcelIndir = () => {
    const veri = hakedisOzeti.musteriOzeti.map(o => ({
      'Müşteri': o.musteri,
      'Toplam': o.toplam,
      'Onaylanan': o.onaylanan,
      'Ödenen': o.odenen,
      'Net Bakiye': o.netBakiye
    }));
    excelYaz(veri, 'Hakediş', 'hakedis.xlsx');
  };

  const faturaExcelIndir = () => {
    const veri = faturalar.map(f => {
      const m = musteriler.find(x => x.id === f.musteriId);
      return {
        'Müşteri': m?.sirketUnvani || '',
        'Fatura No': f.faturaNo,
        'Tarih': f.tarih,
        'Tutar': f.tutar,
        'Onaylanan': f.onaylanan,
        'Ödenen': f.odenen,
        'Kalan': parseSayi(f.tutar) - parseSayi(f.odenen),
        'Valör Tarihi': f.valorTarihi,
        'Notlar': f.notlar,
        'Durum': f.durum
      };
    });
    excelYaz(veri, 'Faturalar', 'faturalar.xlsx');
  };

  const musteriGuncelle = (alan, deger) => {
    setMusteriler(eski => eski.map(m => m.id === seciliId ? { ...m, [alan]: deger } : m));
    musteriPut(seciliId, { [alan]: deger }).catch(err => console.error('Güncelleme hatası:', err));
  };

  const bankaDurumu = (musteri, banka) => {
  const liste = (musteri?.entegrasyonBanka || '').split(',').filter(Boolean);
  const kayit = liste.find(k => k.startsWith(banka + ':'));
  return kayit ? kayit.split(':')[1] : null;
};

const posDurumDegistirMusteri = (musteri, banka) => {
  const liste = (musteri.entegrasyonBanka || '').split(',').filter(Boolean);
  const mevcut = liste.find(k => k.startsWith(banka + ':'));
  let yeniListe;
  if (!mevcut) {
    yeniListe = [...liste, `${banka}:Aktif`];
     } else {
    const yeniDurum = mevcut.endsWith(':Aktif') ? 'Pasif' : 'Aktif';
    yeniListe = liste.map(k => k.startsWith(banka + ':') ? `${banka}:${yeniDurum}` : k);
  }
  const yeniDeger = yeniListe.join(',');
  setMusteriler(eski => eski.map(m => m.id === musteri.id ? { ...m, entegrasyonBanka: yeniDeger } : m));
  musteriPut(musteri.id, { entegrasyonBanka: yeniDeger }).catch(err => console.error('Güncelleme hatası:', err));
};

const posKaldirMusteri = (musteri, banka) => {
  const liste = (musteri.entegrasyonBanka || '').split(',').filter(Boolean);
  const yeniListe = liste.filter(k => !k.startsWith(banka + ':'));
  const yeniDeger = yeniListe.join(',');
  setMusteriler(eski => eski.map(m => m.id === musteri.id ? { ...m, entegrasyonBanka: yeniDeger } : m));
  musteriPut(musteri.id, { entegrasyonBanka: yeniDeger }).catch(err => console.error('Güncelleme hatası:', err));
};

const guvenli3DOku = (musteri, banka) => {
  const liste = (musteri?.entegrasyonBanka || '').split(',').filter(Boolean);
  const kayit = liste.find(k => k.startsWith(banka + ':'));
  return kayit ? kayit.split(':')[2] || '' : '';
};

const kartSemasiOku = (musteri, banka) => {
  const liste = (musteri?.entegrasyonBanka || '').split(',').filter(Boolean);
  const kayit = liste.find(k => k.startsWith(banka + ':'));
  return kayit ? kayit.split(':')[3] || '' : '';
};

const posEkleMusteri = (musteri, banka, guvenli3D) => {
  const liste = (musteri.entegrasyonBanka || '').split(',').filter(Boolean);
  const yeniListe = [...liste, `${banka}:Aktif:${guvenli3D}:`];
  const yeniDeger = yeniListe.join(',');
  setMusteriler(eski => eski.map(m => m.id === musteri.id ? { ...m, entegrasyonBanka: yeniDeger } : m));
  musteriPut(musteri.id, { entegrasyonBanka: yeniDeger }).catch(err => console.error('Güncelleme hatası:', err));
};

const kartSemasiSec = (musteri, banka, sema) => {
  const liste = (musteri.entegrasyonBanka || '').split(',').filter(Boolean);
  const yeniListe = liste.map(k => {
    if (!k.startsWith(banka + ':')) return k;
    const parcalar = k.split(':');
    return `${parcalar[0]}:${parcalar[1]}:${parcalar[2] || ''}:${sema}`;
  });
  const yeniDeger = yeniListe.join(',');
  setMusteriler(eski => eski.map(m => m.id === musteri.id ? { ...m, entegrasyonBanka: yeniDeger } : m));
  musteriPut(musteri.id, { entegrasyonBanka: yeniDeger }).catch(err => console.error('Güncelleme hatası:', err));
};

  const musteriSil = () => {
    if (!seciliMusteri || !window.confirm(`${seciliMusteri.sirketUnvani} silinsin mi?`)) return;
    fetch(`${API_BASE}/Musteri/${seciliMusteri.id}`, { method: 'DELETE' })
      .then(() => {
        setMusteriler(eski => eski.filter(m => m.id !== seciliMusteri.id));
        setSeciliId(null);
      })
      .catch(err => console.error('Müşteri silinemedi:', err));
  };

  const musteriEkle = () => {
    if (!yeniForm.sirketUnvani.trim()) return;

    fetch(`${API_BASE}/Musteri`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...yeniForm, asama: 'Teklif', durum: 'Görüşülen', ciro: '' })
    })
      .then(res => res.json())
      .then(yeniMusteri => {
        setMusteriler(eski => [...eski, yeniMusteri]);
        setSeciliId(yeniMusteri.id);
        setFormAcik(false);
        setYeniForm({ sirketUnvani: '', markaAdi: '', domain: '', email: '', telefon: '', sehir: '', semt: '', temsilci: '' });
        setAktifSekme('Müşteriler');
      })
      .catch(err => console.error('Müşteri eklenemedi:', err));
  };

  const asamaDegistir = (yeniAsama) => {
    if (!seciliMusteri || yeniAsama === seciliMusteri.asama) return;
    const asamaTarihi = new Date().toISOString().slice(0, 10);

    setMusteriler(eski => eski.map(m => m.id === seciliId ? { ...m, asama: yeniAsama, asamaTarihi } : m));
    musteriPut(seciliId, { asama: yeniAsama, asamaTarihi }).catch(err => console.error('Aşama güncellenemedi:', err));
  };


  const tarihEkle = () => {
    if (!yeniTarih || !yeniYorum.trim() || !seciliMusteri) return;
    islemPost({
      musteriId: seciliMusteri.id, tip: 'Not', tarih: yeniTarih, not: yeniYorum
    }, () => { setYeniTarih(''); setYeniYorum(''); });
  };

  const tarihSil = (tid) => {
    fetch(`${API_BASE}/Islemler/${tid}`, { method: 'DELETE' })
      .then(() => setIslemler(eski => eski.filter(i => i.id !== tid)))
      .catch(err => console.error('İşlem silinemedi:', err));
  };

const googleGirisYap = () => {
  const client = window.google.accounts.oauth2.initCodeClient({
    client_id: GOOGLE_CLIENT_ID,
    scope: GOOGLE_SCOPE,
    ux_mode: 'popup',
    callback: (yanit) => {
      fetch(`${API_BASE}/GoogleAuth/Kod`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kullaniciId: kullanici.id, kod: yanit.code })
      })
        .then(res => res.json())
        .then(data => setGoogleToken(data.accessToken))
        .catch(err => console.error('Google kod değişimi başarısız:', err));
    },
  });
  client.requestCode();
};

const googleEtkinlikleriGetir = (token) => {
  fetch('https://www.googleapis.com/calendar/v3/calendars/primary/events?singleEvents=true&orderBy=startTime&timeMin=' + new Date().toISOString(), {
    headers: { Authorization: `Bearer ${token}` }
  })
    .then(res => res.json())
    .then(data => setGoogleEtkinlikler(data.items || []))
    .catch(err => console.error('Takvim etkinlikleri alınamadı:', err));
};

const googleEtkinlikEkle = () => {
  if (!yeniTarih || !yeniYorum.trim() || !googleToken) return;
  fetch('https://www.googleapis.com/calendar/v3/calendars/primary/events', {
    method: 'POST',
    headers: { Authorization: `Bearer ${googleToken}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      summary: yeniYorum,
      start: { date: yeniTarih },
      end: { date: yeniTarih },
    }),
  })
    .then(res => res.json())
    .then(() => { setYeniTarih(''); setYeniYorum(''); googleEtkinlikleriGetir(googleToken); })
    .catch(err => console.error('Etkinlik eklenemedi:', err));
};

const googleEtkinlikSil = (eventId) => {
  fetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events/${eventId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${googleToken}` },
  })
    .then(() => setGoogleEtkinlikler(eski => eski.filter(e => e.id !== eventId)))
    .catch(err => console.error('Etkinlik silinemedi:', err));
};

  if (!kullanici) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)' }}>
      <div className="crm-card" style={{ width: 320 }}>
        <h2 style={{ marginBottom: 4 }}>Treps CRM</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: 16, fontSize: 13 }}>Giriş yap</p>
        <input className="form-input" placeholder="Kullanıcı adı" value={girisForm.kullaniciAdi} onChange={e => setGirisForm({ ...girisForm, kullaniciAdi: e.target.value })} style={{ marginBottom: 8 }} />
        <input className="form-input" type="password" placeholder="Şifre" value={girisForm.sifre} onChange={e => setGirisForm({ ...girisForm, sifre: e.target.value })} onKeyDown={e => e.key === 'Enter' && girisYap()} style={{ marginBottom: 8 }} />
        {girisHata && <p style={{ color: '#b91c1c', fontSize: 13, marginBottom: 8 }}>{girisHata}</p>}
        <button className="new-button" onClick={girisYap} style={{ width: '100%' }}>Giriş Yap</button>
      </div>
    </div>
  );
}

  return (
    <div className="crm-layout">
      {/* SIDEBAR */}
      <aside className="crm-sidebar">
        <div className="crm-logo"><span className="logo-icon">T</span> Treps <small>CRM</small></div>
        <nav className="sidebar-menu">
          {['Dashboard', 'Müşteriler', 'Takvim', 'Raporlar', 'İşlemler', 'Sanal POS', 'Kullanıcılar'].map(s => (
            <React.Fragment key={s}>
              <button className={`menu-btn ${aktifSekme === s ? 'active' : ''}`} onClick={() => { setAktifSekme(s); if (s === 'Takvim' && !googleToken) googleGirisYap(); if (s === 'İşlemler') setIslemAltSekme('Tümü'); }}>
                {SEKME_IKONLARI[s]}
                <span className="menu-label">{s}</span>
              </button>
              {s === 'İşlemler' && aktifSekme === 'İşlemler' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, paddingLeft: 16 }}>
                  {['İş Ortakları', 'Hakediş', 'Faturalar'].map(alt => (
                    <button
                      key={alt}
                      onClick={() => setIslemAltSekme(alt)}
                      style={{ textAlign: 'left', background: 'none', border: 'none', padding: '6px 10px', fontSize: 12, borderRadius: 6, cursor: 'pointer', color: islemAltSekme === alt ? 'var(--primary)' : 'var(--text-muted)', fontWeight: islemAltSekme === alt ? 700 : 400 }}
                    >
                      {alt}
                    </button>
                  ))}
                </div>
              )}
            </React.Fragment>
          ))}
        </nav>
      </aside>

      

      {/* MAIN CONTENT */}
      <main className="crm-main">
        <header className="crm-header">
          <h2>Treps CRM</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, position: 'relative' }}>
            <button onClick={() => setHatirlatmaAcik(a => !a)} style={{ position: 'relative', background: 'none', border: 'none', fontSize: 20, cursor: 'pointer' }}>
              🔔
              {bugununHatirlatmalari.length > 0 && (
                <span style={{ position: 'absolute', top: -4, right: -4, background: '#b91c1c', color: '#fff', borderRadius: '50%', fontSize: 10, width: 16, height: 16, display: 'grid', placeItems: 'center' }}>
                  {bugununHatirlatmalari.length}
                </span>
              )}
            </button>
            {hatirlatmaAcik && (
              <div style={{ position: 'absolute', top: 30, right: 0, background: '#fff', border: '1px solid var(--border)', borderRadius: 8, padding: 12, minWidth: 240, boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 10 }}>
                <b style={{ fontSize: 13 }}> Hatırlatmalar</b>
                {bugununHatirlatmalari.length === 0 ? (
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>Bugün için hatırlatma yok.</p>
                ) : (
                  bugununHatirlatmalari.map(m => (
                    <div key={m.id} style={{ marginTop: 8, cursor: 'pointer' }} onClick={() => { setSeciliId(m.id); setAktifSekme('Müşteriler'); setHatirlatmaAcik(false); }}>
                      <b style={{ fontSize: 13 }}>{m.sirketUnvani}</b>
                      <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '2px 0 0' }}>{m.planNotu || '—'}</p>
                    </div>
                  ))
                )}
              </div>
            )}
            <button onClick={() => window.location.href = 'mailto:'} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 6, padding: '5px 12px', cursor: 'pointer', fontSize: 13 }}>✉ E-posta</button>
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{kullanici.adSoyad}</span>
            <button onClick={cikisYap} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 6, padding: '4px 10px', cursor: 'pointer', fontSize: 12 }}>Çıkış</button>
            <span className="avatar">{kullanici.adSoyad?.[0] || 'İ'}</span>
          </div>
        </header>

        {/* ── DASHBOARD ── */}
        {aktifSekme === 'Dashboard' && (
          <>
            <div className="crm-card" style={{ margin: '0 28px 16px' }}>
              <p style={{ margin: '0 0 2px', fontWeight: 600 }}>İyi günler, {kullanici.adSoyad?.split(' ')[0] || 'İlayda'} 👋</p>
              <p style={{ margin: '0 0 10px', color: 'var(--text-muted)', fontSize: 13 }}>Satış ve müşteri performansınızın özeti.</p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                {['Bugün', 'Dün', 'Bu Hafta', 'Bu Ay'].map(f => (
                  <button key={f} onClick={() => setDonemFiltre(f)} style={{ padding: '4px 14px', borderRadius: 20, border: '1px solid var(--border)', background: donemFiltre === f ? 'var(--primary)' : 'transparent', color: donemFiltre === f ? '#fff' : 'inherit', cursor: 'pointer', fontSize: 13 }}>
                    {f}
                  </button>
                ))}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
                <div className="metric-card"><p className="stat-label">Toplam Ciro</p><h3>{formatPara(toplamCiro)}</h3></div>
                <div className="metric-card"><p className="stat-label">Dönem Cirosu</p><h3>{formatPara(donemMetrikleri.ciro)}</h3></div>
                <div className="metric-card"><p className="stat-label">Dönem Hakedişi</p><h3>{formatPara(donemMetrikleri.hakedis)}</h3></div>
                <div className="metric-card"><p className="stat-label">Dönem İşlem Sayısı</p><h3>{donemMetrikleri.sayi}</h3></div>
              </div>
              <div style={{ marginTop: 16 }}>
                <h4 style={{ margin: '0 0 8px' }}>Ciro (günlük)</h4>
                <SimpleLineChart points={donemSeries} width={900} height={140} />
              </div>
            </div>

            <div className="crm-card" style={{ margin: '0 28px 16px' }}>
              <h3>Müşteri Özeti</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 20 }}>
                <div className="metric-card"><p className="stat-label">Toplam Müşteri</p><h3>{musteriler.length}</h3></div>
                <div className="metric-card"><p className="stat-label">Aktif Müşteri</p><h3>{aktifMusteriSayisi}</h3></div>
                <div className="metric-card"><p className="stat-label">Pasif Müşteri</p><h3>{musteriler.length - aktifMusteriSayisi}</h3></div>
                <div className="metric-card"><p className="stat-label">Kazanılan</p><h3>{kazanilan}</h3></div>
              </div>

              <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', justifyContent: 'space-around', marginBottom: 16 }}>
                {DURUMLAR.map(durum => {
                  const sayi = musteriler.filter(m => durumHesapla(m) === durum).length;
                  const yuzde = musteriler.length ? Math.round(sayi / musteriler.length * 100) : 0;
                  const renk = { 'Görüşülen': 'var(--primary)', 'Bekleyen': '#f59e0b', 'Kazanılan': '#22c55e', 'Kaybedilen': '#ef4444' }[durum];
                  return (
                    <div
                      key={durum}
                      onClick={() => setSecilenDurum(secilenDurum === durum ? null : durum)}
                      style={{ cursor: 'pointer', borderRadius: 12, padding: 8, outline: secilenDurum === durum ? `2px solid ${renk}` : 'none' }}
                    >
                      <CircleProgress percent={yuzde} value={sayi} label={durum} color={renk} />
                    </div>
                  );
                })}
              </div>

              {secilenDurum && (
                <div>
                  <h4 style={{ marginBottom: 8 }}>{secilenDurum} Müşteriler</h4>
                  {musteriler.filter(m => durumHesapla(m) === secilenDurum).length === 0 ? (
                    <p className="bos-mesaj">Bu durumda müşteri yok.</p>
                  ) : (
                    musteriler.filter(m => durumHesapla(m) === secilenDurum).map(m => (
                      <div key={m.id} className="task-item" style={{ flexDirection: 'column', alignItems: 'flex-start', marginBottom: 10 }}>
                        <b>{m.sirketUnvani}</b>
                        <small style={{ color: 'var(--text-muted)' }}>
                          Marka: {m.markaAdi || '—'} &nbsp;|&nbsp; Domain: {m.domain || '—'} &nbsp;|&nbsp; Temsilci: {m.temsilci || '—'}
                        </small>
                        <small style={{ color: 'var(--text-muted)' }}>
                          İlk Görüşme: {ilkGorusmeTarihi(m.id)} &nbsp;|&nbsp; Son Yorum: {sonYorum(m.id)}
                        </small>
                        {secilenDurum === 'Kazanılan' && <small style={{ color: '#10b981' }}>Sözleşme Tarihi: {m.asamaTarihi || '—'}</small>}
                        {secilenDurum === 'Bekleyen' && <small style={{ color: '#f59e0b' }}>Neden Bekliyor: {m.beklemeSebebi || '—'}</small>}
                        {secilenDurum === 'Kaybedilen' && <small style={{ color: '#b91c1c' }}>Neden Kaybedildi: {m.kayipSebebi || '—'}</small>}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            <section className="content-grid">
              <div className="crm-card" style={{ minHeight: 300 }}>
                <h3>Müşteriler</h3>
                {!musteriler.length && <p className="bos-mesaj">Henüz Müşteri Yok.</p>}
                {ASAMALAR.filter(a => musteriler.some(m => m.asama === a)).map(asama => (
                  <div key={asama} style={{ marginBottom: 14 }}>
                    <div className="asama-baslik">{asama}</div>
                    {musteriler.filter(m => m.asama === asama).map(m => (
                      <div key={m.id} className="task-item" style={{ cursor: 'pointer', flexDirection: 'column', alignItems: 'flex-start' }} onClick={() => { setSeciliId(m.id); setAktifSekme('Müşteriler'); }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                          <b>{m.sirketUnvani}</b>
                          {LIMITLER[asama] && gunFarki(m.asamaTarihi) >= LIMITLER[asama] && <span className="uyari-badge">{gunFarki(m.asamaTarihi)} gün</span>}
                        </div>
                        <small style={{ color: 'var(--text-muted)' }}>
                          Durum: {m.durum || '—'} &nbsp;|&nbsp; Temsilci: {m.temsilci || '—'}
                        </small>
                        {!!musteriCirosu(m.id) && <small style={{ color: 'var(--text-muted)' }}>{formatPara(musteriCirosu(m.id))}</small>}
                        {m.planTarihi && <small style={{ color: '#4f46e5' }}>{m.planTarihi} — {m.planNotu}</small>}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              <div className="crm-card" style={{ minHeight: 300 }}>
                <h3>Son Aktiviteler</h3>
                {hatirlatmalar.map(m => (
                  <div
                    key={`h-${m.id}`}
                    className="gorev-item uyari"
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                    onClick={() => { setSeciliId(m.id); setAktifSekme('Müşteriler'); }}
                  >
                    <span> <b>{m.sirketUnvani}</b> — {m.asama} aşamasında</span>
                    <span className="uyari-badge">{gunFarki(m.asamaTarihi)} gün</span>
                  </div>
                ))}
                {[...islemler].sort((a, b) => b.tarih.localeCompare(a.tarih)).slice(0, 6).map(i => {
                  const m = musteriler.find(x => x.id === i.musteriId);
                  return (
                    <div key={i.id} className="task-item" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10 }} onClick={() => { setSeciliId(i.musteriId); setAktifSekme('Müşteriler'); }}>
                      <span className="mini-avatar" style={{ width: 28, height: 28, borderRadius: '50%', fontSize: 12, flexShrink: 0 }}>{m?.sirketUnvani?.[0] || '?'}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                          <b>{m?.sirketUnvani || '—'}</b>
                          <small style={{ color: 'var(--text-muted)' }}>{i.tarih}</small>
                        </div>
                        <small style={{ color: 'var(--text-muted)' }}>{i.tip}{i.not ? ` — ${i.not}` : ''}</small>
                      </div>
                    </div>
                  );
                })}
                {!hatirlatmalar.length && !islemler.length && <p className="bos-mesaj">Henüz aktivite yok.</p>}
              </div>
            </section>
          </>
        )}


        {/* ── MÜŞTERİLER ── */}
        {aktifSekme === 'Müşteriler' && (
          <>

          <section className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <div className="stat-card"><div><p className="stat-label">Toplam Müşteri</p><h3>{musteriler.length}</h3></div></div>
            <div className="stat-card"><div><p className="stat-label">Aktif Fırsat</p><h3>{musteriler.filter(m => !['Kazanıldı', 'Kaybedildi'].includes(m.asama)).length}</h3></div></div>
            <div className="stat-card"><div><p className="stat-label">Toplam Ciro</p><h3>{formatPara(toplamCiro)}</h3></div></div>
          </section>
<div className="record-bar">
  <button className="new-button" onClick={() => setFormAcik(true)}>+ Yeni Müşteri</button>
  <input
    className="form-input"
    placeholder="Müşteri Ara"
    value={arama}
    onChange={e => setArama(e.target.value)}
    style={{ width: 180 }}
  />
</div>

<div className="tablo-wrap" style={{ margin: '0 28px' }}>
  <table className="islem-tablo">
    <thead>
      <tr><th>Profil</th><th>İletişim</th><th>Durum</th><th>Ciro</th></tr>
    </thead>
    <tbody>
      {filtrelenmisMusteriler.map(m => {
        const durumRenk = { 'Kazanılan': 'Başarılı', 'Kaybedilen': 'Başarısız', 'Bekleyen': 'İşleniyor', 'Görüşülen': 'Not' }[durumHesapla(m)] || 'Not';
        return (
          <tr key={m.id} onClick={() => setSeciliId(m.id)} style={{ cursor: 'pointer', background: seciliId === m.id ? 'var(--primary-light)' : 'transparent' }}>
            <td style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="avatar" style={{ width: 28, height: 28, fontSize: 12 }}>{m.sirketUnvani?.[0] || '?'}</span>
              {m.sirketUnvani}
            </td>
            <td>{m.email || '—'}<br /><small style={{ color: 'var(--text-muted)' }}>{m.telefon || '—'}</small></td>
           <td><span className={`islem-tip-rozet islem-tip-${durumRenk}`}>{durumHesapla(m)}</span></td>
            <td>{formatPara(musteriCirosu(m.id))}</td>
          </tr>
        );
      })}
    </tbody>
  </table>
</div>

            {formAcik && (
              <div className="mini-form">
                <input className="form-input" placeholder="Şirket Adı *" value={yeniForm.sirketUnvani} onChange={e => setYeniForm({ ...yeniForm, sirketUnvani: e.target.value })} />
                <input className="form-input" placeholder="Marka Adı *" value={yeniForm.markaAdi} onChange={e => setYeniForm({ ...yeniForm, markaAdi: e.target.value })} />
                <input className="form-input" placeholder=".com" value={yeniForm.domain} onChange={e => setYeniForm({ ...yeniForm, domain: e.target.value })} />
                <input className="form-input" placeholder="Satış Temsilcisi" value={yeniForm.temsilci} onChange={e => setYeniForm({ ...yeniForm, temsilci: e.target.value })} />
                <input className="form-input" placeholder="@outlook.com" value={yeniForm.email} onChange={e => setYeniForm({ ...yeniForm, email: e.target.value })} />
                <input className="form-input" placeholder="Telefon" value={yeniForm.telefon} onChange={e => setYeniForm({ ...yeniForm, telefon: e.target.value })} />
                <input className="form-input" placeholder="Şehir" value={yeniForm.sehir} onChange={e => setYeniForm({ ...yeniForm, sehir: e.target.value })} />
                <input className="form-input" placeholder="Semt" value={yeniForm.semt} onChange={e => setYeniForm({ ...yeniForm, semt: e.target.value })} />
                <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                  <button onClick={musteriEkle} className="new-button">Kaydet</button>
                  <button onClick={() => setFormAcik(false)}>İptal</button>
                </div>
              </div>
            )}

            {!seciliMusteri ? (
              <p className="bos-mesaj">Müşteri seçin ya da yeni ekleyin.</p>
            ) : (
              <main className="record-layout">
                <section className="record-main">
                  <div className="stage-bar">
                    {ASAMALAR.map((asama, i) => {
                      const aktifIndex = ASAMALAR.indexOf(seciliMusteri.asama);
                      const asamaSayisi = musteriler.filter(m => m.asama === asama).length;
                      return (
                        <button key={asama} className={i <= aktifIndex ? 'done' : ''} onClick={() => asamaDegistir(asama)}>
                          {asama}{i < aktifIndex && ' ✓'}
                          {asamaSayisi > 0 && (
                            <span style={{ marginLeft: 6, background: '#e2e8f0', color: '#64748b', borderRadius: 10, padding: '1px 7px', fontSize: 11 }}>
                              {asamaSayisi}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>


                  <article className="detail-card">
                    {seciliMusteri.asama === 'Kazanıldı' && <div className="won-ribbon">KAZANILDI</div>}
                    <div className="detail-heading">
                      <div className="avatar" style={{ width: 72, height: 72, borderRadius: 8, fontSize: 32 }}>
                        {seciliMusteri.sirketUnvani?.[0] || '?'}
                      </div>
                      <div style={{ flex: 1 }}>
                        <h1 style={{ margin: 0, fontSize: 28 }}>{seciliMusteri.sirketUnvani}</h1>
                      </div>
                      <button onClick={musteriSil} style={{ background: '#fee2e2', color: '#b91c1c', border: 'none', borderRadius: 6, padding: '6px 12px', cursor: 'pointer' }}>Sil</button>
                    </div>

                    {durumHesapla(seciliMusteri) === 'Kaybedilen' && (
                      <label style={{ display: 'block', marginBottom: 16 }}>
                        Kaybedilme Sebebi
                        <input className="form-input" style={{ marginTop: 4 }} value={seciliMusteri.kayipSebebi || ''} onChange={e => musteriGuncelle('kayipSebebi', e.target.value)} placeholder="Örn. Fiyat yüksek bulundu" />
                      </label>
                    )}

                    {durumHesapla(seciliMusteri) === 'Bekleyen' && (
                      <label style={{ display: 'block', marginBottom: 16 }}>
                        Bekleme Sebebi
                        <input className="form-input" style={{ marginTop: 4 }} value={seciliMusteri.beklemeSebebi || ''} onChange={e => musteriGuncelle('beklemeSebebi', e.target.value)} placeholder="Örn. Bütçe onayı bekleniyor" />
                      </label>
                    )}

                    <div className="value-row">
                      <div><span>Ciro</span><b style={{ display: 'block', marginTop: 8 }}>{formatPara(musteriCirosu(seciliMusteri.id))}</b></div>
                      <div><span>Teklif Oranı</span><input className="form-input" style={{ marginTop: 4 }} placeholder="%" value={seciliMusteri.teklifOrani || ''} onChange={e => musteriGuncelle('teklifOrani', e.target.value)} /></div>
                      <div><span>Hakediş</span><b style={{ display: 'block', marginTop: 8 }}>{hakedisHesapla(musteriCirosu(seciliMusteri.id), seciliMusteri.teklifOrani)}</b></div>
                      <div><span>Satış Temsilcisi</span><b style={{ display: 'block', marginTop: 8 }}>{seciliMusteri.temsilci || '—'}</b></div>
                      <div className="value-row" style={{ marginTop: 12 }}>
                        <div><span>Yönlendiren (İş Ortağı)</span><input className="form-input" style={{ marginTop: 4 }} placeholder="Örn. Ahmet Yılmaz" value={seciliMusteri.yonlendiren || ''} onChange={e => musteriGuncelle('yonlendiren', e.target.value)} /></div>
                        <div><span>Gelir Payı Oranı</span><input className="form-input" style={{ marginTop: 4 }} placeholder="%" value={seciliMusteri.gelirPayiOrani || ''} onChange={e => musteriGuncelle('gelirPayiOrani', e.target.value)} /></div>
                      </div>
                    </div>

                    <Bilgi etiketi="E-posta" deger={seciliMusteri.email} />
                    <Bilgi etiketi="Telefon" deger={seciliMusteri.telefon} />
                    <Bilgi etiketi="Şehir" deger={seciliMusteri.sehir} />
                    <Bilgi etiketi="Semt" deger={seciliMusteri.semt} />
                    <Bilgi etiketi="Aşama Başlangıcı" deger={seciliMusteri.asamaTarihi} />

                    {/* ENTEGRASYON SEÇİMLERİ */}
                    <div style={{ marginTop: 16, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                      <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Muhasebe Programı</span>
                      <select className="form-input" style={{ marginTop: 6 }} value={seciliMusteri.muhasebeProgramlari || ''} onChange={e => musteriGuncelle('muhasebeProgramlari', e.target.value)}>
                        <option value="">Seçiniz...</option>
                        {MUHASEBE_PROGRAMLARI.map(m => <option key={m} value={m}>{m}</option>)}
                      </select>
                    </div>

                    {/* GELECEK PLAN / HATIRLATICI */}
                    <div style={{ marginTop: 16, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                      <span style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 600 }}>Gelecek Plan & Hatırlatıcı</span>
                      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <input type="date" className="form-input" style={{ width: 150 }} value={seciliMusteri.planTarihi || ''} onChange={e => musteriGuncelle('planTarihi', e.target.value)} />
                        <input className="form-input" style={{ flex: 1 }} placeholder="Plan Notu (Örn. Görüşme yapılacak)" value={seciliMusteri.planNotu || ''} onChange={e => musteriGuncelle('planNotu', e.target.value)} />
                      </div>
                    </div>

                    {/* İŞLEM / TARİH EKLEME KISMI */}
                    <div style={{ marginTop: 16, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                      <span style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 600 }}>Tarihli Not & Güncelleme Ekle</span>
                      <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                        <input type="date" className="form-input" style={{ width: 150 }} value={yeniTarih} onChange={e => setYeniTarih(e.target.value)} />
                        <input className="form-input" style={{ flex: 1 }} placeholder="Açıklama / Yorum" value={yeniYorum} onChange={e => setYeniYorum(e.target.value)} />
                        <button onClick={tarihEkle} className="new-button">Ekle</button>
                      </div>

                      <div style={{ marginTop: 12 }}>
                        {islemler.filter(i => i.musteriId === seciliMusteri.id).map(i => (
                          <div key={i.id} className="task-item" style={{ justifyContent: 'space-between' }}>
                            <span><small style={{ color: 'var(--primary)', fontWeight: 600 }}>{i.tarih}</small> - {i.not || i.tip}</span>
                            <button onClick={() => tarihSil(i.id)} style={{ background: 'none', border: 'none', color: '#b91c1c', cursor: 'pointer', fontSize: 12 }}>Sil</button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </article>
                </section>
              </main>
            )}
          </>
        )}

          {/* ── TAKVİM ── */}
          {aktifSekme === 'Takvim' && (
            <div className="crm-card" style={{ margin: '0 28px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <button onClick={() => setTakvimAy(new Date(takvimAy.getFullYear() - 1, 0, 1))}>‹</button>
                <h3 style={{ margin: 0 }}>{takvimAy.getFullYear()}</h3>
                <button onClick={() => setTakvimAy(new Date(takvimAy.getFullYear() + 1, 0, 1))}>›</button>
              </div>

              {!googleToken && (
                <p className="bos-mesaj">Google Takvim bağlantısı bekleniyor... <span style={{ color: 'var(--primary)', cursor: 'pointer', fontWeight: 600 }} onClick={googleGirisYap}>Tekrar dene</span></p>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
                {Array.from({ length: 12 }, (_, ay) => (
                  <div key={ay}>
                    <b style={{ fontSize: 13 }}>{new Date(takvimAy.getFullYear(), ay, 1).toLocaleDateString('tr-TR', { month: 'long' })}</b>
                    <div className="takvim-grid" style={{ marginTop: 6 }}>
                      {HAFTA_GUNLERI.map(g => <div key={g} className="takvim-baslik">{g}</div>)}
                      {ayGunleriOlustur(takvimAy.getFullYear(), ay).map((tarih, idx) => {
                        if (!tarih) return <div key={idx} />;
                        const tStr = tarihStr(tarih);
                        const gununEtkinlikleri = etkinliklerTarihe[tStr];
                        return (
                          <div
                            key={idx}
                            className={`takvim-gun${gununEtkinlikleri ? ' dolu' : ''}${seciliGun === tStr ? ' secili' : ''}`}
                            title={gununEtkinlikleri ? gununEtkinlikleri.join('\n') : ''}
                            onClick={() => { setSeciliGun(tStr); setYeniTarih(tStr); }}
                          >
                            {tarih.getDate()}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              {seciliGun && (
                <div className="crm-card" style={{ marginTop: 20 }}>
                  <h3>{seciliGun}</h3>
                  {(etkinliklerTarihe[seciliGun] || []).length === 0 && <p className="bos-mesaj">Bu günde etkinlik yok.</p>}
                  {googleEtkinlikler.filter(e => (e.start?.date || e.start?.dateTime?.slice(0, 10)) === seciliGun).map(e => (
                    <div key={e.id} className="task-item" style={{ justifyContent: 'space-between' }}>
                      <span>{e.summary || '(başlıksız)'}</span>
                      <button onClick={() => googleEtkinlikSil(e.id)} style={{ background: 'none', border: 'none', color: '#b91c1c', cursor: 'pointer' }}>×</button>
                    </div>
                  ))}
                  <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                    <input className="form-input" placeholder="Etkinlik başlığı..." value={yeniYorum} onChange={e => setYeniYorum(e.target.value)} style={{ flex: 1 }} />
                    <button className="new-button" onClick={googleEtkinlikEkle} disabled={!googleToken}>Ekle</button>
                  </div>
                </div>
              )}
            </div>
          )}

        {/* ── RAPORLAR ── */}
        {aktifSekme === 'Raporlar' && (
          <div style={{ padding: '0 28px' }}>
            <div className="crm-card" style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <h3 style={{ margin: 0 }}>Dönem Özeti</h3>
                <button className="new-button" onClick={excelIndir}>Excel'e Aktar</button>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16, marginTop: 12 }}>
                {['Bugün', 'Son 7 Gün', 'Son 30 Gün', 'Bu Ay'].map(f => (
                  <button key={f} onClick={() => setRaporDonem(f)} style={{ padding: '4px 14px', borderRadius: 20, border: '1px solid var(--border)', background: raporDonem === f ? 'var(--primary)' : 'transparent', color: raporDonem === f ? '#fff' : 'inherit', cursor: 'pointer', fontSize: 13 }}>
                    {f}
                  </button>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
                <div><p className="stat-label">Başarı Oranı</p><h3>%{raporMetrikleri.oran}</h3></div>
                <div><p className="stat-label">Başarılı / Başarısız</p><h3>{raporMetrikleri.basarili} / {raporMetrikleri.basarisiz}</h3></div>
                <div><p className="stat-label">En Aktif Banka</p><h3>{raporMetrikleri.enAktifBanka}</h3></div>
                <div><p className="stat-label">Dönem Cirosu</p><h3>{formatPara(raporMetrikleri.donemCiro)}</h3></div>
              </div>
            </div>

            <section className="stats-grid">
              <div className="stat-card"><div><p className="stat-label">Toplam Müşteri</p><h3>{musteriler.length}</h3></div></div>
              <div className="stat-card"><div><p className="stat-label">Kazanılan</p><h3>{kazanilan}</h3></div></div>
              <div className="stat-card"><div><p className="stat-label">Kazanma Oranı</p><h3>%{musteriler.length ? Math.round(kazanilan / musteriler.length * 100) : 0}</h3></div></div>
              <div className="stat-card"><div><p className="stat-label">Toplam Ciro</p><h3>{formatPara(toplamCiro)}</h3></div></div>
            </section>

<div className="crm-card" style={{ marginTop: 16 }}>
  <h3>Satış (Aşama Raporu)</h3>
  <div className="tablo-wrap">
    <table className="islem-tablo">
      <thead>
        <tr><th>Aşama</th><th>Müşteri Sayısı</th><th>Toplam Ciro</th><th>Ort. Gün (bu aşamada)</th></tr>
      </thead>
      <tbody>
        {ASAMALAR.map(asama => {
          const buAsamadakiler = musteriler.filter(m => m.asama === asama);
          const toplamCiroBuAsama = buAsamadakiler.reduce((t, m) => t + musteriCirosu(m.id), 0);
          const gunler = buAsamadakiler.map(m => gunFarki(m.asamaTarihi)).filter(g => g > 0);
          const ortGun = gunler.length ? Math.round(gunler.reduce((t, g) => t + g, 0) / gunler.length) : 0;
          return (
            <tr key={asama}>
              <td>{asama}</td>
              <td>{buAsamadakiler.length}</td>
              <td>{formatPara(toplamCiroBuAsama)}</td>
              <td>{ortGun} gün</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  </div>
</div>

            <div className="crm-card" style={{ marginTop: 16 }}>
              <h3>Son İşlemler</h3>
              {odemeler.length === 0 ? (
                <p className="bos-mesaj">Kayıt yok.</p>
              ) : (
                <div className="tablo-wrap">
                  <table className="islem-tablo">
                    <thead>
                      <tr><th>Tarih</th><th>İşlem Tipi</th><th>Tutar</th><th>Durum</th></tr>
                    </thead>
                    <tbody>
                      {[...odemeler].sort((a, b) => b.tarih.localeCompare(a.tarih)).slice(0, 10).map(o => (
                        <tr key={o.id}>
                          <td>{o.tarih}</td>
                          <td>{o.islemTipi}</td>
                          <td>{formatPara(o.tutar)}</td>
                          <td><span className={`islem-tip-rozet islem-tip-${o.durum}`}>{o.durum}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="crm-card" style={{ marginTop: 16, marginBottom: 16 }}>
              <h3>Kayıtlı Kart Raporları</h3>
              <p className="stat-label" style={{ marginBottom: 12 }}>Sistem genelinde {kayitliKartlar.length} benzersiz kart kaydı</p>
              {kayitliKartlar.length === 0 ? (
                <p className="bos-mesaj">Kayıt yok.</p>
              ) : (
                <div className="tablo-wrap">
                  <table className="islem-tablo">
                    <thead>
                      <tr><th>Kart</th><th>Kart Bankası</th><th>Kart Tipi</th><th>Müşteri</th></tr>
                    </thead>
                    <tbody>
                      {kayitliKartlar.map(k => (
                        <tr key={k.kart}>
                          <td>{k.kart}</td>
                          <td>{k.kartBankasi}</td>
                          <td>{k.kartTipi}</td>
                          <td>{k.musteri}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── İŞLEMLER SEKME İÇERİĞİ ── */}
         
{aktifSekme === 'İşlemler' && (
  <div className="crm-card" style={{ margin: '0 28px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
      <h3 style={{ margin: 0 }}>İşlemler</h3>
      <button className="new-button" onClick={() => {
        if (islemAltSekme === 'Tümü') excelIndir();
        else if (islemAltSekme === 'İş Ortakları') isOrtaklariExcelIndir();
        else if (islemAltSekme === 'Hakediş') hakedisExcelIndir();
        else if (islemAltSekme === 'Faturalar') faturaExcelIndir();
      }}>Excel'e Aktar</button>
    </div>
    {islemAltSekme === 'Tümü' && (
    odemeler.length === 0 ? (
      <p className="bos-mesaj">Ödeme kaydı yok.</p>
    ) : (
      <div className="tablo-wrap">
        <table className="islem-tablo">
          <thead>
            <tr>
              <th>Müşteri</th><th>Banka</th><th>Sanal POS</th><th>Sipariş No</th><th>İşlem No</th>
              <th>İşlem Tipi</th><th>Durum</th><th>Tarih</th><th>Tutar</th><th>Para Birimi</th>
              <th>E-posta</th><th>Kart</th><th>Kart Bankası</th><th>Kart Tipi</th><th>3D Güvenli</th><th>Sonuç</th>
            </tr>
          </thead>
          <tbody>
            {odemeler.map(o => {
              const m = musteriler.find(x => x.id === o.musteriId);
              return (
                <tr key={o.id}>
                  <td>{m?.sirketUnvani || '—'}</td>
                  <td>{o.banka}</td>
                  <td>{o.sanalPos}</td>
                  <td>{o.siparisNo}</td>
                  <td>{o.islemNo}</td>
                  <td>{o.islemTipi}</td>
                  <td><span className={`islem-tip-rozet islem-tip-${o.durum}`}>{o.durum}</span></td>
                  <td>{o.tarih}</td>
                  <td>{formatPara(o.tutar)}</td>
                  <td>{o.paraBirimi}</td>
                  <td>{o.eposta}</td>
                  <td>{o.kart}</td>
                  <td>{o.kartBankasi}</td>
                  <td>{o.kartTipi}</td>
                  <td>{o.guvenli3D}</td>
                  <td>{o.sonuc}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    )
)}

{islemAltSekme === 'Hakediş' && (
  <div>
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
      <div className="crm-card" style={{ flex: 1, minWidth: 180 }}>
        <p className="stat-label">Toplam Tutar</p>
        <h3>{formatPara(hakedisOzeti.toplamTutar)}</h3>
      </div>
      <div className="crm-card" style={{ flex: 1, minWidth: 180 }}>
        <p className="stat-label">Ödenen</p>
        <h3>{formatPara(hakedisOzeti.odenen)}</h3>
      </div>
      <div className="crm-card" style={{ flex: 1, minWidth: 180 }}>
        <p className="stat-label">Net Bakiye</p>
        <h3>{formatPara(hakedisOzeti.netBakiye)}</h3>
      </div>
    </div>

    <div className="tablo-wrap">
      <table className="islem-tablo">
        <thead>
          <tr><th>Müşteri</th><th>Toplam</th><th>Onaylanan</th><th>Ödenen</th><th>Net Bakiye</th></tr>
        </thead>
        <tbody>
          {hakedisOzeti.musteriOzeti.map((o, i) => (
            <tr key={i}>
              <td>{o.musteri}</td>
              <td>{formatPara(o.toplam)}</td>
              <td>{formatPara(o.onaylanan)}</td>
              <td>{formatPara(o.odenen)}</td>
              <td>{formatPara(o.netBakiye)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {hakedisOzeti.musteriOzeti.length === 0 && <p className="bos-mesaj">Henüz fatura kaydı yok.</p>}
    </div>
  </div>
)}

{islemAltSekme === 'İş Ortakları' && (
  <div className="pos-grid">
    {isOrtaklari.length === 0 && <p className="bos-mesaj">Henüz yönlendiren/iş ortağı bilgisi girilmiş müşteri yok.</p>}
    {isOrtaklari.map(o => (
      <div key={o.ad} className="pos-kart" style={{ cursor: 'default', alignItems: 'stretch' }}>
        <b>{o.ad}</b>
        <span>{o.musteriListesi.length} alt üye işyeri &nbsp;·&nbsp; {formatPara(o.toplamHakedis)} hakediş</span>
        <div style={{ marginTop: 10 }}>
          {o.musteriListesi.map(m => (
            <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, padding: '6px 0', borderTop: '1px solid var(--border)' }}>
              <span>{m.sirketUnvani}</span>
              <span>{formatPara(Math.floor(musteriCirosu(m.id) * parseSayi(m.gelirPayiOrani) / 100))}</span>
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
)}

{islemAltSekme === 'Faturalar' && (
  <div>
    <div className="mini-form" style={{ margin: '0 0 16px', maxWidth: 'none', flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center' }}>
      <select className="form-input" style={{ width: 'auto' }} value={yeniFaturaForm.musteriId} onChange={e => setYeniFaturaForm({ ...yeniFaturaForm, musteriId: e.target.value })}>
        <option value="">Müşteri seç</option>
        {musteriler.map(m => <option key={m.id} value={m.id}>{m.sirketUnvani}</option>)}
      </select>
      <input className="form-input" style={{ width: 130 }} placeholder="Fatura No" value={yeniFaturaForm.faturaNo} onChange={e => setYeniFaturaForm({ ...yeniFaturaForm, faturaNo: e.target.value })} />
      <input type="date" className="form-input" style={{ width: 150 }} value={yeniFaturaForm.tarih} onChange={e => setYeniFaturaForm({ ...yeniFaturaForm, tarih: e.target.value })} />
      <input className="form-input" style={{ width: 100 }} placeholder="Tutar" value={yeniFaturaForm.tutar} onChange={e => setYeniFaturaForm({ ...yeniFaturaForm, tutar: e.target.value })} />
      <input type="date" className="form-input" style={{ width: 150 }} value={yeniFaturaForm.valorTarihi} onChange={e => setYeniFaturaForm({ ...yeniFaturaForm, valorTarihi: e.target.value })} />
      <input className="form-input" style={{ flex: 1, minWidth: 140 }} placeholder="Not" value={yeniFaturaForm.notlar} onChange={e => setYeniFaturaForm({ ...yeniFaturaForm, notlar: e.target.value })} />
      <button className="new-button" onClick={() => {
        if (!yeniFaturaForm.musteriId || !yeniFaturaForm.faturaNo || !yeniFaturaForm.tarih || !yeniFaturaForm.tutar) return;
        faturaEkle({ ...yeniFaturaForm, musteriId: Number(yeniFaturaForm.musteriId) });
        setYeniFaturaForm({ musteriId: '', faturaNo: '', tarih: '', tutar: '', valorTarihi: '', notlar: '' });
      }}>+ Yeni Fatura</button>
    </div>

    <div className="tablo-wrap">
      <table className="islem-tablo">
        <thead>
          <tr>
            <th>Müşteri</th><th>Fatura No</th><th>Tarih</th><th>Tutar</th><th>Onaylanan</th>
            <th>Ödenen</th><th>Kalan</th><th>Valör Tarihi</th><th>Notlar</th><th>Durum</th><th>İşlemler</th>
          </tr>
        </thead>
        <tbody>
          {faturalar.map(f => {
            const m = musteriler.find(x => x.id === f.musteriId);
            const kalan = parseSayi(f.tutar) - parseSayi(f.odenen);
            const durumRozet = f.durum === 'Ödendi' ? 'Başarılı' : f.durum === 'Onaylandı' ? 'İşleniyor' : 'Not';
            return (
              <tr key={f.id}>
                <td>{m?.sirketUnvani || '—'}</td>
                <td>{f.faturaNo}</td>
                <td>{f.tarih}</td>
                <td>{formatPara(f.tutar)}</td>
                <td>{formatPara(f.onaylanan)}</td>
                <td>{formatPara(f.odenen)}</td>
                <td>{formatPara(kalan)}</td>
                <td>{f.valorTarihi || '—'}</td>
                <td>{f.notlar || '—'}</td>
                <td><span className={`islem-tip-rozet islem-tip-${durumRozet}`}>{f.durum}</span></td>
                <td style={{ display: 'flex', gap: 6 }}>
                  {f.durum === 'Onaylanmadı' && <button onClick={() => faturaOnayla(f)} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 4, padding: '2px 8px', cursor: 'pointer', fontSize: 11 }}>Onayla</button>}
                  {f.durum !== 'Ödendi' && <button onClick={() => faturaOde(f)} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 4, padding: '2px 8px', cursor: 'pointer', fontSize: 11 }}>Ödendi</button>}
                  <button onClick={() => faturaSil(f.id)} style={{ background: 'none', border: 'none', color: '#b91c1c', cursor: 'pointer' }}>×</button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {faturalar.length === 0 && <p className="bos-mesaj">Henüz fatura kaydı yok.</p>}
    </div>
  </div>
)}
  </div>
)}

{aktifSekme === 'Sanal POS' && (
  <div style={{ padding: '0 28px' }}>
    <div style={{ background: 'var(--primary-light)', borderRadius: 12, padding: '16px 20px', marginBottom: 16 }}>
      <h3 style={{ margin: 0 }}>Sanal POS Yönetimi</h3>
      <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-muted)' }}>Ödeme sağlayıcıları ve sanal POS konfigürasyonları</p>
    </div>

    <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', justifyContent: 'space-between' }}>
      <input className="form-input" placeholder="Banka ara..." value={posArama} onChange={e => setPosArama(e.target.value)} style={{ maxWidth: 260 }} />
      <div style={{ display: 'flex', gap: 8 }}>
        {['Tümü', 'Aktif', 'Pasif'].map(f => (
          <button key={f} onClick={() => setPosFiltre(f)} style={{ padding: '4px 14px', borderRadius: 20, border: '1px solid var(--border)', background: posFiltre === f ? 'var(--primary)' : 'transparent', color: posFiltre === f ? '#fff' : 'inherit', cursor: 'pointer', fontSize: 13 }}>
            {f}
          </button>
        ))}
      </div>
    </div>

    <div className="pos-grid">
      {BANKALAR.filter(b => b.toLowerCase().includes(posArama.toLowerCase())).map(b => {
        const musteriListesi = musteriler
          .map(m => ({ m, durum: bankaDurumu(m, b) }))
          .filter(({ durum }) => posFiltre === 'Tümü' ? durum : durum === posFiltre);
        return (
          <div key={b} className="pos-kart" style={{ cursor: 'default', alignItems: 'stretch' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <b>{b}</b>
              <button className="new-button" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => setEklemeAcikBanka(eklemeAcikBanka === b ? null : b)}>+ POS Ekle</button>
            </div>

            {eklemeAcikBanka === b && (
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <select className="pos-ekle-select" value={eklemeMusteriId} onChange={e => setEklemeMusteriId(e.target.value)}>
                  <option value="">Müşteri seç</option>
                  {musteriler.filter(m => !bankaDurumu(m, b)).map(m => <option key={m.id} value={m.id}>{m.sirketUnvani}</option>)}
                </select>
                <label style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14 }}>
                  <span className="toggle-switch">
                    <input type="checkbox" checked={eklemeGuvenli3D === 'Açık'} onChange={e => setEklemeGuvenli3D(e.target.checked ? 'Açık' : 'Kapalı')} />
                    <span className="toggle-slider"></span>
                  </span>
                  3D Secure
                </label>
                <button className="pos-ekle-buton" onClick={() => {
                  const secilen = musteriler.find(m => m.id === Number(eklemeMusteriId));
                  if (secilen) posEkleMusteri(secilen, b, eklemeGuvenli3D);
                  setEklemeAcikBanka(null);
                  setEklemeMusteriId('');
                }}>Ekle</button>
              </div>
            )}



            <div style={{ marginTop: 10 }}>
              {musteriListesi.length === 0 ? (
                <span style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', textAlign: 'center', padding: '14px 0' }}>Henüz sanal POS eklenmemiş</span>
              ) : musteriListesi.map(({ m, durum }) => (
                <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, padding: '6px 0', borderTop: '1px solid var(--border)' }}>
                  <div>
                    <div>{m.sirketUnvani}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span
                        onClick={() => posDurumDegistirMusteri(m, b)}
                        style={{ cursor: 'pointer', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600, background: durum === 'Aktif' ? 'var(--primary)' : 'var(--border)', color: durum === 'Aktif' ? '#fff' : 'var(--text-muted)' }}
                      >
                        {durum}
                      </span>
                      <select className="form-input" style={{ width: 'auto', fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 10, border: '1px solid var(--border)', color: 'var(--text-muted)', background: '#fff' }} value={kartSemasiOku(m, b)} onChange={e => kartSemasiSec(m, b, e.target.value)}>
                      <option value="">Kart Şeması</option>
                      {KART_SEMALARI.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    </div>
                  </div>
                  <button onClick={() => posKaldirMusteri(m, b)} style={{ background: 'none', border: 'none', color: '#b91c1c', cursor: 'pointer', fontSize: 14 }}>×</button>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>


  </div>
)}

{aktifSekme === 'Kullanıcılar' && (
  <div className="crm-card" style={{ margin: '0 28px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
      <h3 style={{ margin: 0 }}>Kullanıcılar</h3>
      <button className="new-button" onClick={() => setKullaniciFormAcik(a => !a)}>+ Yeni Kullanıcı</button>
    </div>

    {kullaniciFormAcik && (
      <div className="mini-form" style={{ marginBottom: 16 }}>
        <input className="form-input" placeholder="Kullanıcı Adı *" value={yeniKullaniciForm.kullaniciAdi} onChange={e => setYeniKullaniciForm({ ...yeniKullaniciForm, kullaniciAdi: e.target.value })} />
        <input className="form-input" placeholder="Ad Soyad" value={yeniKullaniciForm.adSoyad} onChange={e => setYeniKullaniciForm({ ...yeniKullaniciForm, adSoyad: e.target.value })} />
        <input className="form-input" type="password" placeholder="Şifre *" value={yeniKullaniciForm.sifre} onChange={e => setYeniKullaniciForm({ ...yeniKullaniciForm, sifre: e.target.value })} />
        <select className="form-input" value={yeniKullaniciForm.kullaniciTipi} onChange={e => setYeniKullaniciForm({ ...yeniKullaniciForm, kullaniciTipi: e.target.value })}>
          <option value="Portal">Portal</option>
          <option value="API">API</option>
        </select>
        <select className="form-input" value={yeniKullaniciForm.yetki} onChange={e => setYeniKullaniciForm({ ...yeniKullaniciForm, yetki: e.target.value })}>
          <option value="">Yetki seçin</option>
          <option value="Yönetici">Yönetici</option>
          <option value="Satış Temsilcisi">Satış Temsilcisi</option>
          <option value="Görüntüleyici">Görüntüleyici</option>
        </select>
        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <button onClick={kullaniciEkle} className="new-button">Kaydet</button>
          <button onClick={() => setKullaniciFormAcik(false)}>İptal</button>
        </div>
      </div>
    )}

    {kullanicilar.length === 0 ? (
      <p className="bos-mesaj">Henüz kullanıcı yok.</p>
    ) : (
      <div className="tablo-wrap">
        <table className="islem-tablo">
          <thead>
            <tr>
              <th>Kullanıcı Adı</th><th>Ad Soyad</th><th>Kullanıcı Tipi</th><th>Yetki</th><th>Durum</th><th>İşlemler</th>
            </tr>
          </thead>
          <tbody>
            {kullanicilar.map(k => (
              <tr key={k.id}>
                <td>{k.kullaniciAdi}</td>
                <td>{k.adSoyad}</td>
                <td>{k.kullaniciTipi}</td>
                <td>{k.yetki}</td>
                <td>
                  <span className={`islem-tip-rozet islem-tip-${k.durum === 'Aktif' ? 'Başarılı' : 'Başarısız'}`}>{k.durum}</span>
                </td>
                <td style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => kullaniciDurumDegistir(k)} style={{ fontSize: 12, cursor: 'pointer', border: '1px solid var(--border)', background: 'none', borderRadius: 6, padding: '4px 8px' }}>
                    {k.durum === 'Aktif' ? 'Pasif Yap' : 'Aktif Yap'}
                  </button>
                  <button onClick={() => kullaniciSil(k.id)} style={{ fontSize: 12, cursor: 'pointer', border: 'none', background: 'none', color: '#b91c1c' }}>Sil</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
      </div>
    )}
  </div>
)}

  <div className="slider-wrap">
            <div className="slider-track">
              {[...ODEME_KURULUSLARI, ...BANKALAR, ...ODEME_KURULUSLARI, ...BANKALAR].map((ad, i) => (
                <div key={i} className="slider-kart">{ad} <span className="ok">→</span></div>
              ))}
            </div>
          </div>
      </main>
    </div>
  );
}

