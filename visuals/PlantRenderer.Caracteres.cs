// SYMBIOSE — PlantRenderer.Caracteres.cs (partial de PlantRenderer, D139 caractères
// vivants ⑤). Ce que la plante sait de ses CARACTÈRES HÉRITABLES côté vue.
//
// ⑤ ne pose que la donnée de debug du survol G : la LIGNÉE VÉCUE de l'année
// (fécondation, pollen donné, part autofécondée), relue par WorldView.Genes.cs.
// Les signes visibles dérivés (`signes_car`, `rejets`, `sans_graines`, pont 0.6.20)
// sont dessinés au tronçon ⑥ — ce fichier est leur place.
//
// 📖 Pédagogie : comme `PlageThermique`, une simple propriété C# auto-implémentée
// (`{ get; set; }`) : le compilateur génère le champ caché. Pas de redessin à la
// pose — la valeur n'est lue qu'au survol, jamais par _Draw.

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>Lignée vécue (pont 0.6.20) : [fécondation, pollen donné, part
		/// autofécondée ∈ [0,1]] ; null si absente (ancien serveur, plante morte).</summary>
		public float[] FecondationVecue { get; set; }
	}
}
