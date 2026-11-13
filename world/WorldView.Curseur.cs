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
//
// ICÔNES & CURSEUR ③ — le curseur prend l'ICÔNE DU GESTE armé :
//  - deux FORMES de curseur système portent chacune une texture : `Arrow` = la
//    main gantée (inchangée), `Cross` (FormeGeste) = l'icône du geste armé, son
//    point chaud = le pixel actif noté au ② (IconesPointsChauds) ;
//  - `Input.SetDefaultCursorShape` choisit la forme montrée HORS interface. Sur
//    un Control qui capte la souris (panneau, barre, tiroir), Godot montre la
//    forme du Control (`MouseDefaultCursorShape`, Arrow par défaut) → la main
//    revient d'elle-même sur l'interface, sans test de survol à écrire : on ne
//    clique pas un bouton avec une bêche ;
//  - on ne repose une texture qu'au CHANGEMENT de geste (comparaison d'un verbe
//    par image, coût nul) : quel que soit le chemin qui arme le geste (barre,
//    Ctrl+molette, macro, banc), le curseur suit.

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

		// Forme système qui porte l'icône du geste (la main garde Arrow).
		private const Input.CursorShape FormeGeste = Input.CursorShape.Cross;

		private ImageTexture _curseurRepos, _curseurTap;
		// Verbe dont l'icône est posée sur FormeGeste ; null = aucun geste (main).
		private string _curseurVerbe;
		private bool _curseurIcone;                    // l'icône du geste est-elle montrée ?
		private Vector2 _curseurIconeHotspot;          // point chaud de l'icône posée (px écran)
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
			// Geste armé : l'icône reste fixe (l'animation d'exécution viendra au ④).
			if (_curseurIcone) return;
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
			Input.SetCustomMouseCursor(null, FormeGeste);
			Input.SetDefaultCursorShape(Input.CursorShape.Arrow);
			_curseurVerbe = null;
			_curseurIcone = false;
			IconeGeste.Liberer();   // textures d'icônes en cache (palette, tiroir, planche,
			                        // et celle du curseur : c'est le même cache)
		}

		// Cuisson déléguée au moteur d'icônes (ICÔNES & CURSEUR ①) : les lettres
		// K, W, S, Y de la main sont dans son alphabet, aux mêmes couleurs de la
		// palette maître → rendu de la main inchangé.
		private static ImageTexture CuireMain(string[] motif) =>
			IconeGeste.Cuire(motif, CurseurEchelle);

		/// <summary>Chaque frame (_Process) : fin du tap + losange du plot survolé.
		/// Coût : un FindPlot (8 tuiles) + un déplacement de nœud, pas de redraw —
		/// et seulement quand la clé de survol a changé (T3, WorldView.Survol.cs).</summary>
		private void UpdateCurseur()
		{
			if (_tapFinMs != 0 && Time.GetTicksMsec() >= _tapFinMs)
			{
				_tapFinMs = 0;
				Input.SetCustomMouseCursor(_curseurRepos, Input.CursorShape.Arrow, CurseurHotspot);
			}
			SuivreGesteCurseur();
			SuivreTemoinCurseur();   // capture VM seulement (WorldView.CurseurTemoin.cs)
			if (_plotHover == null)
			{
				// Enfant DIRECT du SubViewport : survit à RebuildWorld (rotation),
				// et sa position suit l'orientation (clé de survol, T3).
				_plotHover = new PlotHover { Name = "PlotHover", ZIndex = 3 };
				AddWorld(_plotHover);
			}
			// Respiration (geste armé) : son rythme propre, hors clé de survol.
			_plotHover.Modulate = new Color(1f, 1f, 1f, AlphaLosange());
			if (!_survolSale) return;   // position du losange inchangée (T3)
			Vector2 w = _sourisMonde;
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
		}

		/// <summary>Chaque frame : si le geste armé a changé, pose son icône sur la
		/// forme FormeGeste et en fait la forme par défaut (hors interface) ; sans
		/// geste (ou geste sans grille), la forme par défaut redevient la main.
		/// La texture vient du cache d'IconeGeste (×2, l'échelle de la main).</summary>
		private void SuivreGesteCurseur()
		{
			string verbe = _gesteIndex >= 0 && _gesteIndex < Gestes.Length ? Gestes[_gesteIndex].Verb : null;
			if (verbe == _curseurVerbe) return;   // rien n'a changé : on ne touche à rien
			_curseurVerbe = verbe;
			ImageTexture tex = IconeGeste.Texture(verbe, CurseurEchelle);
			if (tex == null || !IconesPointsChauds.PointsChauds.TryGetValue(verbe, out var p))
			{
				_curseurIcone = false;
				Input.SetDefaultCursorShape(Input.CursorShape.Arrow);
				return;
			}
			// Centre du pixel actif, en px écran : (X + ½) × échelle.
			_curseurIconeHotspot = new Vector2((p.X + 0.5f) * CurseurEchelle, (p.Y + 0.5f) * CurseurEchelle);
			_curseurIcone = true;
			Input.SetCustomMouseCursor(tex, FormeGeste, _curseurIconeHotspot);
			Input.SetDefaultCursorShape(FormeGeste);
		}

		// Respiration UNIQUEMENT geste armé ; sinon contour fixe et discret.
		private float AlphaLosange()
		{
			if (_gesteIndex < 0) return 0.8f;
			float t = Time.GetTicksMsec() / 1000f;
			return 0.55f + 0.45f * (0.5f + 0.5f * Mathf.Sin(t * Mathf.Tau / RespirationPeriodeS));
		}
	}
}
