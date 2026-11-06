// SYMBIOSE — PlantRenderer.GerbesFleurs.cs (partial, sprint VERGER VIVANT ④)
// Les GERBES DE FLEURS : un bouquet de fleurs d'arbre en une seule pièce de l'atlas des gerbes
// (Gerbes.cs), posé au bout d'une brindille par-dessus le feuillage, de ×0,5 à ×4.
//
// 📖 Pédagogie — pourquoi une pièce et pas des fleurs une à une. Au pic, un cerisier doit paraître
// blanc. Une fleur de 3 cm fait ~9 px à ×2 : il en faudrait des milliers, chacune un tracé à
// chaque pose du vent. Une gerbe de fleurs en porte 4 à 14 pour UN tracé, comme les gerbes de
// feuilles : le nombre de tracés reste celui des bouts de brindille, quelques centaines par arbre.
//
//  • TROIS COUCHES de même taille : les fleurs ouvertes (teinte de la fleur), leurs cœurs (teinte
//    `FlowerHeart`, un second tracé seulement dès ×2, en dessous le cœur fait moins d'un pixel), et
//    les boutons (petites pièces, teinte du bouton d'espèce).
//  • Une seule série pour toutes les espèces : la forme de la fleur ne se lit pas en dessous de ×8,
//    seule la couleur la distingue (blanc pur, blanc rosé, bouton rose).
//  • Même ancrage que les gerbes de feuilles (pied en bas au milieu) : posées au même point, les
//    fleurs couvrent le haut de la touffe.
//
// Déterministe (canaux 587-597 au hash, zéro Random, philo #3) ; golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		internal enum CoucheFleur { Fleurs, Coeurs, Boutons }

		// Par palier (×0,5, ×1, ×2, ×4) : fleurs par gerbe, côté d'une fleur ouverte, côté d'un bouton [choix].
		private static readonly int[] FleursParGerbe = { 4, 7, 10, 14 };
		private static readonly int[] TailleFleurGerbe = { 1, 2, 5, 7 };
		private static readonly int[] TailleBoutonGerbe = { 1, 1, 2, 3 };
		private static readonly Dictionary<(int, int, CoucheFleur), Rect2I> _gerbesFleurs = new();

		// Rangement à la suite des gerbes de feuilles, même étagère par palier. Rend la hauteur totale.
		private static int RangerGerbesFleurs(int y)
		{
			for (int p = 0; p < GerbeCotes.Length; p++)
			{
				int n = GerbeCotes[p], x = 0;
				for (int v = 0; v < GerbeVariantes; v++)
					foreach (CoucheFleur couche in System.Enum.GetValues(typeof(CoucheFleur)))
					{
						if (x + n > GerbeAtlasLargeur) { x = 0; y += n + 1; }
						_gerbesFleurs[(p, v, couche)] = new Rect2I(x, y, n, n);
						x += n + 1;
					}
				y += n + 1;
			}
			return y;
		}

		// Une fleur de côté t en niveaux du kit : point, bouton, étoile, corolle du kit, puis 5 pétales ronds.
		private static byte[] MotifFleur(int t)
		{
			switch (t)
			{
				case 1: return new byte[] { KitBase };
				case 2: return new byte[] { KitBase, KitBase, KitLumiere, KitBase };
				case 3: return new byte[] { 0, KitBase, 0, KitBase, KitCoeur, KitBase, 0, KitLumiere, 0 };
			}
			var niv = new byte[t * t];
			float c = t * 0.5f, rp = t * 0.22f, dp = t * 0.28f;
			for (int y = 0; y < t; y++)
				for (int x = 0; x < t; x++)
				{
					var q = new Vector2(x + 0.5f - c, y + 0.5f - c);
					if (q.Length() < t * 0.15f) { niv[y * t + x] = KitCoeur; continue; }
					for (int k = 0; k < 5; k++)
					{
						float a = -Mathf.Pi * 0.5f + Mathf.Tau * k / 5f;
						if (q.DistanceTo(new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * dp) > rp) continue;
						// Lumière côté sud = bas de la pièce, comme tout le kit.
						niv[y * t + x] = q.Y > t * 0.15f ? KitLumiere : q.Y < -t * 0.15f ? KitOmbre : KitBase;
						break;
					}
				}
			return niv;
		}

		// Les fleurs d'une gerbe dans une ellipse autour du haut de la pièce, du fond vers l'avant.
		private static void PeindreGerbesFleurs(byte[] rg)
		{
			for (int p = 0; p < GerbeCotes.Length; p++)
			{
				int n = GerbeCotes[p], tf = TailleFleurGerbe[p], tb = TailleBoutonGerbe[p];
				byte[] fleur = MotifFleur(tf), petite = MotifFleur(tf >= 5 ? tf - 2 : tf), bouton = MotifFleur(tb);
				for (int v = 0; v < GerbeVariantes; v++)
				{
					var sites = new List<Vector2>();
					var centre = new Vector2(n * 0.5f, n * 0.45f);
					for (int k = 0; k < FleursParGerbe[p]; k++)
					{
						float a = Mathf.Tau * Hash01(587, p, v * 64 + k), d = Mathf.Sqrt(Hash01(589, p, v * 64 + k));
						sites.Add(Dans(centre + new Vector2(Mathf.Cos(a) * n * 0.4f, Mathf.Sin(a) * n * 0.36f) * d, n, tf));
					}
					sites.Sort((a, b) => a.Y.CompareTo(b.Y));
					for (int k = 0; k < sites.Count; k++)
					{
						byte[] motif = k % 3 == 2 ? petite : fleur;
						int t = k % 3 == 2 && tf >= 5 ? tf - 2 : tf;
						Estamper(rg, _gerbesFleurs[(p, v, CoucheFleur.Fleurs)], sites[k], motif, t, false);
						Estamper(rg, _gerbesFleurs[(p, v, CoucheFleur.Coeurs)], sites[k], motif, t, true);
						Estamper(rg, _gerbesFleurs[(p, v, CoucheFleur.Boutons)], sites[k], bouton, tb, false);
					}
				}
			}
		}

		// `coeurs` : seuls les pixels de cœur, en ton de base ; sinon toute la fleur, cœur compris (il est
		// recouvert par la couche des cœurs, ou fondu dans la fleur sous ×2).
		private static void Estamper(byte[] rg, Rect2I r, Vector2 centre, byte[] niv, int t, bool coeurs)
		{
			byte[] codes = CodesFleuron(niv, t);
			int ox = Mathf.FloorToInt(centre.X - t * 0.5f), oy = Mathf.FloorToInt(centre.Y - t * 0.5f);
			for (int y = 0; y < t; y++)
				for (int x = 0; x < t; x++)
				{
					int i = y * t + x, px = ox + x, py = oy + y;
					if (niv[i] == KitVide || (coeurs && niv[i] != KitCoeur)) continue;
					if (px < 0 || py < 0 || px >= r.Size.X || py >= r.Size.Y) continue;
					Poser(rg, r, px, py, niv[i] == KitCoeur ? KitBase : niv[i], codes[i]);
				}
		}

		/// <summary>×0,5 à ×4 : une gerbe de fleurs (ou de boutons) sur une part des bouts de petit bois,
		/// continue avec `floraison`. Même pied que la gerbe de feuilles du même bout.</summary>
		private void DrawGerbesFleurs(in OrganPalette pal)
		{
			int palier = PalierGerbe(WorldView.CurrentZoom);
			float part = PartFleursArbre() * PartBrindillesFleuries;
			if (palier < 0 || part <= 0f || FleursCachees) return;
			AssurerGerbes();
			float z = WorldView.CurrentZoom, boutons = PartBoutons();
			Vector3 c = _structure.ColletCm;
			FicheFleurArbre fiche = FicheFleurs(pal);
			bool idx = Indexe, coeurs = palier >= 2;
			bool pend = RecettesRameaux[_structure.SpeciesName].Port <= PortPendant;
			int palF = idx ? PaletteIndexee.Palette(pal.Flower) : -1, palB = idx ? PaletteIndexee.Palette(fiche.Bouton) : -1;
			int palC = idx ? PaletteIndexee.Palette(FlowerHeart) : -1;
			Color[] rF = idx ? null : RampeLitterale(pal.Flower, false), rB = idx ? null : RampeLitterale(fiche.Bouton, false);
			Color[] rC = idx ? null : RampeLitterale(FlowerHeart, false);
			float demi = GerbeDemiCm * WorldView.PxPerCmZ;
			foreach (var e in BoisDuHouppier())
			{
				if (palier <= PalierGerbeLoin && Hash01(555, e.Cle, e.Rang) < PartGerbesLoin) continue;
				if (Hash01(543, e.Cle, e.Rang) >= part) continue;
				float zPied = e.B.Z + (pend ? demi / WorldView.PxPerCmZ : -GerbeDemiCm);
				Vector2 pied = Iso(e.B.X - c.X, e.B.Y - c.Y, zPied);
				int v = (int)(Hash01(591, e.Cle, e.Rang) * GerbeVariantes) % GerbeVariantes;
				bool miroir = Hash01(593, e.Cle, e.Rang) < 0.5f, bouton = Hash01(579, e.Cle, e.Rang) < boutons;
				Rect2I r = _gerbesFleurs[(palier, v, bouton ? CoucheFleur.Boutons : CoucheFleur.Fleurs)];
				if (idx) PoserGerbeIndexee(r, pied, z, bouton ? palB : palF, miroir, pend);
				else PoserGerbeLitterale(r, pied, z, bouton ? rB : rF, miroir, pend);
				if (bouton || !coeurs) continue;
				r = _gerbesFleurs[(palier, v, CoucheFleur.Coeurs)];
				if (idx) PoserGerbeIndexee(r, pied, z, palC, miroir, pend);
				else PoserGerbeLitterale(r, pied, z, rC, miroir, pend);
			}
		}
	}
}
