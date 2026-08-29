namespace backend.Dtos;

public record UpdateMusteriDto(
    string SirketUnvani,
    string MarkaAdi,
    string Domain,
    string Email,
    string Telefon,
    string Sehir,
    string Temsilci,
    string Asama,
    string Ciro,
    string Durum,
    string BeklemeSebebi,
    string KayipSebebi,
    string AsamaTarihi = "",
    string Entegrasyon = "",
    string EntegrasyonBanka = "",
    string MuhasebeProgramlari = "",
    string TeklifOrani = "",
    string PlanTarihi = "",
    string PlanNotu = "",
    string Yonlendiren = "",
    string GelirPayiOrani = ""
);
