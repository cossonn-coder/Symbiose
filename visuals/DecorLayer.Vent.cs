// SYMBIOSE — DecorLayer.Vent.cs (CASSÉ À L'ÉCRAN ⑥ — la lisière animée au vent et à la lumière)
// Partial de DecorLayer : (1) les UNIFORMES du shader du décor, posés chaque image —
// soleil réel (le même que les plantes, PaletteIndexee.Soleil), palier affiché, vent
// (bloc `weather.wind` du snapshot via WindWave : force, direction, risées, temps) ;
// (2) l'AMPLITUDE de vent de chaque pièce, fixée à la construction de la maille.
//
// 📖 Pédagogie — l'animation est un SIGNAL (DA SNES) : sous WindWave.CalmForce la force
// envoyée au shader vaut 0 → aucun sommet ne bouge, l'image est figée. Au vent, AUCUN
// redessin CPU : la maille reste la même, seul le vertex shader déplace les sommets
// (comme un registre de scroll matériel : la carte ne bouge pas en mémoire, le
// décalage est appliqué à la lecture).
//
// 📖 Les MÊMES fronts que les plantes : WindWave.PoseFor calcule une phase à partir de
// la position MONDE projetée sur la direction du vent. Le shader, lui, ne connaît que
// la position CANVAS ; comme la projection iso est affine, « monde · direction » est
// une fonction affine du point canvas : on la précalcule ici (onde_k, onde_c) avec
// WorldView.ScreenToWorld — la même projection inverse que le picking.

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Amplitude au sommet, en fraction de la hauteur de la pièce (px internes) :
		// houppiers (cf. AmpArbre) > sous-bois > roseaux > herbes ; roche = 0.
		private const float AmpArbre = 0.03f;   // fraction de la hauteur d'un arbre (px canvas)
		private static float AmpPiece(Piece f) => f switch
		{
			Piece.SousBois => 0.40f,
			Piece.Roncier => 0.20f,
			Piece.Roseau => 0.30f,
			Piece.HerbeHaute => 0.30f,
			Piece.Herbe => 0.25f,
			Piece.Fleur => 0.25f,
			_ => 0f,   // galets, blocs ; bouquets de houppier = vent de leur arbre
		};

		/// <summary>Vent d'une pièce posée (pied = bas-centre, `hPx` = hauteur en px
		/// internes) : rien à faire si un arbre est en cours (ses bouquets suivent l'arbre).</summary>
		private void VentPiece(Piece f, Vector2 pied, int hPx, uint h)
		{
			if (_ventArbre) return;
			float hCanvas = hPx / ZoomConstr;
			Vent(AmpPiece(f) * hCanvas, pied.Y, hCanvas, (h >> 8 & 0xff) / 255f);
		}

		/// <summary>Vent d'un arbre : nul au pied, `AmpArbre` × hauteur au sommet.</summary>
		private void VentArbre(Vector2 pied, float hautPx, uint h)
		{
			Vent(AmpArbre * hautPx, pied.Y, hautPx, (h >> 8 & 0xff) / 255f);
			_ventArbre = true;
		}

		private void FinArbre()
		{
			Vent(0f, 0f, 1f, 0f);
			_ventArbre = false;
		}

		// Derniers uniformes envoyés (on n'écrit qu'au changement).
		private float _uZoom = -1f, _uForce = -1f;
		private Vector2 _uSoleil = new(float.NaN, 0f), _uDir;

		/// <summary>Chaque image (_Process) : soleil, palier, vent → shader.</summary>
		private void MajUniformes()
		{
			var m = MateriauDecor;
			Vector2 sol = PaletteIndexee.Soleil;
			if (!float.IsNaN(sol.X) && !sol.IsEqualApprox(_uSoleil)) { _uSoleil = sol; m.SetShaderParameter("soleil", sol); }
			float z = ZoomMaille;   // la grille des pixels internes est celle de la maille affichée
			if (z != _uZoom) { _uZoom = z; m.SetShaderParameter("zoom", z); }
			float force = WindWave.Active ? WindWave.Force : 0f;
			if (force != _uForce) { _uForce = force; m.SetShaderParameter("vent_force", force); }
			if (force <= 0f) return;   // calme : rien ne bouge, rien d'autre à écrire
			Vector2 dw = WindWave.Downwind;
			Vector2 d = WorldView.WorldToScreenOffset(dw.X, dw.Y);   // suit la rotation D35
			d = d.LengthSquared() > 1e-8f ? d.Normalized() : Vector2.Right;
			if (d != _uDir) { _uDir = d; m.SetShaderParameter("vent_dir", d); }
			// Phase = (monde · aval) / (λ × échelle) − f × échelle × t, comme PoseFor.
			float echelle = 0.5f + force;
			float lam = WindWave.OndeLambdaCm * echelle;
			float c0 = WorldView.ScreenToWorld(Vector2.Zero).Dot(dw);
			float kx = WorldView.ScreenToWorld(Vector2.Right).Dot(dw) - c0;
			float ky = WorldView.ScreenToWorld(Vector2.Down).Dot(dw) - c0;
			m.SetShaderParameter("onde_k", new Vector2(kx, ky) / lam);
			m.SetShaderParameter("onde_c", c0 / lam);
			m.SetShaderParameter("onde_f", WindWave.OndeFreqHz * echelle);
			m.SetShaderParameter("temps", (float)WindWave.Temps);
			m.SetShaderParameter("risees", new Vector4(WindWave.Risee(0), WindWave.Risee(1),
													   WindWave.Risee(2), WindWave.Risee(3)));
		}
	}
}
