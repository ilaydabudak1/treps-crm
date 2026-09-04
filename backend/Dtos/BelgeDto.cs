namespace backend.Dtos;
public record BelgeDto(
    int Id,
    int MusteriId,
    string DosyaAdi,
    string Tip,
    string Aciklama,
    string YuklenmeTarihi,
    string Yukleyen,
    long Boyut,
    string DosyaYolu
);