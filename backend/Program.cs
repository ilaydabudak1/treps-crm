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
Directory.CreateDirectory("Belgeler");
app.UseStaticFiles(new StaticFileOptions
{
    FileProvider = new Microsoft.Extensions.FileProviders.PhysicalFileProvider(Path.Combine(builder.Environment.ContentRootPath, "Belgeler")),
    RequestPath = "/BelgeDosyalari"
});

List<MusteriDto> Musteriler = new();
int sonrakiMusteriId = 1;

app.MapGet("/Musteri", () => Musteriler);

app.MapGet("/Musteri/{id}", (int id) =>
{
    var musteri = Musteriler.FirstOrDefault(m => m.Id == id);
    return musteri is null ? Results.NotFound() : Results.Ok(musteri);
});

app.MapPost("/Musteri", (CreateMusteriDto yeniMusteriDto) =>
{
    MusteriDto musteri = new(
        sonrakiMusteriId++,
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

    Musteriler.Add(musteri);

    return Results.Created($"/Musteri/{musteri.Id}", musteri);
});

app.MapPut("/Musteri/{id}", (int id, UpdateMusteriDto updateMusteriDto) =>
{
    var index = Musteriler.FindIndex(m => m.Id == id);
    if (index == -1) return Results.NotFound();

    MusteriDto guncellenmis = new(
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

    Musteriler[index] = guncellenmis;

    return Results.NoContent();
});

app.MapDelete("/Musteri/{id}", (int id) =>
{
    Musteriler.RemoveAll(m => m.Id == id);
    return Results.NoContent();
});




List<IslemDto> Islemler = new();
int sonrakiIslemId = 1;

app.MapGet("/Islemler", () => Islemler);

app.MapGet("/Islemler/{musteriId}", (int musteriId) =>
    Islemler.Where(i => i.MusteriId == musteriId).ToList());

app.MapPost("/Islemler", (CreateIslemDto yeniIslemDto) =>
{
    IslemDto islem = new(
        sonrakiIslemId++,
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

app.MapDelete("/Islemler/{id}", (int id) =>
{
    Islemler.RemoveAll(i => i.Id == id);
    return Results.NoContent();
});


List<OdemeDto> Odemeler = new();
int sonrakiOdemeId = 1;

app.MapGet("/Odemeler", () => Odemeler);
app.MapGet("/Odemeler/{musteriId}", (int musteriId) =>
    Odemeler.Where(o => o.MusteriId == musteriId).ToList());

app.MapPost("/Odemeler", (CreateOdemeDto dto) =>
{
    var kayit = new OdemeDto(
        sonrakiOdemeId++, dto.MusteriId, dto.Banka, dto.SanalPos, dto.SiparisNo,
        $"TRX-{DateTime.Now:yyyyMMddHHmmss}", dto.IslemTipi, "Başarılı", dto.Tarih,
        dto.Tutar, dto.ParaBirimi, dto.Eposta, dto.Kart, dto.KartBankasi, dto.KartTipi,
        dto.Guvenli3D, "Onaylandı"
    );
    Odemeler.Add(kayit);
    return Results.Created($"/Odemeler/{kayit.Id}", kayit);
});

Dictionary<string, int> Oturumlar = new();
const string GOOGLE_TOKEN_DOSYASI = "google-tokens.json";
Dictionary<int, string> GoogleRefreshTokenlar = File.Exists(GOOGLE_TOKEN_DOSYASI)
    ? JsonSerializer.Deserialize<Dictionary<int, string>>(File.ReadAllText(GOOGLE_TOKEN_DOSYASI)) ?? new()
    : new();

List<KullaniciKayit> Kullanicilar = new()
{
    new KullaniciKayit { Id = 1, KullaniciAdi = "ilayda", AdSoyad = "İlayda Budak", SifreHash = BCrypt.Net.BCrypt.HashPassword("000000"), KullaniciTipi = "Portal", Yetki = "Yönetici", Durum = "Aktif" }
};
int sonrakiKullaniciId = 2;

app.MapGet("/Kullanicilar", () =>
    Kullanicilar.Select(k => new KullaniciDto(k.Id, k.KullaniciAdi, k.AdSoyad, k.KullaniciTipi, k.Yetki, k.Durum)).ToList());

app.MapPost("/Kullanicilar", (CreateKullaniciDto yeniKullaniciDto) =>
{
    var kayit = new KullaniciKayit
    {
        Id = sonrakiKullaniciId++,
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
    var kayit = Kullanicilar.FirstOrDefault(k => k.Id == id);
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
    var kayit = Kullanicilar.FirstOrDefault(k => k.KullaniciAdi == loginDto.KullaniciAdi);

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
int sonrakiFaturaId = 1;

app.MapGet("/Faturalar", () => Faturalar);

app.MapPost("/Faturalar", (CreateFaturaDto dto) =>
{
    var kayit = new FaturaDto(sonrakiFaturaId++, dto.MusteriId, dto.FaturaNo, dto.Tarih, dto.Tutar, "0", "0", dto.ValorTarihi, dto.Notlar, "Onaylanmadı");
    Faturalar.Add(kayit);
    return Results.Created($"/Faturalar/{kayit.Id}", kayit);
});

app.MapPut("/Faturalar/{id}", (int id, UpdateFaturaDto dto) =>
{
    var index = Faturalar.FindIndex(f => f.Id == id);
    if (index == -1) return Results.NotFound();

    var guncellenmis = Faturalar[index] with { Onaylanan = dto.Onaylanan, Odenen = dto.Odenen, Durum = dto.Durum };
    Faturalar[index] = guncellenmis;
    return Results.NoContent();
});

app.MapDelete("/Faturalar/{id}", (int id) =>
{
    Faturalar.RemoveAll(f => f.Id == id);
    return Results.NoContent();
});

List<BelgeDto> Belgeler = new();
int sonrakiBelgeId = 1;

app.MapPost("/Belgeler", async (HttpRequest request) =>
{
    var form = await request.ReadFormAsync();
    var dosya = form.Files["dosya"];
    if (dosya is null) return Results.BadRequest("Dosya seçilmedi.");
    var musteriId = int.Parse(form["musteriId"]!);
    var tip = form["tip"].ToString();
    var aciklama = form["aciklama"].ToString();
    var yuklenmeTarihi = form["yuklenmeTarihi"].ToString();
    var yukleyen = form["yukleyen"].ToString();

    var klasor = Path.Combine("Belgeler", musteriId.ToString());
    Directory.CreateDirectory(klasor);
    var dosyaAdi = $"{Guid.NewGuid()}_{dosya.FileName}";
    var diskYolu = Path.Combine(klasor, dosyaAdi);

    using (var stream = new FileStream(diskYolu, FileMode.Create))
    {
        await dosya.CopyToAsync(stream);
    }
    var kayit = new BelgeDto(sonrakiBelgeId++, musteriId, dosya.FileName, tip, aciklama, yuklenmeTarihi, yukleyen, dosya.Length, $"{musteriId}/{dosyaAdi}");
    Belgeler.Add(kayit);

    return Results.Created($"/Belgeler/{kayit.Id}", kayit);
});

app.MapGet("/Belgeler/{musteriId}", (int musteriId) =>
    Belgeler.Where(b => b.MusteriId == musteriId).ToList());

app.MapDelete("/Belgeler/{id}", (int id) =>
{
    var belge = Belgeler.FirstOrDefault(b => b.Id == id);
    if (belge is null) return Results.NotFound();

    var diskYolu = Path.Combine("Belgeler", belge.DosyaYolu);
    if (File.Exists(diskYolu))
    {
        File.Delete(diskYolu);
    }
    Belgeler.RemoveAll(b => b.Id == id);
    return Results.NoContent();
});

app.Run();

public class KullaniciKayit
{
    public int Id { get; set; }
    public string KullaniciAdi { get; set; } = "";
    public string AdSoyad { get; set; } = "";
    public string SifreHash { get; set; } = "";
    public string KullaniciTipi { get; set; } = "";
    public string Yetki { get; set; } = "";
    public string Durum { get; set; } = "";
}
