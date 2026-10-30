// SYMBIOSE — PuddleLayer.Signaux.cs (sprint MARE VIVANTE ③ — les signaux de l'eau)
// Pose, chaque image, les uniforms des TROIS signaux du shader de l'eau
// (`visuals/eau_mare.gdshader`, §③) — l'eau ne s'anime au-delà du scintillement
// que pour DIRE un état :
//   · vent  : WindWave (la même source que les plantes et la lisière — `Active` sous
//             le seuil de calme = aucune ride), direction AVAL vue par l'écran iso ;
//   · pluie : MeteoPlantes.Pluie (la même lecture du bloc `weather` que le feuillage
//             mouillé et les gouttes de WeatherLayer) ;
//   · gobage : MacroLife.ProiesDeMare (moustiques / libellules PEINTS) → ≤ 8 points.
// Le shader n'applique les trois que sur l'EAU LIBRE (jamais sur la glace ni la vase).
//
// 📖 Pédagogie — pas de redessin : les rides et les ronds sont calculés PAR PIXEL au
// GPU à partir de TIME. Le CPU n'écrit qu'un uniform quand sa valeur CHANGE (vent qui
// tourne, averse qui commence, snapshot qui déplace la nuée) : la couche garde UN
// lot et UN draw call, sans re-tessellation.

using Godot;

namespace Symbiose
{
	public partial class PuddleLayer
	{
		private const int GobagesMax = 8;   // = taille de `gobages[]` dans le shader
		private float _uVentForce = -1f, _uPluie = -1f;
		private Vector2 _uVentDir;
		private int _uVersionMare = -1;
		private Vector2 _uOrient = new(float.NaN, float.NaN);

		private void MajSignaux()
		{
			var m = MateriauEau;
			float force = WindWave.Active ? WindWave.Force : 0f;
			if (force != _uVentForce) { _uVentForce = force; m.SetShaderParameter("vent_force", force); }
			if (force > 0f)
			{
				// Gradient ÉCRAN de la coordonnée « aval » du MONDE (comme onde_k de
				// DecorLayer.Vent.cs) : ses lignes de niveau sont les crêtes, donc
				// perpendiculaires au vent SUR LE SOL puis projetées en iso — et non
				// perpendiculaires à l'écran (qui donnait des traits verticaux, « pluie »).
				Vector2 dw = WindWave.Downwind;
				float c0 = WorldView.ScreenToWorld(Vector2.Zero).Dot(dw);
				var d = new Vector2(WorldView.ScreenToWorld(Vector2.Right).Dot(dw) - c0,
									WorldView.ScreenToWorld(Vector2.Down).Dot(dw) - c0);
				d = d.LengthSquared() > 1e-8f ? d.Normalized() : Vector2.Right;   // suit D35
				if (d != _uVentDir) { _uVentDir = d; m.SetShaderParameter("vent_dir", d); }
			}
			float pluie = MeteoPlantes.Pluie;
			if (pluie != _uPluie) { _uPluie = pluie; m.SetShaderParameter("pluie", pluie); }
			MajGobages(m);
		}

		// Points de gobage en coordonnées CANVAS (celles de VERTEX dans le shader) :
		// relus au snapshot (VersionMare) ou à la rotation de vue seulement.
		private void MajGobages(ShaderMaterial m)
		{
			var macro = _view?.Macro;
			if (macro == null) return;
			Vector2 orient = WorldView.WorldToScreen(0f, 0f);   // signature de rotation
			if (macro.VersionMare == _uVersionMare && orient == _uOrient) return;
			_uVersionMare = macro.VersionMare;
			_uOrient = orient;
			var pts = new Vector4[GobagesMax];
			int n = 0;
			foreach (Vector2 w in macro.ProiesDeMare)
			{
				if (n == GobagesMax) break;
				Vector2 s = WorldView.WorldToScreen(w.X, w.Y);
				// Déphasage stable tiré de la position (pas de Random) : chaque point
				// gobe à son heure, jamais tous ensemble.
				uint h = (uint)(int)(w.X * 7.0f) * 2654435761u ^ (uint)(int)(w.Y * 3.0f) * 40503u;
				pts[n++] = new Vector4(s.X, s.Y, (h & 0xffff) / 65536f, 0f);
			}
			m.SetShaderParameter("gobages", pts);
			m.SetShaderParameter("n_gobages", n);
		}
	}
}
