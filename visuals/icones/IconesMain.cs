// SYMBIOSE — icones/IconesMain.cs (sprint ICÔNES & CURSEUR ② — données, famille « main »)
// Grilles 16×16 des icônes de la famille MAIN (cf. `sim/actions/familles.py`) :
// les gestes à mains nues ou presque. Alphabet de couleurs : en-tête de
// `visuals/IconeGeste.cs`. Fichier de DONNÉES : aucune logique. Pour retoucher une
// icône, modifier ses lettres puis regarder la planche (`tools/capture_vm.sh -I`).
// Les points chauds (pixel actif de chaque icône) sont dans `IconesPointsChauds.cs`.

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesMain
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Panier d'osier à anse, rempli de fruits rouges (un jaune à droite).
			["recolter"] = new[]
			{
				"................",
				".....KKKKKK.....",
				"....KC....CK....",
				"...KC......CK...",
				"...KC..KK..CK...",
				"...KCKKRRKKCK...",
				"..KKKRRKRRYKKK..",
				".KCKRWRRRKYYKCK.",
				".KCCKKKKKKKKCCK.",
				".KCBCCBCCBCCBCK.",
				".KBCCBCCBCCBCCK.",
				"..KCBCCBCCBCCK..",
				"..KBCCBCCBCCBK..",
				"...KBBBBBBBBK...",
				"....KKKKKKKK....",
				"................",
			},
			// Pomme rouge croquée : la morsure à droite montre la chair crème.
			["manger"] = new[]
			{
				"................",
				".......KK.......",
				"......KBKKKK....",
				"......KBKVVGK...",
				"...KKKKBKKKK....",
				"..KRRRRKRRRK....",
				".KRWRRRRRRKK....",
				".KRWRRRRRKLK....",
				".KRRRRRRKLLK....",
				".KRRRRRRKLLK....",
				".KRRRRRRRKLLK...",
				"..KRRRRRRRKKK...",
				"..KRRRRRRRRK....",
				"...KRRKKRRK.....",
				"....KK..KK......",
				"................",
			},
			// Poignée de feuilles mortes (une orangée, une jaune) tenue dans le gant.
			["glaner"] = new[]
			{
				"................",
				"....KK....KK....",
				"...KOOK..KYYK...",
				"..KOOOOKKYYYYK..",
				"..KOOBOKKYCYYK..",
				"..KOOBOOKYCYYK..",
				"...KOOBOKCYYK...",
				"....KOOBKCYK....",
				".....KOBKCK.....",
				"....KKKBKCKK....",
				"...KWWWKKKWSK...",
				"...KWWWWWWSSK...",
				"...KWWWWWSSSK...",
				"....KWWWWSSK....",
				".....KKKKKK.....",
				"................",
			},
			// Botte de cuir vue de profil, semelle sombre, éclats sous le talon.
			["ecraser"] = new[]
			{
				"................",
				"....KKKKK.......",
				"....KCCCK.......",
				"....KCCBK.......",
				"....KCCBK.......",
				"....KCCBK.......",
				"....KCCBKK......",
				"....KCCCCCKK....",
				"...KCCCCCCCCK...",
				"...KCBBBBBBBBK..",
				"...KKKKKKKKKKK..",
				"...KMMKMMMMMMK..",
				"...KKK.KKKKKKK..",
				".K............K.",
				"..K..K....K..K..",
				"................",
			},
			// Coccinelle posée sur une feuille : l'auxiliaire qu'on accueille.
			["favoriser_auxiliaire"] = new[]
			{
				"................",
				"................",
				".....KK..KK.....",
				"......K..K......",
				".....KKKKKK.....",
				"....KKNKKNKK....",
				"...KRRRKKRRRK...",
				"..KRWRRKKRRRRK..",
				"..KRRKRKKRKRRK..",
				"..KRRRRKKRRRRK..",
				"..KRRRRKKRKRRK..",
				"...KRKRKKRRRK...",
				".KKKKRRKKRRKKKK.",
				".KVVVKKKKKKVVGK.",
				"..KKVVVVVVVGKK..",
				"....KKKKKKKK....",
			},
		};
	}
}
