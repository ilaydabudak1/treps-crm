using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace backend.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Musteriler",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    SirketUnvani = table.Column<string>(type: "text", nullable: false),
                    MarkaAdi = table.Column<string>(type: "text", nullable: false),
                    Domain = table.Column<string>(type: "text", nullable: false),
                    Email = table.Column<string>(type: "text", nullable: false),
                    Telefon = table.Column<string>(type: "text", nullable: false),
                    Sehir = table.Column<string>(type: "text", nullable: false),
                    Temsilci = table.Column<string>(type: "text", nullable: false),
                    Asama = table.Column<string>(type: "text", nullable: false),
                    Ciro = table.Column<string>(type: "text", nullable: false),
                    Durum = table.Column<string>(type: "text", nullable: false),
                    BeklemeSebebi = table.Column<string>(type: "text", nullable: false),
                    KayipSebebi = table.Column<string>(type: "text", nullable: false),
                    AsamaTarihi = table.Column<string>(type: "text", nullable: false),
                    Entegrasyon = table.Column<string>(type: "text", nullable: false),
                    EntegrasyonBanka = table.Column<string>(type: "text", nullable: false),
                    MuhasebeProgramlari = table.Column<string>(type: "text", nullable: false),
                    TeklifOrani = table.Column<string>(type: "text", nullable: false),
                    PlanTarihi = table.Column<string>(type: "text", nullable: false),
                    PlanNotu = table.Column<string>(type: "text", nullable: false),
                    Yonlendiren = table.Column<string>(type: "text", nullable: false),
                    GelirPayiOrani = table.Column<string>(type: "text", nullable: false),
                    Semt = table.Column<string>(type: "text", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Musteriler", x => x.Id);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Musteriler");
        }
    }
}
