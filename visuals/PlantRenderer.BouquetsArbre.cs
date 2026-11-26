// SYMBIOSE — PlantRenderer.BouquetsArbre.cs (partial, sprint BOIS & ARBRES ④)
// Les FLEURS D'ARBRE AU PALIER ×4 en BOUQUETS CUITS : un éperon fleuri = UNE pièce splat
// (`bouquet_corolles`, 11 corolles en dôme ; `bouquet_boutons` à la montée), posée sur les mêmes
// sites que les fleurs une à une de ×8 (FleursHouppier : bout de chaque bout de bois + éperon au
// milieu des brindilles, même tirage au hash, canal 543).
//
// 📖 Pédagogie — pourquoi le ×4 était clairsemé. Le kickoff supposait le plafond de 1 500 fleurs
// (`FleursArbreMax`). Mesuré : un pommier du banc `verger_floraison` n'a que 36 bouts de bois
// → ~210 fleurs, loin du plafond. Le vide venait de la TAILLE : une fleur de 3 cm fait 5-6 px à
// ×4, un bouquet de 4 fleurs un point. L'ancienne gerbe en serrait 14 sur 30 cm. Le bouquet cuit
// porte 11 corolles sur ~10 cm pour 2 tracés (pétales + cœurs), au lieu de 2 tracés PAR fleur.
//
// Densité = l'indice du moteur (philo #5) : la part des sites fleuris suit `floraison`
// (PartFleursArbre), sans plafond ; la part de bouquets en boutons suit PartBoutons, comme les
// gerbes. Aucun site hors de `floraison`. Zéro Random (canaux 543, 579, 607), golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>×4, pièces allumées : un bouquet cuit par site fleuri. Faux si les recettes ne sont
		/// pas sur disque (la vue retombe alors sur les fleurs une à une).</summary>
		private bool DrawBouquetsArbre(Vector3 c, in OrganPalette pal, in FicheFleurArbre fiche)
		{
			if (!SplatsIci || !SplatPlanches.Vues("bouquet_corolles", out _, out _, out _)
				|| !SplatPlanches.Vues("bouquet_boutons", out _, out _, out _)) return false;
			float part = PartFleursArbre() * PartBrindillesFleuries, boutons = PartBoutons();
			_lotPrairie?.Vider();   // pas de lot périmé vidé par la 1ʳᵉ pièce (cf. DrawPiecesFleurs)
			if (part <= 0f) return true;
			foreach (var e in BoisDuHouppier())
				for (int site = 0; site < (e.EstRameau ? 1 : 2); site++)
				{
					int rang = e.Rang + site * 4096;
					if (Hash01(543, e.Cle, rang) >= part) continue;
					Vector3 p = site == 0 ? e.B : e.B.Lerp(e.A, 0.45f);
					Vector2 pos = Iso(p.X - c.X, p.Y - c.Y, p.Z);
					int graine = Melange(e.Cle, rang) & 0xFFFFF;
					if (Hash01(579, e.Cle, rang) < boutons)
						PoserOrganeSplat("bouquet_boutons", pos, Vector2.Zero, fiche.Bouton, graine);
					else
						PoserOrganeSplat("bouquet_corolles", pos, Vector2.Zero, pal.Flower, graine);
				}
			return true;
		}
	}
}
