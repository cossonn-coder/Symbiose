// SYMBIOSE — icones/IconesStructures.cs (sprint ICÔNES & CURSEUR ② — données, famille « structures »)
// Grilles 16×16 des icônes de la famille STRUCTURES (cf. `sim/actions/familles.py`) :
// ce qu'on pose au jardin. Alphabet de couleurs : en-tête de `visuals/IconeGeste.cs`.
// Fichier de DONNÉES : aucune logique. Pour retoucher une icône, modifier ses
// lettres puis regarder la planche (`tools/capture_vm.sh -I`).
// Voisins à ne pas confondre : le pot nu (poser), le pot porté par deux gants
// (déplacer) ; le bac de culture, large et bas, ≠ le bac à compost, haut et à
// claire-voie ; la pergola de bois ≠ l'ombrière grise sous son soleil ; le voile
// blanc, large et bas ≠ la cloche de verre, haute et étroite.

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesStructures
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Pot de terre cuite rempli de terreau, sans plante.
			["poser_pot"] = new[]
			{
				"................",
				"................",
				"....KKKKKKKK....",
				"..KKBTBBTBBTKK..",
				".KOOOOOOOOOOOBK.",
				".KOLOOOOOOOOOBK.",
				".KKKKKKKKKKKKKK.",
				"..KOOOOOOOOOBK..",
				"..KOLOOOOOOOBK..",
				"..KOOOOOOOOOBK..",
				"...KOOOOOOOBK...",
				"...KOOOOOOOBK...",
				"...KOOOOOOOBK...",
				"....KKKKKKKK....",
				"................",
				"................",
			},
			// Bac de culture : caisse de planches large et basse, trois jeunes pousses.
			["poser_bac_culture"] = new[]
			{
				"................",
				"................",
				"................",
				"...K....K....K..",
				"..KVK..KVK..KVK.",
				"..KGK..KGK..KGK.",
				"KKKKKKKKKKKKKKKK",
				"KTBTTBTTTBTTBTTK",
				"KKKKKKKKKKKKKKKK",
				"KCCCCCCCCCCCCCBK",
				"KCCCCCCCCCCCCCBK",
				"KKKKKKKKKKKKKKKK",
				"KCCCCCCCCCCCCCBK",
				"KBBBBBBBBBBBBBBK",
				"KKKKKKKKKKKKKKKK",
				"................",
			},
			// Pot soulevé par deux gants, son ombre restée au sol.
			["deplacer_pot"] = new[]
			{
				"................",
				"................",
				"...KKKKKKKKKK...",
				"...KOOOOOOOBK...",
				"...KKKKKKKKKK...",
				".KKKKOOOOOBKKKK.",
				"KWWWKOOOOOBKWWSK",
				"KWWWKOOOOOBKWWSK",
				"KWWSKOOOOOBKWSSK",
				".KKKKKOOOBKKKKK.",
				".....KOOOBK.....",
				".....KKKKKK.....",
				"................",
				"....NNNNNNNN....",
				".....NNNNNN.....",
				"................",
			},
			// Tuteur : un piquet de bois droit, une liane verte qui s'y enroule.
			["poser_tuteur"] = new[]
			{
				".......KK.......",
				"......KCBK......",
				"......KCBK.KK...",
				"...KK.KCBKKVVK..",
				"..KVVKKCBKVVGK..",
				"..KVVVKCGVVGK...",
				"...KKVVVGKKK....",
				"......KVBK......",
				"......KCVVKK....",
				"...KK.KCBVVVK...",
				"..KVVKKCBKVGK...",
				"..KVVVVGBKKK....",
				"...KKKVVBK......",
				"......KCVK......",
				"......KCBK......",
				".......KK.......",
			},
			// Treillis : cadre et croisillons de lattes, sur deux pieds.
			["poser_treillis"] = new[]
			{
				"................",
				".KKKKKKKKKKKKK..",
				".K..C..C..C..K..",
				".K..C..C..C..K..",
				".KBBCBBCBBCBBK..",
				".K..C..C..C..K..",
				".K..C..C..C..K..",
				".KBBCBBCBBCBBK..",
				".K..C..C..C..K..",
				".K..C..C..C..K..",
				".KBBCBBCBBCBBK..",
				".K..C..C..C..K..",
				".K..C..C..C..K..",
				".KKKKKKKKKKKKK..",
				".K...........K..",
				".K...........K..",
			},
			// Pergola : deux poteaux, une poutre, les chevrons qui dépassent, une
			// liane qui pend au milieu.
			["poser_pergola"] = new[]
			{
				"................",
				".KK..KK..KK..KK.",
				"KCCKKCCKKCCKKCCK",
				"KCCCCCCCCCCCCCBK",
				"KKKKKKKKKKKKKKKK",
				"..KCBK.VG.KCBK..",
				"..KCBKVGVVKCBK..",
				"..KCBK.VG.KCBK..",
				"..KCBK..V.KCBK..",
				"..KCBK....KCBK..",
				"..KCBK....KCBK..",
				"..KCBK....KCBK..",
				"..KCBK....KCBK..",
				"..KCBK....KCBK..",
				"..KKKK....KKKK..",
				"................",
			},
			// Pelote de raphia, un brin qui dépasse : de quoi nouer une canne.
			["palisser"] = new[]
			{
				"................",
				"................",
				".....KKKKKK.....",
				"...KKLLLLLLKK...",
				"..KLLLCLLCLLLK..",
				"..KLLCLLCLLCLK..",
				".KLLCLLCLLCLLLK.",
				".KLCLLCLLCLLCLK.",
				".KLLLCLLCLLCLLK.",
				".KLLCLLCLLCLLLK.",
				"..KCLLCLLCLLCK..",
				"..KLLCLLCLLLLK..",
				"...KKLLLLLLKKK..",
				".....KKKKKK.KLK.",
				"..........KKLK..",
				".........KLLK...",
			},
			// Perchoir en T, un merle posé dessus (bec jaune).
			["poser_perchoir"] = new[]
			{
				"................",
				"......KKK.......",
				".....KNNNKK.....",
				".....KNWNNYY....",
				"....KNNNNK......",
				"...KNNNNNK......",
				"..KKKNNKK.......",
				".KKKKKKKKKKKKKK.",
				".KCCCCCCCCCCCBK.",
				".KKKKKKCBKKKKKK.",
				"......KCBK......",
				"......KCBK......",
				"......KCBK......",
				"......KCBK......",
				"......KCBK......",
				"......KKKK......",
			},
			// Voile d'hivernage : tunnel bas de toile blanche sur ses arceaux, une
			// pousse au chaud dans l'ouverture.
			["poser_voile"] = new[]
			{
				"................",
				"................",
				"................",
				"....KKKKKKKK....",
				"..KKWWWSWWWWKK..",
				".KWWWWSWWWWSWWK.",
				".KWWWWSWWWWSWWK.",
				"KWWWWSWWWWSKKKWK",
				"KWWWWSWWWWKTTTKK",
				"KWWWWSWWWWKTVTTK",
				"KWWWWSWWWSKVGVTK",
				"KWWWWSWWWSKTGTTK",
				"KKWWWSWWWSKTTTKK",
				"KBKKKKKKKKKKKKBK",
				"................",
				"................",
			},
			// Cloche de verre à bouton, une jeune plante à l'abri dessous.
			["poser_cloche"] = new[]
			{
				".......KK.......",
				"......KSSK......",
				"......KKKK......",
				".....KAAAAK.....",
				"....KAWAAAAK....",
				"...KAWAAAAAEK...",
				"...KAWAAAAAEK...",
				"...KAAAKKAAEK...",
				"...KAAKVVKAEK...",
				"...KAAKVGKAEK...",
				"...KAAAKGKAEK...",
				"...KAAAKGKAEK...",
				"...KAAAKGKAEK...",
				"..KKKKKKKKKKKK..",
				"..KTBTTBTTBTTK..",
				"..KKKKKKKKKKKK..",
			},
			// Ombrière : toile grise tramée sur deux piquets, le soleil au-dessus,
			// une pousse à l'ombre dessous.
			["poser_ombriere"] = new[]
			{
				"............KK..",
				"...........KYYK.",
				"...........KYYK.",
				"............KK..",
				"................",
				"KKKKKKKKKKKKKKKK",
				"KNMNMNMNMNMNMNMK",
				"KMNMNMNMNMNMNMNK",
				"KKKKKKKKKKKKKKKK",
				".KCK........KCK.",
				".KCK........KCK.",
				".KCK..K..K..KCK.",
				".KCK.KVKKGK.KCK.",
				".KCK..KVGK..KCK.",
				".KCK...KK...KCK.",
				".KKK........KKK.",
			},
			// Ruche de paille tressée (cloche à bourrelets), trou d'envol sombre.
			["poser_ruche"] = new[]
			{
				"................",
				"......KKKK......",
				"....KKYYYYKK....",
				"...KYYLYYYYYK...",
				"...KOOOOOOOOK...",
				"..KYYLYYYYYYOK..",
				"..KOOOOOOOOOOK..",
				".KYYLYYYYYYYYOK.",
				".KOOOOOOOOOOOOK.",
				".KYYLYYYKKYYYOK.",
				".KOOOOOKTTKOOOK.",
				".KYYLYYKTTKYYOK.",
				".KKKKKKKKKKKKKK.",
				"KCCCCCCCCCCCCCBK",
				"KKKKKKKKKKKKKKKK",
				"................",
			},
			// Pot de miel : bocal ventru doré, couvercle de métal.
			["recolter_miel"] = new[]
			{
				"................",
				"................",
				".....KKKKKK.....",
				"....KSSSSSMK....",
				"....KKKKKKKK....",
				".....KAAAAK.....",
				"...KKKKKKKKKK...",
				"..KYYYYYYYYYOK..",
				"..KYWYYYYYYYOK..",
				"..KYWYYYYYYYOK..",
				"..KYWYYYYYYOOK..",
				"..KYYYYYYYYOOK..",
				"..KYYYYYYYOOOK..",
				"..KYYYYOOOOOOK..",
				"...KKKKKKKKKK...",
				"................",
			},
		};
	}
}
