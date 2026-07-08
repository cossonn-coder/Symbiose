// SYMBIOSE — WorldView.Paillage.cs (partial de WorldView, sprint équilibre invasion ⑧, D69)
// Le câblage VUE du PAILLAGE : applique le bloc `paillage` du snapshot (tapis de
// mulch au sol, MulchLayer) — lecture seule (protocole 0.5.20). La donnée (profondeur,
// nature du mulch) vient du moteur, Python reste source de vérité : ici on ne fait que
// PROJETER, jamais recalculer (Godot est « bête »).
//
// 📖 Pédagogie — l'ABRI de la faune sous le mulch (D11, tronçon ⑥) est DÉJÀ rendu :
// le moteur fait émerger plus de faune ombrophile (carabe/lombric/cloporte/hérisson/
// limace) sur les plots mulchés (le champ de population lit `paillage` comme habitat),
// et cette densité accrue arrive au snapshot dans le bloc `sprites` que MacroLife
// dessine déjà. Aucun code de vue spécifique à l'abri : plus de mulch → plus de
// bestioles à son ombre, automatiquement. La couche mulch (dessous) + la vie macro
// (dessus) racontent ensemble « la couverture abrite le vivant ».

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Tapis de mulch au sol (⑧) : layer batché, enfant direct de WorldView (survit
		// à RebuildWorld). Lit le bloc `paillage` (0.5.20). ZIndex 1 = bande de la
		// litière (cf. instanciation dans WorldView.cs).
		private MulchLayer _mulchLayer;

		// Applique le bloc `paillage` (lecture tolérante : un snapshot pré-0.5.20 n'a
		// pas la clé → pas de mulch dessiné, jamais de crash). Reconstruction pleine
		// (le mulch est inerte entre deux semaines, pas de fondu à tenir).
		private void ApplyPaillage(GDict paillage)
		{
			_mulchLayer?.SetPaillage(paillage, _origins);
		}
	}
}
