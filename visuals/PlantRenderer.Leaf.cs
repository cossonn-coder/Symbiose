// SYMBIOSE — PlantRenderer.Leaf.cs (partial de PlantRenderer)
// FORME DE FEUILLE PAR ESPÈCE (tronçon ②, conception RENDU_FEUILLAGE §2, E3-forme).
//
// Trou comblé : jusqu'ici TOUTE feuille était une ellipse générique unique
// (`DrawVolumeEllipse`, cf. Organs.cs). Ici on choisit une SILHOUETTE par espèce
// dans un catalogue FERMÉ de 6 archétypes (doc §2.1), dessinée directement en C#
// (dérogation actée à D10 — la forme de feuille est un fait de RENDU, sans
// équivalent moteur).
//
// Invariants (doc §1, NON négociables) :
//  • Jamais d'aplat (E4) : chaque sous-élément passe par `DrawVolumeEllipse`
//    (volume 2 valeurs) — SAUF sous le plancher de rayon, où une mini-feuille
//    naissante est peinte en 1 valeur nue (le croissant d'ombre serait illisible).
//  • Déterminisme total : ZÉRO Random. Tout jitter (angle/longueur des lobes et
//    folioles) dérive du `Hash01(canal, i, j)` stable défini dans Organs.cs.
//  • Le bois n'est pas teinté par le feuillage : on ne touche que le limbe.
//
// Couche B PURE : zéro Python, zéro pont. La FORME (②) et les NERVURES (③, doc
// §3.2) — la 3ᵉ valeur posée APRÈS le volume. Ni pétiole (④), ni croissance (⑤).
//
// NERVURES (③) : ce partial gagne la nervation. Choix de localisation — ③ ajoute
// ~100 ldc (teinte + dispatch + 3 topologies), total ≈ 240 ldc code pur, SOUS le
// seuil ~350 ; et nervure ∝ archétype (même `LeafProfile`, même `LeafFrame`) →
// responsabilité cohérente « silhouette + nervation de la feuille ». Pas de
// partial supplémentaire.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// --- Catalogue fermé d'archétypes (doc §2.1) -------------------------
		// Du plus simple au plus composé. Une espèce non mappée → Elliptique.
		private enum LeafShape
		{
			Elliptique, // ellipse actuelle (défaut)              — générique, basilic
			Lanceolee,  // ellipse très élancée (ratio long/large ↑) — saule, graminées
			Cordee,     // ellipse + échancrure basale (cœur)     — haricot, lierre
			Lobee,      // 3-5 lobes = ellipses fusionnées         — vigne, érable, courge
			Composee,   // N folioles le long d'un rachis          — tomate, frêne, rosier
			Aciculaire, // trait court épais (aiguille)            — conifères
		}

		// --- Descripteur de feuille par espèce (doc §2.2) --------------------
		// Aspect = élancement longueur/largeur (1 = rond, 3 = très étiré).
		// Count  = nb de lobes (Lobee) ou de folioles (Composee), sinon 0.
		// VeinLighter = sens du shift de la nervure (③) : DÉCLARÉ ici, PAS encore
		//               exploité ; ② ne dessine aucune nervure.
		private readonly record struct LeafProfile(
			LeafShape Shape, float Aspect, int Count, bool VeinLighter);

		// Table per-espèce EN REGARD de `Palettes` (Organs.cs). Même clé = nom de
		// CLASSE Python (`species` du snapshot). Mappage initial ; défaut Elliptique
		// partout ailleurs (jamais bloquant, on enrichit au fil).
		private static readonly System.Collections.Generic.Dictionary<string, LeafProfile>
			LeafProfiles = new()
			{
				// --- Cultivées potagères --------------------------------------
				["Tomato"]    = new(LeafShape.Composee,  1.6f, 5, true),  // feuille composée pennée
				["Pepper"]    = new(LeafShape.Elliptique, 1.7f, 0, true), // limbe simple ovale-lancéolé
				["Bean"]      = new(LeafShape.Cordee,    1.2f, 3, true),  // foliole large en cœur
				["Clover"]    = new(LeafShape.Cordee,    1.0f, 3, false), // folioles arrondies (rendu cordé)
				["Sunflower"] = new(LeafShape.Cordee,    1.2f, 0, false), // grand limbe cordé rugueux
				["Carrot"]    = new(LeafShape.Composee,  1.4f, 5, true),  // feuillage très découpé
				["Zucchini"]  = new(LeafShape.Lobee,     1.0f, 5, true),  // grande feuille palmilobée
				["CornSalad"] = new(LeafShape.Elliptique, 1.6f, 0, true), // rosette de spatules
				["Garlic"]    = new(LeafShape.Lanceolee, 3.2f, 0, false), // long ruban dressé
				// --- Compagnes / mellifères / engrais verts -------------------
				["Yarrow"]    = new(LeafShape.Composee,  1.3f, 5, false), // feuillage plumeux finement divisé
				["Phacelia"]  = new(LeafShape.Composee,  1.4f, 5, false), // feuille pennatiséquée
				["Borage"]    = new(LeafShape.Elliptique, 1.5f, 0, false), // grande feuille ovale poilue
				["Comfrey"]   = new(LeafShape.Lanceolee, 2.4f, 0, false), // grande feuille lancéolée
				["Mustard"]   = new(LeafShape.Lobee,     1.5f, 3, true),  // feuille lyrée (lobe terminal large)
				// --- Aromatiques persistantes (Lamiacées evergreen) ----------
				["Thyme"]     = new(LeafShape.Aciculaire, 3.0f, 0, false), // micro-feuilles linéaires
				["Lavender"]  = new(LeafShape.Lanceolee, 3.5f, 0, false),  // feuilles étroites gris-vert
				// --- Sous-arbrisseau acidophile ------------------------------
				["Vaccinium"] = new(LeafShape.Elliptique, 1.6f, 0, false), // petit limbe ovale
				// --- Pérennes ligneuses (vergers) ----------------------------
				["AppleTree"]  = new(LeafShape.Elliptique, 1.5f, 0, true), // limbe ovale denté
				["Fig"]        = new(LeafShape.Lobee,     1.0f, 5, true),  // grande feuille palmilobée
				["CherryTree"] = new(LeafShape.Elliptique, 1.9f, 0, true), // limbe ovale-lancéolé
				["WalnutTree"] = new(LeafShape.Composee,  1.7f, 5, false), // feuille composée pennée
				["OakTree"]    = new(LeafShape.Lobee,     1.6f, 5, false), // limbe lobé caractéristique
			};
		private static readonly LeafProfile DefaultLeaf =
			new(LeafShape.Elliptique, 1.15f / 0.65f, 0, true); // = proportions de l'ellipse historique

		// Plancher de rayon (doc §1) : sous ce demi-grand-axe ÉCRAN, on retombe sur
		// UNE ellipse 1 valeur, quelle que soit la forme (lobes/folioles illisibles
		// à cette taille — mini-feuille naissante). Synergie future avec ⑤.
		private const float LeafFloorRadiusPx = 3f;
		// Repli LOD (doc §2.3 encadré) : au-dessous de ce zoom, toute forme retombe
		// sur Elliptique (la silhouette fine est invisible de loin). Aligné sur le
		// MinZoom des autres couches détail (MacroLife, LitterLayer).
		private const float LeafShapeMinZoom = 4f;

		// ---------------------------------------------------------------------
		// LITIÈRE AU SOL (⑥, doc §6.3) — silhouette de feuille MORTE posée à plat.
		// Réutilise EXACTEMENT le dispatch de forme par espèce (DrawShapeBySpecies)
		// pour que la litière de pommier ait des feuilles de pommier — repli
		// Elliptique si l'espèce est inconnue (ce qui est le cas en pratique : le
		// moteur ne trace pas l'espèce d'origine d'une parcelle, §6.3). Trois
		// différences avec une feuille vivante :
		//  • POSE À PLAT : le caller passe déjà un (rx,ry) APLATI (calotte réduite) ;
		//  • VOLUME ≥ 2 valeurs conservé (invariant §1) → DrawVolumeEllipse sous-jacent ;
		//  • pas de pétiole, pas de croissance (la feuille est détachée et inerte).
		// PUBLIQUE : appelée par LeafLitterLayer, qui se sert d'un PlantRenderer comme
		// STYLO (les primitives de dessin sont des méthodes d'instance de CanvasItem).
		// `species` est passé en paramètre (≠ feuille vivante qui lit _structure) :
		// la litière n'a pas de structure, juste une espèce présumée.
		public void DrawLitterLeaf(string species, Vector2 c, float rx, float ry, Color col, int seed)
		{
			// (i,j) = graine de jitter : on dérive deux canaux du seed du plot+rang
			// pour que deux feuilles d'un même amas diffèrent, stable inter-frames.
			DrawShapeBySpecies(species, c, rx, ry, col, seed & 0xffff, (seed >> 16) & 0xffff);
		}

		// ---------------------------------------------------------------------
		// TRACÉ — dispatch par archétype. `c` = centre écran, (rx,ry) = demi-axes
		// du volume global déjà calculés par Organs.cs (rx = grand axe sud-est).
		// (i,j) = identité (segment, feuille) → graine déterministe du jitter.
		// ---------------------------------------------------------------------
		private void DrawLeafShape(Vector2 c, float rx, float ry, Color col, int i, int j)
		{
			// Une feuille VIVANTE lit son espèce dans _structure ; la litière la
			// passe en argument (DrawLitterLeaf). On factorise le tracé commun.
			DrawShapeBySpecies(_structure.SpeciesName, c, rx, ry, col, i, j);
		}

		// Cœur commun du tracé (vivant + litière) : choix d'archétype par espèce,
		// plancher de rayon, repli LOD, volume, nervures. `species` explicite.
		private void DrawShapeBySpecies(string species, Vector2 c, float rx, float ry, Color col, int i, int j)
		{
			// Plancher de rayon : feuille trop petite → 1 ellipse 1 valeur nue.
			if (rx < LeafFloorRadiusPx)
			{
				DrawEllipse(c, rx, ry, col);
				return;
			}

			if (!LeafProfiles.TryGetValue(species, out var prof))
				prof = DefaultLeaf;

			// T6 — PALIER HAUT (×16+) : contour FIDÈLE authoré par espèce (volume +
			// nervures) au lieu de l'amas d'ellipses. Si l'espèce n'a pas de contour
			// mappé, TryDrawLeafOutline retourne false → on retombe proprement sur
			// l'archétype ci-dessous (repli intermédiaire inchangé). Ne se déclenche
			// qu'au zoom rapproché : en dessous la silhouette fine est invisible et
			// le contour coûterait pour rien (perf, sprint plantes du 2026-07-09).
			if (WorldView.CurrentZoom >= LeafOutlineMinZoom
				&& TryDrawLeafOutline(species, c, rx, ry, col, i, j))
				return;

			// Repli LOD : au dézoom, tout redevient une ellipse volumée simple.
			bool lod = WorldView.CurrentZoom < LeafShapeMinZoom;
			LeafShape shape = lod ? LeafShape.Elliptique : prof.Shape;

			switch (shape)
			{
				case LeafShape.Lanceolee:  DrawLanceolee(c, rx, ry, col, prof); break;
				case LeafShape.Cordee:     DrawCordee(c, rx, ry, col, prof); break;
				case LeafShape.Lobee:      DrawLobee(c, rx, ry, col, prof, i, j); break;
				case LeafShape.Composee:   DrawComposee(c, rx, ry, col, prof, i, j); break;
				case LeafShape.Aciculaire: DrawAciculaire(c, rx, ry, col, prof); break;
				default:                   DrawVolumeEllipse(c, rx, ry, col); break; // Elliptique
			}

			// ③ NERVURES — 3ᵉ valeur posée APRÈS le volume (se lit par-dessus
			// ombre+lumière). Pas au repli LOD : la silhouette fine est invisible
			// de loin, une ligne 1 px y serait illisible/du bruit.
			if (!lod)
				DrawLeafVeins(c, rx, ry, col, shape, prof, i, j);
		}

		// ---------------------------------------------------------------------
		// NERVURES (③, doc §3.2) — la 3ᵉ valeur. Teinte = HueShift LÉGER du limbe
		// (jamais sa couleur exacte, E2), sens donné par `LeafProfile.VeinLighter`
		// (true = plus claire) et amplitude par `VeinShift`. Tracé = fines lignes
		// 1 px NON antialiasées (cohérent pixel-art). Topologie ∝ archétype.
		// ---------------------------------------------------------------------

		// Amplitude du décalage de teinte de la nervure (lum passé à HueShift).
		// Léger : la nervure se devine, elle ne barre pas le limbe. Ajustable F5.
		private const float VeinShift = 0.22f;

		private void DrawLeafVeins(
			Vector2 c, float rx, float ry, Color limbe, LeafShape shape, LeafProfile p, int i, int j)
		{
			// Sens du shift : plus claire (lum>0, vers le chaud) ou plus sombre
			// (lum<0, vers le froid) — HueShift garde le pixel-art (jamais gris).
			float lum = p.VeinLighter ? VeinShift : -VeinShift;
			Color vein = HueShift(limbe, lum);

			switch (shape)
			{
				case LeafShape.Lobee:      DrawPalmateVeins(c, rx, ry, vein, p, i, j); break;
				case LeafShape.Composee:   DrawComposeeVeins(c, rx, ry, vein, p, i, j); break;
				case LeafShape.Aciculaire: break; // aucune (trop fin, illisible au pixel)
				default:                   DrawPennateVeins(c, rx, ry, vein, p, i, j); break;
			}
		}

		// Une fine ligne 1 px NON antialiasée (le geste de base de toute nervure).
		private void DrawVein(Vector2 a, Vector2 b, Color col) =>
			DrawLine(a, b, col, 1f, antialiased: false);

		// --- Penninerve (Elliptique / Lanceolee / Cordee) --------------------
		// 1 médiane qui suit l'axe + 2-4 latérales obliques par paires opposées,
		// écartées au HASH (canal 43, zéro Random). Les latérales partent de la
		// médiane et filent vers le bord, inclinées vers le sommet (sud).
		private void DrawPennateVeins(Vector2 c, float rx, float ry, Color col, LeafProfile p, int i, int j)
		{
			var (axis, cross) = LeafFrame();
			Vector2 tipS = c + axis * ry;   // sommet (sud)
			Vector2 tipN = c - axis * ry;   // base   (nord)
			DrawVein(tipN, tipS, col);      // médiane

			int pairs = 1 + (int)(Hash01(43, i, j) * 2.99f); // 1 à 3 paires → 2-6 latérales
			for (int k = 1; k <= pairs; k++)
			{
				// position le long de la médiane, de la base vers le sommet
				float t = (float)k / (pairs + 1);            // 0..1
				Vector2 anchor = tipN.Lerp(tipS, t);
				// longueur oblique décroissante vers le sommet, jittée au hash
				float reach = rx * (0.9f - 0.4f * t) * (0.8f + 0.3f * Hash01(47, i, j + k));
				// oblique : composante latérale + remontée vers le sommet
				Vector2 obl = (cross + axis * 0.6f);
				obl = obl.LengthSquared() > 1e-6f ? obl.Normalized() : cross;
				DrawVein(anchor, anchor + obl * reach, col);
				DrawVein(anchor, anchor - (cross - axis * 0.6f).Normalized() * reach, col);
			}
		}

		// --- Palmée (Lobee) : une nervure par lobe, rayonnant de la BASE -------
		// Même éventail que `DrawLobee` (span/axe), mais on trace un rayon plein
		// de la base de la feuille (nord) vers chaque lobe — pas de jitter croisé.
		private void DrawPalmateVeins(Vector2 c, float rx, float ry, Color col, LeafProfile p, int i, int j)
		{
			var (axis, cross) = LeafFrame();
			int n = Mathf.Clamp(p.Count, 3, 5);
			float span = Mathf.Pi * 0.9f;                    // = éventail de DrawLobee
			Vector2 baseP = c - axis * (ry * 0.6f);          // base commune (nord)
			for (int k = 0; k < n; k++)
			{
				float frac = n > 1 ? (float)k / (n - 1) : 0.5f;
				float ja = (Hash01(31, i, j + k) - 0.5f) * (span / n) * 0.6f; // = jitter de DrawLobee
				float ang = (frac - 0.5f) * span + ja;
				Vector2 dir = axis * Mathf.Cos(ang) + cross * Mathf.Sin(ang);
				DrawVein(baseP, baseP + dir * (rx * 1.05f), col);
			}
		}

		// --- Composée : une médiane par foliole (le long du rachis, doc §3.2) --
		// On reprend la disposition de `DrawComposee` (rachis sur l'axe, folioles
		// opposées + terminale) et on trace la médiane de chaque foliole.
		private void DrawComposeeVeins(Vector2 c, float rx, float ry, Color col, LeafProfile p, int i, int j)
		{
			var (axis, cross) = LeafFrame();
			int n = Mathf.Clamp(p.Count, 3, 5);
			float folR = rx * 0.40f;
			float sideOff = ry * 0.55f;
			Vector2 baseP = c - axis * (rx * 0.7f);
			DrawVein(baseP, baseP + axis * (rx * 1.45f), col); // rachis (nervure centrale)
			for (int k = 0; k < n; k++)
			{
				float frac = (k + 0.5f) / n;
				Vector2 along = baseP + axis * (rx * 1.4f * frac);
				float jit = (Hash01(41, i, j + k) - 0.5f) * sideOff * 0.4f; // = jitter de DrawComposee
				float taper = 1f - 0.35f * frac;
				Vector2 gC = along + cross * (sideOff + jit);  // centre foliole droite
				Vector2 dC = along - cross * (sideOff - jit);  // centre foliole gauche
				// médiane de chaque foliole, orientée du rachis vers son centre.
				DrawVein(along, gC + (gC - along).Normalized() * folR * taper, col);
				DrawVein(along, dC + (dC - along).Normalized() * folR * taper, col);
			}
		}

		// L'AXE de la feuille à l'écran : on étire la silhouette selon SouthDir()
		// (même convention d'éclairage/projection que les volumes, Palette.cs) →
		// la feuille « pointe » vers le sud-projeté, cohérent inter-frames/rotation.
		private static (Vector2 axis, Vector2 cross) LeafFrame()
		{
			Vector2 axis = SouthDir();                       // direction du grand axe
			Vector2 cross = new Vector2(-axis.Y, axis.X);    // largeur (perpendiculaire)
			return (axis, cross);
		}

		// --- Lancéolée : ellipse très élancée (Aspect élevé) -----------------
		// On ré-amincit le volume historique selon l'Aspect du profil (limbe étroit).
		private void DrawLanceolee(Vector2 c, float rx, float ry, Color col, LeafProfile p)
		{
			float narrow = Mathf.Clamp(1.7f / Mathf.Max(1f, p.Aspect), 0.25f, 1f);
			DrawVolumeEllipse(c, rx, ry * narrow, col);
		}

		// --- Cordée : limbe + lobes basaux qui figurent l'échancrure en cœur --
		// Le limbe principal (volume) + deux petites calottes à la base, écartées
		// de l'axe → silhouette de cœur. Déterministe, sans hash (forme fixe).
		private void DrawCordee(Vector2 c, float rx, float ry, Color col, LeafProfile p)
		{
			var (axis, cross) = LeafFrame();
			// Le limbe est un peu raccourci au sommet pour laisser place aux oreilles.
			DrawVolumeEllipse(c + axis * (ry * 0.15f), rx, ry * 0.9f, col);
			float ear = ry * 0.5f;
			Vector2 baseP = c - axis * (ry * 0.45f);          // vers la base (nord)
			DrawVolumeEllipse(baseP + cross * (rx * 0.35f), ear, ear * 0.8f, col);
			DrawVolumeEllipse(baseP - cross * (rx * 0.35f), ear, ear * 0.8f, col);
		}

		// --- Lobée : Count lobes = ellipses fusionnées rayonnant du centre -----
		// Jitter d'angle/longueur par HASH (canaux 31/37) → stable, pas deux
		// feuilles identiques mais reproductibles (doc §2.3, philo #3).
		private void DrawLobee(Vector2 c, float rx, float ry, Color col, LeafProfile p, int i, int j)
		{
			var (axis, cross) = LeafFrame();
			int n = Mathf.Clamp(p.Count, 3, 5);
			float span = Mathf.Pi * 0.9f;                     // éventail ~160°, ouvert vers le sud
			float lobeR = rx * 0.55f;                         // chaque lobe ~ moitié du rayon
			for (int k = 0; k < n; k++)
			{
				// angle réparti dans l'éventail + jitter borné au hash
				float frac = n > 1 ? (float)k / (n - 1) : 0.5f;
				float ja = (Hash01(31, i, j + k) - 0.5f) * (span / n) * 0.6f;
				float ang = (frac - 0.5f) * span + ja;
				Vector2 dir = axis * Mathf.Cos(ang) + cross * Mathf.Sin(ang);
				float len = lobeR * (0.8f + 0.4f * Hash01(37, i, j + k)); // longueur jittée
				Vector2 lc = c + dir * len;
				DrawVolumeEllipse(lc, lobeR * 0.6f, lobeR * 0.45f, col);
			}
			// Petit volume central qui soude les lobes (évite la silhouette « étoile »).
			DrawVolumeEllipse(c, rx * 0.45f, ry * 0.45f, col);
		}

		// --- Composée : Count folioles = petites ellipses le long d'un rachis --
		// Le rachis suit l'axe ; les folioles s'opposent par paires, jitter au hash.
		private void DrawComposee(Vector2 c, float rx, float ry, Color col, LeafProfile p, int i, int j)
		{
			var (axis, cross) = LeafFrame();
			int n = Mathf.Clamp(p.Count, 3, 5);
			float folR = rx * 0.40f;                          // petite foliole
			float sideOff = ry * 0.55f;                       // écart latéral au rachis
			Vector2 baseP = c - axis * (rx * 0.7f);           // pied du rachis (nord)
			for (int k = 0; k < n; k++)
			{
				float frac = (k + 0.5f) / n;
				Vector2 along = baseP + axis * (rx * 1.4f * frac);
				float jit = (Hash01(41, i, j + k) - 0.5f) * sideOff * 0.4f;
				// folioles opposées (gauche/droite), rétrécissant vers le sommet
				float taper = 1f - 0.35f * frac;
				DrawVolumeEllipse(along + cross * (sideOff + jit), folR * taper, folR * 0.55f * taper, col);
				DrawVolumeEllipse(along - cross * (sideOff - jit), folR * taper, folR * 0.55f * taper, col);
			}
			// Foliole terminale au bout du rachis.
			DrawVolumeEllipse(baseP + axis * (rx * 1.45f), folR, folR * 0.6f, col);
		}

		// --- Aciculaire : trait court épais (aiguille) — 1 valeur tolérée car
		// trop fine pour un croissant lisible, mais on garde 2 valeurs via le
		// volume étiré. Aspect élevé → très étroite.
		private void DrawAciculaire(Vector2 c, float rx, float ry, Color col, LeafProfile p)
		{
			float thin = Mathf.Clamp(1.4f / Mathf.Max(1f, p.Aspect), 0.2f, 0.5f);
			DrawVolumeEllipse(c, rx * 0.85f, ry * thin, col);
		}
	}
}
