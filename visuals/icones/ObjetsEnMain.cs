// SYMBIOSE — icones/ObjetsEnMain.cs (sprint GESTES LISIBLES ④ — données)
// Grilles 16×16 des OBJETS EN MAIN : ce que le curseur porte entre les deux clics d'un
// geste à deux temps (conception §6). Clé = verbe du geste. Le pot n'a pas de grille :
// c'est le pot lui-même qui suit la souris (WorldView.ObjetEnMain.cs).
// Alphabet de couleurs : en-tête de `visuals/IconeGeste.cs` (K contour, C/B bois
// clair/sombre, T humus, V/G verts, '.' transparent…). Fichier de DONNÉES : aucune logique.

using System.Collections.Generic;

namespace Symbiose
{
	internal static class ObjetsEnMain
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Bouture : un rameau coupé en biseau, trois feuilles vertes au bout.
			["bouturer"] = new[]
			{
				"................",
				"..........KKK...",
				".........KVVGK..",
				"....KKK..KVGGK..",
				"...KVVGK.KGGK...",
				"...KVGGKKCK.....",
				"....KGGKCBKKK...",
				".....KKCBKKVGK..",
				"......KCBKVGGK..",
				".....KCBK.KKK...",
				"....KCBK........",
				"...KCBK.........",
				"..KCBK..........",
				"..KCK...........",
				"..KK............",
				"................",
			},
			// Greffon : un rameau nu coupé en biseau, deux yeux (bourgeons) verts.
			["greffer"] = new[]
			{
				"................",
				"............KK..",
				"...........KCK..",
				"..........KCBK..",
				".........KCBKV..",
				"........KCBK....",
				".......KCBK.....",
				"......KCBKV.....",
				".....KCBK.......",
				"....KCBK........",
				"...KCBK.........",
				"..KCBK..........",
				"..KCK...........",
				"..KK............",
				"................",
				"................",
			},
			// Pelletée de compost : un tas d'humus sombre, grumeleux, piqué de vert.
			["epandre"] = new[]
			{
				"................",
				"................",
				"................",
				"................",
				"......KKKK......",
				"....KKTBTTKK....",
				"...KTTBTTVBTK...",
				"..KTBTTTBTTTTK..",
				"..KTTVTTTTBTTK..",
				".KTTBTTTBTTTVTK.",
				".KBTTTTVTTBTTTK.",
				".KTTTBTTTTTTBTK.",
				"..KKKKKKKKKKKK..",
				"................",
				"................",
				"................",
			},
		};
	}
}
