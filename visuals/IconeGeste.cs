// SYMBIOSE — IconeGeste.cs (sprint ICÔNES & CURSEUR ① — moteur d'icônes)
// LA CUISSON DES ICÔNES DE GESTES : une icône est une GRILLE DE CARACTÈRES 16×16
// (un `string[]` de 16 lignes de 16 lettres), cuite UNE fois en texture puis
// réutilisée. Même patron que la main gantée du curseur (WorldView.Curseur.cs),
// qui passe désormais par ici.
//
// ALPHABET DE COULEURS — UNIQUE pour toutes les icônes (une lettre = une couleur
// de la palette maître `Palette16.Maitre`, jamais une couleur brute) :
//
//   .  transparent
//   K  contour            (ardoise nuit)      N  ombre            (ardoise moyenne)
//   M  métal sombre       (gris pierre)       S  métal clair      (granite chaud)
//   W  blanc              (chaux)             L  paille / toile   (crème)
//   B  bois sombre        (brun)              C  bois clair       (terre sèche)
//   T  terre / humus      (humus froid)       O  terre cuite      (argile orangée)
//   G  vert sombre        (feuillage)         V  vert clair       (pousse tendre)
//   E  eau                (bleu moyen)        A  eau claire       (reflet de ciel)
//   R  rouge              (accent fruit)      Y  jaune            (accent fleur)
//
// 16 lettres : c'est la CONTRAINTE qui fait la cohérence (une icône SNES tient en
// 4 à 6 couleurs ; toutes les icônes piochent dans le même petit nuancier). Les
// lettres K, W, S, Y sont celles de la main gantée : son rendu ne change pas.
// La SILHOUETTE d'un geste pressenti = la même grille, toutes lettres confondues
// en une seule teinte sombre (`TeinteSilhouette`).
//
// 📖 Pédagogie Godot/C# :
//  - `Image` est un tableau de pixels côté CPU ; `ImageTexture` en est la copie
//    côté carte graphique, celle qu'on dessine. On peint l'Image pixel par pixel
//    (256 pixels), on l'agrandit en `Nearest` (chaque pixel devient un carré net,
//    multiple ENTIER : pas de flou), puis on la téléverse une fois.
//  - CACHE : `Texture(verbe, échelle, silhouette)` ne cuit qu'au premier appel.
//    Un `_Draw` peut donc la demander à chaque redessin sans rien recalculer.
//  - LIBÉRATION explicite (`Liberer`, appelée à la sortie du jeu) : sans elle, le
//    ramasse-miettes C# finalise les textures APRÈS l'arrêt du moteur de rendu, et
//    Godot signale une fuite (constaté au banc VM sur la main gantée).
//
// Les grilles elles-mêmes vivent dans `visuals/icones/`, un fichier par famille
// de gestes (mêmes familles que le tiroir, `sim/actions/familles.py`).

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	internal static class IconeGeste
	{
		public const int Cote = 16;   // côté d'une grille, en pixels logiques

		// Lettre → rang dans Palette16.Maitre (rampes : verts 0-7, terre/bois 8-12,
		// argile 13-16, sable 17-19, pierre 20-25, blanc 26, eau 27-29, accents 30-33).
		private static readonly Dictionary<char, int> Alphabet = new()
		{
			['K'] = 20, ['N'] = 22, ['M'] = 23, ['S'] = 25,
			['W'] = 26, ['L'] = 18,
			['B'] = 9,  ['C'] = 11, ['T'] = 8,  ['O'] = 15,
			['G'] = 2,  ['V'] = 5,
			['E'] = 28, ['A'] = 29,
			['R'] = 30, ['Y'] = 31,
		};
		// Teinte unique des silhouettes : ardoise moyenne, lisible sur la plaque
		// sombre des cases (c'est le gris qu'avaient déjà les gestes pressentis).
		private static Color TeinteSilhouette => Palette16.Maitre[22];

		// REGISTRE : les familles dans l'ordre du tiroir, chacune son dictionnaire
		// verbe → grille. Une famille absente n'a pas encore d'icône (repli :
		// l'ancien dessin de GesteIcon). Complet depuis le tronçon ② (8 familles,
		// 46 gestes) : `Defauts` ci-dessous le vérifie à chaque démarrage en debug.
		public static readonly (string Nom, Dictionary<string, string[]> Grilles)[] Familles =
		{
			("main", IconesMain.Grilles),
			("sol", IconesSol.Grilles),
			("semis", IconesSemis.Grilles),
			("taille", IconesTaille.Grilles),
			("eau", IconesEau.Grilles),
			("compost", IconesCompost.Grilles),
			("structures", IconesStructures.Grilles),
			("paysage", IconesPaysage.Grilles),
		};

		private static readonly Dictionary<(string, int, bool), ImageTexture> _cache = new();

		/// <summary>Grille du geste, ou null si son icône n'est pas encore dessinée.</summary>
		public static string[] Grille(string verbe)
		{
			if (verbe == null) return null;
			foreach (var (_, grilles) in Familles)
				if (grilles.TryGetValue(verbe, out string[] g)) return g;
			return null;
		}

		public static bool Existe(string verbe) => Grille(verbe) != null;

		/// <summary>Texture de l'icône d'un geste (en cache), à `echelle` px écran par
		/// pixel logique ; `silhouette` = variante en une teinte. Null si le geste
		/// n'a pas de grille.</summary>
		public static ImageTexture Texture(string verbe, int echelle, bool silhouette = false)
		{
			if (verbe == null) return null;
			var cle = (verbe, echelle, silhouette);
			if (_cache.TryGetValue(cle, out ImageTexture tex)) return tex;
			string[] grille = Grille(verbe);
			if (grille == null) return null;
			tex = silhouette ? CuireSilhouette(grille, echelle) : Cuire(grille, echelle);
			_cache[cle] = tex;
			return tex;
		}

		/// <summary>Cuit une grille en couleurs. HORS cache : l'appelant possède la
		/// texture et la libère (cas de la main gantée).</summary>
		public static ImageTexture Cuire(string[] grille, int echelle) =>
			Peindre(grille, echelle, silhouette: false);

		/// <summary>Même forme, une seule teinte sombre (geste pressenti).</summary>
		public static ImageTexture CuireSilhouette(string[] grille, int echelle) =>
			Peindre(grille, echelle, silhouette: true);

		private static ImageTexture Peindre(string[] grille, int echelle, bool silhouette) =>
			ImageTexture.CreateFromImage(PeindreImage(grille, echelle, silhouette));

		/// <summary>La grille peinte en `Image` CPU, sans la téléverser (④ : les images
		/// d'animation du curseur sont données à l'OS sous cette forme — lui passer une
		/// texture l'obligerait à la relire depuis la carte graphique).</summary>
		public static Image PeindreImage(string[] grille, int echelle, bool silhouette = false)
		{
			var img = Image.CreateEmpty(Cote, Cote, false, Image.Format.Rgba8);
			for (int y = 0; y < Cote; y++)
				for (int x = 0; x < Cote; x++)
				{
					// Une grille mal formée (ligne courte, lettre hors alphabet) se
					// voit à la planche : le pixel reste transparent, sans planter.
					char c = y < grille.Length && x < grille[y].Length ? grille[y][x] : '.';
					if (!Alphabet.TryGetValue(c, out int rang)) continue;
					img.SetPixel(x, y, silhouette ? TeinteSilhouette : Palette16.Maitre[rang]);
				}
			img.Resize(Cote * echelle, Cote * echelle, Image.Interpolation.Nearest);
			return img;
		}

		/// <summary>VÉRIFICATION DE DÉMARRAGE (debug) : la liste des défauts du jeu
		/// d'icônes, vide si tout est en ordre. Contrôle que chaque verbe de
		/// `verbes` (la table `Gestes[]` de la vue) a sa grille, que chaque grille
		/// fait 16×16 dans l'alphabet, et qu'elle a un point chaud posé sur un pixel
		/// peint. Une grille fautive ne plante pas le jeu (pixel transparent) : sans
		/// ce contrôle, la faute ne se verrait qu'en regardant la planche.</summary>
		public static List<string> Defauts(IEnumerable<string> verbes)
		{
			var defauts = new List<string>();
			foreach (string verbe in verbes)
				if (!Existe(verbe)) defauts.Add($"{verbe} : aucune grille (repli sur l'ancien dessin)");
			foreach (var (_, grilles) in Familles)
				foreach (var (verbe, g) in grilles)
				{
					bool forme = g.Length == Cote;
					foreach (string ligne in g)
					{
						forme &= ligne.Length == Cote;
						foreach (char c in ligne)
							if (c != '.' && !Alphabet.ContainsKey(c))
								defauts.Add($"{verbe} : lettre '{c}' hors alphabet");
					}
					if (!forme) { defauts.Add($"{verbe} : grille qui n'est pas 16×16"); continue; }
					if (!IconesMouvements.Mouvements.ContainsKey(verbe))
						defauts.Add($"{verbe} : pas de mouvement d'animation (④)");
					if (AnimationGeste.Suite(verbe) == null)
						defauts.Add($"{verbe} : pas de suite d'images (GESTES LISIBLES ②)");
					if (!IconesPointsChauds.PointsChauds.TryGetValue(verbe, out var p))
						defauts.Add($"{verbe} : pas de point chaud");
					else if (p.X < 0 || p.X >= Cote || p.Y < 0 || p.Y >= Cote || g[p.Y][p.X] == '.')
						defauts.Add($"{verbe} : point chaud ({p.X}, {p.Y}) hors du dessin");
				}
			defauts.AddRange(AnimationGeste.DefautsSuites(verbes));
			return defauts;
		}

		/// <summary>Une grille 16×16 dont chaque lettre est dans l'alphabet (ou '.').</summary>
		public static bool Valide(string[] g)
		{
			if (g.Length != Cote) return false;
			foreach (string ligne in g)
			{
				if (ligne.Length != Cote) return false;
				foreach (char c in ligne)
					if (c != '.' && !Alphabet.ContainsKey(c)) return false;
			}
			return true;
		}

		/// <summary>Libère toutes les textures en cache (sortie du jeu).</summary>
		public static void Liberer()
		{
			foreach (ImageTexture tex in _cache.Values) tex.Dispose();
			_cache.Clear();
		}
	}
}
