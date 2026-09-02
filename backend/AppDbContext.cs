using Microsoft.EntityFrameworkCore;
using backend.Dtos;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<MusteriDto> Musteriler => Set<MusteriDto>();

    public DbSet<IslemDto> Islemler => Set<IslemDto>();
     public DbSet<OdemeDto> Odemeler => Set<OdemeDto>();
     public DbSet<KullaniciKayit> Kullanicilar => Set<KullaniciKayit>();
     public DbSet<FaturaDto> Faturalar => Set<FaturaDto>();
}