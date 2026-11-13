// SYMBIOSE — WorldView.Habitats.cs (partial de WorldView, GESTES LISIBLES ④)
// Deux lectures du snapshot pour que les gestes sur la FAUNE se comprennent :
//  - `habitats_auxiliaires` (pont 0.6.15) : `favoriser_auxiliaire` doit SE VOIR. Chaque
//    tige qui porte des rondelles `auxiliaire` est dessinée (HabitatAuxiliaire) ;
//  - `volants` (pont 0.6.14) : les espèces qui volent ne sont pas des cibles d'`ecraser`
//    (le moteur les refuse ; la vue ne les désigne même pas, WorldView.ActionDispatch).
//
// 📖 Où pousse la tige ? La rondelle est au niveau de la TUILE (pas d'un plot, cf.
// `sim/actions/gestes.favoriser_auxiliaire`) ; le moteur donne le RANG de la tige
// (`slot_id`, 0..9). La vue range ces dix tiges à intervalles réguliers le long du bord
// nord de la tuile : une convention de placement fixe (déterministe), pas un fait
// inventé — le nombre de tiges et de rondelles reste celui du moteur.
// Reconstruction pleine à chaque snapshot (une poignée de nœuds, patron des conteneurs) :
// le pivot de vue repasse par ApplySnapshot, les tiges suivent.

using System.Collections.Generic;
using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private const int TigesParTuile = 10;          // = StakeSlot 0–9 du moteur
		private const float TigeBordNordCm = 12f;      // retrait de la tige depuis le bord nord

		private readonly List<HabitatAuxiliaire> _habitats = new();
		private HashSet<string> _volants;               // null = clé absente (ancien serveur)

		private void LireVolants(GDict snap)
		{
			if (!snap.ContainsKey("volants")) return;
			_volants = new HashSet<string>();
			foreach (var v in snap["volants"].AsGodotArray()) _volants.Add(v.AsString());
		}

		private void ApplyHabitats(GDict snap)
		{
			if (!snap.ContainsKey("habitats_auxiliaires") || _objects == null) return;
			foreach (var h in _habitats)
				if (IsInstanceValid(h)) h.QueueFree();
			_habitats.Clear();
			var bloc = snap["habitats_auxiliaires"].AsGodotDictionary();
			foreach (var kv in bloc)
			{
				string tuile = kv.Key.AsString();
				if (!GeometrieTuile(tuile, out Vector2 o, out _, out int cols)) continue;
				foreach (var e in kv.Value.AsGodotArray())
				{
					// Format 0.6.15 : [slot_id, n] (n rondelles `auxiliaire`, 1..3).
					var t = e.AsGodotArray();
					int slot = t[0].AsInt32();
					float x = o.X + (slot + 0.5f) * cols * PlotCm / TigesParTuile;
					float y = o.Y + TigeBordNordCm;
					int c = Mathf.Clamp((int)((x - o.X) / PlotCm), 0, cols - 1);
					var node = new HabitatAuxiliaire
					{
						Position = WorldToScreen(x, y) - new Vector2(0f, ReliefRiseAtPlot(tuile, 0, c)),
						ZIndex = ZObjet(x, y),
						Name = $"habitat_{tuile}_{slot}",
					};
					node.Init(t[1].AsInt32());
					_objects.AddChild(node);
					_habitats.Add(node);
				}
			}
		}
	}
}
