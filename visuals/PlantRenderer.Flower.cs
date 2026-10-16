// SYMBIOSE — PlantRenderer.Flower.cs (partial de PlantRenderer)
// FORME DE FLEUR PAR FAMILLE BOTANIQUE (tronçon T2, sprint RENDU AMBIANCE §3).
//
// Trou comblé : jusqu'ici TOUTE fleur était une corolle générique à 5 pétales
// (DrawFlower dans Organs.cs) ; seule la COULEUR était par espèce
// (`OrganPalette.Flower`). Ici on choisit une SILHOUETTE par FAMILLE dans un
// catalogue FERMÉ de 6 archétypes (ombelle, capitule, épi…), dessinée directement
// en C# — calque exact du patron des feuilles (`PlantRenderer.Leaf.cs`).
//
// Couche B PURE : zéro Python, zéro pont (dérogation D10, comme la forme de
// feuille : la corolle est un fait de RENDU sans équivalent moteur). La famille
// est portée par une table espèce→archétype en C# (kickoff : « préférer la table
// C# » — aucune famille dans le snapshot aujourd'hui).
//
// Invariants (repris de Leaf.cs, NON négociables) :
//  • Jamais d'aplat (E4) : chaque sous-corolle passe par `DrawVolumeCircle`
//    (volume 2 valeurs) — SAUF sous le plancher de rayon, où la fleur retombe
//    sur une tache 1 valeur (le croissant d'ombre serait illisible).
//  • Déterminisme total : ZÉRO Random. Tout jitter (pédicelles, rayons) dérive
//    de `Hash01(canal, i, j)` stable défini dans Organs.cs.
//  • On ne touche PAS la couleur : on réutilise `OrganPalette.Flower` de l'espèce.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// --- Catalogue fermé d'archétypes de corolle (conception §3.1) --------
		// Du plus simple au plus composé. Une espèce non mappée → Simple.
		private enum FlowerShape
		{
			Simple,        // 5 pétales radiaux (l'existant)     — Rosaceae, bourrache
			Ombelle,       // taches sur pédicelles rayonnants   — Apiaceae (carotte)
			Capitule,      // disque central + couronne de rayons — Asteraceae (tournesol)
			Papilionacee,  // étendard + 2 ailes + carène        — Fabaceae (haricot)
			Epi,           // grappe verticale de fleurons       — Lamiaceae/Brassicaceae
			Clochette,     // corolle tubulaire pendante         — Ericaceae (myrtille)
		}

		// --- Descripteur de fleur par espèce (conception §3.2) ----------------
		// Count  = nb de fleurons (Ombelle/Capitule rayons/Epi), sinon 0.
		// Aspect = élancement de la corolle (Epi vertical, Clochette tubulaire).
		private readonly record struct FlowerProfile(FlowerShape Shape, int Count, float Aspect);

		// Table per-espèce EN REGARD de `Palettes` (Organs.cs). Même clé = nom de
		// CLASSE Python (`species` du snapshot). Mappage par FAMILLE botanique ;
		// défaut Simple partout ailleurs (jamais bloquant, on enrichit au fil).
		private static readonly System.Collections.Generic.Dictionary<string, FlowerProfile>
			FlowerProfiles = new()
			{
				// --- Rosaceae + bourrache → Simple (5 pétales) ----------------
				["AppleTree"]  = new(FlowerShape.Simple, 5, 1.0f), // fleur de pommier rosée
				["CherryTree"] = new(FlowerShape.Simple, 5, 1.0f), // fleur de cerisier
				["Strawberry"] = new(FlowerShape.Simple, 5, 1.0f), // fraisier : 5 pétales blancs (Rosaceae)
				["SweetViolet"] = new(FlowerShape.Simple, 5, 1.0f), // violette : corolle à 5 pétales (rendu simple)
				["Borage"]     = new(FlowerShape.Simple, 5, 1.0f), // étoile bleue à 5 pétales
				// --- Apiaceae → Ombelle ---------------------------------------
				["Carrot"]     = new(FlowerShape.Ombelle, 9, 1.0f), // ombelle blanche
				// --- Asteraceae → Capitule (disque + rayons) ------------------
				["Sunflower"]  = new(FlowerShape.Capitule, 14, 1.0f), // grand capitule d'or
				["Yarrow"]     = new(FlowerShape.Capitule, 8, 1.0f),  // corymbe de petits capitules
				["Mugwort"]    = new(FlowerShape.Capitule, 6, 1.0f),  // armoise : menus capitules ternes (Asteraceae)
				// --- Fabaceae → Papilionacée ----------------------------------
				["Bean"]       = new(FlowerShape.Papilionacee, 0, 1.2f), // fleur en papillon
				["Clover"]     = new(FlowerShape.Papilionacee, 0, 1.1f), // capitule papilionacé (rendu simple)
				// --- Lamiaceae / Brassicaceae / Boraginaceae → Épi ------------
				["Lavender"]   = new(FlowerShape.Epi, 6, 2.4f), // épi violet dressé
				["Thyme"]      = new(FlowerShape.Epi, 5, 1.8f), // glomérules en épi lâche
				["Comfrey"]    = new(FlowerShape.Epi, 5, 1.6f), // cyme scorpioïde (rendu épi)
				["Mustard"]    = new(FlowerShape.Epi, 6, 2.0f), // grappe jaune allongée
				["Phacelia"]   = new(FlowerShape.Epi, 6, 1.8f), // cyme enroulée (rendu épi)
				// --- Ericaceae → Clochette ------------------------------------
				["Vaccinium"]  = new(FlowerShape.Clochette, 0, 1.5f), // clochette urcéolée
			};
		private static readonly FlowerProfile DefaultFlower =
			new(FlowerShape.Simple, 5, 1.0f);

		// Plancher de rayon (invariant E4, calque LeafFloorRadiusPx) : sous ce
		// demi-rayon ÉCRAN une corolle composée est illisible → une tache 1 valeur.
		private const float FlowerFloorRadiusPx = 2.5f;
		// (Ex-repli LOD FlowerShapeMinZoom retiré au D106 T6 : la corolle n'est
		// dessinée qu'à partir du palier ORGANES ×8 — à ×4 la fleur est un point,
		// PlantRenderer.PaliersHauts.cs.)

		// Rayon de base d'une corolle à l'écran (px). L'ancien DrawFlower codait
		// ~3.6 px de rayon d'implantation des pétales ; on garde cet ordre.
		private const float FlowerBaseRadiusPx = 4.0f;

		// ---------------------------------------------------------------------
		// TRACÉ — dispatch par archétype. `c` = centre écran ; (i,j) = identité
		// (site organe, canal) → graine déterministe du jitter. Remplace l'ancien
		// DrawFlower (5 pétales génériques) : signature enrichie, même appelant.
		// ---------------------------------------------------------------------
		private void DrawFlowerShape(Vector2 c, OrganPalette pal, int i, int j)
		{
			float r = FlowerBaseRadiusPx;
			// Plancher de rayon : trop petite → une tache volumée simple, pas de
			// composition (le croissant d'ombre reste, jamais d'aplat).
			if (r < FlowerFloorRadiusPx)
			{
				DrawVolumeCircle(c, r, pal.Flower);
				return;
			}

			if (!FlowerProfiles.TryGetValue(_structure.SpeciesName, out var prof))
				prof = DefaultFlower;

			FlowerShape shape = prof.Shape;
			switch (shape)
			{
				case FlowerShape.Ombelle:      DrawOmbelle(c, r, pal, prof, i, j); break;
				case FlowerShape.Capitule:     DrawCapitule(c, r, pal, prof, i, j); break;
				case FlowerShape.Papilionacee: DrawPapilionacee(c, r, pal, prof); break;
				case FlowerShape.Epi:          DrawEpi(c, r, pal, prof, i, j); break;
				case FlowerShape.Clochette:    DrawClochette(c, r, pal, prof); break;
				default:                       DrawSimple(c, r, pal); break;
			}
			// Palier INTIME (×32, D106 T6) : étamines par archétype.
			if (AuPalier(PalierIntimeZoom)) DrawEtamines(c, r, shape);
		}

		// --- Simple : 5 pétales radiaux + cœur (= l'ancien DrawFlower) ---------
		// Conservé à l'identique (tailles px du prototype) → continuité visuelle
		// pour les Rosaceae et la bourrache, et repli LOD de toutes les autres.
		private void DrawSimple(Vector2 c, float r, OrganPalette pal)
		{
			for (int p = 0; p < 5; p++)
			{
				float a = Mathf.Tau * p / 5f;
				DrawVolumeCircle(c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * (r * 0.9f),
								 r * 0.65f, pal.Flower);
			}
			DrawCircle(c, r * 0.5f, FlowerHeart);
		}

		// --- Ombelle (Apiaceae) : N petites taches au bout de pédicelles --------
		// rayonnants d'un point (la carotte : ombelle blanche plate). Longueur de
		// pédicelle jittée au hash → l'ombelle n'est pas un cercle parfait.
		private void DrawOmbelle(Vector2 c, float r, OrganPalette pal, FlowerProfile p, int i, int j)
		{
			int n = Mathf.Clamp(p.Count, 5, 12);
			float spread = r * 1.4f;
			Color pedicel = HueShift(pal.Flower, -OrganShade); // tige claire de la fleur
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * k / n;
				float len = spread * (0.7f + 0.5f * Hash01(53, i, j + k));
				Vector2 tip = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * len;
				DrawLine(c, tip, pedicel, 1f, antialiased: false);
				DrawVolumeCircle(tip, r * 0.32f, pal.Flower); // fleuron au bout
			}
		}

		// --- Capitule (Asteraceae) : disque central sombre + couronne de rayons -
		// (tournesol, achillée). Les rayons = pétales ligulés = petites ellipses
		// allongées radialement, puis un disque de fleurons au centre.
		private void DrawCapitule(Vector2 c, float r, OrganPalette pal, FlowerProfile p, int i, int j)
		{
			int n = Mathf.Clamp(p.Count, 6, 16);
			float petalR = r * 1.15f;
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * k / n;
				Vector2 dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				// pétale ligulé posé sur son rayon, longueur légèrement jittée.
				float len = petalR * (0.85f + 0.25f * Hash01(59, i, j + k));
				DrawVolumeCircle(c + dir * (len * 0.6f), r * 0.55f, pal.Flower);
			}
			// disque central : cœur de fleurons bruns-dorés (2 valeurs).
			DrawVolumeCircle(c, r * 0.6f, FruitRotten); // cœur sombre du capitule
			DrawCircle(c, r * 0.3f, FlowerHeart);       // centre lumineux
		}

		// --- Papilionacée (Fabaceae) : étendard + 2 ailes + carène --------------
		// La fleur en « papillon » du haricot/trèfle. Trois volumes empilés :
		// un grand pétale dressé (étendard, au sud-projeté), deux ailes latérales,
		// une carène basse. Forme FIXE (pas de hash → une fleur pisiforme nette).
		private void DrawPapilionacee(Vector2 c, float r, OrganPalette pal, FlowerProfile p)
		{
			var axis = SouthDir();
			var cross = new Vector2(-axis.Y, axis.X);
			// carène (dessous), puis ailes, puis étendard (dessus) — ordre de pile.
			DrawVolumeCircle(c + axis * (r * 0.35f), r * 0.55f, pal.Flower);         // carène
			DrawVolumeCircle(c + cross * (r * 0.6f), r * 0.5f, pal.Flower);          // aile droite
			DrawVolumeCircle(c - cross * (r * 0.6f), r * 0.5f, pal.Flower);          // aile gauche
			DrawEllipse(c - axis * (r * 0.45f),
						r * 0.9f * p.Aspect, r * 0.75f, HueShift(pal.Flower, OrganLit)); // étendard éclairé
		}

		// --- Épi (Lamiaceae/Brassicaceae) : pile verticale de fleurons ----------
		// La lavande/moutarde : grappe dressée. On empile Count fleurons le long de
		// l'axe (sud-projeté), du plus large en bas au plus serré en haut, jitter
		// latéral léger au hash. Aspect = allongement de l'épi.
		private void DrawEpi(Vector2 c, float r, OrganPalette pal, FlowerProfile p, int i, int j)
		{
			int n = Mathf.Clamp(p.Count, 3, 8);
			var axis = -SouthDir();               // l'épi monte (vers le nord-projeté = haut)
			var cross = new Vector2(-axis.Y, axis.X);
			float step = r * 1.3f * p.Aspect / n; // pas vertical entre fleurons
			for (int k = 0; k < n; k++)
			{
				float up = (k - (n - 1) * 0.5f) * step;
				float jit = (Hash01(61, i, j + k) - 0.5f) * r * 0.4f;
				Vector2 fc = c + axis * up + cross * jit;
				float taper = 1f - 0.4f * (k / (float)n); // fleurons plus fins vers le sommet
				DrawVolumeCircle(fc, r * 0.5f * taper, pal.Flower);
			}
		}

		// --- Clochette (Ericaceae) : corolle tubulaire pendante -----------------
		// La myrtille : petite urne fermée qui pend. Un corps ovale allongé selon
		// l'axe (tube) + une lèvre resserrée en bas. Aspect = allongement du tube.
		private void DrawClochette(Vector2 c, float r, OrganPalette pal, FlowerProfile p)
		{
			var down = SouthDir();                // la clochette pend vers le sud-projeté (bas)
			// corps du tube (ellipse allongée selon l'axe de pente).
			DrawVolumeEllipse(c, r * 0.7f, r * 0.55f * p.Aspect, pal.Flower);
			// lèvre resserrée en bout de tube (ouverture plus sombre).
			DrawVolumeCircle(c + down * (r * 0.55f * p.Aspect),
							 r * 0.4f, HueShift(pal.Flower, -OrganShade));
		}
	}
}
