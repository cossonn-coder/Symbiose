// SYMBIOSE — PlantRenderer.BancSeuil.cs (partial, INFO-BULLE DU VIVANT ②)
// Le côté PLANTE du banc de mesure du SEUIL DE VISIBILITÉ (WorldView.BancSeuil.cs) :
// pose sur la plante témoin un état de santé ARTIFICIEL (un seul symptôme colorant
// d'intensité i, ou une vitalité 1 − i, ou un automne i), sur fond sain, pour que
// le banc compare l'image rendue à celle de l'état sain (i = 0).
//
// 📖 Pédagogie — pourquoi forcer l'état ici et pas au pont : on veut mesurer la
// CHAÎNE DE RENDU (teinte → cuisson → écran), pas la simulation. Le banc remplace
// donc ce que le snapshot aurait posé (SetSymptoms / SetVitality / Automne), par
// les MÊMES portes d'entrée : aucun chemin de dessin dédié, l'image mesurée est
// exactement celle du jeu. Banc VM seulement (mode capture) — jamais appelé au F5.

using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>Causes du canal COULEUR (celles dont le banc mesure le seuil).</summary>
		internal static IEnumerable<string> CausesColorantes => ColorantTints.Keys;

		/// <summary>État de banc : fond sain (vitalité 1, automne 0, aucun symptôme),
		/// puis `cause` à l'intensité `i` — une cause colorante, "vitalite" (manque
		/// i) ou "automne" (phénophase i). i = 0 → la plante saine de référence.</summary>
		internal void ForcerEtatBanc(string cause, float i)
		{
			_structure.Automne = cause == "automne" ? i : 0f;
			_vitalite = cause == "vitalite" ? 1f - i : 1f;
			var syms = new Godot.Collections.Array();
			if (i > 0f && ColorantTints.ContainsKey(cause))
				syms.Add(new GDict { ["cause"] = cause, ["intensity"] = i });
			SetSymptoms(syms);   // pose la teinte + Invalidate (recuisson)
		}
	}
}
