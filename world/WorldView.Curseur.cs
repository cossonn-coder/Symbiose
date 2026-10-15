// SYMBIOSE — WorldView.Curseur.cs (partial de WorldView, jardin vivant T1)
// Le CURSEUR VIVANT : une petite main gantée SNES (cuite procéduralement, deux
// images : repos / « tap ») + le LOSANGE DE SURVOL du plot visé (PlotHover).
//
// Principe du sprint (animation = SIGNAL, jamais décor) :
//  - le curseur est IMMOBILE ; il ne « tape » (≈150 ms) qu'en réponse à un clic ;
//  - le losange est STATIQUE ; il ne « respire » que quand un geste est ARMÉ
//    (slot 1..9 choisi) — il signale « un clic ici agira ».
//
// 📖 Pédagogie Godot/C# :
//  - Input.SetCustomMouseCursor remplace le curseur SYSTÈME par une texture :
//    c'est l'OS qui le dessine (aucun coût de rendu, pas de latence d'une frame).
//    Il est donc HORS SubViewport → non quantifié ; on le peint directement avec
//    les couleurs de la palette maître pour rester cohérent.
//  - Le « hotspot » = le pixel de l'image qui EST le point cliqué (le bout de
//    l'index). Il reste fixe entre les deux images : le tap déplace le dessin,
//    jamais le point d'action.

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Main gantée 16×16 (index levé, pouce à gauche). K = contour, W = gant,
		// S = ombre du gant, Y = étincelle du tap, '.' = transparent.
		private static readonly string[] MainRepos =
		{
			"....KK..........",
			"...KWWK.........",
			"...KWWK.........",
			"...KWSK.........",
			"...KWSKKK.......",
			"...KWSKWWKK.....",
			"...KWSKWSKWKK...",
			".KKKWWWWSKWSWK..",
			"KWWKWWWWWWWSWK..",
			"KWSWWWWWWWWWSK..",
			".KSWWWWWWWWWSK..",
			"..KSWWWWWWWSK...",
			"...KSWWWWWSK....",
			"....KSSSSSK.....",
			".....KKKKK......",
			"................",
		};
		// Tap : la main s'enfonce d'un pixel, index raccourci, deux étincelles.
		private static readonly string[] MainTap =
		{
			".Y.........Y....",
			"....KK..........",
			"...KWWK.........",
			"...KWSKKK.......",
			"...KWSKWWKK.....",
			"...KWSKWSKWKK...",
			".KKKWWWWSKWSWK..",
			"KWWKWWWWWWWSWK..",
			"KWSWWWWWWWWWSK..",
			".KSWWWWWWWWWSK..",
			"..KSWWWWWWWSK...",
			"...KSWWWWWSK....",
			"....KSSSSSK.....",
			".....KKKKK......",
			"................",
			"................",
		};
		private const int CurseurEchelle = 2;          // 1 px de dessin = 2 px écran (= grille pixel-art)
		private static readonly Vector2 CurseurHotspot = new(4.5f * CurseurEchelle, 0f);
		private const ulong TapDureeMs = 150;
		private const float RespirationPeriodeS = 1.4f;

		private ImageTexture _curseurRepos, _curseurTap;
		private ulong _tapFinMs;                       // 0 = pas de tap en cours
		private PlotHover _plotHover;

		/// <summary>Cuit les deux images du curseur et pose l'image de repos.
		/// Appelé une fois par _Ready (la cuisson coûte ~2×256 pixels).</summary>
		private void InitCurseur()
		{
			_curseurRepos = CuireMain(MainRepos);
			_curseurTap = CuireMain(MainTap);
			Input.SetCustomMouseCursor(_curseurRepos, Input.CursorShape.Arrow, CurseurHotspot);
		}

		/// <summary>Clic gauche dans le monde : la main « tape » brièvement.</summary>
		private void TapCurseur()
		{
			Input.SetCustomMouseCursor(_curseurTap, Input.CursorShape.Arrow, CurseurHotspot);
			_tapFinMs = Time.GetTicksMsec() + TapDureeMs;
		}

		/// <summary>_ExitTree : rend le curseur système et libère les textures
		/// TOUT DE SUITE (sinon le GC les finalise après l'arrêt du moteur de rendu
		/// → fuite signalée à la sortie, constaté au banc VM).</summary>
		private void LibererCurseur()
		{
			Input.SetCustomMouseCursor(null);
			_curseurRepos?.Dispose();
			_curseurTap?.Dispose();
			_curseurRepos = _curseurTap = null;
		}

		private static ImageTexture CuireMain(string[] motif)
		{
			var img = Image.CreateEmpty(16, 16, false, Image.Format.Rgba8);
			for (int y = 0; y < 16; y++)
				for (int x = 0; x < 16; x++)
					img.SetPixel(x, y, motif[y][x] switch
					{
						'K' => Palette16.MaitreSombre,
						'W' => Palette16.MaitreBlanc,
						'S' => Palette16.MaitreGranite,
						'Y' => Palette16.MaitreJaune,
						_   => Colors.Transparent,
					});
			img.Resize(16 * CurseurEchelle, 16 * CurseurEchelle, Image.Interpolation.Nearest);
			return ImageTexture.CreateFromImage(img);
		}

		/// <summary>Chaque frame (_Process) : fin du tap + losange du plot survolé.
		/// Coût : un FindPlot (8 tuiles) + un déplacement de nœud, pas de redraw.</summary>
		private void UpdateCurseur()
		{
			if (_tapFinMs != 0 && Time.GetTicksMsec() >= _tapFinMs)
			{
				_tapFinMs = 0;
				Input.SetCustomMouseCursor(_curseurRepos, Input.CursorShape.Arrow, CurseurHotspot);
			}
			if (_plotHover == null)
			{
				// Enfant DIRECT du SubViewport : survit à RebuildWorld (rotation),
				// et sa position est recalculée chaque frame → suit l'orientation.
				_plotHover = new PlotHover { Name = "PlotHover", ZIndex = 3 };
				AddWorld(_plotHover);
			}
			Vector2 w = ScreenToWorld(WorldMouseCanvas());
			if (_origins == null || !FindPlot(w, out string tile, out int r, out int c)
				|| !_origins.TryGetValue(tile, out Vector2 org))
			{
				_plotHover.Visible = false;
				return;
			}
			_plotHover.Visible = true;
			// Centre du plot (comme BuildGround), remonté du relief du sol (D57).
			_plotHover.Position = WorldToScreen(org.X + (c + 0.5f) * PlotCm, org.Y + (r + 0.5f) * PlotCm)
				- new Vector2(0f, ReliefRiseAtPlot(tile, r, c));
			// Respiration UNIQUEMENT geste armé ; sinon contour fixe et discret.
			float a = 0.8f;
			if (_gesteIndex >= 0)
			{
				float t = Time.GetTicksMsec() / 1000f;
				a = 0.55f + 0.45f * (0.5f + 0.5f * Mathf.Sin(t * Mathf.Tau / RespirationPeriodeS));
			}
			_plotHover.Modulate = new Color(1f, 1f, 1f, a);
		}
	}
}
