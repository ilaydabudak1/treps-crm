import React, { useState, useMemo, useEffect } from 'react';
import './index.css';
import * as XLSX from 'xlsx';

// ── SABİTLER VE YARDIMCI FONKSİYONLAR ──
const ASAMALAR = ['Teklif', 'Değerlendirme', 'Sözleşme', 'Kazanıldı', 'Kaybedildi'];
const DURUMLAR = ['Görüşülen', 'Bekleyen', 'Kazanılan', 'Kaybedilen'];
const LIMITLER = { Teklif: 3, Değerlendirme: 3, Sözleşme: 5 };

const ODEME_KURULUSLARI = ['Qnbpay', 'İyzico', 'Payinall', 'Paynkolay', 'Lidio', 'ParatikaParam', 'PayTR', 'ZiraatPay', 'VakıfPay', 'MorPara', 'Moka', 'United', 'Tami'];
const BANKALAR = ['GarantiBBVA', 'Ziraat', 'TEB', 'VakıfBank', 'HalkBank', 'QNB', 'DenizBank', 'KuveytTürk', 'Türkiye İş Bankası', 'Akbank', 'Albaraka'];
const MUHASEBE_PROGRAMLARI = ['Logo', 'Netsis', 'Mikro', 'Paraşüt', 'Zirve', 'Bizim Hesap', 'Odoo', 'Nebim', 'ETA', 'Uyumsoft', 'Dia'];

const API_BASE = 'http://localhost:5279';

const gunFarki = t => t ? Math.floor((new Date() - new Date(t)) / 86400000) : 0;
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

