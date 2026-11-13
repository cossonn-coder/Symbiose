// SYMBIOSE — icones/AnimsMain.cs (sprint GESTES LISIBLES ② — données, famille « main »)
// LES SUITES D'IMAGES des gestes de la famille MAIN (format : en-tête de
// `AnimsEau.cs` et de `visuals/EtapeGeste.cs`). Fichier de DONNÉES : aucune
// logique. Planche de contrôle : `tools/capture_vm.sh -W`.
// Deux grilles DESSINÉES ici : la coccinelle ailes mi-ouvertes et ouvertes (une
// aile qui s'ouvre ne s'obtient pas en tournant l'icône).

using System.Collections.Generic;
using static Symbiose.EtapeGeste;

namespace Symbiose
{
	internal static class AnimsMain
	{
		// Coccinelle : élytres qui s'écartent, ailes claires qui pointent dessous.
		private static readonly string[] CoccinelleMiOuverte =
		{
			"................",
			"................",
			".....KK..KK.....",
			"......K..K......",
			".....KKKKKK.....",
			"...KKKNKKNKKK...",
			"..KRRRKKKKRRRK..",
			".KRWRRKNNKRRRRK.",
			".KRRKRKNNKRKRRK.",
			".KRRRRKNNKRRRRK.",
			".KRRRRKNNKRKRRK.",
			"..KRKRKKKKRRRK..",
			".KKKKKKAAKKKKKK.",
			".KVVVKAAAAKVVGK.",
			"..KKVVVVVVVGKK..",
			"....KKKKKKKK....",
		};
		// Élytres levés en V, ailes membraneuses déployées de chaque côté.
		private static readonly string[] CoccinelleOuverte =
		{
			"................",
			"KK...KK..KK...KK",
			"KRK...K..K...KRK",
			"KRRK.KKKKKK.KRRK",
			".KRRKKNKKNKKRRK.",
			".KRWRKKNNKKRRRK.",
			"..KRRKKNNKKRKK..",
			"..KKKAKNNKAKK...",
			".KAAWAKNNKAWAAK.",
			"KAAWAAKNNKAAWAAK",
			"KAWAAKKNNKKAAWAK",
			".KKKK.KKKK.KKKK.",
			".KKKK..KK..KKKK.",
			".KVVVKKKKKKVVGK.",
			"..KKVVVVVVVGKK..",
			"....KKKKKKKK....",
		};

		public static readonly Dictionary<string, Etape[]> Suites = new()
		{
			// Le panier se lève, plonge, un fruit tombe dedans, deux éclats : c'est cueilli.
			["recolter"] = new[]
			{
				T(0, -2),
				T(0, 3),
				T(0, 3, (8, 0, 'R'), (9, 0, 'R'), (8, 1, 'R'), (9, 1, 'R')),
				T(0, 2, (8, 3, 'R'), (9, 3, 'R'), (8, 4, 'R'), (9, 4, 'R')),
				T(0, 0, (3, 0, 'Y'), (12, 0, 'Y'), (2, 2, 'W'), (13, 2, 'W')),
			},
			// La pomme monte vers la bouche (en haut à droite), croc : des miettes de
			// chair volent puis retombent.
			["manger"] = new[]
			{
				T(0, -2),
				T(1, -4),
				T(1, -4, (13, 1, 'L'), (14, 3, 'L'), (12, 0, 'R')),
				T(0, -2, (14, 6, 'L'), (13, 9, 'L'), (15, 4, 'R')),
				T(0, 0, (14, 13, 'L'), (12, 15, 'L')),
			},
			// Des feuilles quittent le tas et montent vers la main, qui se referme
			// (éclats) : on ramasse la litière par terre.
			["glaner"] = new[]
			{
				T(0, -1),
				T(0, 0, (3, 11, 'O'), (4, 11, 'Y')),
				T(0, 0, (3, 9, 'Y'), (4, 10, 'O'), (13, 10, 'O')),
				T(0, 0, (4, 8, 'O'), (3, 7, 'Y'), (13, 8, 'Y')),
				T(0, -1, (12, 4, 'Y'), (13, 3, 'W'), (2, 1, 'Y')),
			},
			// Le pied monte HAUT (6 pixels), retombe franchement, la poussière s'écarte.
			["ecraser"] = new[]
			{
				T(0, -3),
				T(0, -6),
				T(0, -2),
				T(0, 1, (1, 13, 'C'), (14, 13, 'C'), (0, 12, 'T'), (15, 12, 'T')),
				T(0, 0, (0, 11, 'C'), (15, 11, 'C'), (1, 14, 'T'), (14, 14, 'T'), (0, 15, 'C'), (15, 15, 'C')),
			},
			// La coccinelle entrouvre ses élytres, déploie ses ailes (deux images, des
			// éclats : elle est bien accueillie), puis les replie.
			["favoriser_auxiliaire"] = new[]
			{
				D(CoccinelleMiOuverte, 0, 0),
				D(CoccinelleOuverte, 0, 0),
				D(CoccinelleOuverte, 0, 0, (2, 0, 'Y'), (13, 0, 'Y')),
				D(CoccinelleMiOuverte, 0, 0, (0, 3, 'W'), (15, 4, 'W')),
				T(0, 0),
			},
		};
	}
}
