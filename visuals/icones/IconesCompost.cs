// SYMBIOSE — icones/IconesCompost.cs (sprint ICÔNES & CURSEUR — données, famille « compost »)
// Grilles 16×16 des icônes de la famille COMPOST (cf. `sim/actions/familles.py`).
// Alphabet de couleurs : en-tête de `visuals/IconeGeste.cs` (K contour, C/B bois
// clair/sombre, T humus, V/G verts, '.' transparent…). Fichier de DONNÉES : aucune
// logique. Pour retoucher une icône, modifier ses lettres puis regarder la
// planche (`tools/capture_vm.sh -I`).

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesCompost
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Bac à compost : caisse de planches à claire-voie, humus sombre qui
			// dépasse en haut, deux brins verts fraîchement jetés dessus.
			["poser_bac"] = new[]
			{
				"................",
				"................",
				"......V..G......",
				"...KKTVTTGTKK...",
				"..KTTTTTTTTTTK..",
				".KKKKKKKKKKKKKK.",
				".KCCCKCCCCKCCCK.",
				".KCCCKCCCCKCCCK.",
				".KBBBKBBBBKBBBK.",
				".KCCCKCCCCKCCCK.",
				".KCCCKCCCCKCCCK.",
				".KBBBKBBBBKBBBK.",
				".KCCCKCCCCKCCCK.",
				".KCCCKCCCCKCCCK.",
				".KKKKKKKKKKKKKK.",
				"................",
			},
			// Pile à bois : six rondins vus en bout, empilés en pyramide.
			["poser_pile"] = new[]
			{
				"................",
				"................",
				"......KKK.......",
				".....KCCCK......",
				".....KCBCK......",
				".....KCCCK......",
				"....KKKKKKK.....",
				"...KCCCKCCCK....",
				"...KCBCKCBCK....",
				"...KCCCKCCCK....",
				"..KKKKKKKKKKK...",
				".KCCCKCCCKCCCK..",
				".KCBCKCBCKCBCK..",
				".KCCCKCCCKCCCK..",
				"..KKK.KKK.KKK...",
				"................",
			},
			// Tas de déchets verts : épluchures, feuilles et tiges en vrac.
			["composter"] = new[]
			{
				"................",
				"................",
				"................",
				"......KK........",
				".....KVVK..KK...",
				".....KVGK.KYYK..",
				"....KKVGKKYYK...",
				"...KOOKGVVKYKK..",
				"..KOOVVVVGVVOOK.",
				"..KVVGVOOVVGVOK.",
				".KVGVVOOVGVVVGVK",
				".KGVVBVVGGVBVVGK",
				".KBGBBGBBGBBGBBK",
				".KBBBBBBBBBBBBBK",
				"..KKKKKKKKKKKKK.",
				"................",
			},
			// Fourche à fumier : UN manche à poignée, trois dents écartées.
			["retourner"] = new[]
			{
				".....KKKKK......",
				".....KCCCK......",
				".....KKCKK......",
				"......KCK.......",
				"......KCK.......",
				"......KBK.......",
				"......KCK.......",
				"......KBK.......",
				".KKKKKKSKKKKKK..",
				".KSSSSSSSSSSMK..",
				".KSKKKKSKKKKMK..",
				".KSK..KSK..KMK..",
				".KSK..KSK..KMK..",
				".KSK..KSK..KMK..",
				".KSK..KSK..KMK..",
				"..K....K....K...",
			},
			// Brouette de métal chargée de compost mûr, roue à gauche.
			["epandre"] = new[]
			{
				"................",
				"................",
				"................",
				"....KKKKKK......",
				"..KKBBTBBBKK....",
				".KBBTBBBBTBBK...",
				"KKKKKKKKKKKKKKK.",
				"KSSSSSSSSSSMKCCK",
				".KSSSSSSSSSMKKKK",
				".KSSSSSSSSMMK...",
				"..KSSSSSSMMK....",
				"..KKKKKKKKKK....",
				".KKK.....KBK....",
				"KMSMK....KBK....",
				"KMMMK....KBK....",
				".KKK....KKKK....",
			},
			// Un seul rondin couché, coupe claire à gauche, moignon de branche.
			["empiler_bois"] = new[]
			{
				"................",
				"................",
				"................",
				"................",
				".........KK.....",
				"........KCBK....",
				"..KKKKKKKCBKKK..",
				".KLLKCCCCCCCCCK.",
				"KLCLLKCCCCCCCBBK",
				"KLCCLKBCCCBBBBBK",
				"KLLCLKBBBBBBBBBK",
				".KLLKBBBBBBBBBK.",
				"..KKKKKKKKKKKK..",
				"................",
				"................",
				"................",
			},
			// Gerbe de paille liée en son milieu (silhouette en sablier).
			["pailler"] = new[]
			{
				"................",
				".K.K.K..K.K.K...",
				".KYKLKKKLKYKLK..",
				".KLYLYLLYLYLYK..",
				"..KLYLYLLYLYK...",
				"..KLLYLYLYLLK...",
				"...KLYLLYLYK....",
				"....KKKKKKK.....",
				"....KBBBBBK.....",
				"....KKKKKKK.....",
				"...KLYLLYLYK....",
				"..KLLYLYLYLLK...",
				"..KLYLYLLYLYK...",
				".KLYLYLLYLYLYK..",
				".KKKKKKKKKKKKK..",
				"................",
			},
			// Broyeur : trémie de métal, caisse orangée sur roue, copeaux qui giclent.
			["broyer"] = new[]
			{
				"................",
				"KKKKKKKK........",
				"KMSSSSMK........",
				".KMSSMK..KKKKK..",
				".KMSSMK..KSSSMK.",
				"KKKKKKKKKKSKKKK.",
				"KOOOOOOOOOSK.C..",
				"KOOOOOOOOOOK...C",
				"KOOOWWOOOOOK.C..",
				"KOOOOOOOOOBK..C.",
				"KOBBBBBBBBBK.C.C",
				"KKKKKKKKKKKK.CCC",
				"..KKK...K.K.CCCC",
				".KMSMK..K.K.KKKK",
				".KMMMK..KKK.....",
				"..KKK...........",
			},
		};
	}
}
