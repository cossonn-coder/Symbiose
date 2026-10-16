// SYMBIOSE — SolTexture.cs (SS² Rendu pixel-art, tronçon T2)
// CUISSON de la texture de SOL d'un plot (cap
// docs/rendu/pixelart/conception_rendu_pixelart.md §5, bloc « Relief du SOL »).
// Avant T2 le sol
// était un APLAT : WorldView.Monde posait un losange Polygon2D d'une seule
// couleur par plot (+ damier ±5 %). C'était le dernier aplat du rendu.
//
// CE QU'ON CUIT, en UNE passe, dans une Image ~39×20 px (la taille du losange
// iso interne, cf. WorldView.Projection) :
//   1. RELIEF bombé « lumière du sud » — le sol n'est plus plat : la moitié
//      orientée vers le SUD-MONDE est éclaircie (hue-shift CHAUD), la moitié
//      nord assombrie + refroidie (hue-shift FROID). Même grammaire chromatique
//      que les plantes (PlantRenderer.Palette : hue-shifting jaune/bleu) — c'est
//      tout l'intérêt de la palette partagée : sol et organes s'éclairent pareil.
//   2. GRAIN dithering 3 valeurs — un Hash déterministe par pixel (philo #3,
//      ZÉRO Random) quantifié en −1/0/+1 module LÉGÈREMENT la valeur. Micro-
//      texture de terre, grossière à dessein (39×20 px = pixel art assumé).
//
// 📖 ESPACE DE CUISSON (le point délicat). La texture est en pixels ÉCRAN du
// losange (mêmes cotes que MakeLozenge). Le RELIEF doit pointer vers le
// sud-MONDE, qui à l'écran tombe sur un sommet différent selon l'orientation
// D35. On résout ça SANS géométrie ad hoc : WorldView.WorldToScreenOffset(0,1)
// projette le vecteur monde « plein sud » dans CE MÊME espace écran ET applique
// déjà la rotation de vue. On cuit donc le gradient le long de ce vecteur → les
// 4 orientations sortent de la MÊME formule, juste une projection sud différente.
// D'où 4 textures par type de sol (≤ 4 sols × 4 orient = 16, cachées par
// WorldView.Monde). Filtre Nearest posé par l'appelant sur le Sprite2D.
//
// Statique, déclaratif : un fichier = une responsabilité (cuire un losange de
// sol). Aucun état, aucun lien moteur → golden trivialement préservé.

using Godot;

namespace Symbiose
{
	internal static class SolTexture
	{
		// Cotes de l'image cuite = losange iso interne, arrondies au pixel
		// supérieur (la diagonale doit tenir entière dans l'image).
		// Exposées (D106 T2) : le maillage du sol (SolMaillage) reproduit la
		// géométrie EXACTE de l'ancien Sprite2D centré, qui faisait W×H px.
		internal static readonly int W = Mathf.CeilToInt(WorldView.TileWPx);   // ~39
		internal static readonly int H = Mathf.CeilToInt(WorldView.TileHPx);   // ~20

		// --- Amplitudes (à régler au F5) ------------------------------------
		// Relief DOUX : le sol est mat, pas un organe rond — on suggère un bombé,
		// on ne sculpte pas une bille. lum ∈ [−ReliefAmp, +ReliefAmp] le long de
		// l'axe nord→sud, passé au hue-shift comme pour les plantes.
		private const float ReliefAmp = 0.22f;
		// Grain : pas de valeur d'un cran de dither (faible → ne noie pas le
		// relief). 3 niveaux : −GrainStep / 0 / +GrainStep sur la VALEUR HSV.
		private const float GrainStep = 0.05f;

		// Hue-shift LOCAL — réplique fidèle de PlantRenderer.HueShift (mêmes
		// teintes cibles WarmHue/CoolHue, mêmes forces) mais STATIQUE : la
		// version plante est une méthode d'instance (lit le champ _coolShiftScale,
		// hors-sujet ici). Dupliquer 6 lignes vaut mieux qu'extraire un état
		// d'instance dans un statique — l'iso-comportement chromatique sol↔plante
		// est le contrat, pas le partage de code. Constantes copiées de Palette.cs.
		private const float HueShiftStrength = 0.5f;
		private const float ValueStrength = 0.5f;
		private const float SatStrength = 0.2f;
		private const float WarmHue = 0.13f;   // jaune chaud (lumière)
		private const float CoolHue = 0.60f;   // bleu froid (ombre)

		private static Color HueShift(Color c, float lum)
		{
			float h = c.H, s = c.S, v = c.V;
			float target = lum >= 0f ? WarmHue : CoolHue;
			h = HueTowards(h, target, Mathf.Abs(lum) * HueShiftStrength);
			v = Mathf.Clamp(v + lum * ValueStrength, 0f, 1f);
			s = Mathf.Clamp(s + Mathf.Max(0f, -lum) * SatStrength, 0f, 1f);
			var outc = Color.FromHsv(h, s, v);
			outc.A = c.A;
			return outc;
		}

