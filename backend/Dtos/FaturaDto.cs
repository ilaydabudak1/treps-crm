namespace backend.Dtos;
public record FaturaDto(
    int Id,
    int MusteriId,
    string FaturaNo,
    string Tarih,
    string Tutar,
    string Onaylanan,
    string Odenen,
    string ValorTarihi,
    string Notlar,
    string Durum
);
