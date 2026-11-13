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
			// GESTES LISIBLES ② (redessiné, l'ancienne pince de doigts n'était pas
			// comprise) : une MAIN gantée entière, venue d'en haut à droite (manchette
			// sombre), pouce et index refermés sur le bourgeon vert du bout d'une
			// jeune tige à deux feuilles. On lit « des doigts qui pincent une pousse ».
			["pincer"] = new[]
			{
				"..........KKKKK.",
				"........KKWWWSNK",
				"...KKKKKWWWWSSNK",
				"..KWWWWWWWWWWSSK",
				"..KKKKKKWWWWWSSK",
				"..KVVK...KWWWSK.",
				"..KKKKKKWWWWWSK.",
				"..KWWWWWWWWWSK..",
				"...KKKKKKKKKK...",
				"....KGK.........",
				".KK.KGK.KK......",
				"KVVKKGKKVVK.....",
				"KVGVKGKVGVK.....",
				".KKKKGKKKK......",
				"....KGK.........",
				".....K..........",
			},
			// Poing ganté (la manche de cuir part à droite) serré sur une tige : la
			// touffe verte dépasse au-dessus.
			["arracher"] = new[]
			{
				"................",
				"..KK.KKK..KK....",
				".KVVKVVVKKVVK...",
				".KVVVKVVKVVGK...",
				"..KVVKVGKVGK....",
				"...KKVVGGKK.....",
				".....KVGK.......",
				"...KKKKKKKKKKKKK",
				"..KWWKWWKWWSKCCK",
				"..KWWKWWKWWSKCBK",
				"..KWWWWWWWSSKCBK",
				"..KWWWWWWSSSKBBK",
				"...KKKKKKKKKKKKK",
				".....KVGK.......",
				".....KVGK.......",
				"......KK........",
			},
			// Sécateur (redessiné au ②, l'ancien se lisait comme une croix) : un bec
			// de métal en haut à gauche, rivet jaune, deux poignées rouges écartées
			// vers le bas et la droite. GESTES LISIBLES ② : outils INVERSÉS — le
			// sécateur est l'outil de la TAILLE (rameaux fins), la scie celui de la
			// COUPE (une branche entière).
			["tailler"] = new[]
			{
				"................",
				".KK.............",
				".KSKK...........",
				"..KSSKK.........",
				"..KMSSSK........",
				"...KMSSSK.......",
				"....KKMSSK......",
				"......KYYKKK....",
				"......KYYRRRKK..",
				".....KRRKKRRRRK.",
				".....KRRK.KKRRK.",
				"....KRRK....KK..",
				"....KRRK........",
				"...KRRK.........",
				"...KRK..........",
				"....K...........",
			},
			// Scie d'élagage : longue lame courbe dentée, poignée de bois ajourée.
			// (GESTES LISIBLES ② : c'est l'icône de `couper`, cf. ci-dessus.)
			["couper"] = new[]
			{
				"................",
				".K..............",
				"KSK.............",
				"KSSKK...........",
				".KSSSKK.........",
				".KMSSSSKK.......",
				"..KMSSSSSKK.....",
				"..K.KMSSSSSKK...",
				"....K.KMSSSSSK..",
				"......K.KMSSKKK.",
				"........K.KKCCCK",
				"..........KCCKCK",
				"..........KCBKCK",
				"...........KBBBK",
				"............KKK.",
				"................",
			},
		};
	}
}
