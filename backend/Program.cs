using backend.Dtos;
using System.Text.Json;
using Microsoft.EntityFrameworkCore;




var builder = WebApplication.CreateBuilder(args);
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("VeriTabani")));

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


app.MapGet("/Musteri", async (AppDbContext db) => await db.Musteriler.ToListAsync());

app.MapGet("/Musteri/{id}", async (int id, AppDbContext db) =>
{
    var musteri = await db.Musteriler.FindAsync(id);
    return musteri is null ? Results.NotFound() : Results.Ok(musteri);
});

app.MapPost("/Musteri", async (CreateMusteriDto yeniMusteriDto, AppDbContext db) =>
{
    MusteriDto musteri = new(
        0,
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

    db.Musteriler.Add(musteri);
    await db.SaveChangesAsync();

    return Results.Created($"/Musteri/{musteri.Id}", musteri);
});

app.MapPut("/Musteri/{id}", async (int id, UpdateMusteriDto updateMusteriDto, AppDbContext db) =>
{
    var mevcut = await db.Musteriler.FindAsync(id);
    if (mevcut is null) return Results.NotFound();

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

    db.Entry(mevcut).CurrentValues.SetValues(guncellenmis);
    await db.SaveChangesAsync();

    return Results.NoContent();
});

app.MapDelete("/Musteri/{id}", async (int id, AppDbContext db) =>
{
    var musteri = await db.Musteriler.FindAsync(id);
    if (musteri is not null)
    {
        db.Musteriler.Remove(musteri);
        await db.SaveChangesAsync();
    }
    return Results.NoContent();
});




app.MapGet("/Islemler",async (AppDbContext db) => await db.Islemler.ToListAsync());

app.MapGet("/Islemler/{musteriId}", async (int musteriId, AppDbContext db) =>
{
    List<IslemDto> musteriIslemleri = await db.Islemler.Where(i => i.MusteriId == musteriId).ToListAsync();
    return musteriIslemleri;
});

app.MapPost("/Islemler", async (CreateIslemDto yeniIslemDto, AppDbContext db) =>
{
    IslemDto islem = new(
       0,
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

    db.Islemler.Add(islem);
    await db.SaveChangesAsync();

    return Results.Created($"/Islemler/{islem.Id}", islem);
});

app.MapDelete ("/Islemler/{id}" , async (int id, AppDbContext db) =>
{
    var islem = await db.Islemler.FindAsync(id);
    if (islem is not null)
    {
        db.Islemler.Remove(islem);
        await db.SaveChangesAsync();
    }
    return Results.NoContent();
});


app.MapGet("/Odemeler" , async (AppDbContext db) => await db.Odemeler.ToListAsync());
app.MapGet("/Odemeler/{musteriId}" , async (int musteriId, AppDbContext db) =>
    await db.Odemeler.Where(o => o.MusteriId == musteriId).ToListAsync());

Dictionary<string, int> Oturumlar = new();
const string GOOGLE_TOKEN_DOSYASI = "google-tokens.json";
Dictionary<int, string> GoogleRefreshTokenlar = File.Exists(GOOGLE_TOKEN_DOSYASI)
    ? JsonSerializer.Deserialize<Dictionary<int, string>>(File.ReadAllText(GOOGLE_TOKEN_DOSYASI)) ?? new()
    : new();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    if (!db.Kullanicilar.Any())
    {
        db.Kullanicilar.Add(new KullaniciKayit { KullaniciAdi = "ilayda", AdSoyad = "İlayda Budak", SifreHash = BCrypt.Net.BCrypt.HashPassword("000000"), KullaniciTipi = "Portal", Yetki = "Yönetici", Durum = "Aktif" });
        db.SaveChanges();
    }
}

app.MapGet("/Kullanicilar", async (AppDbContext db) =>
    await db.Kullanicilar.Select(k => new KullaniciDto(k.Id, k.KullaniciAdi, k.AdSoyad, k.KullaniciTipi, k.Yetki, k.Durum)).ToListAsync());

app.MapPost("/Kullanicilar", async (CreateKullaniciDto yeniKullaniciDto, AppDbContext db) =>
{
    var kayit = new KullaniciKayit
    {
        KullaniciAdi = yeniKullaniciDto.KullaniciAdi,
        AdSoyad = yeniKullaniciDto.AdSoyad,
        SifreHash = BCrypt.Net.BCrypt.HashPassword(yeniKullaniciDto.Sifre),
        KullaniciTipi = yeniKullaniciDto.KullaniciTipi,
        Yetki = yeniKullaniciDto.Yetki,
        Durum = "Aktif"
    };
    db.Kullanicilar.Add(kayit);
    await db.SaveChangesAsync();
    var dto = new KullaniciDto(kayit.Id, kayit.KullaniciAdi, kayit.AdSoyad, kayit.KullaniciTipi, kayit.Yetki, kayit.Durum);
    return Results.Created($"/Kullanicilar/{kayit.Id}", dto);
});

app.MapPut("/Kullanicilar/{id}", async (int id, UpdateKullaniciDto updateDto, AppDbContext db) =>
{
    var kayit = await db.Kullanicilar.FindAsync(id);
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
    await db.SaveChangesAsync();
    return Results.NoContent();
});

app.MapDelete("/Kullanicilar/{id}", async (int id, AppDbContext db) =>
{
    var kayit = await db.Kullanicilar.FindAsync(id);
    if (kayit is not null)
    {
        db.Kullanicilar.Remove(kayit);
        await db.SaveChangesAsync();
    }
    return Results.NoContent();
});

app.MapPost("/Login", async (LoginDto loginDto, AppDbContext db) =>
{
    var kayit = await db.Kullanicilar.FirstOrDefaultAsync(k => k.KullaniciAdi == loginDto.KullaniciAdi);

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

app.MapGet("/Faturalar", async (AppDbContext db) => await db.Faturalar.ToListAsync());

app.MapPost("/Faturalar", async (CreateFaturaDto dto, AppDbContext db) =>
{
    var kayit = new FaturaDto(0, dto.MusteriId, dto.FaturaNo, dto.Tarih, dto.Tutar, "0", "0", dto.ValorTarihi, dto.Notlar, "Onaylanmadı");
    db.Faturalar.Add(kayit);
    await db.SaveChangesAsync();
    return Results.Created($"/Faturalar/{kayit.Id}", kayit);
});

app.MapPut("/Faturalar/{id}", async (int id, UpdateFaturaDto dto, AppDbContext db) =>
{
    var kayit = await db.Faturalar.FindAsync(id);
    if (kayit is null) return Results.NotFound();

    var guncellenmis = kayit with { Onaylanan = dto.Onaylanan, Odenen = dto.Odenen, Durum = dto.Durum };
    db.Entry(kayit).CurrentValues.SetValues(guncellenmis);
    await db.SaveChangesAsync();
    return Results.NoContent();
});

app.MapDelete("/Faturalar/{id}", async (int id, AppDbContext db) =>
{
    var kayit = await db.Faturalar.FindAsync(id);
    if (kayit is not null)
    {
        db.Faturalar.Remove(kayit);
        await db.SaveChangesAsync();
    }
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