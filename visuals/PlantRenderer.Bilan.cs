// SYMBIOSE — PlantRenderer.Bilan.cs (partial de PlantRenderer, PLANTE VIVANTE ⑥, D140 G)
// Ce que la vue montre du BILAN CARBONE d'une plante (pont 0.6.21) :
//   · `feuillage_bilan` (part des feuilles PORTÉES) → MOINS de feuilles dessinées. Ce
//     n'est pas une teinte de dégât : la densité passe par `PlantStructure.PartPortee`,
//     que tous les ports lisent déjà (StructureLoader la remplit depuis le snapshot) ;
//   · `reserves` (part de la capacité) → la plante à bout de forces TERNIT, par le
//     canal existant de la vitalité (`SetVitality` → ApplyVitality). On lui donne les
//     FORCES = min(1, réserves / R_CONFORT), et non `vitalite` : la vitalité moteur
//     compte aussi le feuillage, qui se voit déjà en nombre de feuilles — un chêne
//     défeuillé à réserves pleines doit paraître NU, pas malade (conception §3, §9).
//
// 📖 Pédagogie (côté vue, à la manière de l'embarqué) : la vue ne recalcule aucun
// bilan, elle LIT deux registres que le moteur publie chaque semaine et les traduit
// en signes (densité, teinte, une phrase). Le seul état gardé ici est la valeur de la
// semaine précédente du feuillage, pour savoir s'il REMONTE (« refait ses feuilles ») —
// un détecteur de front, comme sur une entrée échantillonnée.
//
// Philo #5 : aucun chiffre hors Maj+F3 ; les phrases viennent de la légende Python
// (`voix_bilan`, sim/signes_corpus.py), la vue ne choisit que laquelle dire.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Miroir de `plants/base/instance.py` R_CONFORT : réserves au-dessus desquelles
		// la plante ne manque de rien (vitalité moteur = min(1, réserves/R_CONFORT) × …).
		public const float RConfort = 0.5f;
		// Seuils des phrases (réglage F5). Forces < 0,6 = réserves < 0,3 : la teinte est
		// déjà franchement ternie (ApplyVitality) ; feuillage < 0,6 = la couronne a perdu
		// près de la moitié de ses feuilles, ça se voit à tout palier.
		public const float SeuilEpuise = 0.6f;
		public const float SeuilClairseme = 0.6f;
		public const float SeuilRefait = 0.95f;   // au-dessus : feuillage complet, rien à dire

		private float _feuillageBilan = 1f, _reserves = 1f;
		private bool _feuillageMonte;   // dernière variation du feuillage = une hausse
		private bool _bilanLu;          // une 1re valeur reçue : avant, pas de « variation »

		// Lus par l'info-bulle (Maj+F3 seulement pour les valeurs brutes).
		public float FeuillageBilan => _feuillageBilan;
		public float Reserves => _reserves;

		/// <summary>Bilan de la semaine : `vitalite` (repli si le pont ne publie pas les
		/// réserves, < 0 = absentes), `feuillage` ∈ [0,1], `reserves` ∈ [0,1].</summary>
		public void SetBilan(float vitalite, float feuillage, float reserves)
		{
			if (!Mathf.IsEqualApprox(feuillage, _feuillageBilan))
			{
				// Ne bouge qu'au CHANGEMENT : deux snapshots de la même semaine (une
				// action rejouée) ne doivent pas effacer la hausse.
				// La 1re valeur reçue n'est pas une variation (le défaut 1 n'a jamais été vu).
				_feuillageMonte = _bilanLu && feuillage > _feuillageBilan;
				_feuillageBilan = feuillage;
			}
			_bilanLu = true;
			_reserves = reserves < 0f ? 1f : reserves;
			SetVitality(reserves < 0f ? vitalite : Mathf.Min(1f, reserves / RConfort));
		}

		/// <summary>Clé de la phrase de bilan (`voix_bilan`), ou null si rien à dire.
		/// « épuisé » n'est dit que si la teinte se voit au palier (`santeVisible`) — on
		/// ne dit pas ce qu'on ne montre pas ; le nombre de feuilles se voit partout.</summary>
		public string EtatBilan(bool santeVisible)
		{
			if (santeVisible && _vitalite < SeuilEpuise) return "epuise";
			if (_feuillageMonte && _feuillageBilan < SeuilRefait) return "refait";
			if (_feuillageBilan < SeuilClairseme) return "clairseme";
			return null;
		}
	}
}
