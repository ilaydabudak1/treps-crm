using backend.Dtos;
using System.Text.Json;




var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(Options =>
{
    Options.AddPolicy("FrontendPolicy" , policy =>
    {
        policy.WithOrigins("http://localhost:3000")
                .AllowAnyHeader()
                .AllowAnyMethod();

    });
});

var app = builder.Build();
app.UseCors("FrontendPolicy");


List<MusteriDto> Musteri = new()
{
new MusteriDto(1, "Lidya Teknoloji", "Treps", "trepscrm.com", "treps@outlook.com", "05001112233", "İstanbul", "İlayda Budak", "Teklif", "50000", "Görüşülen", "", ""),
new MusteriDto(2, "Oygut Travel.", "tatilheyecanı", "tatilheyecani.com", "oktayoygut@mac.com", "05002223344", "Ankara", "Oktay Oygut", "Sözleşme", "120000", "Bekleyen", "", "")
};
app.MapGet("/Musteri", () => Musteri);
app.MapGet("/Musteri/{id}", (int id) =>
{
    MusteriDto? musteri = Musteri.Find(m => m.Id == id);
    return musteri is null ? Results.NotFound() : Results.Ok(musteri);
});

app.MapPost("/Musteri", (CreateMusteriDto yeniMusteriDto) =>
{
    MusteriDto musteri = new(
        Musteri.Count + 1,
        yeniMusteriDto.SirketUnvani,
        yeniMusteriDto.MarkaAdi,
        yeniMusteriDto.Domain,
        yeniMusteriDto.Email,
        yeniMusteriDto.Telefon,
        yeniMusteriDto.Sehir,
        yeniMusteriDto.Temsilci,
        yeniMusteriDto.Asama,
        yeniMusteriDto.Ciro,
        yeniMusteriDto.Durum,
        yeniMusteriDto.BeklemeSebebi,
        yeniMusteriDto.KayipSebebi,
        yeniMusteriDto.AsamaTarihi,
        yeniMusteriDto.Entegrasyon,
        yeniMusteriDto.EntegrasyonBanka,
        yeniMusteriDto.MuhasebeProgramlari,
        yeniMusteriDto.TeklifOrani,
        yeniMusteriDto.PlanTarihi,
        yeniMusteriDto.PlanNotu,
        yeniMusteriDto.Yonlendiren,
        yeniMusteriDto.GelirPayiOrani,
        yeniMusteriDto.Semt
    );

    Musteri.Add(musteri);

    return Results.Created($"/Musteri/{musteri.Id}", musteri);
});

app.MapPut ("/Musteri/{id}" , (int id, UpdateMusteriDto updateMusteriDto) =>
{
    var index = Musteri.FindIndex(m => m.Id == id);
    if (index == -1)
    {
        return Results.NotFound();   
    }
    Musteri[index] = new MusteriDto(
        id,
        updateMusteriDto.SirketUnvani,
        updateMusteriDto.MarkaAdi,
        updateMusteriDto.Domain,
        updateMusteriDto.Email,
        updateMusteriDto.Telefon,
        updateMusteriDto.Sehir,
        updateMusteriDto.Temsilci,
        updateMusteriDto.Asama,
        updateMusteriDto.Ciro,
        updateMusteriDto.Durum,
        updateMusteriDto.BeklemeSebebi,
        updateMusteriDto.KayipSebebi,
        updateMusteriDto.AsamaTarihi,
        updateMusteriDto.Entegrasyon,
        updateMusteriDto.EntegrasyonBanka,
        updateMusteriDto.MuhasebeProgramlari,
        updateMusteriDto.TeklifOrani,
        updateMusteriDto.PlanTarihi,
        updateMusteriDto.PlanNotu,
        updateMusteriDto.Yonlendiren,
        updateMusteriDto.GelirPayiOrani,
        updateMusteriDto.Semt
    );
    return Results.NoContent();
}
);
app.MapDelete("/Musteri/{id}" , (int id) =>
{
    Musteri.RemoveAll(m => m.Id == id);
    return Results.NoContent();
});



List<IslemDto> Islemler = new()
{
    new IslemDto(1, 1, "Teklif", new DateOnly(2025, 8, 12), "İlayda Budak", "Kredi Kartı", "", "İyzico", "GarantiBBVA", "İlk teklif gönderildi", 0),
    new IslemDto(2, 1, "Sözleşme", new DateOnly(2025, 9, 3), "İlayda Budak", "Havale", "F-2025-001", "Qnbpay", "Ziraat", "Sözleşme imzalandı", 50000),
    new IslemDto(3, 2, "Teklif", new DateOnly(2025, 8, 20), "Oktay Oygut", "Kredi Kartı", "", "PayTR", "Akbank", "Teklif sunuldu", 0)
};

app.MapGet("/Islemler", () => Islemler);

app.MapGet("/Islemler/{musteriId}", (int musteriId) =>
{
    List<IslemDto> musteriIslemleri = Islemler.Where(i => i.MusteriId == musteriId).ToList();
    return musteriIslemleri;
});

