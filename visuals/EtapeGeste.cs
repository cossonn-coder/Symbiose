// SYMBIOSE — EtapeGeste.cs (sprint GESTES LISIBLES ② — images qui décomposent un geste)
// UNE IMAGE D'ANIMATION d'un geste, décrite comme une ÉTAPE appliquée à l'icône :
//   - source : l'icône du geste, OU une GRILLE DESSINÉE 16×16 (même alphabet
//     qu'`IconeGeste`) pour les poses impossibles par transformation — la main
//     ouverte avant de saisir une touffe, la coccinelle ailes ouvertes ;
//   - ROTATION autour d'un PIVOT (en degrés, positif = sens des aiguilles d'une
//     montre à l'écran) : l'arrosoir se penche, la hache s'arme puis frappe ;
//   - DÉCALAGE (Dx, Dy, en pixels de grille) : le pied monte haut puis retombe ;
//   - PIXELS D'EFFET aux coordonnées ABSOLUES de la grille finale (gouttes, mottes,
//     éclats), peints DERRIÈRE le dessin (seulement sur un pixel transparent), sauf
//     si l'étape est marquée `Dessus()` : alors ils recouvrent le dessin, et la
//     lettre '.' y EFFACE un pixel (la morsure qui s'agrandit).
// Le point chaud du curseur ne bouge jamais : c'est le dessin qui bouge dessous.
//
// 📖 Pédagogie C# :
//  - `record struct` = une petite valeur immuable avec égalité par contenu ;
//    `this with { Devant = true }` en fabrique une copie modifiée sans muter.
//  - ROTATION « à l'envers » : pour chaque pixel de DESTINATION on cherche le
//    pixel SOURCE qui y atterrit (rotation inverse), au voisin le plus proche.
//    Faire l'inverse (pousser chaque source vers sa destination) laisserait des
//    TROUS dans le dessin tourné. Aucun aléa : même étape, mêmes pixels.
//  - `using static Symbiose.EtapeGeste;` dans les fichiers de données permet
//    d'écrire `T(0, -3)` au lieu de `EtapeGeste.T(0, -3)`.

using System;

namespace Symbiose
{
	/// <summary>Une image d'animation : source (null = l'icône), rotation, décalage, effets.</summary>
	internal readonly record struct Etape(string[] Grille, float Angle, float PivotX, float PivotY,
		int Dx, int Dy, bool Devant, (int X, int Y, char C)[] Effets)
	{
		/// <summary>Même étape, effets peints PAR-DESSUS le dessin ('.' efface).</summary>
		public Etape Dessus() => this with { Devant = true };
	}

	internal static class EtapeGeste
	{
		// ── Fabriques (vocabulaire des fichiers de données `icones/Anims*.cs`) ──

		/// <summary>L'icône décalée de (dx, dy), plus des effets.</summary>
		public static Etape T(int dx, int dy, params (int, int, char)[] effets) =>
			new(null, 0f, 0f, 0f, dx, dy, false, effets);

		/// <summary>L'icône tournée de `angle` degrés autour du pixel (px, py), puis décalée.</summary>
		public static Etape R(float angle, float px, float py, int dx, int dy, params (int, int, char)[] effets) =>
			new(null, angle, px, py, dx, dy, false, effets);

		/// <summary>Une grille dessinée à la place de l'icône, décalée de (dx, dy).</summary>
		public static Etape D(string[] grille, int dx, int dy, params (int, int, char)[] effets) =>
			new(grille, 0f, 0f, 0f, dx, dy, false, effets);

		/// <summary>Le patron « l'objet descend de haut et touche le sol » : chute de
		/// 6 puis 3 pixels, tassement d'un pixel, poussière qui s'écarte sur la ligne
		/// `bas` (le pied de l'objet). Partagé par tout ce qu'on POSE.</summary>
		public static Etape[] Poser(int bas) => new[]
		{
			T(0, -6),
			T(0, -3),
			T(0, 1, (2, bas, 'C'), (13, bas, 'C'), (1, bas - 1, 'L'), (14, bas - 1, 'L')),
			T(0, 0, (0, bas - 1, 'C'), (15, bas - 1, 'C'), (1, bas - 3, 'L'), (14, bas - 3, 'L')),
		};