		// Plus court chemin sur le cercle des teintes (copie de Palette.cs).
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

		// Hash entier → [0,1) déterministe — même mix xorshift que
		// PlantRenderer.Hash01 (un seul langage de bruit dans le rendu). Sert ici
		// le grain dithering du sol, indexé par pixel (x, y) + un canal.
		private static float Hash01(int channel, int x, int y)
		{
			uint h = (uint)channel * 0x9E3779B1u
				   ^ (uint)x * 0x85EBCA77u ^ (uint)y * 0xC2B2AE3Du;
			h ^= h >> 15; h *= 0x2C1B3C6Du;
			h ^= h >> 12; h *= 0x297A2D39u;
			h ^= h >> 15;
			return (h & 0xFFFFFF) / 16777216f;
		}

		/// <summary>
		/// Cuit le losange de sol (relief sud + grain) pour une couleur de sol et
		/// une orientation D35 donnée. L'orientation choisit la direction
		/// sud-MONDE projetée à l'écran (WorldToScreenOffset) → le bombé suit le
		/// jardin quand on tourne la vue. Texture en filtre Nearest (l'appelant
		/// le pose sur le Sprite2D). Hors du losange : alpha 0 (pas de carré
		/// opaque qui dépasse).
		/// </summary>
		public static ImageTexture BakeLozenge(Color soil, int orientation)
		{
			var img = Image.CreateEmpty(W, H, false, Image.Format.Rgba8);

			// Demi-cotes du losange (espace centré sur l'image).
			float hw = WorldView.TileWPx / 2f;
			float hh = WorldView.TileHPx / 2f;
			float cx = (W - 1) / 2f, cy = (H - 1) / 2f;   // centre image (pixels)

			// Direction sud-MONDE projetée à l'écran POUR CETTE ORIENTATION :
			// WorldToScreenOffset applique déjà le quart de tour de la vue. On la
			// lit en posant temporairement l'orientation voulue (la projection est
			// statique). Normalisée → produit scalaire = position le long du sud.
			Vector2 south = SouthDir(orientation);

			for (int py = 0; py < H; py++)
				for (int px = 0; px < W; px++)
				{
					// Position du pixel relative au centre du losange.
					float dx = px - cx, dy = py - cy;

					// Test « dans le losange » : |x/hw| + |y/hh| <= 1.
					if (Mathf.Abs(dx) / hw + Mathf.Abs(dy) / hh > 1f)
					{
						img.SetPixel(px, py, new Color(0f, 0f, 0f, 0f));
						continue;
					}

					// RELIEF : projection (signée) du pixel sur l'axe sud, ramenée
					// dans [−1,1] par la demi-diagonale, → lum ∈ [−ReliefAmp, +Amp].
					// Côté sud (proj > 0) → chaud/clair ; côté nord → froid/sombre.
					float proj = (dx * south.X + dy * south.Y) / hw;
					float lum = Mathf.Clamp(proj, -1f, 1f) * ReliefAmp;

					// GRAIN : Hash pixel quantifié en 3 niveaux (−1/0/+1). Choix du
					// hash plutôt qu'un Bayer 4×4 : sur 39×20 px le motif Bayer
					// régulier « quadrillerait » visiblement ; le hash donne un
					// grain de terre désordonné mais DÉTERMINISTE (rejouable). À
					// arbitrer au F5 si le rendu Bayer est préféré.
					int level = (int)(Hash01(2, px, py) * 3f) - 1;   // −1, 0 ou +1
					lum += level * GrainStep;

					img.SetPixel(px, py, HueShift(soil, lum));
				}

			var tex = ImageTexture.CreateFromImage(img);
			return tex;
		}

		// Direction sud-MONDE projetée à l'écran pour une orientation donnée.
		// 📖 On NE mute PAS l'orientation globale de la vue (effet de bord
		// dangereux en pleine cuisson) : on rejoue ICI la MÊME transformation que
		// WorldToScreenOffset, mais pour l'orientation passée en argument plutôt
		// que celle de la vue. C'est le vecteur monde plein sud (0,+1) → quart de
		// tour linéaire (dx,dy)→(dy,−dx) appliqué `orientation` fois → projection
		// iso 2:1. Identique au calcul plante (PlantRenderer.SouthDir) à
		// l'orientation courante ; ici on le paramètre pour cuire les 4 variantes.
		private static Vector2 SouthDir(int orientation)
		{
			float dx = 0f, dy = 1f;
			for (int i = 0; i < orientation; i++)
				(dx, dy) = (dy, -dx);
			var d = new Vector2((dx - dy) * WorldView.PxPerCmX,
								(dx + dy) * WorldView.PxPerCmY);
			return d.LengthSquared() > 1e-6f ? d.Normalized() : new Vector2(0f, 1f);
		}
	}
}