app.MapPost("/Islemler", (CreateIslemDto yeniIslemDto) =>
{
    IslemDto islem = new(
        Islemler.Count + 1,
        yeniIslemDto.MusteriId,
        yeniIslemDto.Tip,
        yeniIslemDto.Tarih,
        yeniIslemDto.SatisTemsilcisi,
        yeniIslemDto.OdemeTuru,
        yeniIslemDto.FaturaNo,
        yeniIslemDto.OdemeKurulusu,
        yeniIslemDto.OdemeYontemi,
        yeniIslemDto.Not,
        yeniIslemDto.Tutar
    );

    Islemler.Add(islem);

    return Results.Created($"/Islemler/{islem.Id}", islem);
});

app.MapDelete ("/Islemler/{id}" , (int id) =>
{
    Islemler.RemoveAll(i => i.Id == id);
    return Results.NoContent();
});



List<OdemeDto> Odemeler = new()
    {
    new OdemeDto(1, 1, "tkpay", "tkpay", "ORD-1-a9F2k", "TRX-1-x7Qw2p", "Satış", "Başarılı", "2026-08-20 14:22:10", 1250, "TRY", "info@lidyateknoloji.com", "5456 16** **** 5418", "QNB", "CREDIT", "Evet", "900"),
    new OdemeDto(2, 1, "tkpay", "tkpay", "ORD-1-b3H8m", "TRX-1-y2Rt9q", "Satış", "Başarılı", "2026-08-22 09:11:47", 890, "TRY", "info@lidyateknoloji.com", "4021 55** **** 7732", "Akbank", "CREDIT", "Evet", "900"),
    new OdemeDto(3, 2, "moka", "moka", "ORD-2-c7J1n", "TRX-2-z8Sv3r", "Satış", "İşleniyor", "2026-08-25 16:40:02", 3200, "TRY", "oktayoygut@mac.com", "5241 88** **** 1109", "Ziraat", "DEBIT", "Hayır", "İşleniyor"),
    new OdemeDto(4, 2, "moka", "moka", "ORD-2-d5K4p", "TRX-2-w1Tu6s", "Satış", "Başarısız", "2026-08-26 11:05:33", 540, "TRY", "oktayoygut@mac.com", "5456 16** **** 5418", "Akbank", "CREDIT", "Evet", "INT001")
    };



app.MapGet("/Odemeler" , () => Odemeler);
app.MapGet("/Odemeler/{musteriId}" , (int musteriId) =>
Odemeler.Where(o => o.MusteriId == musteriId).ToList());

List<KullaniciKayit> Kullanicilar = new()
{
    new KullaniciKayit { Id = 1, KullaniciAdi = "ilayda", AdSoyad = "İlayda Budak", SifreHash = BCrypt.Net.BCrypt.HashPassword("000000"), KullaniciTipi = "Portal", Yetki = "Yönetici", Durum = "Aktif" },
    
};

Dictionary<string, int> Oturumlar = new();
const string GOOGLE_TOKEN_DOSYASI = "google-tokens.json";
Dictionary<int, string> GoogleRefreshTokenlar = File.Exists(GOOGLE_TOKEN_DOSYASI)
    ? JsonSerializer.Deserialize<Dictionary<int, string>>(File.ReadAllText(GOOGLE_TOKEN_DOSYASI)) ?? new()
    : new();

app.MapGet("/Kullanicilar", () =>
    Kullanicilar.Select(k => new KullaniciDto(k.Id, k.KullaniciAdi, k.AdSoyad, k.KullaniciTipi, k.Yetki, k.Durum)).ToList());

app.MapPost("/Kullanicilar", (CreateKullaniciDto yeniKullaniciDto) =>
{
    var kayit = new KullaniciKayit
    {
        Id = Kullanicilar.Count + 1,
        KullaniciAdi = yeniKullaniciDto.KullaniciAdi,
        AdSoyad = yeniKullaniciDto.AdSoyad,
        SifreHash = BCrypt.Net.BCrypt.HashPassword(yeniKullaniciDto.Sifre),
        KullaniciTipi = yeniKullaniciDto.KullaniciTipi,
        Yetki = yeniKullaniciDto.Yetki,
        Durum = "Aktif"
    };
    Kullanicilar.Add(kayit);
    var dto = new KullaniciDto(kayit.Id, kayit.KullaniciAdi, kayit.AdSoyad, kayit.KullaniciTipi, kayit.Yetki, kayit.Durum);
    return Results.Created($"/Kullanicilar/{kayit.Id}", dto);
});

app.MapPut("/Kullanicilar/{id}", (int id, UpdateKullaniciDto updateDto) =>
{
    var kayit = Kullanicilar.Find(k => k.Id == id);
    if (kayit is null) return Results.NotFound();

    kayit.KullaniciAdi = updateDto.KullaniciAdi;
    kayit.AdSoyad = updateDto.AdSoyad;
    kayit.KullaniciTipi = updateDto.KullaniciTipi;
    kayit.Yetki = updateDto.Yetki;
    kayit.Durum = updateDto.Durum;
    if (!string.IsNullOrWhiteSpace(updateDto.Sifre))
    {
        kayit.SifreHash = BCrypt.Net.BCrypt.HashPassword(updateDto.Sifre);
    }
    return Results.NoContent();
});

