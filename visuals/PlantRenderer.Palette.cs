// SYMBIOSE — PlantRenderer.Palette.cs (partial de PlantRenderer, SS② Palette)
// FONDATION CHROMATIQUE 16-bit (cap docs/conception/CONCEPTION_RENDU_PIXELART.md
// §5/§6). Trois idées de la palette SNES, portées sur les plantes :
//
//  1. RAMPE 2-3 valeurs — un aplat (une couleur par organe) devient une mini-
//     rampe. Le bois n'est plus « vert OU brun » mais une lignification continue
//     vert-tendre → olive → brun, indexée par l'épaisseur du segment.
//  2. HUE-SHIFTING — pour assombrir/éclaircir, on ne tire PAS vers le noir/blanc
//     (terne) : on décale la TEINTE. L'ombre va vers le froid (bleu), la lumière
//     vers le chaud (jaune). C'est *la* signature 16-bit.
//  3. LUMIÈRE DU SUD — le soleil est au sud dans le moteur (WorldView.Soleil,
//     modèle E-O symétrique). On éclaire donc la face orientée SUD de chaque
//     organe (volume), on ombre la face nord. On prend une direction sud FIXE
//     (pas le soleil animé) : un éclairage stable inter-frames, déterministe,
//     qui ne scintille pas au balayage horaire de l'ombre.
//
// Tout est statique/déterministe (zéro Random, philo #3). Décoration de vue
// pure : le moteur n'est pas touché, le golden est préservé.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// --- Réglages hue-shift (à ajuster au F5) ----------------------------
		// Force du décalage de teinte (1 = on atteindrait la teinte cible).
		private const float HueShiftStrength = 0.5f;
		// Combien |lum| pousse la VALEUR (clarté) et la SATURATION (ombres + saturées).
		private const float ValueStrength = 0.5f;
		private const float SatStrength = 0.2f;
		// Teintes cibles HSV (H sur [0,1)) : jaune chaud pour la lumière, bleu
		// froid pour l'ombre — la base même du hue-shifting pixel-art.
		private const float WarmHue = 0.13f;   // ~47° jaune
		private const float CoolHue = 0.60f;   // ~216° bleu

		// Profondeur du volume : de combien on ombre/éclaire chaque face.
		private const float BranchShade = 0.28f, BranchLit = 0.32f;
		private const float OrganShade = 0.30f, OrganLit = 0.38f;

		// --- Calotte éclairée (sémiologie `ombre`, T1) -----------------------
		// Facteur de rayon de la calotte lumineuse dans DrawVolumeEllipse. Défaut
		// 0.66 (valeur historique). Réduit ∝ `_ombre` UNIQUEMENT sur le chemin
		// feuille (limbe chétif/étiolé). PLANCHER E4 : la calotte ne disparaît
		// JAMAIS — borné à 0.30 même à `_ombre=1`, on garde 2 valeurs (ombre +
		// calotte), jamais d'aplat. (Plancher à ajuster au F5.)
		private const float LitFactorDefault = 0.66f;
		private const float LitFactorFloor = 0.30f;
		// Toggle inter-appels (option a du kickoff) : posé à l'entrée de la boucle
		// feuilles, remis à LitFactorDefault juste après — fruits/fleurs intacts.
		private float _litFactor = LitFactorDefault;

		// --- Repli palette T3 (§5) : froid atténué sous symptôme colorant -----
		// Plancher du facteur d'amplitude du shift FROID quand un symptôme colore
		// le limbe à FOND (`_colorAmount=1`). À `_colorAmount=0` (sain) le facteur
		// vaut 1 → hue-shift SS² PLEIN, aucune régression. K=0.5 (à régler au F5) :
		// on garde la moitié du froid au pic de coloration — assez de volume pour
		// que la feuille ne s'aplatisse pas, pas assez pour noyer un jaune sous le
		// bleu côté nord. Même mécanisme de toggle que `_litFactor` (cf. Organs.cs).
		private const float ColorCoolShiftFloor = 0.5f;
		// Facteur courant d'amplitude du shift FROID (1 = plein, hors symptôme).
		// Posé à Lerp(1, ColorCoolShiftFloor, _colorAmount) avant la boucle
		// feuilles, remis à 1 juste après — lu par HueShift pour lum<0 seulement.
		private float _coolShiftScale = 1f;

		// --- Rampe de lignification (branches vert → brun) -------------------
		// Teinte intermédiaire olive : un lerp RGB direct vert→brun passerait par
		// un gris-kaki mort ; le stop olive garde la rampe vivante (3 valeurs).
		// Teinte centralisée dans Palette16 (T1) — ApexColor/WoodColor le sont aussi.
		private static readonly Color WoodOlive = Palette16.BoisOlive;
		// T1 volet B — index de la rampe sur l'ÂGE du segment, plus son épaisseur.
		// POURQUOI : la lignification est un processus TEMPOREL. Un jeune rameau,
		// même fin, reste vert (tendre) tant qu'il est jeune ; un gros apex récent
		// ne devrait pas brunir. L'épaisseur était un proxy trompeur (un rameau
		// fin mais vieux ↔ un gros apex jeune). L'âge est le vrai meneur : un
		// rameau pleinement ligneux en ~LignifyFullWeeks semaines (~2 mois).
		// Valeur à confirmer au F5.
		private const float LignifyFullWeeks = 8.0f;

		// Part ligneuse [0,1] d'un segment : un apex (pointe) reste tendre (0),
		// le bois brunit avec l'ÂGE (T1 volet B). C'est l'index de la rampe.
		private static float Lignification(Segment s) =>
			s.IsApex ? 0f : Mathf.Clamp(s.AgeWeeks / LignifyFullWeeks, 0f, 1f);

		// Rampe 3 valeurs : vert-tendre (= ApexColor) → olive → brun (= WoodColor).
		// Deux segments de lerp pour traverser l'olive (et non couper droit).
		private static Color WoodRamp(float lig) =>
			lig < 0.5f
				? ApexColor.Lerp(WoodOlive, lig * 2f)
				: WoodOlive.Lerp(WoodColor, (lig - 0.5f) * 2f);

		// --- Fond de vitalité (santé & résilience ④) -------------------------
		// La vitalité continue [0,1] du snapshot ternit le tissu vert ∝ son manque
		// (1 − vitalité). DEUX gestes chromatiques, en HSV pour rester dans l'esprit
		// palette (pas d'interpolation RGB libre) :
		//  · DÉSATURATION — la chlorophylle s'épuise : le vert perd son éclat, tire
		//    vers le terne. C'est le signal dominant (un feuillage sain est SATURÉ).
		//  · LÉGER ASSOMBRISSEMENT — le port se fane, la valeur baisse un peu.
		// PLANCHERS (à régler au F5) : même à vitalité 0 on GARDE de la saturation
		// (VitFloorSat) et de la valeur (VitFloorVal) → le tissu reste lisible et
		// vert-terne, jamais un aplat gris mort. La MORT (vitalité 0 → `etat` "mort")
		// est portée par le squelette (SetSkeleton), pas par cette teinte : ici on
		// peint l'AFFAIBLISSEMENT du vivant, philo #5 (indice, pas chiffre).
		// Un `manque` léger (vitalité 0.9) donne un tissu à peine terni — le dégradé
		// est CONTINU, pas un palier (l'observateur lit l'usure progressive, ①).
		private const float VitDesatStrength = 0.55f; // combien le manque désature
		private const float VitDimStrength   = 0.22f; // combien le manque assombrit
		private const float VitFloorSat = 0.25f;      // saturation plancher (jamais gris)
		private const float VitFloorVal = 0.55f;      // valeur plancher (jamais noir)

		private Color ApplyVitality(Color tissue)
		{
			if (_vitalite >= 0.999f) return tissue;   // plante saine → identité stricte
			float manque = 1f - _vitalite;
			float h = tissue.H, s = tissue.S, v = tissue.V;
			// Désature (chlorophylle qui s'épuise) : on rabote la saturation ∝ manque,
			// puis on tient le plancher VitFloorSat (jamais un vert-gris illisible).
			s = Mathf.Max(s * (1f - manque * VitDesatStrength), s * VitFloorSat);
			// Assombrit un peu (port qui se fane) : valeur rabotée ∝ manque, tenue au
			// plancher VitFloorVal (relatif à la valeur d'origine → jamais noir).
			v = Mathf.Max(v * (1f - manque * VitDimStrength), v * VitFloorVal);
			var outc = Color.FromHsv(h, s, v);
			outc.A = tissue.A;
			return outc;
		}

		// --- Hue-shifting -----------------------------------------------------
		// Décale une couleur vers la lumière (lum>0 : + clair, + chaud) ou
		// l'ombre (lum<0 : + sombre, + froid, + saturé). Travaille en HSV car
		// la teinte y est une coordonnée directe. L'alpha d'entrée est préservé.
		//
		// Repli palette T3 (§5) : seule l'amplitude du shift de TEINTE FROIDE
		// (lum<0, vers le bleu) est multipliée par `_coolShiftScale` (1 = plein,
		// SS² inchangé). Sur un limbe que le symptôme colore franchement
		// (`_colorAmount` élevé), `_coolShiftScale` < 1 empêche le froid de
		// reverdir/bleuir le jaune (chlorose/sénescence) au point de le rendre
		// illisible côté nord. La VALEUR (clarté) et la SATURATION ne sont PAS
		// touchées (le volume reste lisible) — on borne juste la dérive de teinte.
		// `_coolShiftScale` ne vaut < 1 QUE pendant la boucle feuilles (toggle posé
		// dans Organs.cs) : branches, fruits, fleurs, silhouette gardent le froid
		// plein. Tissu sain (`_colorAmount=0` → `_coolShiftScale=1`) = zéro régression.
		private Color HueShift(Color c, float lum)
		{
			float h = c.H, s = c.S, v = c.V;
			float target = lum >= 0f ? WarmHue : CoolHue;
			float hueAmt = Mathf.Abs(lum) * HueShiftStrength
				* (lum < 0f ? _coolShiftScale : 1f);
			h = HueTowards(h, target, hueAmt);
			v = Mathf.Clamp(v + lum * ValueStrength, 0f, 1f);
			// Seules les ombres (lum<0) gagnent en saturation (couleur plus dense).
			s = Mathf.Clamp(s + Mathf.Max(0f, -lum) * SatStrength, 0f, 1f);
			var outc = Color.FromHsv(h, s, v);
			outc.A = c.A;
			return outc;
		}

		// Interpolation de teinte sur le CERCLE chromatique (H boucle à 1.0) :
		// on prend le plus court chemin, sinon un vert→jaune ferait le tour par
		// le rouge/magenta. d ramené dans [-0.5, 0.5].
		private static float HueTowards(float h, float target, float amt)
		{
			float d = target - h;
			if (d > 0.5f) d -= 1f;
			if (d < -0.5f) d += 1f;
			float nh = h + d * amt;
			if (nh < 0f) nh += 1f;
			if (nh >= 1f) nh -= 1f;
			return nh;
		}

		// Direction « vers le sud » À L'ÉCRAN : on projette le vecteur monde
		// (0, +1) = plein sud. Passe par WorldToScreenOffset → suit la rotation
		// de vue (D35) comme les ombres : tourner le monde tourne l'éclairage.
		private static Vector2 SouthDir()
		{
			var d = WorldView.WorldToScreenOffset(0f, 1f);
			return d.LengthSquared() > 1e-6f ? d.Normalized() : new Vector2(0f, 1f);
		}

		// --- Volume 2 valeurs (organes ronds : feuilles, fruits, pétales) ----
		// Une masse pleine en teinte d'ombre froide + une calotte éclairée plus
		// petite décalée vers le sud → le croissant d'ombre reste côté nord. Le
		// même geste sert feuilles, fruits et fleurs (cohérence chromatique).
		//
		// Sémiologie `ombre` (T1, étiolement) — DÉCISION DE DESIGN : la taille de la
		// calotte éclairée est lue dans le champ-toggle `_litFactor` (défaut
		// `LitFactorDefault` = 0.66) plutôt que codée en dur. C'est l'option (a) du
		// kickoff (toggle, et non surcharge `litScale`) : `DrawVolumeEllipse` est
		// appelée par les 6 archétypes de feuille (Leaf.cs) ET par les fruits/fleurs
		// (DrawVolumeCircle). Le toggle concentre TOUT le changement à l'entrée de la
		// boucle feuilles (Organs.cs) — la surcharge (b) aurait forcé à propager un
		// paramètre à travers Lanceolee/Cordee/Lobee/Composee/Aciculaire et leurs
		// appels imbriqués, bien moins lisible. Le toggle est posé juste AVANT la
		// boucle feuilles et REMIS à `LitFactorDefault` juste après → fruits/fleurs
		// (dessinés hors de cette fenêtre) gardent leur calotte normale.
		private void DrawVolumeEllipse(Vector2 center, float rx, float ry, Color baseCol)
		{
			DrawEllipse(center, rx, ry, HueShift(baseCol, -OrganShade));
			DrawEllipse(center + SouthDir() * (ry * 0.5f),
						rx * _litFactor, ry * _litFactor, HueShift(baseCol, OrganLit));
		}

		private void DrawVolumeCircle(Vector2 center, float rad, Color baseCol)
		{
			DrawCircle(center, rad, HueShift(baseCol, -OrganShade));
			DrawCircle(center + SouthDir() * (rad * 0.32f),
					   rad * 0.72f, HueShift(baseCol, OrganLit));
		}

		// --- Volume cylindrique (branches) -----------------------------------
		// Le corps du rameau en teinte d'ombre (le cylindre est majoritairement
		// dans son propre ombrage), plus un liseré éclairé décalé sur la face
		// sud — seulement si le trait est assez large pour le montrer (≥3 px).
		private void DrawBranch(Vector2 p1, Vector2 p2, Color col, float w)
		{
			DrawLine(p1, p2, HueShift(col, -BranchShade), w, antialiased: false);
			if (w >= 3f)
			{
				Vector2 off = SouthDir() * (w * 0.22f);
				float wl = Mathf.Max(1f, Mathf.Round(w * 0.45f));
				DrawLine(p1 + off, p2 + off, HueShift(col, BranchLit), wl,
						 antialiased: false);
			}
		}
	}
}
