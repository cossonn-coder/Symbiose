// SYMBIOSE — icones/IconesSol.cs (sprint ICÔNES & CURSEUR ② — données, famille « sol »)
// Grilles 16×16 des icônes de la famille SOL (cf. `sim/actions/familles.py`).
// Alphabet de couleurs : en-tête de `visuals/IconeGeste.cs`. Fichier de DONNÉES :
// aucune logique. Pour retoucher une icône, modifier ses lettres puis regarder la
// planche (`tools/capture_vm.sh -I`). Voisins à ne pas confondre : la bêche
// (droite, lame plate), la pelle de `creuser` (penchée, avec sa motte), le drain
// de terre cuite de `drainer`.

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesSol
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Bêche droite : poignée en T, manche de bois, lame plate rectangulaire.
			["becher"] = new[]
			{
				"................",
				".....KKKKKK.....",
				".....KCCCCK.....",
				".....KKCCKK.....",
				"......KCBK......",
				"......KCBK......",
				"......KCBK......",
				"......KCBK......",
				"....KKKCBKKK....",
				"....KSSKKSMK....",
				"....KSSSSSMK....",
				"....KSSSSSMK....",
				"....KSSSSSMK....",
				"....KSSSSMMK....",
				".....KMMMMK.....",
				"......KKKK......",
			},
			// Grelinette : DEUX manches, une traverse, quatre dents.
			["grelinette"] = new[]
			{
				".KKK.........KKK",
				".KCK.........KCK",
				".KCK.........KCK",
				".KCK.........KCK",
				".KCK.........KCK",
				".KCK.........KCK",
				".KCK.........KCK",
				".KBK.........KBK",
				".KKKKKKKKKKKKKKK",
				".KSSSSSSSSSSSSMK",
				".KKKKKKKKKKKKKKK",
				".KSK.KSK.KSK.KMK",
				".KSK.KSK.KSK.KMK",
				".KSK.KSK.KSK.KMK",
				".KSK.KSK.KSK.KMK",
				"..K...K...K...K.",
			},
			// Pelle penchée, lame arrondie, et la motte de terre qu'elle vient de sortir.
			["creuser"] = new[]
			{
				"................",
				"............KK..",
				"...........KCCK.",
				"..........KCBK..",
				".........KCBK...",
				"........KCBK....",
				".......KCBK.....",
				"...KK.KCBK......",
				"..KSSKKBK.......",
				".KSSSSSK........",
				".KSSSSSMK...KK..",
				".KSSSSMMK..KBBK.",
				"..KSSMMK..KBBBBK",
				"...KMMK..KBBTBBK",
				"....KK...KKKKKKK",
				"................",
			},
			// Drain de terre cuite couché, l'eau s'en écoule et fait flaque.
			["drainer"] = new[]
			{
				"................",
				"................",
				"................",
				"..KKKKKKKKKK....",
				".KOOOOOOOOOKK...",
				".KOOOOOOOOKOOK..",
				".KOOOOOOOOKTTK..",
				".KOOOOOOOOKTEK..",
				".KBBBBBBBBKEEK..",
				"..KKKKKKKKKEEK..",
				"...........KEAK.",
				"...........KEAK.",
				"..........KEEAEK",
				".........KEAEEEK",
				"..........KKKKK.",
				"................",
			},
			// Plante sortie de terre, la motte et les racines pendantes à nu.
			["deraciner"] = new[]
			{
				"................",
				"...KK.....KK....",
				"..KVVK.KKKVVK...",
				"..KVVVKVVKVGK...",
				"...KVVKVGKGK....",
				"....KKVVGKK.....",
				"......KVGK......",
				"......KVGK......",
				".....KKBBKK.....",
				"....KBCBBBBK....",
				"....KBBBBCBK....",
				"...KBKBBKBKBK...",
				"..KBK.KBK.KBK...",
				"..KK..KBK..KBK..",
				"......KK....KK..",
				"................",
			},
		};
	}
}
