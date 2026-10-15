// SYMBIOSE — PlotHover.cs (sprint JARDIN VIVANT, T1)
// Le LOSANGE DE SURVOL : un contour pixel de 1 px autour du plot (50×50 cm)
// sous la souris. Posé dans le SubViewport monde (il est donc quantifié par la
// palette SNES comme le reste du jardin) ; WorldView le déplace et règle sa
// respiration (WorldView.Curseur.cs) — ce nœud ne fait que DESSINER.
//
// 📖 Pédagogie : la forme ne change jamais (un plot = toujours le même losange
// iso 2:1, à toute orientation de caméra) → un seul _Draw au premier affichage ;
// ensuite on ne bouge que `Position` (survol) et `Modulate` (respiration). Pas
// de QueueRedraw par frame : le GPU réutilise le dessin mis en cache.

using Godot;

namespace Symbiose
{
	public partial class PlotHover : Node2D
	{
		// Trait blanc chaux + ombre portée sombre 1 px dessous : le couple reste
		// lisible sur TOUS les sols (blanc sur terre/argile/herbe, ombre sur le
		// sable clair) — le procédé des curseurs de menus SNES.
		private static readonly Color Trait = Palette16.MaitreBlanc;
		private static readonly Color Ombre = Palette16.MaitreSombre;

		public override void _Draw()
		{
			// Mêmes cotes que MakeLozenge du sol (WorldView.Monde.cs), centrées.
			float hw = WorldView.TileWPx / 2f, hh = WorldView.TileHPx / 2f;
			var pts = new[]
			{
				new Vector2(0f, -hh), new Vector2(hw, 0f),
				new Vector2(0f, hh), new Vector2(-hw, 0f), new Vector2(0f, -hh),
			};
			// Largeur -1 = primitive fine de 1 px, sans anticrénelage (pixel-art).
			DrawSetTransform(new Vector2(0f, 1f));
			DrawPolyline(pts, Ombre, -1f);
			DrawSetTransform(Vector2.Zero);
			DrawPolyline(pts, Trait, -1f);
		}
	}
}
