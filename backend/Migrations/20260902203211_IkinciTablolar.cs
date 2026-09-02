using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace backend.Migrations
{
    /// <inheritdoc />
    public partial class IkinciTablolar : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Faturalar",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    MusteriId = table.Column<int>(type: "integer", nullable: false),
                    FaturaNo = table.Column<string>(type: "text", nullable: false),
                    Tarih = table.Column<string>(type: "text", nullable: false),
                    Tutar = table.Column<string>(type: "text", nullable: false),
                    Onaylanan = table.Column<string>(type: "text", nullable: false),
                    Odenen = table.Column<string>(type: "text", nullable: false),
                    ValorTarihi = table.Column<string>(type: "text", nullable: false),
                    Notlar = table.Column<string>(type: "text", nullable: false),
                    Durum = table.Column<string>(type: "text", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Faturalar", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Islemler",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    MusteriId = table.Column<int>(type: "integer", nullable: false),
                    Tip = table.Column<string>(type: "text", nullable: false),
                    Tarih = table.Column<DateOnly>(type: "date", nullable: false),
                    SatisTemsilcisi = table.Column<string>(type: "text", nullable: false),
                    OdemeTuru = table.Column<string>(type: "text", nullable: false),
                    FaturaNo = table.Column<string>(type: "text", nullable: false),
                    OdemeKurulusu = table.Column<string>(type: "text", nullable: false),
                    OdemeYontemi = table.Column<string>(type: "text", nullable: false),
                    Not = table.Column<string>(type: "text", nullable: false),
                    Tutar = table.Column<decimal>(type: "numeric", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Islemler", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Kullanicilar",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    KullaniciAdi = table.Column<string>(type: "text", nullable: false),
                    AdSoyad = table.Column<string>(type: "text", nullable: false),
                    SifreHash = table.Column<string>(type: "text", nullable: false),
                    KullaniciTipi = table.Column<string>(type: "text", nullable: false),
                    Yetki = table.Column<string>(type: "text", nullable: false),
                    Durum = table.Column<string>(type: "text", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Kullanicilar", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Odemeler",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    MusteriId = table.Column<int>(type: "integer", nullable: false),
                    Banka = table.Column<string>(type: "text", nullable: false),
                    SanalPos = table.Column<string>(type: "text", nullable: false),
                    SiparisNo = table.Column<string>(type: "text", nullable: false),
                    IslemNo = table.Column<string>(type: "text", nullable: false),
                    IslemTipi = table.Column<string>(type: "text", nullable: false),
                    Durum = table.Column<string>(type: "text", nullable: false),
                    Tarih = table.Column<string>(type: "text", nullable: false),
                    Tutar = table.Column<decimal>(type: "numeric", nullable: false),
                    ParaBirimi = table.Column<string>(type: "text", nullable: false),
                    Eposta = table.Column<string>(type: "text", nullable: false),
                    Kart = table.Column<string>(type: "text", nullable: false),
                    KartBankasi = table.Column<string>(type: "text", nullable: false),
                    KartTipi = table.Column<string>(type: "text", nullable: false),
                    Guvenli3D = table.Column<string>(type: "text", nullable: false),
                    Sonuc = table.Column<string>(type: "text", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Odemeler", x => x.Id);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Faturalar");

            migrationBuilder.DropTable(
                name: "Islemler");

            migrationBuilder.DropTable(
                name: "Kullanicilar");

            migrationBuilder.DropTable(
                name: "Odemeler");
        }
    }
}
