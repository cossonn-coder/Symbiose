// SYMBIOSE — ProgressionChargement.cs (sprint LISIÈRE & CHARGEMENT ④, décision L6)
// La PROGRESSION de l'écran de chargement, un nombre de 0 à 1 que le mycélium dessine.
// Quatre phases mesurées, chacune une part fixe de la barre :
//   gerbes (atlas des gerbes) → pont (init + warmup du moteur Python) → montage (arbre de
//   scène) → cuisson du cadre (file de précuisson jusqu'au repos).
// Pendant une phase de durée INCONNUE (gerbes, pont, montage), l'avance est asymptotique
// vers le plafond de la phase ; la cuisson a une fraction CONNUE (1 − file restante / file
// la plus longue vue). La valeur affichée ne recule jamais (max) et rejoint la cible en
// douceur : elle pousse comme un être vivant, sans bond.
//
// 📖 Pédagogie : 1 − e^(−t/τ) monte vite puis ralentit sans jamais atteindre 1 — à t = τ
// (durée attendue) on est à 63 %, à 3τ à 95 %. Une phase plus longue que prévu ne crève
// donc pas son plafond ; plus courte, la phase suivante reprend de son plancher. C'est le
// même lissage exponentiel qu'un filtre RC du 1er ordre en électronique.
//
// Aucun nœud Godot ici : classe pure, testable, appelée par WorldView.Chargement.cs.

namespace Symbiose
{
	public enum PhaseChargement { Gerbes, Pont, Montage, Cuisson, Fini }

	public sealed class ProgressionChargement
	{
		// Parts de la barre = parts des durées MESURÉES (banc `capture_vm.sh -b full -J`, 00_etat ④) :
		// gerbes 0,39 s · pont 14,9 s · montage 1,6-1,7 s · cuisson 15,0-15,6 s [VM llvmpipe charge 3-4,
		// n=2]. Somme 1 (la fin de la cuisson = 1).
		private static readonly float[] Part = { 0.01f, 0.46f, 0.05f, 0.48f };
		// Durée attendue (s) des phases à durée inconnue = τ de l'avance asymptotique (pont : ~2/3 de
		// la mesure VM, le PC est plus rapide ; à 1 τ la phase est à 63 % de sa part).
		private static readonly float[] Tau = { 0.2f, 10f, 1f, 0f };
		// Vitesse du lissage de l'affichage (1/s) : rattrape 63 % de l'écart en 1/6 s.
		private const float Lissage = 6f;

		private PhaseChargement _phase = PhaseChargement.Gerbes;
		private double _t0;
		private float _cible, _affiche;

		/// <summary>La valeur à dessiner (0 → 1), monotone.</summary>
		public float Valeur => _affiche;
		public PhaseChargement Courante => _phase;

		private static float Plancher(PhaseChargement ph)
		{
			float s = 0f;
			for (int i = 0; i < (int)ph && i < Part.Length; i++) s += Part[i];
			return s;
		}

		/// <summary>Passe à la phase `ph` (horloge en s) : la cible monte au moins à son plancher.</summary>
		public void Entrer(PhaseChargement ph, double maintenant)
		{
			_phase = ph;
			_t0 = maintenant;
			_cible = System.Math.Max(_cible, ph == PhaseChargement.Fini ? 1f : Plancher(ph));
		}

		/// <summary>Une image : `fraction` ∈ [0, 1] si la phase la connaît (cuisson), sinon &lt; 0.</summary>
		public void Avancer(double maintenant, double delta, float fraction = -1f)
		{
			if (_phase != PhaseChargement.Fini)
			{
				int i = (int)_phase;
				float f = fraction >= 0f ? System.Math.Min(fraction, 1f)
					: 1f - (float)System.Math.Exp(-(maintenant - _t0) / System.Math.Max(Tau[i], 0.01f));
				_cible = System.Math.Max(_cible, Plancher(_phase) + Part[i] * f);
			}
			float pas = (_cible - _affiche) * (1f - (float)System.Math.Exp(-delta * Lissage));
			_affiche = System.Math.Min(1f, System.Math.Max(_affiche, _affiche + pas));
			if (_cible - _affiche < 0.001f) _affiche = _cible;   // l'exponentielle n'arrive jamais seule
		}
	}
}
