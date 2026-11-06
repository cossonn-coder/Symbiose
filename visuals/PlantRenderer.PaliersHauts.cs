// SYMBIOSE — PlantRenderer.PaliersHauts.cs (partial, sprint RENDU VISIBLE D106 T6)
// Les PALIERS HAUTS du dessin d'une plante : ×4 · ×8 · ×16 · ×32. Ils prolongent
// l'échelle CUMULATIVE des paliers bas (PlantRenderer.Paliers.cs, T5) — chaque
// cran garde tout ce que montrent les plus éloignés et ajoute UNE catégorie
// d'information (conception_rendu_visible.md §4 D4) :
//   ×4  ARCHITECTURE : le bois (segments, DrawSegments) + des MASSES de feuillage
//       (une touffe par tronçon feuillu) ; fleurs et fruits en POINTS colorés.
//   ×8  ORGANES : la feuille à la forme de l'espèce (Leaf.cs), le pétiole, la
//       fleur par famille (Flower.cs), le fruit en globe (maturité lisible).
//   ×16 SYMPTÔMES FINS : nervures, contour fidèle (LeafOutline.cs), morsures
//       (`ravageurs`), criblage + encoches de grêle, bords nécrosés (`gel`,
//       `secheresse`), taches (`maladie`), liseré de givre.
//   ×32 INTIME : nervures secondaires, étamines, poils / pruine / glandes
//       (texture de surface par espèce, table ci-dessous, cosmétique).
//
// Ce fichier tient les seuils et ce qui est PROPRE aux paliers hauts (masses,
// points, détails fins, intime) ; les organes eux-mêmes restent dans leurs
// partials (Organs/Leaf/Flower/Froid), qui demandent `AuPalier(...)` au bon
// endroit. Tout reste déterministe : positions au hash (Hash01), zéro Random.
//
// 📖 Pédagogie : rien de tout ça ne coûte à l'AFFICHAGE (un quad cuit par plante).
// Un palier plus fin coûte à la CUISSON (CPU, file à budget) — c'est pourquoi le
// ×4 dessine des masses (≈ 1 ellipse par tronçon) au lieu de chaque feuille :
// plus lisible ET moins cher à cuire que le feuillage complet d'avant.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// Seuils des paliers hauts (le ×4 = PaliersHautsMinZoom, Paliers.cs).
		internal const float PalierOrganesZoom = 8f;
		internal const float PalierSymptomesZoom = 16f;
		internal const float PalierIntimeZoom = 32f;

		/// <summary>Le zoom courant a-t-il atteint le palier `z` ?</summary>
		private static bool AuPalier(float z) => WorldView.CurrentZoom >= z;

		// Un pixel INTERNE (grille pixel-art) exprimé en px canvas : l'épaisseur
		// des traits fins (nervures secondaires, étamines, poils).
		private static float PixelInterne => 1f / WorldView.CurrentZoom;

		// Masses (×4) : nombre de feuilles voisines regroupées en une masse.
		private const int MasseFeuilles = 3;
		// Points (×4) : rayon d'un point de fleur / part du rayon d'un fruit.
		private const float PointFleurPx = 1f;
		private const float PointFruitPart = 0.5f;
		// Nervures (×16) d'une plante vivante : largeur à l'échelle (FORMES ⑥), 1 px interne
		// jusqu'à ×16, 2 à ×32 (avant : 4 à ×32, grossières) ; et contraste de teinte
		// assez fort pour survivre à la quantification SNES (palette 34).
		private static float NervureLargeur => Mathf.Max(PixelInterne, 0.0625f);
		private const float NervureShift = 0.45f;
		// Nécrose de sécheresse (×16) : bord brûlé beige-brun.
		private static readonly Color SecheEdgeColor = new Color("8a6a3a");

		// ---------------------------------------------------------------------------
		// ×4 — MASSES DE FEUILLAGE (appelé par DrawOrgans sous PalierOrganesZoom)
		// ---------------------------------------------------------------------------

		// Les feuilles RÉELLES (mêmes présences au hash, mêmes positions que le ×8 :
		// PlaceFeuille, Organs.cs) regroupées par paquets de MasseFeuilles voisines
		// d'un rameau : une ellipse volumée couvre chaque paquet. Au cran suivant
		// les feuilles apparaissent là où étaient les masses — rien ne saute.
		// Teinte = celle de la 1ʳᵉ feuille (espèce + automne + santé + givre) ;
		// neige au hash. L'ombre (`_litFactor`) et le repli froid sont posés par
		// DrawOrgans.
		private void DrawMassesFeuillage(Vector3 collet, OrganPalette pal, float automne, float density)
		{
			foreach (var s in _structure.Segments)
			{
				if (!IsLeafy(s)) continue;
				int i = CleSegment(s);   // stable : une coupe ailleurs ne déplace rien (HOUPPIER ④)
				float growth = LeafGrowthFactor(s);
				float r = LeafSizeCm * TailleFeuilleEspece * WorldView.PxPerCmX * growth;
				int n = NbFeuilles(s);
				Vector2 perp = PerpFeuilles(s);
				for (int j0 = 0; j0 < n; j0 += MasseFeuilles)
				{
					var boite = new Rect2();
					int vues = 0;
					for (int j = j0; j < Mathf.Min(n, j0 + MasseFeuilles); j++)
					{
						if (Hash01(17, i, j) >= density) continue;
						Vector2 c = PlaceFeuille(s, i, j, n, perp, collet, growth, out _, out _);
						boite = vues++ == 0 ? new Rect2(c, Vector2.Zero) : boite.Expand(c);
					}
					if (vues == 0 || r <= 0f) continue;
					float rx = boite.Size.X * 0.5f + r * 1.15f;
					float ry = boite.Size.Y * 0.5f + r * 0.65f * LeafOpen;
					Color col = Frosted(SymptomTint(LeafColor(pal, automne, Hash01(13, i, j0))));
					DrawVolumeEllipse(boite.GetCenter(), rx, ry, col);
					if (_snow > 0f && Hash01(47, i, j0) < _snow) DrawSnowCrown(boite.GetCenter(), rx, ry);
				}
			}
		}

		// ---------------------------------------------------------------------------
		// ×4 POINTS → ×8 ORGANES — fleurs et fruits
		// ---------------------------------------------------------------------------

		// Fleurs : VRAI état moteur (`floraison` par plante ≥ FloraisonSeuil, à SA
		// semaine propre — désync ③). ×4 : un point couleur de fleur par site ;
		// ×8 : la tache en grammaire SNES (PoserFleurSnes, FORMES ⑥).
		private void DrawFleurs(Vector3 collet, OrganPalette pal)
		{
			if (Houppier) { DrawFleursHouppier(collet, pal); return; }   // bouquets continus (VERGER VIVANT ④)
			if (_structure.Floraison < FloraisonSeuil) return;
			bool organes = AuPalier(PalierOrganesZoom);
			var sites = OrganSites();
			if (organes) { _lotPrairie ??= new LotTriangles(); _lotPrairie.Vider(); }
			for (int k = 0; k < sites.Count; k++)
			{
				Vector2 c = Iso(sites[k].X - collet.X, sites[k].Y - collet.Y, sites[k].Z);
				if (organes) PoserFleurSnes(c, pal.Flower, k);   // PlantRenderer.FleurSnes.cs
				else DrawPoint(c, PointFleurPx, pal.Flower);
			}
			if (organes) _lotPrairie.DessinerSansMaille(this);
		}

		// Fruits tracés : un par entrée de `_structure.Fruits` (état moteur ③ :
		// maturité vert→mûr→brun, déplétion par `manger`), ancré au bout de son
		// segment porteur, TAILLE ∝ masse. ×4 : point plein couleur de maturité ;
		// ×8 : globe 2 valeurs + reflet ; ×32 : pruine des espèces pruinées.
		private void DrawFruits(Vector3 collet, OrganPalette pal)
		{
			if (Houppier) { DrawFruitsHouppier(); return; }   // brindilles, taille en cm (HOUPPIER ⑤)
			bool organes = AuPalier(PalierOrganesZoom);
			bool pruine = AuPalier(PalierIntimeZoom) && SurfaceDe() == Surface.Pruine;
			for (int k = 0; k < _structure.Fruits.Count; k++)
			{
				var f = _structure.Fruits[k];
				Vector3 p3 = FruitPoint(f);
				Vector2 c = Iso(p3.X - collet.X, p3.Y - collet.Y, p3.Z);
				// masse → rayon (FRUIT_MASSE=0.15 côté moteur → ~4.5 px ; borné).
				float rad = 3.0f + Mathf.Min(f.Masse, 0.3f) * 10f;
				Color col = FruitColor(pal, f.Maturite);
				if (!organes) { DrawPoint(c, rad * PointFruitPart, col); continue; }
				// SS② : globe en 2 valeurs, PUIS le reflet spéculaire blanc. ④ indexé :
				// le globe est un dôme qui s'éclaire côté soleil — pas de reflet fixe.
				DrawVolumeCircle(c, rad, col);
				if (!Indexe)
					DrawCircle(c - new Vector2(rad * 0.3f, rad * 0.3f),
							   rad * 0.3f, new Color(1f, 1f, 1f, 0.45f));
				if (pruine) DrawSemis(c, rad * 0.8f, rad * 0.8f, 8, 101, k, 0, PruineColor);
			}
		}

		// Point de fleur / de fruit (×4) — CASSÉ À L'ÉCRAN ④ : tache de couleur PURE,
		// contour 1 px du ton le plus sombre de sa propre rampe (brief : petits objets).
		private void DrawPoint(Vector2 c, float r, Color col)
		{
			DrawCircle(c, r + PixelInterne, Ton(col, 0));
			DrawCircle(c, r, Ton(col, PaletteIndexee.TonBase));
		}

		// ---------------------------------------------------------------------------
		// ×16 SYMPTÔMES FINS → ×32 INTIME — par feuille (appelé par DrawOrgans)
		// ---------------------------------------------------------------------------

		/// <summary>Détails d'une feuille de centre `c`, rayon `r` : symptômes fins
		/// (×16) puis texture de surface (×32). Rien sous ×16.</summary>
		private void DrawDetailsFeuille(Vector2 c, float r, int i, int j)
		{
			if (!AuPalier(PalierSymptomesZoom)) return;
			DrawLeafDamage(c, r, i, j);
			if (AuPalier(PalierIntimeZoom)) DrawSurfaceFeuille(c, r, i, j);
		}

		// Marques de TEXTURE (canaux additifs de la sémiologie ③), par-dessus le
		// limbe. Ravageurs + grêle CRIBLENT le limbe (petits trous sombres, nombre ∝
		// intensité) ; gel NOIRCIT les bords, sécheresse les BRÛLE (beige-brun) ;
		// maladie pique de pustules. Au hash (i,j,k) → stables inter-frames.
		private void DrawLeafDamage(Vector2 c, float r, int i, int j)
		{
			float bite = Mathf.Min(1f, _ravageurs + _grele); // criblage cumulé
			int holes = Mathf.CeilToInt(bite * 4f);          // 0 à 4 morsures
			for (int k = 0; k < holes; k++)
				DrawCircle(PointDansLimbe(c, r, 23 + k, 29 + k, i, j, 0.3f, 0.55f),
						   r * 0.22f, Trou(LeafHoleColor));
			if (_gel > 0f)
				DrawEllipseOutline(c, r * 1.15f, r * 0.65f, Lit(GelEdgeColor), Mathf.Max(1f, _gel * 2.5f));
			// Sécheresse : nécrose MARGINALE (le bord sèche d'abord), après le gel
			// pour qu'un gel plus fort reste lisible au-dessus d'elle.
			else if (_drought > 0f)
				DrawEllipseOutline(c, r * 1.15f, r * 0.65f * LeafOpen, Lit(SecheEdgeColor),
								   Mathf.Max(PixelInterne, r * 0.15f * _drought));
			// maladie : salt NEUF (37/41) ≠ criblage (23/29) → jamais superposés ;
			// rayon r*0.12 << r*0.22 du criblage (ponctuation, pas morsure).
			int spots = Mathf.CeilToInt(_maladie * 5f);      // 0 à 5 taches
			for (int k = 0; k < spots; k++)
				DrawCircle(PointDansLimbe(c, r, 37 + k, 41 + k, i, j, 0.2f, 0.65f),
						   r * 0.12f, Lit(LeafSpotColor));
		}

		// Un point du limbe au hash : angle (canal ca), rayon relatif dans
		// [r0, r0 + dr] (canal cr), sur l'ellipse de la feuille (1,15 r × 0,65 r).
		private static Vector2 PointDansLimbe(Vector2 c, float r, int ca, int cr, int i, int j,
											  float r0, float dr)
		{
			float a = Hash01(ca, i, j) * Mathf.Tau;
			float d = r0 + dr * Hash01(cr, i, j);
			return c + new Vector2(Mathf.Cos(a) * d * r * 1.15f, Mathf.Sin(a) * d * r * 0.65f);
		}

		// ---------------------------------------------------------------------------
		// ×32 INTIME — texture de surface par espèce (cosmétique, côté vue)
		// ---------------------------------------------------------------------------

		// Surface du limbe (et du fruit) : un fait de RENDU, sans contrepartie
		// moteur (comme la forme de feuille, dérogation D10). Espèce absente = lisse.
		private enum Surface { Lisse, Poils, Pruine, Glandes }
		private static readonly Dictionary<string, Surface> Surfaces = new()
		{
			["Comfrey"] = Surface.Poils,     // consoude : feuille rêche, très velue
			["Borage"] = Surface.Poils,      // bourrache : poils raides blancs
			["Sunflower"] = Surface.Poils,   // tournesol : limbe scabre
			["Tomato"] = Surface.Poils,      // tomate : trichomes glanduleux (odeur)
			["Zucchini"] = Surface.Poils,    // courgette : pétiole et limbe piquants
			["Phacelia"] = Surface.Poils,    // phacélie : hispide
			["Mugwort"] = Surface.Poils,     // armoise : revers argenté tomenteux
			["Lavender"] = Surface.Poils,    // lavande : feutrage gris
			["Thyme"] = Surface.Poils,       // thym : fin duvet
			["Strawberry"] = Surface.Poils,  // fraisier : soies sur les nervures
			["Garlic"] = Surface.Pruine,     // ail : feuille glauque cireuse
			["Vaccinium"] = Surface.Pruine,  // myrtille : baie pruinée bleu-gris
			["Drosera"] = Surface.Glandes,   // drosera : tentacules rouges à glu
		};
		private static readonly Color PoilColor = new Color(1f, 1f, 0.94f, 0.55f);
		private static readonly Color PruineColor = new Color(0.82f, 0.88f, 0.95f, 0.5f);
		private static readonly Color GluColor = new Color(1f, 1f, 1f, 0.8f);

		private Surface SurfaceDe() =>
			Surfaces.TryGetValue(_structure.SpeciesName, out var s) ? s : Surface.Lisse;

		// Poils : courtes soies au bord, vers l'extérieur. Pruine : semis de points
		// pâles sur le limbe. Glandes : tentacules rouges à goutte de glu.
		private void DrawSurfaceFeuille(Vector2 c, float r, int i, int j)
		{
			Surface s = SurfaceDe();
			if (s == Surface.Pruine) { DrawSemis(c, r, r * 0.55f, 6, 103, i, j, PruineColor); return; }
			if (s == Surface.Lisse) return;
			bool glandes = s == Surface.Glandes;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			int n = glandes ? 8 : 10;
			float px = PixelInterne;
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * (k + Hash01(107, i, j + k) * 0.6f) / n;
				var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				Vector2 bord = c + new Vector2(u.X * r * 1.15f, u.Y * r * 0.65f);
				Vector2 pointe = bord + u * r * (glandes ? 0.4f : 0.18f);
				DrawLine(bord, pointe, Lit(glandes ? pal.FruitRipe : PoilColor), px, antialiased: false);
				if (glandes) DrawCircle(pointe, 1.5f * px, Lit(GluColor));
			}
		}

		// Semis de `n` points d'1 px interne dans l'ellipse (rx, ry), au hash de
		// l'organe (i, j) : les mêmes points à chaque cuisson.
		private void DrawSemis(Vector2 c, float rx, float ry, int n, int canal, int i, int j, Color col)
		{
			float px = PixelInterne;
			for (int k = 0; k < n; k++)
			{
				float a = Hash01(canal, i, j * 31 + k) * Mathf.Tau;
				float d = Mathf.Sqrt(Hash01(canal + 1, i, j * 31 + k));
				Vector2 p = c + new Vector2(Mathf.Cos(a) * rx * d, Mathf.Sin(a) * ry * d);
				DrawRect(new Rect2(p, new Vector2(px, px)), Lit(col));
			}
		}

		/// <summary>Nervures secondaires (×32) : de courtes nervilles de part et
		/// d'autre de la médiane, chacune fourchue — le réseau qui se devine entre
		/// les nervures principales (Leaf.cs). Couleur = celle des nervures, adoucie.</summary>
		private void DrawNervuresSecondaires(Vector2 c, float rx, float ry, Color vein, int i, int j)
		{
			var (axis, cross) = LeafFrame();
			float px = Mathf.Max(PixelInterne, NervureLargeur * 0.5f);
			int n = 4 + (int)(Hash01(97, i, j) * 2.99f);
			for (int k = 0; k < n; k++)
			{
				Vector2 ancre = c + axis * (ry * ((k + 0.5f) / n * 1.6f - 0.8f));
				float reach = rx * 0.35f * (0.7f + 0.3f * Hash01(99, i, j + k));
				for (int side = -1; side <= 1; side += 2)
				{
					Vector2 bout = ancre + (cross * side + axis * 0.3f).Normalized() * reach;
					DrawLine(ancre, bout, Lit(vein), px, antialiased: false);
					DrawLine(bout, bout + (cross * side - axis * 0.4f).Normalized() * reach * 0.4f,
							 Lit(vein), px, antialiased: false);
				}
			}
		}

		/// <summary>Étamines (×32) selon l'archétype de corolle : filets + anthères
		/// rayonnants (Simple), fleurons en spirale sur le disque (Capitule), style
		/// qui pointe hors de l'urne (Clochette). Rien ailleurs (cachées ou trop fines).</summary>
		private void DrawEtamines(Vector2 c, float r, FlowerShape shape)
		{
			float px = PixelInterne;
			// Anthères foncées : un écart de teinte léger fondrait dans la palette SNES.
			Color anthere = FruitRotten.Darkened(0.35f);
			switch (shape)
			{
				case FlowerShape.Simple:
					for (int k = 0; k < 8; k++)
					{
						float a = Mathf.Tau * (k + 0.5f) / 8f;
						Vector2 bout = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r * 0.45f;
						DrawLine(c, bout, Lit(FlowerHeart), px, antialiased: false);
						DrawRect(new Rect2(bout, new Vector2(px, px) * 2f), Lit(anthere));
					}
					break;
				case FlowerShape.Capitule:
					for (int k = 0; k < 21; k++)   // spirale de l'angle d'or (fleurons)
					{
						float a = k * 2.39996f, d = r * 0.5f * Mathf.Sqrt((k + 0.5f) / 21f);
						DrawRect(new Rect2(c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * d,
										   new Vector2(px, px) * 2f), Lit(anthere));
					}
					break;
				case FlowerShape.Clochette:
					Vector2 bouche = c + SouthDir() * (r * 0.75f);
					DrawLine(bouche, bouche + SouthDir() * (r * 0.3f), Lit(FlowerHeart), px, antialiased: false);
					break;
			}
		}
	}
}
