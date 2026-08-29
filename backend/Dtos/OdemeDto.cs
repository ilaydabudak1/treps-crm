namespace backend.Dtos;



public record OdemeDto(
    int Id,
    int MusteriId,
    string Banka,
    string SanalPos,
    string SiparisNo,
    string IslemNo,
    string IslemTipi,
    string Durum,
    string Tarih,
    decimal Tutar,
    string ParaBirimi,
    string Eposta,
    string Kart,
    string KartBankasi,
    string KartTipi,
    string Guvenli3D,
    string Sonuc
);