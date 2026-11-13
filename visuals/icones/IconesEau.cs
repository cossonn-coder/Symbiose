// SYMBIOSE — icones/IconesEau.cs (sprint ICÔNES & CURSEUR — données, famille « eau »)
// Grilles 16×16 des icônes de la famille EAU (cf. `sim/actions/familles.py`).
// Alphabet de couleurs : en-tête de `visuals/IconeGeste.cs` (K contour, S/M métal
// clair/sombre, E/A eau/eau claire, '.' transparent…). Fichier de DONNÉES : aucune
// logique. Pour retoucher une icône, modifier ses lettres puis regarder la
// planche (`tools/capture_vm.sh -I`).

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesEau
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Arrosoir de métal penché vers la gauche : pomme en haut à gauche, anse
			// à droite, trois gouttes qui tombent sous la pomme.
			["arroser"] = new[]
			{
				"................",
				"................",
				"................",
				".KK....KKKKKKK..",
				"KSSK...KSSSSSKK.",
				"KMSSK..KMMMMMKSK",
				".KMSSK.KSSSSSK.K",
				"..KMSSKKSSSSSK.K",
				"A..KMSSSSSSSSKSK",
				"...AKMMSSSSSSKK.",
				"E...KKKMSSSSSK..",
				"..A....KMMMMMK..",
				"E......KKKKKKK..",
				"..E.............",
				"................",
				"................",
			},
		};
	}
}
