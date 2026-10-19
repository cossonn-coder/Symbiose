// SYMBIOSE — WorldView.PlancheKit.cs (partial de WorldView, PLANTE ASSEMBLÉE ④)
// BANC D'OBSERVATION « planche du kit » : affiche par-dessus le monde TOUT l'atlas
// du kit (PlantRenderer.Kit.cs) — 6 formes de feuille × 4 tailles × 3 variantes +
// les fleurons — en 3 teintes, à la loupe (×6) et à la taille réelle des paliers
// bas (×2 écran = palier ×1, ×4 écran = palier ×2). Sert à juger la lisibilité des
// pièces AVANT que ⑤ ne les monte sur les plantes. Banc VM :
// `tools/capture_vm.sh -k` (= --capture-kit=1). Pas un livrable joueur.
//
// 📖 Pédagogie Godot/C# : `ImageTexture.CreateFromImage` envoie une Image CPU au
// GPU ; un `TextureRect` l'affiche agrandi. `TextureFilter = Nearest` garde les
// pixels carrés (sinon l'agrandissement les lisse — l'inverse du pixel-art).

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly bool CaptureKit = ArgCapture("kit") == "1";

		// 3 teintes de feuillage (vert franc de tomate, vert sombre de poivron,
		// roux de sénescence) + la fleur de la tomate pour les fleurons.
		private static readonly Color[] PlancheKitTeintes =
			{ new Color("3f9e3a"), new Color("357f33"), new Color("c4702a") };
		private static readonly Color PlancheKitFleur = new Color("e8d24a");

		private void AfficherPlancheKit()
		{
			// Calque à part, AU-DESSUS du HUD (barre de gestes, encart du ciel).
			var hud = new CanvasLayer { Layer = 100 };
			AddChild(hud);
			var racine = new Control { MouseFilter = Control.MouseFilterEnum.Ignore };
			racine.AddChild(new ColorRect { Color = Palette16.SolTerre, Size = new Vector2(1920f, 1080f) });
			hud.AddChild(racine);

			var atlas = PlantRenderer.KitNiveaux;
			int pas = PlantRenderer.KitPasRangee;
			int nbFormes = PlantRenderer.KitFormes.Length;
			var feuilles = new Rect2I(0, 0, atlas.GetWidth(), pas * nbFormes);
			var fleurons = new Rect2I(0, pas * nbFormes, atlas.GetWidth(), pas);
			var fleurTex = ImageTexture.CreateFromImage(
				PlantRenderer.TeindreKit(fleurons, PlantRenderer.RampeKit(PlancheKitFleur)));

			// Grande loupe ×10 sur la 1ʳᵉ teinte (juger au pixel), noms de forme à
			// gauche ; à droite, les 3 teintes ×4 puis la taille réelle des paliers
			// bas : ×2 écran (palier ×1) et ×4 écran (palier ×2).
			const float loupe = 10f, gauche = 130f;
			float droite = gauche + atlas.GetWidth() * loupe + 40f;
			for (int r = 0; r < nbFormes; r++)
				Etiquette(racine, PlantRenderer.KitFormes[r], new Vector2(8f, 16f + r * pas * loupe));
			Etiquette(racine, "Fleurons", new Vector2(8f, 16f + nbFormes * pas * loupe));
			for (int t = 0; t < PlancheKitTeintes.Length; t++)
			{
				var tex = ImageTexture.CreateFromImage(
					PlantRenderer.TeindreKit(feuilles, PlantRenderer.RampeKit(PlancheKitTeintes[t])));
				if (t == 0)
				{
					Piece(racine, tex, new Vector2(gauche, 16f), loupe);
					Piece(racine, fleurTex, new Vector2(gauche, 16f + nbFormes * pas * loupe), loupe);
				}
				float y = 16f + t * (pas * nbFormes * 4f + 20f);
				Piece(racine, tex, new Vector2(droite, y), 4f);
				Piece(racine, tex, new Vector2(droite + atlas.GetWidth() * 4f + 20f, y), 2f);
			}
			GD.Print($"[Kit] planche : atlas {atlas.GetWidth()}×{atlas.GetHeight()} px, "
				+ $"{nbFormes} formes × {PlantRenderer.KitTailles.Length} tailles × {PlantRenderer.KitVariantes} variantes.");
		}

		private static void Piece(Control parent, Texture2D tex, Vector2 o, float echelle) =>
			parent.AddChild(new TextureRect
			{
				Texture = tex, Position = o, Size = tex.GetSize() * echelle,
				ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
				StretchMode = TextureRect.StretchModeEnum.Scale,
				TextureFilter = CanvasItem.TextureFilterEnum.Nearest,
			});

		private static void Etiquette(Control parent, string texte, Vector2 o)
		{
			var l = new Label { Text = texte, Position = o };
			l.AddThemeFontSizeOverride("font_size", 20);
			parent.AddChild(l);
		}
	}
}
