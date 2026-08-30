namespace backend.Dtos;
public record CreateKullaniciDto(
    string KullaniciAdi,
    string AdSoyad,
    string Sifre,
    string KullaniciTipi,
    string Yetki,
    string Durum
);