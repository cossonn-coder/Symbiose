// SYMBIOSE — icones/AnimsSemis.cs (sprint GESTES LISIBLES ② — données, famille « semis »)
// LES SUITES D'IMAGES des gestes de la famille SEMIS (format : en-tête de
// `AnimsEau.cs` et de `visuals/EtapeGeste.cs`). Fichier de DONNÉES : aucune
// logique. Planche de contrôle : `tools/capture_vm.sh -W`.

using System.Collections.Generic;
using static Symbiose.EtapeGeste;

namespace Symbiose
{
	internal static class AnimsSemis
	{
		public static readonly Dictionary<string, Etape[]> Suites = new()
		{
			// La motte descend, touche, se tasse ; deux éclats : c'est en terre.
			["planter"] = Puis(Poser(13), T(0, 0, (3, 0, 'Y'), (12, 0, 'Y'))),
			// Même chose dans un pot.
			["planter_conteneur"] = Puis(Poser(13), T(0, 0, (2, 0, 'Y'), (13, 0, 'Y'))),
			// La bouture plonge dans le verre (éclaboussure), des bulles montent et
			// de petites racines blanches apparaissent au pied de la tige.
			["bouturer"] = new[]
			{
				T(0, -4),
				T(0, -1),
				T(0, 0, (2, 9, 'A'), (12, 9, 'A'), (1, 8, 'W'), (13, 8, 'W')),
				T(0, 0, (5, 12, 'W'), (10, 12, 'W'), (7, 13, 'L')).Dessus(),
				T(0, 0, (5, 11, 'W'), (10, 11, 'W'), (6, 13, 'L'), (7, 13, 'L'), (8, 13, 'L')).Dessus(),
			},
			// Le greffon se pose sur le porte-greffe, le raphia s'enroule (rayures),
			// un bourgeon s'éveille au sommet.
			["greffer"] = new[]
			{
				T(0, -3),
				T(0, 0),
				T(0, 0, (6, 8, 'C'), (8, 8, 'C'), (10, 8, 'C')).Dessus(),
				T(0, 0, (6, 8, 'C'), (8, 8, 'C'), (10, 8, 'C'), (7, 10, 'C'), (9, 10, 'C'), (11, 10, 'C')).Dessus(),
				T(0, 0, (9, 0, 'V'), (10, 1, 'Y'), (5, 2, 'Y')),
			},
		};
	}
}
