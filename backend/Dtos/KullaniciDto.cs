namespace backend.Dtos;

public record KullaniciDto(
    int Id,
    string KullaniciAdi,
    string AdSoyad,
    string KullaniciTipi,
    string Yetki,
    string Durum
);