// SYMBIOSE — icones/AnimsSol.cs (sprint GESTES LISIBLES ② — données, famille « sol »)
// LES SUITES D'IMAGES des gestes de la famille SOL (format : en-tête de
// `AnimsEau.cs` et de `visuals/EtapeGeste.cs`). Fichier de DONNÉES : aucune
// logique. Planche de contrôle : `tools/capture_vm.sh -W`.

using System.Collections.Generic;
using static Symbiose.EtapeGeste;

namespace Symbiose
{
	internal static class AnimsSol
	{
		public static readonly Dictionary<string, Etape[]> Suites = new()
		{
			// La bêche s'arme, s'enfonce, la terre gicle, puis le manche bascule en
			// levier : la motte est soulevée.
			["becher"] = new[]
			{
				T(0, -2),
				T(0, -5),
				T(0, 1, (5, 15, 'C'), (10, 15, 'C')),
				T(0, 1, (3, 14, 'T'), (11, 14, 'T'), (2, 13, 'C'), (12, 13, 'C')),
				R(-20, 7, 15, 0, 0, (2, 12, 'T'), (12, 11, 'T'), (13, 13, 'C')),
			},
			// Les dents s'enfoncent, l'outil se soulève par à-coups : la terre se FEND et
			// se soulève sans se retourner (elle est aérée). Pas de rotation : la
			// grelinette, ajourée, se brouillait en tournant.
			["grelinette"] = new[]
			{
				T(0, -3),
				T(0, 0),
				T(0, 1, (4, 15, 'T'), (8, 15, 'T'), (12, 15, 'T')),
				T(0, -1, (4, 14, 'T'), (8, 13, 'C'), (12, 14, 'T'), (3, 15, 'C'), (13, 15, 'C')),
				T(0, 0, (4, 15, 'C'), (8, 15, 'T'), (12, 15, 'C'), (0, 13, 'T'), (15, 13, 'T')),
			},
			// La pelle s'arme, pique, se relève chargée, jette la terre sur le tas.
			["creuser"] = new[]
			{
				T(2, -3),
				T(-1, 1, (1, 15, 'T'), (6, 15, 'T')),
				R(20, 4, 13, 0, 0, (2, 10, 'T'), (3, 9, 'T'), (4, 10, 'C')),
				R(30, 4, 13, 0, -1, (8, 4, 'T'), (10, 3, 'C'), (9, 2, 'T')),
				T(0, 0, (11, 10, 'T'), (13, 9, 'C'), (14, 10, 'T')),
			},
			// L'eau dévale le drain (un reflet descend) et s'étale au sol, vers la gauche.
			["drainer"] = new[]
			{
				T(0, 0, (12, 7, 'W'), (8, 14, 'A')).Dessus(),
				T(0, 0, (12, 9, 'W'), (7, 14, 'E'), (8, 15, 'A')).Dessus(),
				T(0, 0, (13, 11, 'W'), (4, 15, 'A'), (5, 14, 'E'), (7, 15, 'E')).Dessus(),
				T(0, 0, (12, 12, 'W'), (1, 15, 'A'), (2, 14, 'E'), (4, 15, 'E'), (6, 15, 'A')).Dessus(),
				T(0, 0, (13, 13, 'W'), (0, 15, 'E'), (2, 15, 'A'), (5, 15, 'E')).Dessus(),
			},
			// Traction vers le haut : la plantule monte de 6 pixels, la MOTTE suit en
			// se balançant au bout des racines, des miettes de terre retombent.
			["deraciner"] = new[]
			{
				T(0, -2),
				T(0, -4, (5, 15, 'T'), (9, 15, 'T')),
				T(0, -6, (4, 14, 'T'), (10, 15, 'C'), (7, 15, 'T')),
				R(10, 7, 0, 0, -6, (3, 15, 'T'), (11, 14, 'T')),
				R(-6, 7, 0, 0, -5, (5, 15, 'C'), (12, 15, 'T')),
			},
		};
	}
}
