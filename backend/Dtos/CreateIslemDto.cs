namespace backend.Dtos;

public record CreateIslemDto(
    int MusteriId,
    string Tip,
    DateOnly Tarih,
    string SatisTemsilcisi,
    string OdemeTuru,
    string FaturaNo,
    string OdemeKurulusu,
    string OdemeYontemi,
    string Not,
    decimal Tutar
);
