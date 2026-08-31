namespace backend.Dtos;
public record CreateFaturaDto(
    int MusteriId,
    string FaturaNo,
    string Tarih,
    string Tutar,
    string ValorTarihi = "",
    string Notlar = ""
);
