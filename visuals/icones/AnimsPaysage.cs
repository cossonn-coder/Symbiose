// SYMBIOSE — icones/AnimsPaysage.cs (sprint GESTES LISIBLES ② — données, famille « paysage »)
// LES SUITES D'IMAGES des gestes de la famille PAYSAGE (format : en-tête de
// `AnimsEau.cs` et de `visuals/EtapeGeste.cs`). Fichier de DONNÉES : aucune
// logique. Planche de contrôle : `tools/capture_vm.sh -W`.
// Les outils qu'on BALANCE (hache, serpe, pioche) tournent autour du bas de leur
// manche : ils s'arment (rotation en arrière), puis frappent (rotation en avant).

using System.Collections.Generic;
using static Symbiose.EtapeGeste;

namespace Symbiose
{
	internal static class AnimsPaysage
	{
		// La trogne sans ses rejets : coupe fraîche (crème) au sommet du tronc.
		private static readonly string[] TrogneNue =
		{
			"................",
			"................",
			"................",
			"................",
			"...KKKKKKKKKK...",
			"..KLLCLLLCLLLK..",
			".KCCCCCCBBBBBBK.",
			".KCCCCCBBBBBBBK.",
			"..KKCCCCBBBBKK..",
			"....KCCBBBK.....",
			"....KCCBBBK.....",
			"....KCCBBBK.....",
			"....KCCBBBK.....",
			"...KCCCBBBBK....",
			"..KKKKKKKKKKK...",
			"................",
		};

		public static readonly Dictionary<string, Etape[]> Suites = new()
		{
			// La hache s'arme loin en arrière, frappe : éclats de bois.
			["abattre"] = new[]
			{
				R(20, 9, 15, 0, 0),
				R(35, 9, 15, 0, 0),
				R(-12, 9, 15, 0, 0, (0, 8, 'C'), (1, 10, 'L')),
				R(-12, 9, 15, 0, 0, (0, 3, 'C'), (0, 11, 'L'), (2, 12, 'C')),
				T(0, 0, (0, 14, 'C'), (2, 15, 'L')),
			},
			// La serpe s'arme, tranche les rejets du pied : des brins verts tombent.
			["receper"] = new[]
			{
				R(-20, 5, 15, 0, 0),
				R(-30, 5, 15, 0, 0),
				R(15, 5, 15, 0, 0, (13, 8, 'G'), (14, 6, 'C')),
				R(15, 5, 15, 0, 0, (14, 11, 'G'), (12, 13, 'V')),
				T(0, 0, (13, 15, 'G'), (11, 15, 'V')),
			},
			// Éclats au sommet : les rejets tombent de chaque côté de la trogne nue,
			// puis de nouveaux bourgeons pointent (elle repart).
			["eteter"] = new[]
			{
				T(0, 0, (3, 4, 'W'), (7, 4, 'W'), (12, 4, 'W')).Dessus(),
				D(TrogneNue, 0, 0, (2, 2, 'V'), (3, 3, 'G'), (12, 1, 'G'), (13, 2, 'V')),
				D(TrogneNue, 0, 0, (1, 7, 'V'), (1, 8, 'G'), (14, 9, 'G'), (15, 10, 'V')),
				D(TrogneNue, 0, 0, (0, 13, 'V'), (1, 14, 'G'), (15, 13, 'G'), (14, 14, 'V')),
				D(TrogneNue, 0, 0, (5, 3, 'V'), (9, 3, 'V'), (0, 14, 'V'), (15, 14, 'G')),
			},
			// Une vague monte à gauche, vient frapper la digue, gicle, retombe : la
			// digue tient.
			["endiguer"] = new[]
			{
				T(0, 0, (0, 4, 'A'), (1, 4, 'W')),
				T(0, 0, (2, 4, 'A'), (3, 4, 'W'), (1, 4, 'A')),
				T(0, 0, (4, 4, 'W'), (5, 3, 'A'), (6, 2, 'W')),
				T(0, 0, (6, 1, 'W'), (7, 2, 'A'), (4, 3, 'A')),
				T(0, 0, (3, 4, 'A'), (0, 4, 'W')),
			},
			// Un reflet descend la rigole d'un bout à l'autre : l'eau est déviée.
			["deriver"] = new[]
			{
				T(0, 0, (11, 2, 'W'), (10, 3, 'W')).Dessus(),
				T(0, 0, (8, 4, 'W'), (7, 5, 'W')).Dessus(),
				T(0, 0, (6, 6, 'W'), (6, 7, 'W')).Dessus(),
				T(0, 0, (8, 9, 'W'), (9, 10, 'W')).Dessus(),
				T(0, 0, (11, 11, 'W'), (12, 12, 'W')).Dessus(),
			},
			// La pioche s'arme, frappe la roche : éclats de pierre.
			["entailler"] = new[]
			{
				R(20, 7, 13, 0, 0),
				R(30, 7, 13, 0, 0),
				R(-10, 7, 13, 0, 1, (0, 7, 'S'), (1, 6, 'M')),
				R(-10, 7, 13, 0, 1, (0, 10, 'M'), (1, 12, 'S'), (2, 9, 'S')),
				T(0, 0, (1, 15, 'S'), (0, 14, 'M')),
			},
		};
	}
}
