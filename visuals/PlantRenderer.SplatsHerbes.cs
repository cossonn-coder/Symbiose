// SYMBIOSE — PlantRenderer.SplatsHerbes.cs (partial, sprint RELIQUATS DES PLANTES ④)
// Les PIÈCES SPLAT des herbacées qui restaient DESSINÉES faute de recette (00_etat ④bis du
// sprint (a), « Reste DESSINÉ ») :
//  • TRÈFLE : feuille à 3 folioles (`feuille_trefle`) ; 4 folioles (`feuille_trefle4`) sur le pied
//    que le MOTEUR marque `quatre_feuilles` (sim/quatre_feuilles.py, ~1 pied sur 200) — la vue ne
//    tire aucune rareté elle-même : un trèfle à quatre feuilles qu'on ne pourrait pas cueillir
//    serait un faux indice (philo #5) ;
//  • BUISSON : chaque « grain » de la masse devient un rameau de thym (`feuille_thym`) ou une
//    touffe de lames de lavande (`feuille_lavande`), posé sur le dôme sombre qui fait le coussin ;
//  • FÉTUQUE : sa panicule rousse (`panicule_fetuque`) au bout de la tige nue.
// Les anthères du blé et le cœur des fleurons du kit sont des sur-couches / pièces déjà posées
// ailleurs (SplatsDetails.cs, KitSplats.cs).
//
// Même outillage et même interrupteur que le ④ (Maj+F11, SYMBIOSE_SPLATS=0) ; chaque fonction rend
// false quand elle n'a rien posé, et l'ancien dessin vectoriel prend le relais, intact.
// Feuilles (trèfle, thym, lavande) : à TOUS les paliers (D4, ⑤bis) ; panicule : organe, dès ×2
// (OrganesSplatMinZoom, SplatsBas.cs), comme les autres têtes.
//
// 📖 Pédagogie : un crochet = « essaie la pièce, sinon dessine comme avant ». C'est le patron du
// repli (fallback) : le nouveau chemin s'ajoute DEVANT l'ancien sans le modifier, et un seul
// interrupteur permet de comparer les deux à l'écran.
//
// Déterministe (hash, zéro Random), purement visuel : golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>Feuille de trèfle de folioles de `tailleCm`, à plat, centrée en `p` (sommet du
		/// pétiole), tournée de `az` au sol. Le pétiole reste un trait (dès ×8, comme PoserFeuille).</summary>
		private bool PoserTrefleSplat(Vector3 p, float tailleCm, int folioles, float az, Color col, int k)
		{
			string recette = folioles == 4 ? "feuille_trefle4" : "feuille_trefle";
			if (!SplatsIci || !SplatPlanches.Vues(recette, out _, out _, out _)) return false;
			Vector2 centre = Iso(p.X, p.Y, p.Z);
			if (AuPalier(PalierOrganesZoom))
				_lotPrairie.Ligne(Iso(p.X, p.Y, 0f), centre, Ton(col, 1), PixelInterne);
			return PoserPieceFeuille(recette, centre, 0f, WorldView.WorldToScreenOffset(Mathf.Cos(az), Mathf.Sin(az)),
				k, col, tailleCm);
		}

		/// <summary>Un grain de la masse du buisson en `c`, tourné vers `dehors` (direction ÉCRAN, du
		/// centre du dôme vers le grain) : rameau de thym, ou touffe de lames pour une feuille Ruban.</summary>
		private bool PoserGrainSplat(bool lames, Vector2 c, Vector2 dehors, Color col, float grainCm, int k) =>
			SplatsIci && PoserPieceFeuille(lames ? "feuille_lavande" : "feuille_thym", c, 0f, dehors, k, col, grainCm);

		/// <summary>Panicule de la fétuque au bout de sa tige (`tete`), teinte des épillets roux.</summary>
		private bool PoserPaniculeFetuqueSplat(Vector2 tete, Color teinte, int graine) =>
			PoserOrganeSplat("panicule_fetuque", tete, Vector2.Zero, teinte, graine);
	}
}
