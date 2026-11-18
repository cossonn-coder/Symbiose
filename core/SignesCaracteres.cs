// SYMBIOSE — SignesCaracteres.cs (D139 caractères vivants ⑥)
// Les SIGNES VISIBLES des caractères héritables d'une plante, tels que le pont les envoie
// (`signes_car`, pont 0.6.20, `sim/signes_caracteres.py`). Jamais un gène brut : le moteur
// a déjà traduit chaque caractère en grandeur de dessin, la vue ne fait que la lire.
//
//   teinte_fleur    [teinte °, saturation]  couleur_fleur (axe de l'espèce)
//   echelle_fleur   × rayon de la fleur      taille_fleur (√)
//   contraste_guides ∈ [0, 1]                guide_nectar (lignes, œil central)
//   matite_feuille  ∈ [0, 1]                 coriacite_feuille (0,5 = neutre)
//   port            ∈ [−1, 1]                dominance_apicale (buisson → flèche)
//
// `echelle_fruit` n'est PAS lu : la masse d'un fruit envoyée par le pont (`fruits[].masse`)
// porte déjà le gène `taille_fruit` (decompo.nouer), et le rayon dessiné la suit (Ports.cs,
// RayonFruit). Le relire ici compterait le gène deux fois.
//
// 📖 Pédagogie : une classe C# `sealed` à champs publics se lit comme un `struct` C rempli
// une fois. Elle est construite sur le thread du pool (PlanteLue.Lire), puis seulement LUE
// par le fil principal : aucun verrou nécessaire, personne ne l'écrit ensuite.

using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public sealed class SignesCaracteres
	{
		/// <summary>Plante sans signe de fleur : pas d'axe de couleur (anémophile…).</summary>
		public bool AFleur;
		public float TeinteDeg, Saturation, EchelleFleur = 1f, ContrasteGuides = 0.5f;
		public float MatiteFeuille = 0.5f, Port;

		/// <summary>Lit `signes_car` (tolérant : clé absente = valeur neutre).</summary>
		public static SignesCaracteres Lire(GDict d)
		{
			var s = new SignesCaracteres();
			if (LectureSnap.A(d, "matite_feuille")) s.MatiteFeuille = LectureSnap.F(d, "matite_feuille");
			if (LectureSnap.A(d, "port")) s.Port = LectureSnap.F(d, "port");
			if (!LectureSnap.A(d, "teinte_fleur")) return s;
			using (var t = LectureSnap.Tab(d, "teinte_fleur"))
			{
				s.TeinteDeg = (float)LectureSnap.D(t, 0);
				s.Saturation = (float)LectureSnap.D(t, 1);
			}
			s.AFleur = true;
			if (LectureSnap.A(d, "echelle_fleur")) s.EchelleFleur = LectureSnap.F(d, "echelle_fleur");
			if (LectureSnap.A(d, "contraste_guides")) s.ContrasteGuides = LectureSnap.F(d, "contraste_guides");
			return s;
		}
	}
}
