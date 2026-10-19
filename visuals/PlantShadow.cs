// SYMBIOSE — PlantShadow.cs
// Ombre-capsule au sol d'une plante (t4 volet C, isolée en C2 — retour perf
// Nico). Extrait de PlantRenderer.cs au refactor SS⑦.
//
// Disque monde de rayon spread glissé depuis le collet le long de la direction
// d'ombre solaire, sur hauteur × 1/tan(élévation) — le modèle EXACT des
// ombres-capsules du moteur (fields/light.py §3). Nœud séparé : quand UpdateSun
// balaye (≥ 2°), il ne fait QueueRedraw QUE sur ces nœuds — un petit polygone
// chacun — jamais sur les segments des plantes. Chaque point passe par
// WorldToScreenOffset → l'ombre suit AUSSI la rotation de la vue (D35). Touche O
// (WorldView.ShadowsOn) : _Draw vide = coût nul.

using Godot;

namespace Symbiose
{
	public partial class PlantShadow : Node2D
	{
		private static readonly Color ShadowColor = new Color(0f, 0f, 0f, 0.18f);
		private float _spreadCm = 8f;    // rayon de la capsule (étalement)
		private float _heightCm = 10f;   // hauteur de cime → longueur d'ombre

		public void SetExtent(float spreadCm, float heightCm)
		{
			_spreadCm = spreadCm;
			_heightCm = heightCm;
			QueueRedraw();
		}

		// Banc PERF VUE ① : chronométré (PerfPostes) — appels/s = redessins d'ombre.
		public override void _Draw()
		{
			long t0 = PerfPostes.Debut();
			DessinerOmbre();
			PerfPostes.Fin(PerfPostes.Poste.OmbreDraw, t0);
		}

		private void DessinerOmbre()
		{
			if (!WorldView.ShadowsOn) return;
			Vector2 dir = WorldView.SunShadowDir;            // unité, monde
			Vector2 end = dir * (_heightCm * WorldView.SunInvTan);
			float a0 = Mathf.Atan2(dir.Y, dir.X);
			const int n = 8;                                  // par demi-cercle
			var pts = new Vector2[2 * (n + 1)];
			int k = 0;
			for (int i = 0; i <= n; i++)                      // arrière (collet)
			{
				float a = a0 + Mathf.Pi / 2f + Mathf.Pi * i / n;
				pts[k++] = WorldView.WorldToScreenOffset(
					_spreadCm * Mathf.Cos(a), _spreadCm * Mathf.Sin(a));
			}
			for (int i = 0; i <= n; i++)                      // avant (bout d'ombre)
			{
				float a = a0 - Mathf.Pi / 2f + Mathf.Pi * i / n;
				pts[k++] = WorldView.WorldToScreenOffset(
					end.X + _spreadCm * Mathf.Cos(a), end.Y + _spreadCm * Mathf.Sin(a));
			}
			// Soleil bas → lumière faible → ombre plus pâle (et plus longue).
			var col = ShadowColor;
			col.A = ShadowColor.A * Mathf.Clamp(WorldView.SunStrength * 1.4f, 0.3f, 1f);
			DrawColoredPolygon(pts, col);
		}
	}
}
