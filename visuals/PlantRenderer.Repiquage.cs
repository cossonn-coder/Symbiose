// SYMBIOSE — PlantRenderer.Repiquage.cs (partial, sprint DÉPART DU JARDIN ⑥, D140 C)
// Le CHOC DE REPIQUAGE se voit, sans chiffre (philo #5) : un plant sorti de son pot a
// perdu une part de son chevelu (motte, ou chignon s'il était à l'étroit). Le moteur
// exporte cette part, `memoires.racines_coupees` ∈ [0, 1] (pont 0.6.25), qui redescend
// au fil des semaines où la plante refait ses racines (`sim/repiquage.py`).
//
// Signe choisi (kickoff ⑥) : les feuilles PENDENT un peu, proportionnellement à ce qui
// manque — la plante boit mal tant que ses poils absorbants ne sont pas refaits. Même
// canal que le froid (abaissement ajouté à LeafDropCm, PlantRenderer.Meteo.cs), en plus
// discret : un repiquage n'est pas une gelée. Aucune teinte : c'est le port qui le dit.
//
// 📖 Pédagogie — comme la posture thermique, la valeur est QUANTIFIÉE (4 échelons) : la
// plante ne se recuit qu'au changement d'échelon, au pas du snapshot hebdomadaire
// (chignon 0,70 → 0,55 → 0,40 → 0,25 → 0,10 → 0 : un cran de moins par semaine).

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const float EchelonsRepiquage = 4f;
		// Abaissement des feuilles (cm) à racines_coupees = 1 (jamais atteint : un chignon
		// coupe 0,70 → ≈ 4 cm, la moitié de ce que fait une plante saisie par le froid).
		private const float PendRepiquageCm = 6f;

		private float _repiquage;   // part du chevelu manquante, quantifiée ∈ [0, 1]

		/// <summary>Part du chevelu perdue au repiquage (snapshot) ; salit la plante au
		/// changement d'échelon seulement.</summary>
		public void SetRepiquage(float racinesCoupees)
		{
			float q = Mathf.Round(Mathf.Clamp(racinesCoupees, 0f, 1f) * EchelonsRepiquage) / EchelonsRepiquage;
			if (q == _repiquage) return;   // early-out : pas de cuisson
			_repiquage = q;
			Invalidate();
		}

		/// <summary>Abaissement (cm) des feuilles par le choc : ajouté à LeafDropCm.</summary>
		private float PendRepiquageDropCm => _repiquage * PendRepiquageCm;

		/// <summary>Recopie l'état de repiquage vers le pinceau de cuisson.</summary>
		private void CopierRepiquage(PlantRenderer brush) => brush._repiquage = _repiquage;
	}
}
