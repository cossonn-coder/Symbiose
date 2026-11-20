// SYMBIOSE — PlantRenderer.SplatsBas.cs (partial, sprint PRÉCUISSON SPLATS ⑤bis)
// Les PIÈCES SPLAT aux paliers BAS (×0,5 / ×1 / ×2) pour les PORTS : herbacées à fiche,
// prairie et lianes se dessinent par leur port à TOUS les paliers (PlantRenderer.cs,
// DessinerPrairie/Port/Liane) — le kit du ⑤ ne les atteint pas. D4 (Nico) : « tous les
// zooms en splats ». Les crochets du ④/④bis valent donc aussi sous ×4 (`SplatsIci` sans
// plancher de palier) ; là où un port prenait un RACCOURCI de loin avant le crochet
// (losange de la tige, tache du tapis), le crochet passe devant le raccourci.
//
// Même interrupteur (Maj+F11, SYMBIOSE_SPLATS=0) ; ancien dessin intact derrière chaque
// crochet. Les pièces ×0,5-×2 sont celles que l'outil a cuites dès le ① (même recette,
// palier différent : 3 à 9 px par organe).
//
// 📖 Pédagogie : de loin, le port gardait ses PROPRES simplifications (moins de feuilles,
// cf. PartFeuillesLoin*) — on n'y touche pas : c'est la DENSITÉ d'information du palier.
// Seule la FORME de chaque organe change (pièce au lieu du losange ou du triangle).
//
// Déterministe (hash, zéro Random), purement visuel : golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// LISIBILITÉ vérifiée sur captures (planche_especes, 00_etat ⑤bis) : à ×0,5 et ×1, une pièce
		// d'ORGANE (tête, fleur, fruit, épi, gousse…) fait 1 à 3 px et perd la tache de couleur
		// qui fait reconnaître l'espèce de loin (cœur jaune du tournesol → anneau pâle, ombelles
		// crème de l'achillée → vert, point rouge du fraisier, grappes de la moutarde). Le dessin
		// garde ces organes sous ×2 ; les FEUILLES restent en pièces à tous les paliers.
		internal const float OrganesSplatMinZoom = 2f;

		private bool OrganesSplatIci => SplatsIci && AuPalier(OrganesSplatMinZoom);

		/// <summary>Tapis (fraisier…) de loin : chaque foliole de la feuille en pièce, comme au ×4,
		/// au lieu de la tache ronde ; false = rien posé (la tache prend le relais).</summary>
		private bool PoserFoliolesSplat(FichePort f, FeuillePosee fe, Color col)
		{
			if (!SplatsIci) return false;
			string recette = RecetteFeuille(f.Feuille, f.Marque);
			int nb = Mathf.Max(f.Tapis.Folioles, 1);
			bool posee = false;
			for (int i = 0; i < nb; i++)
				posee |= PoserFeuilleSplat(recette, fe with { U = fe.U.Rotated(i * Mathf.Tau / nb) }, col);
			return posee;
		}
	}
}
