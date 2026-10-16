// SYMBIOSE — WorldView.Piqure.cs (partial de WorldView, arc pollinisation ⑦ §J)
// LA RÉACTION TEMPS RÉEL de la piqûre (couche joueur, phase Saison). Le moteur
// EXPOSE l'état (champ `alarme` par plot + densité d'abeilles via les butineurs) ;
// la vue, elle, ANIME la piqûre et applique le coût Vigueur. Câblé chaque frame
// en Saison depuis _Process.
//
// 📖 Pédagogie — pourquoi « vue pure » et ce que ça implique (décision Nico) :
// le pont moteur ne parle qu'aux frontières de semaine (60 s), mais la piqûre
// est par-frame. Ici la perte de Vigueur est LOCALE et AFFICHÉE — elle est
// ÉCRASÉE au prochain snapshot (le moteur n'en sait rien). C'est un prototype de
// RESSENTI, pas la persistance : faire débiter la Vigueur et injecter la
// perturbation côté moteur demanderait un aller-retour (verbe dédié) — laissé à
// un sprint futur. Conséquence assumée : aucune ligne Python, golden non touché.
//
// 📖 Pédagogie — pas de Random (esprit MacroLife) : on N'tire PAS un dé à chaque
// frame. On ACCUMULE un débit `taux × intensité × densité × delta` ; chaque fois
// que l'accumulateur franchit 1, UNE piqûre part. Plus l'alarme est forte et les
// abeilles nombreuses, plus les piqûres pleuvent — émergent, déterministe, sans
// règle « −X Vigueur » arbitraire (philo #2). L'accumulateur se VIDE dès qu'on
// quitte un foyer (curseur hors alarme/abeille) : pas de piqûre « en retard ».
//
// 📖 Pédagogie — l'enfumoir est porté IMPLICITEMENT : le moteur ne dépose
// l'alarme du canal miel que si la récolte est À NU (équipé → aucun foyer). Seul
// « écraser une abeille » dépose toujours. Donc l'atténuation §J vit déjà dans
// la PRÉSENCE/ABSENCE de foyers — la vue n'a pas à connaître l'équipement.

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Rayon (cm monde) autour du curseur où une abeille en alarme peut piquer.
		private const float RayonPiqureCm = 70f;
		// Gain : piqûres/seconde = TauxPiqure × intensité_alarme × densité_abeille.
		// Calibrage post-F5 (« ça pique trop / pas assez » → cette seule constante).
		private const float TauxPiqure = 0.8f;
		// Coût Vigueur d'une piqûre (LOCAL, écrasé au prochain snapshot — MVP).
		private const float CoutPiqure = 1.5f;
		private float _stingAccum;     // accumulateur déterministe (cf. en-tête)

		// Appelée chaque frame en phase Saison (depuis _Process). Early-out total
		// hors alarme/abeille → coût nul (le cas NORMAL : aucun foyer posé).
		private void TickPiqure(float delta)
		{
			if (_world == null || _foragerLayer == null || _vigueur <= 0.0)
			{
				_stingAccum = 0f;
				return;
			}
			Vector2 w = _sourisMonde;   // souris de la frame (T3)
			if (!FindPlot(w, out string tile, out int r, out int c))
			{
				_stingAccum = 0f;   // curseur hors tuile (chemin/maison)
				return;
			}
			float intensite = AlarmeAt(tile, r, c);
			if (intensite <= 0f) { _stingAccum = 0f; return; }
			float densite = _foragerLayer.DensiteAbeillePres(w, RayonPiqureCm);
			if (densite <= 0f) { _stingAccum = 0f; return; }

			_stingAccum += delta * TauxPiqure * intensite * densite;
			// Boucle bornée : à débit raisonnable l'accumulateur ne dépasse 1 que
			// d'un cran par frame ; le `while` couvre un débit exceptionnel.
			while (_stingAccum >= 1f)
			{
				_stingAccum -= 1f;
				Piquer(w);
			}
		}

		// Intensité d'alarme au plot (tile, r, c), 0 si aucun foyer (lookup O(1)).
		private float AlarmeAt(string tile, int r, int c) =>
			_alarme.TryGetValue(tile, out var d)
			&& d.TryGetValue((r, c), out float v) ? v : 0f;

		// UNE piqûre : coût Vigueur LOCAL (clampé ≥ 0) + éclat au point monde.
		private void Piquer(Vector2 w)
		{
			_vigueur = System.Math.Max(0.0, _vigueur - CoutPiqure);
			UpdateActionHud();
			AddWorld(new PiqureFlash
			{
				Position = WorldToScreen(w.X, w.Y),
				ZIndex = 20,   // au-dessus des objets (10) — un effet, pas un volume
			});
		}
	}
}
