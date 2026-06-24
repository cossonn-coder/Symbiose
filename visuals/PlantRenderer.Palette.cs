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

		// --- Rampe de lignification (branches vert → brun) -------------------
		// Teinte intermédiaire olive : un lerp RGB direct vert→brun passerait par
		// un gris-kaki mort ; le stop olive garde la rampe vivante (3 valeurs).
		private static readonly Color WoodOlive = new Color("8a7a38");
		// Au-delà de cette épaisseur un segment est considéré pleinement ligneux.
		private const float LignifyFullCm = 3.0f;

		// Part ligneuse [0,1] d'un segment : un apex (pointe) reste tendre (0),
		// le bois épaissit vers 1. C'est l'index de la rampe.
		private static float Lignification(Segment s) =>
			s.IsApex ? 0f : Mathf.Clamp(s.ThicknessCm / LignifyFullCm, 0f, 1f);

		// Rampe 3 valeurs : vert-tendre (= ApexColor) → olive → brun (= WoodColor).
		// Deux segments de lerp pour traverser l'olive (et non couper droit).
		private static Color WoodRamp(float lig) =>
			lig < 0.5f
				? ApexColor.Lerp(WoodOlive, lig * 2f)
				: WoodOlive.Lerp(WoodColor, (lig - 0.5f) * 2f);

		// --- Hue-shifting -----------------------------------------------------
		// Décale une couleur vers la lumière (lum>0 : + clair, + chaud) ou
		// l'ombre (lum<0 : + sombre, + froid, + saturé). Travaille en HSV car
		// la teinte y est une coordonnée directe. L'alpha d'entrée est préservé.
		private static Color HueShift(Color c, float lum)
		{
			float h = c.H, s = c.S, v = c.V;
			float target = lum >= 0f ? WarmHue : CoolHue;
			h = HueTowards(h, target, Mathf.Abs(lum) * HueShiftStrength);
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
