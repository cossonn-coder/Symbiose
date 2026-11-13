// SYMBIOSE — icones/IconesMouvements.cs (sprint ICÔNES & CURSEUR ④ — données)
// LE MOUVEMENT de chaque geste : la petite animation que joue le curseur quand le
// pont répond « appliqué ». Les animations sont PARTAGÉES par famille de
// mouvement (conception_refonte_palette.md §5), pas dessinées geste par geste :
// verser, couper, frapper, poser, ramasser, remuer, écraser. Le dessin de
// chaque image vit dans `visuals/AnimationGeste.cs` ; ici, seulement la table.
//
// Rangée par mouvement (et non par famille du tiroir) : c'est ce qui se lit le
// mieux quand on se demande « que fait le curseur quand je bêche ? ». La
// vérification de démarrage (`IconeGeste.Defauts`) exige un mouvement par grille.
//
// 📖 Pédagogie C# : un `enum` est une liste fermée de noms (sous le capot, des
// entiers). Le compilateur refuse une faute de frappe : `Mouvement.Fraper`
// n'existe pas, alors qu'une chaîne "fraper" passerait sans bruit.

using System.Collections.Generic;

namespace Symbiose
{
	internal enum Mouvement { Verser, Couper, Frapper, Poser, Ramasser, Remuer, Ecraser }

	internal static class IconesMouvements
	{
		public static readonly Dictionary<string, Mouvement> Mouvements = new()
		{
			// verser : l'eau tombe de la pomme
			["arroser"] = Mouvement.Verser,
			// couper : la lame recule, mord, un brin tombe
			["pincer"] = Mouvement.Couper,
			["couper"] = Mouvement.Couper,
			["tailler"] = Mouvement.Couper,
			["bouturer"] = Mouvement.Couper,
			["greffer"] = Mouvement.Couper,
			// frapper : l'outil se lève, frappe, la terre gicle
			["becher"] = Mouvement.Frapper,
			["grelinette"] = Mouvement.Frapper,
			["creuser"] = Mouvement.Frapper,
			["drainer"] = Mouvement.Frapper,
			["deraciner"] = Mouvement.Frapper,
			["arracher"] = Mouvement.Frapper,
			["entailler"] = Mouvement.Frapper,
			["abattre"] = Mouvement.Frapper,
			["receper"] = Mouvement.Frapper,
			["eteter"] = Mouvement.Frapper,
			["endiguer"] = Mouvement.Frapper,
			["deriver"] = Mouvement.Frapper,
			// poser : l'objet descend et touche le sol, un peu de poussière
			["poser_bac"] = Mouvement.Poser,
			["poser_pile"] = Mouvement.Poser,
			["poser_pot"] = Mouvement.Poser,
			["poser_bac_culture"] = Mouvement.Poser,
			["poser_tuteur"] = Mouvement.Poser,
			["poser_treillis"] = Mouvement.Poser,
			["poser_pergola"] = Mouvement.Poser,
			["poser_perchoir"] = Mouvement.Poser,
			["poser_voile"] = Mouvement.Poser,
			["poser_cloche"] = Mouvement.Poser,
			["poser_ombriere"] = Mouvement.Poser,
			["poser_ruche"] = Mouvement.Poser,
			["planter"] = Mouvement.Poser,
			["planter_conteneur"] = Mouvement.Poser,
			["deplacer_pot"] = Mouvement.Poser,
			["palisser"] = Mouvement.Poser,
			// ramasser : la main plonge, remonte, deux éclats
			["recolter"] = Mouvement.Ramasser,
			["manger"] = Mouvement.Ramasser,
			["glaner"] = Mouvement.Ramasser,
			["recolter_miel"] = Mouvement.Ramasser,
			["favoriser_auxiliaire"] = Mouvement.Ramasser,
			// remuer : un petit cercle, des miettes de terre
			["composter"] = Mouvement.Remuer,
			["retourner"] = Mouvement.Remuer,
			["epandre"] = Mouvement.Remuer,
			["empiler_bois"] = Mouvement.Remuer,
			["pailler"] = Mouvement.Remuer,
			["broyer"] = Mouvement.Remuer,
			// écraser : la botte se lève et retombe, la poussière s'écarte
			["ecraser"] = Mouvement.Ecraser,
		};
	}
}