app.MapDelete("/Kullanicilar/{id}", (int id) =>
{
    Kullanicilar.RemoveAll(k => k.Id == id);
    return Results.NoContent();
});

app.MapPost("/Login", (LoginDto loginDto) =>
{
    var kayit = Kullanicilar.Find(k => k.KullaniciAdi == loginDto.KullaniciAdi);

    if (kayit is null || kayit.Durum != "Aktif" || !BCrypt.Net.BCrypt.Verify(loginDto.Sifre, kayit.SifreHash))
    {
        return Results.Unauthorized();
    }

    string token = Guid.NewGuid().ToString();
    Oturumlar[token] = kayit.Id;

    var dto = new KullaniciDto(kayit.Id, kayit.KullaniciAdi, kayit.AdSoyad, kayit.KullaniciTipi, kayit.Yetki, kayit.Durum);
    return Results.Ok(new { token, kullanici = dto });
});

const string GOOGLE_CLIENT_ID = "711700948552-vorknte8alrnal606lnao1e6ubunmkb2.apps.googleusercontent.com";
var googleClientSecret = builder.Configuration["GoogleClientSecret"];

app.MapPost("/GoogleAuth/Kod", async (GoogleKodDto dto) =>
{
    using var http = new HttpClient();
    var yanit = await http.PostAsync("https://oauth2.googleapis.com/token", new FormUrlEncodedContent(new Dictionary<string, string>
    {
        ["code"] = dto.Kod,
        ["client_id"] = GOOGLE_CLIENT_ID,
        ["client_secret"] = googleClientSecret!,
        ["redirect_uri"] = "postmessage",
        ["grant_type"] = "authorization_code"
    }));
    var icerik = await yanit.Content.ReadAsStringAsync();
    if (!yanit.IsSuccessStatusCode) return Results.BadRequest(icerik);

    using var json = JsonDocument.Parse(icerik);
    var kok = json.RootElement;
    var accessToken = kok.GetProperty("access_token").GetString();
    if (kok.TryGetProperty("refresh_token", out var rt))
    {
        GoogleRefreshTokenlar[dto.KullaniciId] = rt.GetString()!;
        File.WriteAllText(GOOGLE_TOKEN_DOSYASI, JsonSerializer.Serialize(GoogleRefreshTokenlar));
    }

    return Results.Ok(new { accessToken });
});

app.MapGet("/GoogleAuth/Token/{kullaniciId}", async (int kullaniciId) =>
{
    if (!GoogleRefreshTokenlar.TryGetValue(kullaniciId, out var refreshToken))
        return Results.NotFound();

    using var http = new HttpClient();
    var yanit = await http.PostAsync("https://oauth2.googleapis.com/token", new FormUrlEncodedContent(new Dictionary<string, string>
    {
        ["refresh_token"] = refreshToken,
        ["client_id"] = GOOGLE_CLIENT_ID,
        ["client_secret"] = googleClientSecret!,
        ["grant_type"] = "refresh_token"
    }));
    var icerik = await yanit.Content.ReadAsStringAsync();
    if (!yanit.IsSuccessStatusCode) return Results.BadRequest(icerik);

    using var json = JsonDocument.Parse(icerik);
    var accessToken = json.RootElement.GetProperty("access_token").GetString();
    return Results.Ok(new { accessToken });
});

List<FaturaDto> Faturalar = new();

app.MapGet("/Faturalar", () => Faturalar);

app.MapPost("/Faturalar", (CreateFaturaDto dto) =>
{
    var kayit = new FaturaDto(Faturalar.Count + 1, dto.MusteriId, dto.FaturaNo, dto.Tarih, dto.Tutar, "0", "0", dto.ValorTarihi, dto.Notlar, "Onaylanmadı");
    Faturalar.Add(kayit);
    return Results.Created($"/Faturalar/{kayit.Id}", kayit);
});

app.MapPut("/Faturalar/{id}", (int id, UpdateFaturaDto dto) =>
{
    var index = Faturalar.FindIndex(f => f.Id == id);
    if (index == -1) return Results.NotFound();
    var eski = Faturalar[index];
    Faturalar[index] = eski with { Onaylanan = dto.Onaylanan, Odenen = dto.Odenen, Durum = dto.Durum };
    return Results.NoContent();
});

app.MapDelete("/Faturalar/{id}", (int id) =>
{
    Faturalar.RemoveAll(f => f.Id == id);
    return Results.NoContent();
});

app.Run();

class KullaniciKayit
{
    public int Id { get; set; }
    public string KullaniciAdi { get; set; } = "";
    public string AdSoyad { get; set; } = "";
    public string SifreHash { get; set; } = "";
    public string KullaniciTipi { get; set; } = "";
    public string Yetki { get; set; } = "";
    public string Durum { get; set; } = "";
}