		/// <summary>Une suite partagée (ex. `Poser`) prolongée d'images propres au geste.</summary>
		public static Etape[] Puis(Etape[] debut, params Etape[] fin)
		{
			var tout = new Etape[debut.Length + fin.Length];
			debut.CopyTo(tout, 0);
			fin.CopyTo(tout, debut.Length);
			return tout;
		}

		// ── Application ──

		/// <summary>L'image (grille de lettres) d'une étape appliquée à l'icône.</summary>
		public static string[] Appliquer(string[] icone, Etape e)
		{
			int c = IconeGeste.Cote;
			string[] src = e.Grille ?? icone;
			double rad = e.Angle * Math.PI / 180.0, cos = Math.Cos(rad), sin = Math.Sin(rad);
			double cx = e.PivotX + 0.5, cy = e.PivotY + 0.5;   // centre du pixel pivot
			var lignes = new char[c][];
			bool tourne = e.Angle != 0f;
			for (int y = 0; y < c; y++)
			{
				lignes[y] = new char[c];
				for (int x = 0; x < c; x++)
				{
					if (!tourne) { lignes[y][x] = Lire(src, x - e.Dx, y - e.Dy); continue; }
					// On défait le décalage, puis la rotation (inverse) : d'où vient ce pixel ?
					lignes[y][x] = Voter(src, x - e.Dx, y - e.Dy, cx, cy, cos, sin);
				}
			}
			foreach (var (ex, ey, lettre) in e.Effets)
			{
				if (ex < 0 || ex >= c || ey < 0 || ey >= c) continue;   // signalé par Defauts
				if (e.Devant || lignes[ey][ex] == '.') lignes[ey][ex] = lettre;
			}
			var sortie = new string[c];
			for (int y = 0; y < c; y++) sortie[y] = new string(lignes[y]);
			return sortie;
		}

		// Un pixel tourné : au lieu d'un seul point source (voisin le plus proche, qui
		// dédouble ou casse les contours à 20-40°), on lit 4 × 4 points répartis dans
		// le pixel et on garde la lettre LA PLUS FRÉQUENTE (le contour `K` pèse 1,5 :
		// un trait d'un pixel ne doit pas s'évaporer ; à 2 il noircissait tout,
		// constaté à la planche). Égalité : la première lettre rencontrée (ordre
		// fixe → déterministe).
		private const int Sous = 4;
		private static char Voter(string[] src, int x, int y, double cx, double cy, double cos, double sin)
		{
			Span<char> lettres = stackalloc char[Sous * Sous];
			Span<int> poids = stackalloc int[Sous * Sous];
			int n = 0;
			for (int j = 0; j < Sous; j++)
				for (int i = 0; i < Sous; i++)
				{
					double vx = x + (i + 0.5) / Sous - cx, vy = y + (j + 0.5) / Sous - cy;
					char l = Lire(src, (int)Math.Floor(cos * vx + sin * vy + cx),
						(int)Math.Floor(-sin * vx + cos * vy + cy));
					int k = 0;
					while (k < n && lettres[k] != l) k++;
					if (k == n) { lettres[n] = l; poids[n] = 0; n++; }
					poids[k] += l == 'K' ? 3 : 2;
				}
			int meilleur = 0;
			for (int k = 1; k < n; k++) if (poids[k] > poids[meilleur]) meilleur = k;
			return lettres[meilleur];
		}

		// Ce qui sort du cadre (ou d'une ligne courte) est transparent.
		private static char Lire(string[] g, int x, int y) =>
			y >= 0 && y < g.Length && x >= 0 && x < g[y].Length ? g[y][x] : '.';
	}
}
