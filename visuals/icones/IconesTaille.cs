// SYMBIOSE — icones/IconesTaille.cs (sprint ICÔNES & CURSEUR — données, famille « taille »)
// Grilles 16×16 des icônes de la famille TAILLE (cf. `sim/actions/familles.py`).
// Alphabet de couleurs : en-tête de `visuals/IconeGeste.cs` (K contour, S/M métal
// clair/sombre, R rouge, Y jaune, '.' transparent…). Fichier de DONNÉES : aucune
// logique. Pour retoucher une icône, modifier ses lettres puis regarder la
// planche (`tools/capture_vm.sh -I`).

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesTaille
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Sécateur ouvert : deux lames de métal en haut, rivet jaune au
			// croisement, deux poignées rouges en bas.
			["couper"] = new[]
			{
				"................",
				"....K.......K...",
				"...KSK.....KSK..",
				"...KSSK...KSMK..",
				"....KSSK.KSMK...",
				".....KSSKSMK....",
				"......KSSMK.....",
				".......KYK......",
				"......KRKRK.....",
				".....KRK.KRK....",
				"....KRK...KRK...",
				"...KRK.....KRK..",
				"...KRK.....KRK..",
				"....K.......K...",
				"................",
				"................",
			},
		};
	}
}
