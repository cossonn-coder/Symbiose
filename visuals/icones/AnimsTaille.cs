// SYMBIOSE — icones/AnimsTaille.cs (sprint GESTES LISIBLES ② — données, famille « taille »)
// LES SUITES D'IMAGES des gestes de la famille TAILLE (format : en-tête de
// `AnimsEau.cs` et de `visuals/EtapeGeste.cs`). Fichier de DONNÉES : aucune
// logique. Planche de contrôle : `tools/capture_vm.sh -W`.
// Deux grilles DESSINÉES : le sécateur OUVERT (la contre-lame s'écarte) et la main
// ouverte qui approche de la touffe avant de l'empoigner.

using System.Collections.Generic;
using static Symbiose.EtapeGeste;

namespace Symbiose
{
	internal static class AnimsTaille
	{
		// Sécateur (icône de `tailler`) mâchoires ouvertes : la contre-lame part à
		// gauche du rivet, en V avec le bec.
		private static readonly string[] SecateurOuvert =
		{
			"................",
			".KK.............",
			".KSKK...........",
			"..KSSKK.........",
			"..KMSSSK........",
			"...KMSSSK.......",
			"....KKMSSK......",
			".KKKKKKYYKKK....",
			"KMMMMMKYYRRRKK..",
			".KKKKKRRKKRRRRK.",
			".....KRRK.KKRRK.",
			"....KRRK....KK..",
			"....KRRK........",
			"...KRRK.........",
			"...KRK..........",
			"....K...........",
		};
		// La touffe plantée en terre, la main gantée ouverte arrive par la droite.
		private static readonly string[] TouffeMainOuverte =
		{
			"................",
			"..KK.KKK..KK....",
			".KVVKVVVKKVVK...",
			".KVVVKVVKVVGK...",
			"..KVVKVGKVGK....",
			"...KKVVGGKK.....",
			".....KVGK..KKKK.",
			".....KVGK.KWWWWK",
			".....KVGKKWWKKKK",
			".....KVGKKWWWWWK",
			".....KVGK.KWWKKK",
			".....KVGK.KWWWWK",
			".....KVGK..KKKCK",
			".TTTTKVGKTTTKBCK",
			"TTTTTTKKTTTTTKKK",
			"................",
		};

		public static readonly Dictionary<string, Etape[]> Suites = new()
		{
			// Les doigts se serrent (éclat), tirent vers le haut : le bourgeon pincé
			// se détache et tombe à terre.
			["pincer"] = new[]
			{
				T(0, 1, (1, 4, 'Y'), (1, 7, 'Y')),
				T(0, -2, (1, 7, 'V'), (1, 8, 'G')).Dessus(),
				T(0, -2, (3, 3, 'K'), (4, 3, 'K'), (0, 10, 'V'), (1, 11, 'G')).Dessus(),
				T(0, 0, (3, 5, 'K'), (4, 5, 'K'), (1, 14, 'V'), (2, 15, 'G')).Dessus(),
				T(0, 0, (2, 15, 'G'), (3, 15, 'V')),
			},
			// La main ouverte arrive, se FERME sur la touffe, tire : la touffe sort
			// avec ses racines, des mottes retombent.
			["arracher"] = new[]
			{
				D(TouffeMainOuverte, 0, 0),
				T(0, 0, (1, 14, 'T'), (2, 14, 'T'), (10, 14, 'T'), (11, 14, 'T')),
				T(0, -2, (3, 15, 'T'), (9, 15, 'T'), (1, 14, 'T')),
				T(0, -4, (4, 13, 'T'), (9, 14, 'T'), (6, 15, 'C')),
				T(0, -5, (3, 15, 'T'), (10, 15, 'T'), (7, 14, 'C')),
			},
			// La scie (icône de `couper`) va et vient le long de sa lame, la sciure tombe.
			["couper"] = new[]
			{
				T(2, 2),
				T(-1, -1, (1, 5, 'C'), (2, 7, 'L')),
				T(2, 2, (0, 8, 'C'), (2, 9, 'L'), (1, 6, 'C')),
				T(-1, -1, (1, 11, 'C'), (0, 13, 'L'), (2, 10, 'C')),
				T(0, 0, (1, 15, 'C'), (3, 15, 'L'), (0, 14, 'C')),
			},
			// Le sécateur (icône de `tailler`) s'ouvre sur un rameau, se ferme (éclat
			// au bec), le bout coupé tombe.
			["tailler"] = new[]
			{
				D(SecateurOuvert, 0, 0),
				D(SecateurOuvert, 0, 0, (0, 6, 'G'), (1, 6, 'G'), (2, 6, 'V'), (3, 6, 'G')),
				T(0, 0, (0, 0, 'Y'), (3, 0, 'W'), (0, 3, 'W'), (0, 6, 'G'), (1, 7, 'V')).Dessus(),
				T(0, 0, (1, 9, 'G'), (2, 10, 'V')),
				T(0, 0, (1, 13, 'V'), (2, 14, 'G')),
			},
		};
	}
}
