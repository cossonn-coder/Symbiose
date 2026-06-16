// SYMBIOSE — WorldView.Projection.cs (partial de WorldView, SS⑥ refactor global)
// LE pipeline de projection monde → écran (et son inverse). Une seule
// transformation, écrite ici UNE fois, utilisée partout (plots, maison,
// plantes, ombres). C'est la leçon du bug D2 : deux projections « presque
// pareilles » ne coïncident jamais. État de la projection = l'orientation
// (quart de tour) ; les écrivains de cet état sont la caméra (RotateView) et
// _Ready (remise à zéro).

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// -------------------------------------------------------------------
		// CALIBRATION (mesurée sur assets/sprites/tiles/tile_terre.png — D2)
		// Le losange UTILE du sprite fait 78×39 px (iso 2:1 exact) + un socle
		// d'épaisseur ~15 px que le placeholder ignore. 1 plot = 50 cm.
		// -------------------------------------------------------------------
		public const float PlotCm = 50f;                       // = constants.PLOT_CM
		public const float TileWPx = 78f;                      // largeur losange
		public const float TileHPx = 39f;                      // hauteur losange (2:1)
		public const float PxPerCmX = TileWPx / 2f / PlotCm;   // 0.78 px/cm
		public const float PxPerCmY = TileHPx / 2f / PlotCm;   // 0.39 px/cm
		// Échelle verticale (hauteurs dz) : = PxPerCmX, le standard iso 2:1 qui
		// ne « tasse » pas les verticales. Un pommier de 350 cm fait ~273 px.
		public const float PxPerCmZ = PxPerCmX;
		// Côté du monde : 20 m (échelle actée, cf. CLAUDE.md).
		public const float WorldCm = 2000f;

		// --- Orientation de la vue (D35, tranche 4) -------------------------
		// 📖 Pédagogie — pivoter une vue iso n'est PAS tourner le canvas (un
		// canvas tourné donnerait des losanges penchés). On garde la MÊME
		// projection 2:1 et on tourne le MONDE dessous : un quart de tour
		// anti-horaire autour du centre (1000,1000) cm = (x,y) → (y, 2000−x),
		// appliqué Orientation fois AVANT la projection. Conséquence : tout ce
		// qui a été positionné via WorldToScreen garde une Position figée →
		// chaque changement d'orientation passe par RebuildWorld().
		private static int _orientation;   // 0..3 quarts de tour anti-horaires

		/// <summary>
		/// LA projection monde → écran (kickoff t2 : une seule, partout).
		/// x augmente vers l'est (droite-bas du losange), y vers le sud.
		/// Depuis la tranche 4, applique d'abord l'orientation de la vue.
		/// </summary>
		public static Vector2 WorldToScreen(float xCm, float yCm)
		{
			for (int i = 0; i < _orientation; i++)
				(xCm, yCm) = (yCm, WorldCm - xCm);
			return new Vector2((xCm - yCm) * PxPerCmX, (xCm + yCm) * PxPerCmY);
		}

		/// <summary>
		/// Sœur de WorldToScreen pour les OFFSETS (vecteurs, pas points) :
		/// un déplacement relatif (segment − collet d'une plante) ne subit que
		/// la partie LINÉAIRE du quart de tour — (dx,dy) → (dy, −dx) — jamais
		/// la translation WorldCm−x, qui téléporterait l'offset de 20 m.
		/// 📖 C'est la distinction point/vecteur des transformations affines
		/// (le « w=0 » des coordonnées homogènes). Pas une 2ᵉ projection
		/// (leçon D2) : la MÊME, déclinée point/vecteur côte à côte.
		/// </summary>
		public static Vector2 WorldToScreenOffset(float dxCm, float dyCm)
		{
			for (int i = 0; i < _orientation; i++)
				(dxCm, dyCm) = (dyCm, -dxCm);
			return new Vector2((dxCm - dyCm) * PxPerCmX, (dxCm + dyCm) * PxPerCmY);
		}

		/// <summary>
		/// L'INVERSE de WorldToScreen (picking, volet B) : canvas → monde (cm).
		/// 📖 La projection est linéaire (matrice 2×2, déterminant non nul) →
		/// inversible analytiquement : sx=(x−y)·a, sy=(x+y)·b donne
		/// x = sx/2a + sy/2b et y = −sx/2a + sy/2b. Puis on défait l'orientation
		/// — transformations inverses DANS L'ORDRE INVERSE : l'inverse du quart
		/// de tour (x,y)→(y, W−x) est (u,v)→(W−v, u). GetGlobalMousePosition
		/// rend la souris déjà en canvas (pan/zoom caméra défaits par Godot) —
		/// cette fonction est donc le SEUL maillon manquant. Écrite ici, à côté
		/// de l'aller (leçon D2 : jamais deux projections « presque pareilles »).
		/// </summary>
		public static Vector2 ScreenToWorld(Vector2 scr)
		{
			float x = scr.X / (2f * PxPerCmX) + scr.Y / (2f * PxPerCmY);
			float y = -scr.X / (2f * PxPerCmX) + scr.Y / (2f * PxPerCmY);
			for (int i = 0; i < _orientation; i++)
				(x, y) = (WorldCm - y, x);
			return new Vector2(x, y);
		}
	}
}
