using backend.Dtos;




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
        yeniMusteriDto.GelirPayiOrani
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
        updateMusteriDto.GelirPayiOrani
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

List<GorevDto> Gorevler = new();
app.MapGet("/Gorevler" , () => Gorevler);
app.MapPost("/Gorevler" , (CreateGorevDto yeniGorevDto) =>
{
    GorevDto gorev = new(Gorevler.Count + 1, yeniGorevDto.Metin, false);
    Gorevler.Add(gorev);
    return Results.Created($"/Gorevler/{gorev.Id}" , gorev);
}
);
app.MapPut("/Gorevler/{id}" , (int id , UpdateGorevDto updategorevdto) =>
{
    var index = Gorevler.FindIndex(g => g.Id == id);
    if(index == -1)
    {
        return Results.NotFound();   
    }
    Gorevler[index] = new GorevDto(id, updategorevdto.Metin, updategorevdto.Tamam);
     return Results.NoContent();

});

app.MapDelete("/Gorevler/{id}" , (int id) =>
{
    Gorevler.RemoveAll( g => g.Id == id);
    return Results.NoContent();
}
);

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



app.Run();
