// SYMBIOSE — icones/IconesPointsChauds.cs (sprint ICÔNES & CURSEUR ② — données)
// LE POINT CHAUD de chaque icône : le pixel « actif » de l'outil, en coordonnées
// de grille (X de gauche à droite, Y de haut en bas, 0 à 15). C'est le pixel qui
// désigne la cible quand l'icône sert de curseur : la pointe du bec du sécateur,
// le tranchant de la bêche, la pomme de l'arrosoir. Pour un objet qu'on POSE
// (bac, pot, ruche…), c'est le milieu de sa base : là où il touchera le sol.
//
// Table notée au ②, CONSOMMÉE au ③ (`Input.SetCustomMouseCursor(texture, forme,
// pointChaud × échelle)`). Rangée par familles, comme les grilles. La vérification
// de démarrage (`IconeGeste.Defauts`) exige un point chaud par grille, posé sur un
// pixel PEINT : retoucher une grille oblige à revoir sa ligne ici.
//
// 📖 Pédagogie C# : `(int X, int Y)` est un TUPLE nommé — une petite paire de
// valeurs sans avoir à déclarer une classe. `PointsChauds["couper"].X` se lit seul.

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesPointsChauds
	{
		public static readonly Dictionary<string, (int X, int Y)> PointsChauds = new()
		{
			// main
			["recolter"] = (8, 8),              // l'ouverture du panier
			["manger"] = (5, 9),                // la chair du fruit
			["glaner"] = (7, 12),               // le creux du poing
			["ecraser"] = (8, 12),              // sous la semelle
			["favoriser_auxiliaire"] = (7, 9),  // le dos de la coccinelle
			// sol
			["becher"] = (7, 15),               // tranchant de la lame
			["grelinette"] = (6, 15),           // pointe d'une dent
			["creuser"] = (4, 14),              // pointe de la pelle
			["drainer"] = (12, 10),             // bouche du drain
			["deraciner"] = (7, 7),             // le collet
			// semis
			["planter"] = (8, 13),              // pied de la butte
			["bouturer"] = (7, 13),             // fond du verre
			["greffer"] = (8, 9),               // la ligature
			["planter_conteneur"] = (7, 13),    // fond du pot
			// taille
			["pincer"] = (2, 5),                // là où les doigts se rejoignent
			["arracher"] = (6, 10),             // le poing
			["couper"] = (1, 1),                // pointe du bec
			["tailler"] = (0, 2),               // pointe de la scie
			// eau
			["arroser"] = (0, 5),               // la pomme de l'arrosoir
			// compost
			["poser_bac"] = (7, 14),
			["poser_pile"] = (7, 14),
			["composter"] = (7, 13),
			["retourner"] = (7, 15),            // dent du milieu
			["epandre"] = (6, 5),               // le chargement
			["empiler_bois"] = (8, 9),
			["pailler"] = (7, 14),
			["broyer"] = (3, 2),                // la trémie
			// structures
			["poser_pot"] = (7, 13),
			["poser_bac_culture"] = (8, 14),
			["deplacer_pot"] = (7, 10),
			["poser_tuteur"] = (7, 15),         // pied du piquet
			["poser_treillis"] = (1, 15),       // pied gauche
			["poser_pergola"] = (3, 14),        // pied du poteau gauche
			["palisser"] = (10, 15),            // bout du brin
			["poser_perchoir"] = (7, 15),
			["poser_voile"] = (8, 13),
			["poser_cloche"] = (7, 15),
			["poser_ombriere"] = (2, 15),
			["poser_ruche"] = (8, 14),
			["recolter_miel"] = (7, 14),
			// paysage
			["abattre"] = (1, 5),               // tranchant du fer
			["receper"] = (12, 5),              // pointe du crochet
			["eteter"] = (7, 5),                // la tête de la trogne
			["endiguer"] = (10, 3),             // crête de la digue
			["deriver"] = (8, 8),               // le lit de la rigole
			["entailler"] = (0, 4),             // pointe de la pioche
		};
	}
}
