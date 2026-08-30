namespace backend.Dtos;
public record UpdateKullaniciDto(
    string KullaniciAdi,
    string AdSoyad,
    string Sifre,
    string KullaniciTipi,
    string Yetki,
    string Durum
);