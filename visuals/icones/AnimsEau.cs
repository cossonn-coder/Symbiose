// SYMBIOSE — icones/AnimsEau.cs (sprint GESTES LISIBLES ② — données, famille « eau »)
// LES SUITES D'IMAGES des gestes de la famille EAU : chaque image est une `Etape`
// (`visuals/EtapeGeste.cs` : T = icône décalée, R = icône tournée autour d'un
// pivot, D = grille dessinée ; effets en coordonnées absolues de la grille,
// alphabet d'`IconeGeste`). Fichier de DONNÉES : aucune logique. Pour retoucher,
// changer les nombres puis regarder la planche (`tools/capture_vm.sh -W`).
// Angle positif = sens des aiguilles d'une montre à l'écran.

using System.Collections.Generic;
using static Symbiose.EtapeGeste;

namespace Symbiose
{
	internal static class AnimsEau
	{
		public static readonly Dictionary<string, Etape[]> Suites = new()
		{
			// L'arrosoir PIVOTE SUR SA POMME (le point chaud) : l'arrière se lève, il
			// se penche de plus en plus (jusqu'à 55° : l'icône est déjà inclinée de
			// ~30°, il faut pencher fort pour que le bec pointe vers le sol), descend un
			// peu vers la plante, l'eau coule en filet puis éclabousse, il se redresse.
			["arroser"] = new[]
			{
				R(-20, 1, 5, 0, 1),
				R(-40, 1, 5, 0, 3, (1, 10, 'A')),
				R(-55, 1, 5, 0, 5, (1, 11, 'A'), (0, 12, 'E'), (1, 13, 'A'), (2, 14, 'E')),
				R(-55, 1, 5, 0, 5, (0, 12, 'A'), (1, 13, 'E'), (0, 14, 'A'), (1, 15, 'W'),
					(3, 15, 'A'), (4, 14, 'W')),
				R(-25, 1, 5, 0, 2, (1, 15, 'E'), (3, 15, 'W'), (5, 15, 'A')),
			},
		};
	}
}
