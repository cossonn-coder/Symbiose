// SYMBIOSE — icones/IconesSemis.cs (sprint ICÔNES & CURSEUR ② — données, famille « semis »)
// Grilles 16×16 des icônes de la famille SEMIS (cf. `sim/actions/familles.py`).
// Alphabet de couleurs : en-tête de `visuals/IconeGeste.cs`. Fichier de DONNÉES :
// aucune logique. Pour retoucher une icône, modifier ses lettres puis regarder la
// planche (`tools/capture_vm.sh -I`). Quatre jeunes pousses, quatre SUPPORTS :
// la butte de terre (planter), le verre d'eau (bouturer), le tronc ligaturé
// (greffer), le pot de terre cuite (planter en conteneur).

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesSemis
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Plantule à deux cotylédons qui sort d'une butte de terre.
			["planter"] = new[]
			{
				"................",
				"................",
				"..KKK.....KKK...",
				".KVVVK...KVVGK..",
				".KVVVVK.KVVGGK..",
				"..KVVVVKVVGGK...",
				"...KKVVKVGKK....",
				".....KVVGK......",
				"......KVGK......",
				"......KVGK......",
				"...KKKKVGKKKK...",
				"..KCCCCKKCCCBK..",
				".KCCCCCCCCCBBBK.",
				".KCBCCCBCCBBBBK.",
				".KKKKKKKKKKKKKK.",
				"................",
			},
			// Bouture : un rameau feuillu qui trempe dans un verre d'eau.
			["bouturer"] = new[]
			{
				"......KK........",
				".....KVVK..KK...",
				".....KVVGKKVGK..",
				"......KVGKVGGK..",
				"...KK.KVGKGKK...",
				"..KVVKKVGKK.....",
				"..KVVVKVGK......",
				"...KKVVVGK......",
				"..K...KVGK..K...",
				"..KW..KVGK..K...",
				"..KAAAAVGAAAK...",
				"..KAEEEVGEEEK...",
				"..KAEEEKGEEEK...",
				"...KEEEEEEEK....",
				"...KKKKKKKKK....",
				"................",
			},
			// Greffe : un greffon vert planté dans un tronc, ligature de raphia rayée.
			["greffer"] = new[]
			{
				"................",
				"........KK......",
				".......KVVK.KK..",
				".......KVGKKVGK.",
				"........KVGVGK..",
				"........KVGKK...",
				"........KVGK....",
				"......KKKVGK....",
				".....KLLLLLLK...",
				".....KKLKLKLK...",
				".....KLLLLLLK...",
				"......KCCBBK....",
				"......KCCBBK....",
				"......KCCBBK....",
				"......KCCBBK....",
				"......KKKKKK....",
			},
			// Plantule dans un pot de terre cuite.
			["planter_conteneur"] = new[]
			{
				"................",
				"...KK.....KK....",
				"..KVVK...KVGK...",
				"..KVVVK.KVGGK...",
				"...KVVVKVGGK....",
				"....KKVVGKK.....",
				"......KVGK......",
				".KKKKKKVGKKKKKK.",
				".KOOOOOOOOOOOBK.",
				".KKKKKKKKKKKKKK.",
				"..KOOOOOOOOOBK..",
				"..KOOOOOOOOOBK..",
				"...KOOOOOOOBK...",
				"...KOOOOOOOBK...",
				"...KKKKKKKKKK...",
				"................",
			},
		};
	}
}
