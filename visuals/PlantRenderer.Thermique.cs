// SYMBIOSE — PlantRenderer.Thermique.cs (partial, sprint NICHE THERMIQUE ⑤, D139)
// La plante MONTRE où elle en est dans sa plage vivable, sans chiffre (philo #5).
// Le moteur exporte, par plante vivante (pont 0.6.18) :
//   · `posture_thermique` ∈ [−1, 1] : < 0 froid, 0 confort, > 0 chaud ;
//   · `palier_thermique` : pendant · violace · froid · gel · effondre (froid)
//                          replie · fletri_midi · bords_jaunis · brulure (chaud) ; null = étalé.
// Et `leaf_symptoms` peut porter deux marques neuves, `froid` et `brulure`.
//
// Deux canaux, comme la sémiologie (PlantRenderer.cs) :
//  · PORT de la feuille, lu sur la posture : côté froid les feuilles PENDENT (de plus en
//    plus jusqu'à l'effondrement) ; côté chaud elles se REPLIENT de profil (limbe étroit).
//    Confort = feuilles étalées, rien ne change.
//  · TEINTE du palier, posée APRÈS le symptôme dominant (SymptomTint) : violacé, vert
//    détrempé translucide, noirci ; flétri terne, jaune aux bords, brûlé roux. « pendant »
//    et « replié » n'ont pas de teinte : c'est la posture qui les dit.
//  · MARQUES fines (×16, avec les autres dans DrawLeafDamage) : taches détrempées du
//    froid, bord roussi de la brûlure. Elles restent tant que le moteur les porte.
//
// 📖 Pédagogie — précuisson : la posture est QUANTIFIÉE (8 échelons par demi-échelle,
// 2 par palier, comme un CAN à 3 bits). La plante ne se salit (Invalidate → recuisson
// par la file à budget) qu'au changement d'échelon ou de palier, au pas du snapshot
// hebdomadaire : aucune déformation n'est recalculée par frame. La vue ne recalcule
// aucune température : elle traduit ce que le moteur a décidé.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const float EchelonsPosture = 8f;
		// Côté froid : abaissement des feuilles (cm) à posture −1 (effondrée).
		private const float PendThermiqueCm = 10f;
		// Côté chaud : part de fermeture du limbe à posture +1 (même échelle que la
		// canicule, HeatFoldMax : la feuille se roule, se montre de profil).
		private const float PliThermiqueMax = 1f;
		// Teinte d'un palier : part de base + part qui croît dans le palier.
		private const float TeinteBase = 0.6f, TeinteDansPalier = 0.4f;

		private static readonly Color ThViolace = Palette16.ThViolace;
		private static readonly Color ThDetrempe = Palette16.ThDetrempe;
		private static readonly Color ThNoirci = Palette16.ThNoirci;
		private static readonly Color ThBordsJaunis = Palette16.ThBordsJaunis;
		private static readonly Color ThBrule = Palette16.ThBrule;

		private float _posture;          // posture quantifiée ∈ [−1, 1]
		private string _palierTh;        // palier nommé, null = feuilles étalées
		private float _froidMarque, _brulureMarque;   // marques `froid`/`brulure` (leaf_symptoms)

		/// <summary>Plage vivable en °C (pont 0.6.19) : gel, froid, chaud, brûlure, puis
		/// nuit et feuille vécues — NaN si absent. Lue par le survol G (debug) seulement.</summary>
		public float[] PlageThermique { get; set; }

		/// <summary>Posture et palier du snapshot ; salit la plante au changement
		/// d'échelon ou de palier seulement.</summary>
		public void SetThermique(float posture, string palier)
		{
			float q = Mathf.Round(Mathf.Clamp(posture, -1f, 1f) * EchelonsPosture) / EchelonsPosture;
			if (q == _posture && palier == _palierTh) return;   // early-out : pas de cuisson
			_posture = q;
			_palierTh = palier;
			Invalidate();
		}

		/// <summary>Part froide de la posture ∈ [0, 1] (0 = confort).</summary>
		private float PendThermique => Mathf.Max(0f, -_posture);
		/// <summary>Part chaude de la posture ∈ [0, 1] (0 = confort).</summary>
		private float PliThermique => Mathf.Max(0f, _posture) * PliThermiqueMax;

		/// <summary>Abaissement (cm) des feuilles par le froid : ajouté à LeafDropCm.</summary>
		private float PendThermiqueDropCm => PendThermique * PendThermiqueCm;

		// Intensité DANS le palier courant ∈ [0, 1] : chaque palier occupe un quart de la
		// demi-échelle (bandes de sim/engine/posture_thermique.py).
		private float DansPalier()
		{
			float m = Mathf.Abs(_posture) * 4f;
			return m >= 4f ? 1f : m - Mathf.Floor(m);
		}

		/// <summary>Teinte du palier thermique sur un tissu vert (après SymptomTint).
		/// Identité au confort, à « pendant » et à « replié ».</summary>
		private Color TeinteThermique(Color tissu)
		{
			Color cible;
			float part;
			switch (_palierTh)
			{
				case "violace":      cible = ThViolace; part = 0.45f; break;
				case "froid":        cible = ThDetrempe; part = 0.5f; break;
				case "gel":          cible = ThNoirci; part = 0.6f; break;
				case "effondre":     cible = ThNoirci; part = 0.8f; break;
				case "fletri_midi":  cible = Palette16.SymSecheresse; part = 0.3f; break;
				case "bords_jaunis": cible = ThBordsJaunis; part = 0.45f; break;
				case "brulure":      cible = ThBrule; part = 0.65f; break;
				default: return tissu;
			}
			return tissu.Lerp(cible, part * (TeinteBase + TeinteDansPalier * DansPalier()));
		}

		/// <summary>Port d'une feuille de fiche (PointFeuille) : hauteur du point `lg` de
		/// la feuille, abaissée par le froid (le bout pend plus que la base).</summary>
		private float HautZThermique(float hautZ, float lg, float longueur)
		{
			float p = PendThermique;
			return p <= 0f ? hautZ : hautZ * (1f - p) - p * lg * lg * longueur * 0.6f;
		}

		/// <summary>Marques fines thermiques d'une feuille (×16, DrawLeafDamage) :
		/// taches détrempées (froid sans gel), bord roussi (brûlure).</summary>
		private void DrawMarquesThermiques(Vector2 c, float r, int i, int j)
		{
			int taches = Mathf.CeilToInt(_froidMarque * 3f);   // 0 à 3 taches
			for (int k = 0; k < taches; k++)
				DrawCircle(PointDansLimbe(c, r, 71 + k, 73 + k, i, j, 0.15f, 0.5f),
						   r * 0.2f, Lit(ThDetrempe));
			if (_brulureMarque > 0f)
				DrawEllipseOutline(c, r * 1.15f, r * 0.65f * LeafOpen, Lit(ThBrule),
								   Mathf.Max(PixelInterne, r * 0.2f * _brulureMarque));
		}

		/// <summary>Recopie l'état thermique vers le pinceau de cuisson.</summary>
		private void CopierThermique(PlantRenderer brush)
		{
			brush._posture = _posture;
			brush._palierTh = _palierTh;
			brush._froidMarque = _froidMarque;
			brush._brulureMarque = _brulureMarque;
		}
	}
}