// ── ANA BİLEŞEN ──
export default function App() {
  const [musteriler, setMusteriler] = useState([]);
  const [islemler, setIslemler] = useState([]);
  const [gorevler, setGorevler] = useState([]);
  const [odemeler , setOdemeler] = useState([]);

  const [seciliId, setSeciliId] = useState(null);
  const [aktifSekme, setAktifSekme] = useState('Dashboard');
  const [formAcik, setFormAcik] = useState(false);
  const [hatirlatmaAcik, setHatirlatmaAcik] = useState(false);

  const [arama, setArama] = useState('');
  const [donemFiltre, setDonemFiltre] = useState('Bu Ay');
  const [secilenDurum, setSecilenDurum] = useState(null);
  const [posFiltre, setPosFiltre] = useState('Tümü');
  
  const [yeniNot, setYeniNot] = useState('');
  const [yeniGorev, setYeniGorev] = useState('');
  const [yeniTarih, setYeniTarih] = useState('');
  const [yeniYorum, setYeniYorum] = useState('');

  const [yeniForm, setYeniForm] = useState({
    sirketUnvani: '', markaAdi: '', domain: '', email: '', telefon: '', sehir: '', temsilci: ''
  });

  // ── İLK YÜKLEME ──
  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/Islemler`).then(res => res.json()),
      fetch(`${API_BASE}/Musteri`).then(res => res.json()),
      fetch(`${API_BASE}/Gorevler`).then(res => res.json()),
      fetch(`${API_BASE}/Odemeler`).then(res => res.json())
    ]).then(([islemlerVeri, musteriVeri, gorevlerVeri, odemelerVeri]) => {
      setIslemler(islemlerVeri || []);
      setMusteriler(musteriVeri || []);
      setGorevler(gorevlerVeri || []);
      setOdemeler(odemelerVeri || []);
    }).catch(err => console.error('Veriler yüklenirken hata oluştu:', err));
  }, []);

  // ── HESAPLANAN VERİLER & MEMO ──
  const musteriCirosu = (musteriId) => islemler.filter(i => i.musteriId === musteriId).reduce((t, i) => t + Number(i.tutar || 0), 0);

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
        onSuccess?.();
      })
      .catch(err => console.error('İşlem eklenemedi:', err));
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
  const sayfa = XLSX.utils.json_to_sheet(veri);
  const kitap = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(kitap, sayfa, 'İşlemler');
  XLSX.writeFile(kitap, 'islemler.xlsx');
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

const posDurumDegistir = (banka) => {
  if (!seciliMusteri) return;
  const liste = (seciliMusteri.entegrasyonBanka || '').split(',').filter(Boolean);
  const mevcut = liste.find(k => k.startsWith(banka + ':'));
  let yeniListe;
  if (!mevcut) {
    yeniListe = [...liste, `${banka}:Aktif`];
  } else if (mevcut.endsWith(':Aktif')) {
    yeniListe = liste.map(k => k.startsWith(banka + ':') ? `${banka}:Pasif` : k);
  } else {
    yeniListe = liste.filter(k => !k.startsWith(banka + ':'));
  }
  musteriGuncelle('entegrasyonBanka', yeniListe.join(','));
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
        setYeniForm({ sirketUnvani: '', markaAdi: '', domain: '', email: '', telefon: '', sehir: '', temsilci: '' });
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

  const durumDegistir = (yeniDurum) => {
    if (!seciliMusteri || yeniDurum === seciliMusteri.durum) return;
    setMusteriler(eski => eski.map(m => m.id === seciliId ? { ...m, durum: yeniDurum } : m));
    musteriPut(seciliId, { durum: yeniDurum }).catch(err => console.error('Durum güncellenemedi:', err));
  };

  const gorevEkle = () => {
    if (!yeniGorev.trim()) return;
    fetch(`${API_BASE}/Gorevler`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ metin: yeniGorev, tamam: false })
    })
      .then(res => res.json())
      .then(yeniGorevKaydi => {
        setGorevler(eski => [...eski, yeniGorevKaydi]);
        setYeniGorev('');
      })
      .catch(err => console.error('Görev eklenemedi:', err));
  };

  const gorevToggle = (gorev) => {
    fetch(`${API_BASE}/Gorevler/${gorev.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ metin: gorev.metin, tamam: !gorev.tamam })
    })
      .then(() => {
        setGorevler(eski => eski.map(x => x.id === gorev.id ? { ...x, tamam: !x.tamam } : x));
      })
      .catch(err => console.error('Görev güncellenemedi:', err));
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

  return (
    <div className="crm-layout">
      {/* SIDEBAR */}
      <aside className="crm-sidebar">
        <div className="crm-logo"><span className="logo-icon">T</span> Treps <small>CRM</small></div>
        <nav className="sidebar-menu">
          {['Dashboard', 'Müşteriler', 'Takvim', 'Raporlar', 'İşlemler', 'Sanal POS', 'Kullanıcılar'].map(s => (
            <button key={s} className={`menu-btn ${aktifSekme === s ? 'active' : ''}`} onClick={() => setAktifSekme(s)}>{s}</button>
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
            <span className="avatar">İ</span>
          </div>
        </header>

        {/* ── DASHBOARD ── */}
        {aktifSekme === 'Dashboard' && (
          <>
            <div className="crm-card" style={{ margin: '0 28px 16px' }}>
              <p style={{ margin: '0 0 10px', fontWeight: 600 }}>İyi günler, İlayda 👋</p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                {['Bugün', 'Dün', 'Bu Hafta', 'Bu Ay'].map(f => (
                  <button key={f} onClick={() => setDonemFiltre(f)} style={{ padding: '4px 14px', borderRadius: 20, border: '1px solid var(--border)', background: donemFiltre === f ? 'var(--primary)' : 'transparent', color: donemFiltre === f ? '#fff' : 'inherit', cursor: 'pointer', fontSize: 13 }}>
                    {f}
                  </button>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                <div><p className="stat-label">Dönem Cirosu</p><h3>{formatPara(donemMetrikleri.ciro)}</h3></div>
                <div><p className="stat-label">Dönem Hakedişi</p><h3>{formatPara(donemMetrikleri.hakedis)}</h3></div>
                <div><p className="stat-label">Dönem İşlem Sayısı</p><h3>{donemMetrikleri.sayi}</h3></div>
              </div>
            </div>

            <section className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon-wrap stat-icon-mavi"></div>
                <div><p className="stat-label">Toplam Müşteri</p><h3>{musteriler.length}</h3></div>
              </div>
              <div className="stat-card">
                <div className="stat-icon-wrap stat-icon-yesil"></div>
                <div><p className="stat-label">Aktif Müşteri</p><h3>{aktifMusteriSayisi}</h3></div>
              </div>
              <div className="stat-card">
                <div className="stat-icon-wrap stat-icon-kirmizi"></div>
                <div><p className="stat-label">Pasif Müşteri</p><h3>{musteriler.length - aktifMusteriSayisi}</h3></div>
              </div>
              <div className="stat-card">
                <div className="stat-icon-wrap stat-icon-yesil"></div>
                <div><p className="stat-label">Kazanılan</p><h3>{kazanilan}</h3></div>
              </div>
              <div className="stat-card">
                <div className="stat-icon-wrap stat-icon-kirmizi"></div>
                <div><p className="stat-label">Hatırlatma</p><h3>{hatirlatmalar.length}</h3></div>
              </div>
            </section>

            <div className="crm-card" style={{ margin: '0 28px 16px' }}>
              <h3>Durum Dağılımı</h3>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                {DURUMLAR.map(durum => {
                  const sayi = musteriler.filter(m => m.durum === durum).length;
                  return (
                    <button
                      key={durum}
                      onClick={() => setSecilenDurum(secilenDurum === durum ? null : durum)}
                      style={{
                        flex: 1, minWidth: 140, padding: 16, borderRadius: 8,
                        border: secilenDurum === durum ? '2px solid var(--primary)' : '1px solid var(--border)',
                        background: secilenDurum === durum ? 'var(--primary-light)' : '#fff',
                        cursor: 'pointer', textAlign: 'left'
                      }}
                    >
                      <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{durum}</div>
                      <div style={{ fontSize: 24, fontWeight: 'bold' }}>{sayi}</div>
                    </button>
                  );
                })}
              </div>

              {secilenDurum && (
                <div>
                  <h4 style={{ marginBottom: 8 }}>{secilenDurum} Müşteriler</h4>
                  {musteriler.filter(m => m.durum === secilenDurum).length === 0 ? (
                    <p className="bos-mesaj">Bu durumda müşteri yok.</p>
                  ) : (
                    musteriler.filter(m => m.durum === secilenDurum).map(m => (
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
                        {!!musteriCirosu(m.id) && <small style={{ color: 'var(--text-muted)' }}>{formatPara(musteriCirosu(m.id))}</small>}
                        {m.planTarihi && <small style={{ color: '#4f46e5' }}>{m.planTarihi} — {m.planNotu}</small>}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              <div className="crm-card" style={{ minHeight: 300 }}>
                <h3>Görevler</h3>
                {hatirlatmalar.map(m => (
                  <div key={m.id} className="gorev-item uyari">
                    <b>{m.sirketUnvani}</b> — {m.asama} aşamasında {gunFarki(m.asamaTarihi)} gündür
                  </div>
                ))}
                {gorevler.map(g => (
                  <div key={g.id} className={`gorev-item ${g.tamam ? 'tamam' : ''}`} onClick={() => gorevToggle(g)}>
                    {g.tamam ? '☑' : '☐'} {g.metin}
                  </div>
                ))}
                <div className="note-input" style={{ marginTop: 12 }}>
                  <input className="form-input" placeholder="Yeni görev..." value={yeniGorev} onChange={e => setYeniGorev(e.target.value)} onKeyDown={e => e.key === 'Enter' && gorevEkle()} />
                  <button onClick={gorevEkle}>Ekle</button>
                </div>
              </div>
            </section>
          </>
        )}

        {/* ── MÜŞTERİLER ── */}
        {aktifSekme === 'Müşteriler' && (
          <>
            <div className="record-bar">
              <button className="new-button" onClick={() => setFormAcik(true)}>+ Yeni Müşteri</button>
              <input
                className="form-input"
                placeholder="Müşteri Ara"
                value={arama}
                onChange={e => setArama(e.target.value)}
                style={{ width: 180 }}
              />
              <div style={{ display: 'flex', gap: 6, overflowX: 'auto' }}>
                {filtrelenmisMusteriler.map(m => (
                  <button key={m.id} className={`menu-btn ${seciliId === m.id ? 'active' : ''}`} onClick={() => setSeciliId(m.id)} style={{ padding: '6px 12px', whiteSpace: 'nowrap' }}>
                    {m.sirketUnvani}
                  </button>
                ))}
              </div>
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

                  <div className="stage-bar" style={{ marginTop: 8 }}>
                    {DURUMLAR.map(durum => (
                      <button key={durum} className={seciliMusteri.durum === durum ? 'done' : ''} onClick={() => durumDegistir(durum)}>
                        {durum}
                      </button>
                    ))}
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

                    {seciliMusteri.durum === 'Kaybedilen' && (
                      <label style={{ display: 'block', marginBottom: 16 }}>
                        Kaybedilme Sebebi
                        <input className="form-input" style={{ marginTop: 4 }} value={seciliMusteri.kayipSebebi || ''} onChange={e => musteriGuncelle('kayipSebebi', e.target.value)} placeholder="Örn. Fiyat yüksek bulundu" />
                      </label>
                    )}

                    {seciliMusteri.durum === 'Bekleyen' && (
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
                    </div>

                    <Bilgi etiketi="E-posta" deger={seciliMusteri.email} />
                    <Bilgi etiketi="Telefon" deger={seciliMusteri.telefon} />
                    <Bilgi etiketi="Şehir" deger={seciliMusteri.sehir} />
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
            <h3>Takvim</h3>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
              <select className="form-input" style={{ width: 'auto' }} value={seciliId || ''} onChange={e => setSeciliId(Number(e.target.value))}>
                <option value="">Müşteri seç</option>
                {musteriler.map(m => <option key={m.id} value={m.id}>{m.sirketUnvani}</option>)}
              </select>
              <input type="date" className="form-input" style={{ width: 'auto' }} value={yeniTarih} onChange={e => setYeniTarih(e.target.value)} />
              <input className="form-input" placeholder="Yorum..." value={yeniYorum} onChange={e => setYeniYorum(e.target.value)} style={{ flex: 1, minWidth: 160 }} />
              <button className="new-button" onClick={tarihEkle}>Ekle</button>
            </div>
            {[...islemler].sort((a, b) => a.tarih.localeCompare(b.tarih)).map(i => {
              const m = musteriler.find(x => x.id === i.musteriId);
              return (
                <div key={i.id} className="task-item" style={{ justifyContent: 'space-between' }}>
                  <span><small style={{ color: 'var(--primary)', fontWeight: 600 }}>{i.tarih}</small> — {m?.sirketUnvani || '—'}: {i.not || i.tip}</span>
                  <button onClick={() => tarihSil(i.id)} style={{ background: 'none', border: 'none', color: '#b91c1c', cursor: 'pointer' }}>×</button>
                </div>
              );
            })}
            {islemler.length === 0 && <p className="bos-mesaj">Kayıt yok.</p>}
          </div>
        )}

        {/* ── RAPORLAR ── */}
        {aktifSekme === 'Raporlar' && (
          <div style={{ padding: '0 28px' }}>
            <section className="stats-grid">
              <div className="stat-card"><div><p className="stat-label">Toplam Müşteri</p><h3>{musteriler.length}</h3></div></div>
              <div className="stat-card"><div><p className="stat-label">Kazanılan</p><h3>{kazanilan}</h3></div></div>
              <div className="stat-card"><div><p className="stat-label">Kazanma Oranı</p><h3>%{musteriler.length ? Math.round(kazanilan / musteriler.length * 100) : 0}</h3></div></div>
              <div className="stat-card"><div><p className="stat-label">Toplam Ciro</p><h3>{formatPara(musteriler.reduce((t, m) => t + musteriCirosu(m.id), 0))}</h3></div></div>
            </section>
            <div className="crm-card" style={{ marginTop: 16 }}>
              <h3>Aşama Dağılımı</h3>
              {ASAMALAR.map(asama => {
                const sayi = musteriler.filter(m => m.asama === asama).length;
                const oran = musteriler.length ? Math.round(sayi / musteriler.length * 100) : 0;
                return (
                  <div key={asama} style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span>{asama}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>{sayi} müşteri — %{oran}</span>
                    </div>
                    <div style={{ height: 8, background: 'var(--border)', borderRadius: 4 }}>
                      <div style={{ height: 8, width: `${oran}%`, background: 'var(--primary)', borderRadius: 4 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── İŞLEMLER SEKME İÇERİĞİ ── */}
         
{aktifSekme === 'İşlemler' && (
  <div className="crm-card" style={{ margin: '0 28px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
      <h3 style={{ margin: 0 }}>İşlemler</h3>
      <button className="new-button" onClick={excelIndir}>Excel'e Aktar</button>
    </div>
    {odemeler.length === 0 ? (
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
    )}
  </div>
)}

{aktifSekme === 'Sanal POS' && (
  <div className="crm-card" style={{ margin: '0 28px' }}>
    <h3>Sanal POS Yönetimi</h3>
    <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
      <select className="form-input" style={{ width: 'auto' }} value={seciliId || ''} onChange={e => setSeciliId(Number(e.target.value))}>
        <option value="">Müşteri seç</option>
        {musteriler.map(m => <option key={m.id} value={m.id}>{m.sirketUnvani}</option>)}
      </select>
      {['Tümü', 'Aktif', 'Pasif'].map(f => (
        <button key={f} onClick={() => setPosFiltre(f)} style={{ padding: '4px 14px', borderRadius: 20, border: '1px solid var(--border)', background: posFiltre === f ? 'var(--primary)' : 'transparent', color: posFiltre === f ? '#fff' : 'inherit', cursor: 'pointer', fontSize: 13 }}>
          {f}
        </button>
      ))}
    </div>

    {!seciliMusteri ? (
      <p className="bos-mesaj">Önce bir müşteri seçin.</p>
    ) : (
      <div className="pos-grid">
        {BANKALAR
          .filter(b => {
            const d = bankaDurumu(seciliMusteri, b);
            if (posFiltre === 'Aktif') return d === 'Aktif';
            if (posFiltre === 'Pasif') return d === 'Pasif';
            return true;
          })
          .map(b => {
            const d = bankaDurumu(seciliMusteri, b);
            return (
              <div key={b} className={`pos-kart ${d === 'Aktif' ? 'aktif' : ''}`} onClick={() => posDurumDegistir(b)}>
                <b>{b}</b>
                <span>{d || '+ POS Ekle'}</span>
              </div>
            );
          })}
      </div>
    )}
  </div>
)}

        {/* ── KULLANICILAR ── */}
        {aktifSekme === 'Kullanıcılar' && (
          <div className="crm-card" style={{ margin: '0 28px' }}>
            <h3>Kullanıcılar</h3>
            {[{ ad: 'İlayda Budak', rol: 'Yönetici' }, { ad: 'Oktay Oygut', rol: 'Satış Temsilcisi' }].map(k => (
              <div key={k.ad} className="task-item">
                <span>{k.ad}</span>
                <small style={{ color: 'var(--text-muted)' }}>{k.rol}</small>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}