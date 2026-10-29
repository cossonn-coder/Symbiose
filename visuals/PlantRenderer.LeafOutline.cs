// SYMBIOSE — PlantRenderer.LeafOutline.cs (partial de PlantRenderer)
// FEUILLE FIDÈLE AU MODÈLE RÉEL (tronçon T6, sprint RENDU AMBIANCE, D58).
//
// Trou comblé : au zoom rapproché, l'amas d'ellipses de `Leaf.cs` se lisait en
// TACHES ovales, même pour un chêne « lobé » ou une tomate « composée ». Ici on
// pose, AU PALIER HAUT SEULEMENT (×16+), un VRAI CONTOUR de silhouette authoré
// par espèce : polygone fermé façonné d'après la feuille réelle (marge entière /
// dentée / lobée, ou composée pennée à folioles).
//
// Trois paliers LOD (attente honnête) — le dispatch vit dans Leaf.cs :
//  • zoom ≥ PalierSymptomesZoom (16) : CE fichier — contour fidèle + volume + nervures.
//  • [LeafShapeMinZoom(4), 16[   : archétype d'ellipses de Leaf.cs (repli intermédiaire).
//  • < 4                          : tache simple (existant).
// Au dézoom la silhouette fine est de toute façon invisible (2-5 px) : on ne
// PAIE le contour que quand il se voit (peu de plantes à l'écran, culling actif).
//
// Invariants (NON négociables, cf. Leaf.cs / Palette.cs) :
//  • VOLUME ≥ 2 valeurs (E4, jamais d'aplat) : le polygone est rempli en teinte
//    OMBRÉE (HueShift froid), puis une COPIE réduite ~0,8 décalée au SUD est
//    re-remplie en teinte ÉCLAIRÉE — même logique que `DrawVolumeEllipse`, mais
//    sur un contour quelconque au lieu d'une ellipse.
//  • DÉTERMINISME total : contour STATIQUE (aucun aléa de forme) ; le seul jitter
//    est un léger gauchissement de largeur, dérivé de `Hash01` (canaux dédiés,
//    ZÉRO Random). Deux feuilles diffèrent mais sont reproductibles (philo #3).
//  • NERVURES par-dessus : on réutilise `DrawLeafVeins` de Leaf.cs (penninerve /
//    palmée / composée) selon la topologie du contour — pas de code dupliqué.
//  • Filtre Nearest partout, polygone NON antialiasé (cohérent pixel-art).
//
// Dérogation D10 assumée : la FORME de feuille est un fait de RENDU (pas de
// contrepartie moteur), tracée directement en C#. Couche B PURE : zéro Python,
// zéro pont, golden inchangé.
//
// AUTHORING PAR ESPÈCE, sans centaines de coordonnées à la main : chaque espèce
// porte un `OutlineSpec` COMPACT (silhouette de base + marge + profondeur/nombre
// de lobes + composée pennée). Le contour est SYNTHÉTISÉ depuis ce descripteur —
// mais le descripteur est réglé À LA MAIN, feuille réelle sous les yeux. C'est
// « authoré par espèce » (chaque entrée est un choix), lisible et éditable au F5,
// tout en restant fidèle (chêne = lobes profonds arrondis, pommier = ovale denté,
// figuier = palmatilobé, tomate = pennée…). Espèce non mappée → repli archétype.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// Palier HAUT : à partir de ×16 (PalierSymptomesZoom, D106 T6 — ex-
		// LeafOutlineMinZoom) on dessine le contour fidèle ; en dessous l'archétype
		// d'ellipses de Leaf.cs prend le relais. 16 = premier palier entier où une
		// feuille fait assez de pixels pour qu'une marge dentée/lobée se lise
		// (physique du pixel, §3bis.1).

		// --- Descripteur de contour par espèce -------------------------------
		// Silhouette = base × marge × (lobes | folioles). Tout est compact ET
		// réglé à la main d'après la feuille réelle de l'espèce.
		private enum LeafMargin { Entiere, Dentee, Lobee }

		// Base    : élancement du limbe (longueur/largeur), 1 = rond, 3 = ruban.
		// Margin  : bord du limbe (lisse / petites dents / sinus profonds).
		// Lobes   : nb de lobes si Margin=Lobee (paires + pointe), sinon ignoré.
		// LobeCut : profondeur des sinus lobés [0,1] (0.2 = festons, 0.6 = découpé).
		// Tip     : acuité du sommet [0,1] (0 = arrondi obtus, 1 = acuminé pointu).
		// BaseCut : échancrure basale [0,1] (0 = cunéiforme, 1 = cordé/sagitté).
		// Compound: >0 = feuille COMPOSÉE pennée de N folioles (le limbe unique est
		//           abandonné au profit de N petites folioles dentées le long d'un
		//           rachis) ; 0 = limbe simple.
		private readonly record struct OutlineSpec(
			float Aspect, LeafMargin Margin, int Lobes, float LobeCut,
			float Tip, float BaseCut, int Compound);

		// Table per-espèce EN REGARD de `LeafProfiles` (Leaf.cs). Clé = nom de
		// CLASSE Python (`_structure.SpeciesName`). ~27 espèces du catalogue.
		private static readonly System.Collections.Generic.Dictionary<string, OutlineSpec>
			LeafOutlines = new()
			{
				// --- Cultivées potagères -------------------------------------
				["Tomato"]    = new(1.6f, LeafMargin.Dentee, 0, 0f,   0.6f, 0.1f, 5), // composée pennée, folioles dentées
				["Pepper"]    = new(1.9f, LeafMargin.Entiere, 0, 0f,  0.9f, 0.0f, 0), // ovale-lancéolé lisse, acuminé
				["Bean"]      = new(1.2f, LeafMargin.Entiere, 0, 0f,  0.7f, 0.6f, 0), // foliole cordée pointue
				["Clover"]    = new(1.0f, LeafMargin.Dentee, 0, 0f,   0.1f, 0.3f, 0), // foliole obcordée (sommet échancré)
				["Sunflower"] = new(1.2f, LeafMargin.Dentee, 0, 0f,   0.7f, 0.7f, 0), // grand cordé rugueux denté
				["Carrot"]    = new(1.4f, LeafMargin.Dentee, 0, 0f,   0.8f, 0.1f, 5), // très découpé → pennée fine
				["Zucchini"]  = new(1.0f, LeafMargin.Lobee,  5, 0.5f, 0.5f, 0.7f, 0), // palmatilobée large
				["Strawberry"]= new(1.0f, LeafMargin.Dentee, 0, 0f,   0.4f, 0.2f, 3), // trifoliolée dentée
				["CornSalad"] = new(2.0f, LeafMargin.Entiere, 0, 0f,  0.2f, 0.0f, 0), // spatule obtuse en rosette
				["Garlic"]    = new(3.4f, LeafMargin.Entiere, 0, 0f,  0.9f, 0.0f, 0), // long ruban dressé
				["Basil"]     = new(1.5f, LeafMargin.Entiere, 0, 0f,  0.7f, 0.1f, 0), // ovale luisant lisse
				["Mint"]      = new(1.6f, LeafMargin.Dentee, 0, 0f,   0.7f, 0.2f, 0), // ovale denté gaufré
				["Wheat"]     = new(6.0f, LeafMargin.Entiere, 0, 0f,  0.9f, 0.0f, 0), // limbe graminéen linéaire
				["Hemp"]      = new(2.6f, LeafMargin.Dentee,  7, 0.7f, 0.9f, 0.4f, 0), // palmée digitée à folioles étroites
				// --- Compagnes / mellifères / engrais verts ------------------
				["Yarrow"]    = new(1.3f, LeafMargin.Dentee, 0, 0f,   0.8f, 0.1f, 5), // plumeuse finement divisée
				["Phacelia"]  = new(1.4f, LeafMargin.Dentee, 0, 0f,   0.7f, 0.1f, 5), // pennatiséquée
				["Borage"]    = new(1.5f, LeafMargin.Entiere, 0, 0f,  0.5f, 0.2f, 0), // grande ovale poilue
				["Comfrey"]   = new(2.4f, LeafMargin.Entiere, 0, 0f,  0.8f, 0.1f, 0), // grande lancéolée
				["Mustard"]   = new(1.6f, LeafMargin.Lobee,  3, 0.4f, 0.6f, 0.2f, 0), // lyrée (lobe terminal large)
				["BursaPastoris"] = new(1.8f, LeafMargin.Lobee, 5, 0.5f, 0.6f, 0.1f, 0), // rosette lyrée-pennatifide
				["MedicagoLupulina"] = new(1.0f, LeafMargin.Dentee, 0, 0f, 0.4f, 0.2f, 3), // trifoliolée (lupuline)
				["Taraxacum"] = new(2.6f, LeafMargin.Lobee,  5, 0.6f, 0.7f, 0.1f, 0), // pissenlit runciné (dents « lion »)
				// --- Aromatiques persistantes (Lamiacées evergreen) ----------
				["Thyme"]     = new(2.8f, LeafMargin.Entiere, 0, 0f,  0.6f, 0.0f, 0), // micro-feuille linéaire
				["Lavender"]  = new(3.5f, LeafMargin.Entiere, 0, 0f,  0.7f, 0.0f, 0), // étroite gris-vert
				// --- Sauvages / sous-arbrisseaux -----------------------------
				["Nettle"]    = new(1.5f, LeafMargin.Dentee, 0, 0f,   0.8f, 0.5f, 0), // ortie : cordée fortement dentée
				["Vaccinium"] = new(1.6f, LeafMargin.Entiere, 0, 0f,  0.6f, 0.1f, 0), // petit limbe ovale entier
				["Raspberry"] = new(1.2f, LeafMargin.Dentee, 0, 0f,   0.6f, 0.4f, 3), // ronce : composée dentée
				["RunningBamboo"] = new(5.0f, LeafMargin.Entiere, 0, 0f, 0.9f, 0.0f, 0), // lame linéaire
				["SweetViolet"]  = new(1.0f, LeafMargin.Dentee, 0, 0f, 0.3f, 0.7f, 0), // violette : cordée crénelée
				["Ivy"]       = new(1.1f, LeafMargin.Lobee,  5, 0.4f, 0.6f, 0.6f, 0), // lierre palmatilobé cordé
				["Jasmine"]   = new(1.5f, LeafMargin.Entiere, 0, 0f,  0.8f, 0.2f, 3), // jasmin : composée entière
				// --- Pérennes ligneuses (vergers + essences du décor) --------
				["AppleTree"]  = new(1.5f, LeafMargin.Dentee, 0, 0f,  0.6f, 0.1f, 0), // ovale denté
				["Fig"]        = new(1.0f, LeafMargin.Lobee,  5, 0.6f, 0.5f, 0.7f, 0), // grande palmatilobée profonde
				["CherryTree"] = new(1.9f, LeafMargin.Dentee, 0, 0f,  0.9f, 0.1f, 0), // ovale-lancéolé denté, acuminé
				["WalnutTree"] = new(1.7f, LeafMargin.Entiere, 0, 0f, 0.8f, 0.1f, 5), // composée pennée à folioles entières
				["OakTree"]    = new(1.6f, LeafMargin.Lobee,  5, 0.45f,0.2f, 0.3f, 0), // chêne : lobes arrondis + sinus
				["BeechTree"]  = new(1.7f, LeafMargin.Dentee, 0, 0f,  0.7f, 0.1f, 0), // hêtre : ovale ondulé-denté
				["BirchTree"]  = new(1.2f, LeafMargin.Dentee, 0, 0f,  0.8f, 0.3f, 0), // bouleau : triangulaire denté
				["HornbeamTree"] = new(1.7f, LeafMargin.Dentee, 0, 0f, 0.8f, 0.2f, 0), // charme : ovale doublement denté
				["Alder"]      = new(1.3f, LeafMargin.Dentee, 0, 0f,  0.1f, 0.1f, 0), // aulne : obovale à sommet tronqué/échancré, denté
				// FirTree (sapin) : PAS de contour authoré → repli sur l'archétype
				// Aciculaire de Leaf.cs (aiguilles). Un conifère n'a pas de limbe à
				// détourer ; la « phyllotaxie verticillée » est un polish différé (§7).
			};

		// Nb de sommets par demi-bord du limbe simple : assez pour lire les dents/
		// lobes au ×16+, pas trop pour rester léger (2 côtés → ~2×Segments points).
		private const int OutlineSegments = 22;

		// ---------------------------------------------------------------------
		// POINT D'ENTRÉE (appelé par DrawShapeBySpecies dans Leaf.cs, au palier
		// haut UNIQUEMENT). Retourne false si l'espèce n'a pas de contour authoré
		// → le caller retombe sur l'archétype d'ellipses (repli propre).
		// (rx,ry) = demi-axes du volume global déjà calculés par Organs.cs.
		// (i,j) = identité (segment, feuille) → graine déterministe du jitter.
		// ---------------------------------------------------------------------
		private bool TryDrawLeafOutline(string species, Vector2 c, float rx, float ry, Color col, int i, int j)
		{
			if (!LeafOutlines.TryGetValue(species, out var spec))
				return false;

			var (axis, cross) = LeafFrame();
			// Ré-amincissement selon l'élancement authoré (le rx/ry reçu vaut la
			// proportion générique ~1.77 ; on projette sur l'Aspect voulu).
			float halfLen = rx * 1.15f;                 // demi-longueur écran
			float halfWid = halfLen / Mathf.Max(1f, spec.Aspect);

			if (spec.Compound > 0)
			{
				DrawCompoundOutline(c, axis, cross, halfLen, halfWid, col, spec, i, j);
			}
			else
			{
				var poly = BuildLeafPolygon(spec, i, j);
				DrawVolumePolygon(c, axis, cross, halfLen, halfWid, poly, col);
			}

			// NERVURES — 3ᵉ valeur, réutilise le dispatch de Leaf.cs. On mappe la
			// topologie du contour sur l'archétype de nervation correspondant :
			// lobée → palmée, composée → composée, sinon → penninerve.
			LeafShape veinTopo = spec.Compound > 0 ? LeafShape.Composee
				: spec.Margin == LeafMargin.Lobee ? LeafShape.Lobee
				: LeafShape.Elliptique;
			// LeafProfile minimal pour DrawLeafVeins (Count = lobes/folioles ; le
			// sens de teinte reprend la table LeafProfiles si présente, sinon clair).
			int veinCount = spec.Compound > 0 ? spec.Compound
				: spec.Margin == LeafMargin.Lobee ? spec.Lobes : 0;
			bool lighter = !LeafProfiles.TryGetValue(species, out var lp) || lp.VeinLighter;
			var vprof = new LeafProfile(veinTopo, spec.Aspect, veinCount, lighter);
			// Géométrie des nervures CALÉE sur le contour (D106 T6 : devenues visibles,
			// elles débordaient du limbe et filaient en travers). Chaque topologie lit
			// (rx, ry) à sa façon : penninerve/palmée = (largeur, longueur), composée =
			// (longueur, largeur) — cf. Draw*Veins, Leaf.cs.
			var (vrx, vry) = veinTopo == LeafShape.Composee
				? (halfLen * 0.95f, halfWid) : (halfWid * 0.85f, halfLen * 0.95f);
			DrawLeafVeins(c, vrx, vry, col, veinTopo, vprof, i, j);
			return true;
		}

		// ---------------------------------------------------------------------
		// SYNTHÈSE DU CONTOUR (limbe simple) — liste de points normalisés dans le
		// repère feuille : t sur [-1,1] = axe (nord→sud), w = largeur signée.
		// On génère le CÔTÉ DROIT du sommet (sud) vers la base (nord), puis on
		// referme par le côté gauche en miroir. La marge module la largeur locale.
		// ---------------------------------------------------------------------
		private static Vector2[] BuildLeafPolygon(OutlineSpec spec, int i, int j)
		{
			int n = OutlineSegments;
			var right = new Vector2[n + 1];
			for (int k = 0; k <= n; k++)
			{
				// s = 0 au sommet (sud), 1 à la base (nord).
				float s = (float)k / n;
				float t = 1f - 2f * s;                  // +1 (sud) → -1 (nord)

				// Largeur de base du limbe : profil elliptique adouci, effilé au
				// sommet (Tip : plus Tip↑, plus la pointe est fine/acuminée) et
				// échancré à la base (BaseCut : cordé quand ↑).
				float ell = Mathf.Sqrt(Mathf.Max(0f, 1f - t * t)); // demi-ellipse
				// Effilement du sommet : rétrécit la largeur près de s≈0.
				float tipTaper = Mathf.Lerp(1f, Mathf.Pow(Mathf.Max(0f, 1f - s), 0.5f) , spec.Tip * 0.7f);
				float w = ell * tipTaper;

				// MARGE : on module la largeur locale par une ondulation.
				switch (spec.Margin)
				{
					case LeafMargin.Dentee:
						// Petites dents régulières + micro-jitter au hash (vie).
						float teeth = 0.06f * Mathf.Sin(s * Mathf.Pi * 18f);
						teeth *= 0.7f + 0.6f * Hash01(51, i, k);
						w += teeth;
						break;
					case LeafMargin.Lobee:
						// Sinus profonds : `Lobes` festons, creux = LobeCut.
						int lobes = Mathf.Max(3, spec.Lobes);
						float wave = Mathf.Cos(s * Mathf.Pi * (lobes)); // -1..1
						// wave>0 = bosse (lobe), wave<0 = sinus → on creuse d'autant.
						float lob = wave >= 0f ? wave * 0.10f : wave * spec.LobeCut;
						w += lob;
						break;
				}
				w = Mathf.Max(0.02f, w);
				right[k] = new Vector2(t, w);
			}

			// Échancrure basale (cœur/sagitté) : on tire la largeur au NORD vers
			// l'extérieur puis on rentre au ras de l'axe (deux oreilles).
			// Réalisé par un point d'insertion supplémentaire à la base.
			var pts = new System.Collections.Generic.List<Vector2>(2 * n + 4);
			// Côté droit sommet→base.
			for (int k = 0; k <= n; k++)
				pts.Add(new Vector2(right[k].X, +right[k].Y));
			// Échancrure : au point de base, on remonte légèrement vers le nord au
			// centre pour figurer le sinus cordé (si BaseCut>0).
			if (spec.BaseCut > 0f)
				pts.Add(new Vector2(-1f + spec.BaseCut * 0.35f, 0f));
			// Côté gauche base→sommet (miroir).
			for (int k = n; k >= 0; k--)
				pts.Add(new Vector2(right[k].X, -right[k].Y));
			return pts.ToArray();
		}

		// ---------------------------------------------------------------------
		// RENDU VOLUMÉ d'un polygone normalisé — E4 (≥ 2 valeurs) sur contour
		// quelconque : remplissage OMBRÉ plein, puis COPIE réduite ~0,8 décalée au
		// SUD en teinte ÉCLAIRÉE (croissant d'ombre côté nord conservé). Même esprit
		// que DrawVolumeEllipse mais pour une silhouette libre.
		// ---------------------------------------------------------------------
		private void DrawVolumePolygon(
			Vector2 c, Vector2 axis, Vector2 cross, float halfLen, float halfWid,
			Vector2[] norm, Color baseCol)
		{
			// Repère → écran : t (axe) et w (cross), mis à l'échelle des demi-axes.
			Vector2 ToScreen(Vector2 p, float shrink, Vector2 shift) =>
				c + shift + axis * (p.X * halfLen * shrink) + cross * (p.Y * halfWid * shrink);

			var shade = HueShift(baseCol, -OrganShade);
			var lit = HueShift(baseCol, OrganLit);
			Vector2 south = SouthDir();

			// 1) masse pleine ombrée.
			var full = new Vector2[norm.Length];
			for (int k = 0; k < norm.Length; k++) full[k] = ToScreen(norm[k], 1f, Vector2.Zero);
			// CASSÉ À L'ÉCRAN ④ : le contour fidèle est rempli de motifs (Motifs.cs).
			if (_motifs) { RemplirMotif(c, full, baseCol); return; }
			DrawColoredPolygon(full, shade);

			// 2) calotte éclairée : copie réduite décalée au sud (comme la calotte
			// de DrawVolumeEllipse). shrink 0.8, décalage ≈ 0.5·halfWid vers le sud.
			var capShift = south * (halfWid * 0.5f);
			var cap = new Vector2[norm.Length];
			for (int k = 0; k < norm.Length; k++) cap[k] = ToScreen(norm[k], 0.8f, capShift);
			DrawColoredPolygon(cap, lit);
		}

		// ---------------------------------------------------------------------
		// FEUILLE COMPOSÉE — rachis sur l'axe + N folioles opposées (petits limbes
		// dentés) + une terminale. Chaque foliole est un contour volumé à part
		// entière (mêmes invariants). Reprend la disposition de DrawComposee.
		// ---------------------------------------------------------------------
		private void DrawCompoundOutline(
			Vector2 c, Vector2 axis, Vector2 cross, float halfLen, float halfWid,
			Color col, OutlineSpec spec, int i, int j)
		{
			int nPairs = Mathf.Clamp(spec.Compound, 3, 5);
			// Descripteur de foliole : petit limbe ovale/denté, non composé.
			var folSpec = new OutlineSpec(2.0f, spec.Margin == LeafMargin.Entiere
				? LeafMargin.Entiere : LeafMargin.Dentee, 0, 0f, spec.Tip, 0.1f, 0);
			var folPoly = BuildLeafPolygon(folSpec, i, j);

			float folLen = halfLen * 0.34f;             // demi-longueur d'une foliole
			float folWid = folLen / 2.0f;
			float sideOff = halfWid * 0.9f;             // écart au rachis
			Vector2 baseP = c - axis * (halfLen * 0.85f);

			for (int k = 0; k < nPairs; k++)
			{
				float frac = (k + 0.5f) / nPairs;
				Vector2 along = baseP + axis * (halfLen * 1.7f * frac);
				float taper = 1f - 0.30f * frac;         // folioles décroissant vers le sommet
				float jit = (Hash01(41, i, j + k) - 0.5f) * sideOff * 0.3f;
				// Folioles opposées : le grand axe de chaque foliole s'écarte du
				// rachis (oblique vers l'extérieur-sommet), comme dans la nature.
				Vector2 dirR = (cross + axis * 0.5f).Normalized();
				Vector2 dirL = (-cross + axis * 0.5f).Normalized();
				Vector2 crR = new Vector2(-dirR.Y, dirR.X);
				Vector2 crL = new Vector2(-dirL.Y, dirL.X);
				Vector2 cR = along + cross * (sideOff + jit);
				Vector2 cL = along - cross * (sideOff - jit);
				DrawVolumePolygon(cR, dirR, crR, folLen * taper, folWid * taper, folPoly, col);
				DrawVolumePolygon(cL, dirL, crL, folLen * taper, folWid * taper, folPoly, col);
			}
			// Foliole terminale (dans l'axe, au bout du rachis).
			Vector2 tip = baseP + axis * (halfLen * 1.75f);
			DrawVolumePolygon(tip, axis, cross, folLen, folWid, folPoly, col);
		}
	}
}
