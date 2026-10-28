// SYMBIOSE — WorldView.ZoomGpu.cs (partial de WorldView, FLUIDITÉ PC PARTAGE ③)
// Les COMPTEURS « GPU » du journal de zoom (WorldView.ZoomJournal.cs). Au PC, la
// pire image d'un cran ×8→×4 dure 453 ms dont 10 ms seulement sont attribués aux
// postes CPU : on soupçonne ce qui part vers la carte graphique au moment du cran.
// Ce fichier relève, à chaque image de la fenêtre du cran :
//  - la mémoire vidéo / textures / tampons que Godot dit occuper (`Performance`) ;
//  - les pages d'atlas de cuisson NEUVES (création d'une cible de rendu 2048²),
//    resservies depuis la réserve, détruites — et parmi elles les DÉDIÉES (une
//    page à la taille exacte d'une grande plante, ×8+ ; AtlasPages.cs) ;
//  - les RENDUS de page (une page touchée par ≥ 1 cuisson est rendue en entier
//    par le GPU), le nombre de cuissons et la SURFACE cuite (px, PlantBaker.cs).
//
// 📖 Pédagogie (côté embarqué) : ce sont des compteurs libres CUMULÉS (jamais remis
// à zéro), comme un compteur d'octets DMA : on lit une photo à chaque image et on
// fait la différence entre deux photos. Pas d'état à remettre à zéro, pas de course
// entre celui qui compte et celui qui lit.
// ⚠️ Sur la VM (llvmpipe) le TEMPS d'un envoi ne vaut pas celui du PC ; les VOLUMES
// (Mo, pages, pixels par image) sont, eux, transposables — c'est eux qu'on lit.

using Godot;
using System.Globalization;

namespace Symbiose
{
	public partial class WorldView
	{
		private struct CompteursGpu
		{
			public double Vram, Tex, Buf;   // octets (moniteurs Godot)
			public long Creees, CreationUs, Reutil, Detruites, Rendus, Cuissons, Px, DedC, DedD;

			public static CompteursGpu Lire() => new()
			{
				Vram = Performance.GetMonitor(Performance.Monitor.RenderVideoMemUsed),
				Tex = Performance.GetMonitor(Performance.Monitor.RenderTextureMemUsed),
				Buf = Performance.GetMonitor(Performance.Monitor.RenderBufferMemUsed),
				// CreeesTotal compte aussi les pages resservies (même point d'entrée).
				Creees = AtlasPages.CreeesTotal - AtlasPages.ReutiliseesTotal,
				CreationUs = AtlasPages.CreationUsTotal,
				Reutil = AtlasPages.ReutiliseesTotal,
				Detruites = AtlasPages.DetruitesTotal,
				Rendus = AtlasPages.Rendus,
				Cuissons = PlantBaker.Cuissons,
				Px = PlantBaker.PixelsCuits,
				DedC = AtlasPages.DedieesCreeesTotal,
				DedD = AtlasPages.DedieesDetruitesTotal,
			};

			public readonly CompteursGpu Moins(CompteursGpu o) => new()
			{
				Vram = Vram - o.Vram, Tex = Tex - o.Tex, Buf = Buf - o.Buf,
				Creees = Creees - o.Creees, CreationUs = CreationUs - o.CreationUs,
				Reutil = Reutil - o.Reutil, Detruites = Detruites - o.Detruites,
				Rendus = Rendus - o.Rendus, Cuissons = Cuissons - o.Cuissons, Px = Px - o.Px,
				DedC = DedC - o.DedC, DedD = DedD - o.DedD,
			};

			/// <summary>Un delta en clair ; `picVram` ≥ 0 ajoute le pic de mémoire vidéo.</summary>
			public readonly string Texte(double picVram)
			{
				const double Mo = 1048576.0;
				string pic = picVram >= 0 ? string.Create(CultureInfo.InvariantCulture, $" (pic +{picVram / Mo:F1})") : "";
				return string.Create(CultureInfo.InvariantCulture,
					$"vidéo {Vram / Mo:+0.0;-0.0;0} Mo{pic} · textures {Tex / Mo:+0.0;-0.0;0} · tampons {Buf / Mo:+0.0;-0.0;0} · "
					+ $"pages neuves {Creees} dont {DedC} dédiées ({CreationUs / 1000.0:F1} ms) / resservies {Reutil} / "
					+ $"détruites {Detruites} dont {DedD} dédiées · "
					+ $"rendus {Rendus} · cuissons {Cuissons} · {Px / 1e6:F2} Mpx");
			}
		}
	}
}
