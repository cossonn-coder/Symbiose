// SYMBIOSE — icones/AnimsCompost.cs (sprint GESTES LISIBLES ② — données, famille « compost »)
// LES SUITES D'IMAGES des gestes de la famille COMPOST (format : en-tête de
// `AnimsEau.cs` et de `visuals/EtapeGeste.cs`). Fichier de DONNÉES : aucune
// logique. Planche de contrôle : `tools/capture_vm.sh -W`.

using System.Collections.Generic;
using static Symbiose.EtapeGeste;

namespace Symbiose
{
	internal static class AnimsCompost
	{
		// Une bûche de 6 × 3 pixels (bout clair à gauche) dont le coin haut-gauche
		// est en (x, y) : les pixels d'effet d'une image où elle tombe.
		private static (int, int, char)[] Buche(int x, int y) => new[]
		{
			(x + 1, y, 'K'), (x + 2, y, 'K'), (x + 3, y, 'K'), (x + 4, y, 'K'),
			(x, y + 1, 'K'), (x + 1, y + 1, 'L'), (x + 2, y + 1, 'C'), (x + 3, y + 1, 'C'),
			(x + 4, y + 1, 'C'), (x + 5, y + 1, 'K'),
			(x + 1, y + 2, 'K'), (x + 2, y + 2, 'K'), (x + 3, y + 2, 'K'), (x + 4, y + 2, 'K'),
		};

		private static (int, int, char)[] Et((int, int, char)[] a, params (int, int, char)[] b)
		{
			var tout = new (int, int, char)[a.Length + b.Length];
			a.CopyTo(tout, 0);
			b.CopyTo(tout, a.Length);
			return tout;
		}

		public static readonly Dictionary<string, Etape[]> Suites = new()
		{
			// Le bac et la pile descendent et touchent le sol (patron commun).
			["poser_bac"] = Poser(14),
			["poser_pile"] = Poser(14),
			// Une feuille tombe sur le tas, il se tasse, la VAPEUR monte : le compost chauffe.
			["composter"] = new[]
			{
				T(0, 0, (7, 0, 'V'), (8, 0, 'G')),
				T(0, 0, (9, 2, 'V'), (10, 2, 'G')),
				T(0, 1, (3, 6, 'T'), (12, 5, 'T')),
				T(0, 0, (6, 2, 'W'), (10, 1, 'W')),
				T(0, 0, (5, 0, 'W'), (11, 0, 'W'), (8, 1, 'L')),
			},
			// La fourche-bêche s'enfonce, soulève une MOTTE herbe dessus, la motte
			// se RETOURNE en l'air (herbe dessous) et retombe à l'envers.
			// (Pas de rotation de l'outil : la fourche tournée se brouillait.)
			["retourner"] = new[]
			{
				T(0, -3),
				T(0, 1, (4, 15, 'T'), (10, 15, 'T')),
				T(0, -1, (12, 11, 'G'), (13, 11, 'G'), (14, 11, 'G'), (12, 12, 'T'), (13, 12, 'T'), (14, 12, 'T')).Dessus(),
				T(0, -2, (12, 6, 'T'), (13, 6, 'T'), (14, 6, 'T'), (12, 7, 'G'), (13, 7, 'G'), (14, 7, 'G')).Dessus(),
				T(0, 0, (13, 14, 'T'), (14, 14, 'T'), (15, 14, 'T'), (13, 15, 'G'), (14, 15, 'G'), (15, 15, 'G')).Dessus(),
			},
			// La brouette bascule sur sa roue (les bras se lèvent) : le chargement
			// coule par l'avant et s'étale.
			["epandre"] = new[]
			{
				R(-10, 2, 13, 0, 0),
				R(-20, 2, 13, 0, 0, (1, 5, 'T'), (0, 7, 'B')),
				R(-25, 2, 13, 0, 0, (0, 8, 'T'), (1, 10, 'B'), (0, 11, 'T')),
				R(-12, 2, 13, 0, 0, (5, 15, 'T'), (6, 15, 'B'), (0, 12, 'T')),
				T(0, 0, (5, 15, 'T'), (6, 15, 'B'), (7, 15, 'T'), (8, 15, 'T')),
			},
			// Une bûche tombe sur la pile, la pile se tasse, quelques éclats d'écorce.
			["empiler_bois"] = new[]
			{
				T(0, 0, Buche(2, 0)),
				T(0, 0, Buche(2, 2)),
				T(0, 0, Buche(2, 4)),
				T(0, 1, Buche(2, 5)).Dessus(),
				T(0, 0, Et(Buche(2, 4), (0, 3, 'C'), (9, 2, 'L'))).Dessus(),
			},
			// La botte de paille saute, les brins volent et retombent au sol de chaque
			// côté (pas de rotation : la paille tournée s'émiettait, vu à la planche).
			["pailler"] = new[]
			{
				T(0, -3),
				T(0, -2, (1, 9, 'L'), (14, 8, 'Y'), (2, 6, 'Y'), (13, 5, 'L')),
				T(0, 0, (0, 11, 'Y'), (15, 11, 'L'), (1, 9, 'L'), (14, 8, 'Y')),
				T(0, 1, (0, 15, 'L'), (14, 15, 'Y'), (1, 14, 'Y'), (15, 15, 'L')),
				T(0, 0, (0, 15, 'L'), (2, 15, 'Y'), (13, 15, 'L'), (15, 15, 'L')),
			},
			// Une branche entre dans la trémie, la machine vibre, les copeaux jaillissent.
			["broyer"] = new[]
			{
				T(0, 0, (3, 0, 'G'), (4, 0, 'B')),
				T(0, 1, (14, 4, 'C'), (15, 5, 'L')),
				T(0, 0, (13, 3, 'C'), (15, 2, 'L'), (14, 5, 'C')),
				T(0, 1, (15, 1, 'C'), (12, 2, 'L'), (13, 4, 'C')),
				T(0, 0, (15, 0, 'C'), (14, 2, 'L')),
			},
		};
	}
}
