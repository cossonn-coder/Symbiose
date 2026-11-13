// SYMBIOSE — AnimationGeste.cs (sprint ICÔNES & CURSEUR ④, GESTES LISIBLES ②)
//
// GESTES LISIBLES ② — chaque geste a désormais SA PROPRE SUITE de 4 à 6 images
// qui DÉCOMPOSE le mouvement (l'arrosoir se penche et l'eau coule, le pied monte
// haut puis retombe, la main se ferme sur la touffe et tire…). Les suites vivent
// dans `icones/Anims*.cs`, un fichier par famille (registre `Suites` ci-dessous) ;
// une image y est une `Etape` (`EtapeGeste.cs` : grille dessinée, ou icône
// tournée autour d'un pivot / décalée, plus des pixels d'effet). Les anciennes
// recettes par mouvement (ci-dessous) restent le REPLI d'un geste sans suite.
// Les mêmes images servent hors curseur (`TexturesMonde`, gestes de l'automate).
//
// --- en-tête d'origine (④) ---
// LES IMAGES D'ANIMATION du curseur-geste. Quand le pont répond « appliqué »,
// le curseur joue UNE FOIS 3 ou 4 images propres au MOUVEMENT du geste (table
// `icones/IconesMouvements.cs`) ; quand il refuse, une secousse de 2 images,
// commune à tous. Puis le curseur redevient l'icône immobile (animation =
// SIGNAL, jamais décor : rien ne bouge hors action).
//
// FABRICATION — pas de grilles dédiées : chaque image est l'icône du geste
// TRANSFORMÉE, selon une petite « recette » par mouvement. Une étape de recette
// (`Pas`) dit :
//   - de combien DÉCALER le dessin (Dx, Dy, en pixels de grille) ;
//   - de combien l'AVANCER vers sa cible (Avance) : la direction va du centre de
//     la grille vers le point chaud, si bien qu'un sécateur dont le bec est en
//     haut à gauche mord vers le haut à gauche, et une bêche dont la lame est en
//     bas frappe vers le bas — une seule recette sert à 12 outils différents ;
//   - quels PIXELS D'EFFET ajouter (gouttes, éclats, miettes de terre), placés
//     autour du point chaud. Un effet qui sortirait de la grille est reflété de
//     l'autre côté du point chaud (une bêche frappe au bord bas : sa terre gicle
//     vers le haut au lieu de disparaître). Un effet est peint DERRIÈRE le
//     dessin (seulement sur un pixel transparent) : une miette ne troue jamais la
//     lame d'une bêche. Seule exception, l'éclat de la coupe (`Devant`).
// Le POINT CHAUD NE BOUGE PAS : c'est le dessin qui bouge dessous. Le clic vise
// toujours le même pixel de l'écran pendant l'animation.
//
// 📖 Pédagogie Godot/C# :
//  - on garde chaque image sous DEUX formes : l'`Image` CPU, donnée à l'OS par
//    `Input.SetCustomMouseCursor` (lui passer une texture l'obligerait à la
//    relire depuis la carte graphique à chaque image), et l'`ImageTexture`,
//    seulement pour ce que Godot dessine lui-même (planche, témoin de capture) ;
//  - cache par (verbe, sorte, échelle) : un geste n'est cuit qu'à sa première
//    animation (≈ 4 × 256 pixels), jamais pendant qu'elle joue.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	internal static class AnimationGeste
	{
		/// <summary>Repos = l'icône immobile ; Tap = l'image d'un clic (instant, avant
		/// la réponse du pont) ; Execution = geste appliqué ; Refus = geste refusé.</summary>
		public enum Sorte { Repos, Tap, Execution, Refus }

		/// <summary>Une image du curseur : l'Image pour l'OS, la texture pour Godot.</summary>
		public readonly record struct ImageCurseur(Image Img, ImageTexture Tex);

		public const ulong DureeImageMs = 80;   // ≈ 12 images/s : lisible, bref

		// Une étape de recette (cf. en-tête). Effets = (x, y, lettre) autour du point
		// chaud, lettres de l'alphabet d'IconeGeste (donc couleurs de Palette16).
		private readonly record struct Pas(int Avance, int Dx, int Dy, bool Devant, (int X, int Y, char C)[] Effets);

		private static Pas P(int avance, int dx, int dy, params (int, int, char)[] effets) =>
			new(avance, dx, dy, false, effets);
		private static Pas Devant(int avance, int dx, int dy, params (int, int, char)[] effets) =>
			new(avance, dx, dy, true, effets);

		// LES RECETTES — 3 ou 4 images, jouées une fois, ~80 ms chacune.
		private static readonly Dictionary<Mouvement, Pas[]> Recettes = new()
		{
			// verser : l'arrosoir se soulève d'un pixel, un filet d'eau descend de la
			// pomme et éclabousse en touchant le sol (bas de la grille).
			[Mouvement.Verser] = new[]
			{
				P(0, 0, -1, (1, 3, 'A'), (2, 4, 'E')),
				P(0, 0, -1, (1, 5, 'A'), (2, 6, 'E'), (1, 7, 'A')),
				P(0, 0, 0, (1, 8, 'A'), (2, 9, 'E'), (4, 9, 'A')),
				P(0, 0, 0, (1, 10, 'W'), (3, 10, 'A'), (5, 10, 'W'), (2, 9, 'E')),
			},
			// couper : la lame recule (s'ouvre), mord (éclat blanc), un brin vert tombe.
			[Mouvement.Couper] = new[]
			{
				P(-1, 0, 0),
				Devant(1, 0, 0, (0, 0, 'W'), (-1, -1, 'Y'), (1, 1, 'Y')),
				P(0, 0, 0, (2, 2, 'V'), (2, 3, 'G')),
			},
			// frapper : l'outil se lève de deux pixels, frappe, la terre gicle.
			[Mouvement.Frapper] = new[]
			{
				P(-2, 0, 0),
				P(1, 0, 0, (-5, -1, 'T'), (5, -1, 'T'), (-4, 0, 'C'), (4, 0, 'C')),
				P(0, 0, 0, (-6, -3, 'C'), (6, -3, 'C'), (-5, -4, 'T'), (5, -5, 'T')),
			},
			// poser : l'objet descend, touche, un peu de poussière de chaque côté.
			[Mouvement.Poser] = new[]
			{
				P(0, 0, -3),
				P(0, 0, -1),
				P(0, 0, 0, (-7, 1, 'C'), (7, 1, 'C'), (-6, 1, 'C'), (6, 1, 'C')),
				P(0, 0, 0, (-8, 0, 'L'), (8, 0, 'L'), (-7, -1, 'C'), (7, -1, 'C')),
			},
			// ramasser : la main plonge d'un pixel, remonte, deux éclats au-dessus
			// (le langage du « tap » de la main gantée : `Y` aux coins hauts).
			[Mouvement.Ramasser] = new[]
			{
				P(0, 0, 1),
				P(0, 0, -1, (-4, -6, 'Y'), (4, -5, 'Y')),
				P(0, 0, -1, (-5, -7, 'W'), (5, -6, 'W')),
				P(0, 0, 0),
			},
			// remuer : un petit CERCLE (gauche, bas, droite, haut) — pas un va-et-vient,
			// qui se confondrait avec la secousse du refus —, des miettes de terre.
			[Mouvement.Remuer] = new[]
			{
				P(0, -1, 0, (-3, 1, 'T')),
				P(0, 0, 1, (3, 1, 'C')),
				P(0, 1, 0, (-2, 2, 'T'), (3, 0, 'T')),
				P(0, 0, -1),
			},
			// écraser : la botte se lève, retombe, la poussière s'écarte.
			[Mouvement.Ecraser] = new[]
			{
				P(0, 0, -2),
				P(0, 0, 1, (-4, 0, 'C'), (4, 0, 'C')),
				P(0, 0, 0, (-5, -1, 'T'), (5, -1, 'T')),
			},
		};

		// « Non » : secousse horizontale (±2 pixels de grille, GESTES LISIBLES ② —
		// ±1 se perdait à l'écran), aller-retour-aller, commune à tous.
		private static readonly Pas[] Refus = { P(0, -2, 0), P(0, 2, 0), P(0, -2, 0) };
		// Clic : l'outil appuie d'un pixel vers sa cible, le temps d'une image.
		private static readonly Pas[] Tap = { P(1, 0, 0) };
		private static readonly Pas[] Repos = { P(0, 0, 0) };

		// LES SUITES PAR GESTE (GESTES LISIBLES ②), une table par famille du tiroir.
		private static readonly Dictionary<string, Etape[]>[] Suites =
		{
			AnimsMain.Suites, AnimsSol.Suites, AnimsSemis.Suites, AnimsTaille.Suites,
			AnimsEau.Suites, AnimsCompost.Suites, AnimsStructures.Suites, AnimsPaysage.Suites,
		};

		/// <summary>La suite d'images propre au geste, ou null (repli : recette du mouvement).</summary>
		public static Etape[] Suite(string verbe)
		{
			if (verbe == null) return null;
			foreach (var table in Suites)
				if (table.TryGetValue(verbe, out Etape[] suite)) return suite;
			return null;
		}

		private static readonly Dictionary<(string, Sorte, int), ImageCurseur[]> _cache = new();

		/// <summary>Les images d'une sorte d'animation du geste, à `echelle` px écran
		/// par pixel de grille (en cache). Null si le geste n'a pas de grille, de
		/// point chaud ou (pour Execution) de mouvement.</summary>
		public static ImageCurseur[] Images(string verbe, Sorte sorte, int echelle)
		{
			if (verbe == null) return null;
			var cle = (verbe, sorte, echelle);
			if (_cache.TryGetValue(cle, out ImageCurseur[] images)) return images;
			string[] grille = IconeGeste.Grille(verbe);
			Etape[] suite = sorte == Sorte.Execution ? Suite(verbe) : null;
			if (grille != null && suite != null)   // la suite propre au geste
			{
				images = new ImageCurseur[suite.Length];
				for (int i = 0; i < suite.Length; i++)
					images[i] = Cuire(EtapeGeste.Appliquer(grille, suite[i]), echelle);
				_cache[cle] = images;
				return images;
			}
			Pas[] recette = Recette(verbe, sorte);
			if (recette == null || grille == null
				|| !IconesPointsChauds.PointsChauds.TryGetValue(verbe, out var chaud)) return null;
			images = new ImageCurseur[recette.Length];
			for (int i = 0; i < recette.Length; i++)
				images[i] = Cuire(Transformer(grille, chaud, recette[i]), echelle);
			_cache[cle] = images;
			return images;
		}

		private static ImageCurseur Cuire(string[] grille, int echelle)
		{
			Image img = IconeGeste.PeindreImage(grille, echelle);
			return new ImageCurseur(img, ImageTexture.CreateFromImage(img));
		}

		/// <summary>USAGE HORS CURSEUR (GESTES LISIBLES ②, branché au ⑤ : gestes de
		/// l'automate joués comme un sprite du MONDE au point visé) : les images
		/// d'exécution du geste en textures, à `echelle` px par pixel de grille. Même
		/// cache que le curseur ; ne pas les libérer soi-même. Null sans icône.</summary>
		public static Texture2D[] TexturesMonde(string verbe, int echelle)
		{
			ImageCurseur[] images = Images(verbe, Sorte.Execution, echelle);
			if (images == null) return null;
			var textures = new Texture2D[images.Length];
			for (int i = 0; i < images.Length; i++) textures[i] = images[i].Tex;
			return textures;
		}

		/// <summary>VÉRIFICATION (appelée par `IconeGeste.Defauts`, qui signale déjà un
		/// geste sans suite) : chaque suite a 4 à 6 images, chaque grille dessinée est 16×16 dans l'alphabet
		/// (contrôlé par `IconeGeste.Valide`), chaque effet tombe dans la grille.</summary>
		public static List<string> DefautsSuites(IEnumerable<string> verbes)
		{
			var defauts = new List<string>();
			foreach (string verbe in verbes)
			{
				Etape[] suite = Suite(verbe);
				if (suite == null) continue;   // déjà signalé, grille par grille, par IconeGeste.Defauts
				if (suite.Length < 4 || suite.Length > 6)
					defauts.Add($"{verbe} : {suite.Length} images (4 à 6 attendues)");
				foreach (Etape e in suite)
				{
					if (e.Grille != null && !IconeGeste.Valide(e.Grille))
						defauts.Add($"{verbe} : grille d'animation mal formée");
					foreach (var (x, y, _) in e.Effets)
						if (x < 0 || x >= IconeGeste.Cote || y < 0 || y >= IconeGeste.Cote)
							defauts.Add($"{verbe} : effet ({x}, {y}) hors de la grille");
				}
			}
			return defauts;
		}

		private static Pas[] Recette(string verbe, Sorte sorte) => sorte switch
		{
			Sorte.Repos => Repos,
			Sorte.Tap => Tap,
			Sorte.Refus => Refus,
			_ => IconesMouvements.Mouvements.TryGetValue(verbe, out Mouvement m) ? Recettes[m] : null,
		};

		/// <summary>Le nom du mouvement d'un geste, pour le journal de la planche.</summary>
		public static string NomMouvement(string verbe) =>
			IconesMouvements.Mouvements.TryGetValue(verbe, out Mouvement m) ? m.ToString() : "?";

		// Applique une étape à la grille : décalage du dessin, puis effets par-dessus.
		private static string[] Transformer(string[] grille, (int X, int Y) chaud, Pas pas)
		{
			int c = IconeGeste.Cote;
			// Direction de la cible : composante −1, 0 ou +1 selon que le point chaud
			// est franchement d'un côté du centre (7,5) ou près de l'axe (objet posé :
			// point chaud au milieu de la base → on avance vers le bas, tout droit).
			int dirX = Direction(chaud.X), dirY = Direction(chaud.Y);
			int dx = pas.Dx + pas.Avance * dirX, dy = pas.Dy + pas.Avance * dirY;
			var lignes = new char[c][];
			for (int y = 0; y < c; y++)
			{
				lignes[y] = new char[c];
				for (int x = 0; x < c; x++)
				{
					int sx = x - dx, sy = y - dy;   // pixel source : ce qui sort du cadre est perdu
					lignes[y][x] = sx >= 0 && sx < c && sy >= 0 && sy < c && sx < grille[sy].Length
						? grille[sy][sx] : '.';
				}
			}
			foreach (var (ex, ey, lettre) in pas.Effets)
			{
				int x = Reflet(chaud.X, ex), y = Reflet(chaud.Y, ey);
				if (pas.Devant || lignes[y][x] == '.') lignes[y][x] = lettre;   // derrière le dessin
			}
			var sortie = new string[c];
			for (int y = 0; y < c; y++) sortie[y] = new string(lignes[y]);
			return sortie;
		}

		private static int Direction(int v)
		{
			float ecart = v - (IconeGeste.Cote - 1) / 2f;
			return ecart > 2.5f ? 1 : ecart < -2.5f ? -1 : 0;
		}

		// Coordonnée d'un effet : point chaud + écart, reflété s'il sort de la grille,
		// puis bornée (un écart plus grand que la grille entière reste au bord).
		private static int Reflet(int chaud, int ecart)
		{
			int v = chaud + ecart;
			if (v < 0 || v >= IconeGeste.Cote) v = chaud - ecart;
			return Mathf.Clamp(v, 0, IconeGeste.Cote - 1);
		}

		/// <summary>Libère toutes les images en cache (sortie du jeu).</summary>
		public static void Liberer()
		{
			foreach (ImageCurseur[] images in _cache.Values)
				foreach (ImageCurseur im in images) { im.Tex.Dispose(); im.Img.Dispose(); }
			_cache.Clear();
		}
	}
}
