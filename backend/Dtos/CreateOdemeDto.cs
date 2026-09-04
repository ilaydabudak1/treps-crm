namespace backend.Dtos;
public record CreateOdemeDto(
       int MusteriId,
    string Banka,
    string SanalPos,
    string SiparisNo,
    string IslemTipi,
    string Tarih,
    decimal Tutar,
    string ParaBirimi,
    string Eposta,
    string Kart,
    string KartBankasi,
    string KartTipi,
    string Guvenli3D
);