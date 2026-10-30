// SYMBIOSE — NueeMoustiques.cs (sprint MARE VIVANTE ③)
// La NUÉE de moustiques : chaque moustique envoyé par le serveur (≤ 6, en grappe
// au-dessus de la mare) devient 4 « moucherons » de 2 pixels qui DANSENT un peu au-dessus du sol —
// la silhouette qu'on reconnaît d'un moustique, bien avant de voir l'insecte. Lisible
// dès ×4, discrète : des points gris-brun piqués d'un éclat d'aile, pas un essaim noir.
//
// 📖 Pédagogie — pourquoi un nœud à part ? MacroLife ne redessine qu'au snapshot (les
// bêtes sont figées au repos, DA « l'animation est un signal »). La nuée, elle, EST
// le signal « des moustiques sont là » : elle danse tant qu'elle est présente. Elle
// vit donc dans son propre Node2D, enfant de MacroLife (masqué avec lui, touche I),
// qui redessine ses ≤ 48 pixels à 12 Hz — et RIEN quand il n'y a pas de nuée à l'écran.
// Pas de Random : la danse est une somme de sinus déphasés au hash de la bête.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class NueeMoustiques : Node2D
	{
		private const float ZoomMin = 4f;        // en deçà : trop petit pour se lire
		private const int Points = 4;            // pixels par moustique envoyé
		private const float Hz = 12f;            // cadence de la danse
		private const float HauteurPx = 6f;      // au-dessus du sol (px internes)
		private const float AmpX = 6f, AmpY = 3.5f;   // amplitude de la danse (px internes)
		private const float CullMarginPx = 16f;
		private static readonly Color Corps = new("6a5f57");   // = MacroLife moustique
		private static readonly Color Aile = new("c8c4c0");    // = FauneSilhouettes moustique

		private readonly List<(Vector2 W, uint Phase)> _m = new();
		private float _acc;
		private bool _dessinee;   // une image non vide est à l'écran

		public void Poser(List<(Vector2, uint)> moustiques)
		{
			_m.Clear();
			_m.AddRange(moustiques);
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			if (_m.Count == 0 || WorldView.CurrentZoom < ZoomMin)
			{
				if (_dessinee) QueueRedraw();   // une image vide pour effacer
				return;
			}
			_acc += (float)delta;
			if (_acc < 1f / Hz) return;
			_acc = 0f;
			QueueRedraw();
		}

		public override void _Draw()
		{
			_dessinee = false;
			float zoom = WorldView.CurrentZoom;
			if (_m.Count == 0 || zoom < ZoomMin) return;
			float px1 = 1f / zoom;   // 1 pixel interne, en px canvas
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			float t = Time.GetTicksMsec() / 1000f;
			foreach (var (w, ph) in _m)
			{
				Vector2 sol = WorldView.WorldToScreen(w.X, w.Y);
				if (!vis.HasPoint(sol)) continue;
				for (int k = 0; k < Points; k++)
				{
					uint h = ph * 2654435761u + (uint)k * 40503u;
					float a = (h & 0xffff) * (Mathf.Tau / 65536f);
					float b = (h >> 16) * (Mathf.Tau / 65536f);
					float dx = AmpX * (0.7f * Mathf.Sin(t * 5.3f + a) + 0.3f * Mathf.Sin(t * 11.1f + b));
					float dy = AmpY * Mathf.Sin(t * 7.7f + b) - HauteurPx;
					// Calé sur la grille des px internes (jamais de demi-pixel).
					var p = new Vector2(Mathf.Round(sol.X / px1 + dx), Mathf.Round(sol.Y / px1 + dy)) * px1;
					// Un moustique = un pixel de corps + un pixel d'aile CLAIRE au-dessus,
					// qui bat (s'éteint un instant) : l'éclat clair se lit sur l'eau
					// sombre, le corps sur la vase et la terre claires.
					DrawRect(new Rect2(p, new Vector2(px1, px1)), Corps);
					if (Mathf.Sin(t * 9f + a) > -0.4f)
						DrawRect(new Rect2(p - new Vector2(0f, px1), new Vector2(px1, px1)), Aile);
					_dessinee = true;
				}
			}
		}
	}
}
