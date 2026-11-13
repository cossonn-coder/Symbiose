// SYMBIOSE — icones/IconesPaysage.cs (sprint ICÔNES & CURSEUR ② — données, famille « paysage »)
// Grilles 16×16 des icônes de la famille PAYSAGE (cf. `sim/actions/familles.py`) :
// les gestes lourds sur la ceinture du jardin. Alphabet de couleurs : en-tête de
// `visuals/IconeGeste.cs`. Fichier de DONNÉES : aucune logique. Pour retoucher une
// icône, modifier ses lettres puis regarder la planche (`tools/capture_vm.sh -I`).
// Voisins à ne pas confondre : la hache (abattre, fer à gauche d'un long manche),
// la serpe (recéper, lame en crochet vers la droite), la trogne (étêter : c'est
// l'arbre lui-même, tête renflée et rejets).

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesPaysage
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Hache : long manche droit, large fer tourné vers la gauche.
			["abattre"] = new[]
			{
				"................",
				"...KK...KKK.....",
				"..KSSKKKKCK.....",
				".KSSSSSSKCKK....",
				".KSSSSSMKCMK....",
				".KSSSSMMKCMK....",
				".KSSMMMMKCKK....",
				"..KMMKKKKCK.....",
				"...KK...KCK.....",
				"........KBK.....",
				"........KCK.....",
				"........KCK.....",
				"........KBK.....",
				"........KCK.....",
				"........KCK.....",
				"........KKK.....",
			},
			// Serpe : manche court, longue lame qui se recourbe en crochet à droite.
			["receper"] = new[]
			{
				"................",
				"......KKKKKK....",
				"....KKSSSSSSK...",
				"...KSSSSKKKSK...",
				"...KSSSK...KSK..",
				"...KSSSK....K...",
				"...KSSMK........",
				"...KSSMK........",
				"...KSSMK........",
				"...KSMMK........",
				"...KKKKK........",
				"....KCBK........",
				"....KCBK........",
				"....KCBK........",
				"....KCBK........",
				"....KKKK........",
			},
			// Trogne : tronc trapu, tête renflée, rejets verts dressés.
			["eteter"] = new[]
			{
				"...K...KK...K...",
				"..KVK.KVVK.KVK..",
				"..KVK.KVGK.KGK..",
				"...KVKKVGKKGK...",
				"...KKVKVGKGKK...",
				"..KCCKVVGGKBBK..",
				".KCCCCCCBBBBBBK.",
				".KCCCCCBBBBBBBK.",
				"..KKCCCCBBBBKK..",
				"....KCCBBBK.....",
				"....KCCBBBK.....",
				"....KCCBBBK.....",
				"....KCCBBBK.....",
				"...KCCCBBBBK....",
				"..KKKKKKKKKKK...",
				"................",
			},
			// Digue de pierres sèches : l'eau monte à gauche, retenue.
			["endiguer"] = new[]
			{
				"................",
				"................",
				"................",
				"..........KKKK..",
				".........KSSMK..",
				"KKKKKKK.KKKKKKK.",
				"AAAEAAAKKSSKSMK.",
				"EEAEEEKSMKKKKKK.",
				"EEEEEKKKKSSKSSMK",
				"EAEEEKSSMKKKKKKK",
				"EEEEKKKKKSSMKSMK",
				"EEEKSSKSMKKKKKKK",
				"KKKKKKKKKKKKKKKK",
				"................",
				"................",
				"................",
			},
			// Rigole : un filet d'eau qui serpente, deux touffes d'herbe sur ses rives.
			["deriver"] = new[]
			{
				"................",
				".........KKKKK..",
				".......KKAAAEK..",
				"..KK..KAAAEEK...",
				".KVVK.KAAEKK....",
				".KVGKKAAEK......",
				"..KKKAAEEK......",
				"....KAAEEKK.....",
				"....KAAAEEEKK...",
				".....KKAAAEEEK..",
				".......KKAAAEEK.",
				"..KK.....KAAAEEK",
				".KVVK...KAAAEEEK",
				".KVGK..KAAAEEEKK",
				"..KK...KKKKKKK..",
				"................",
			},
			// Pioche plantée près d'un bloc de roche.
			["entailler"] = new[]
			{
				"................",
				"...KKKKKKKKK....",
				".KKSSSSSSSSSKK..",
				"KSSKKKKCKKKKSMK.",
				"KSK...KCK...KMK.",
				".K....KCK....K..",
				"......KBK.......",
				"......KCK.......",
				"......KCK.......",
				"......KBK.......",
				"......KCK..KKK..",
				"......KCK.KSSMK.",
				"......KCKKSSMMMK",
				"......KKKKSMMMMK",
				"..........KKKKKK",
				"................",
			},
		};
	}
}
