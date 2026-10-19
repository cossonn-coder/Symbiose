// SYMBIOSE — WorldView.Tapis.cs (partial de WorldView, sprint RENDU VISIBLE D106 T5)
// L'AGRÉGAT DU TAPIS PAR PLOT (D5) : une plante trop petite pour être lisible au
// palier courant (PlantRenderer.EnTapis, seuil TapisSeuilPx) n'est pas dessinée
// seule — elle « verse » sa présence dans le tapis de son plot. Ici on regroupe
// ces petites plantes par plot (tuile + ligne + colonne) et on passe le résultat
// au SEUL tapis du jeu (visuals/CouvertureLayer.cs), qui le fond avec le champ
// moteur `couverture_sol` : jamais deux voiles verts superposés.
//
// 📖 Pédagogie : c'est une lecture PURE de l'état déjà appliqué aux nœuds (taille
// réelle, espèce, saison) — zéro Random, aucune écologie recalculée. Recalculé
// seulement quand une plante a été (ré)appliquée, retirée, ou que le palier a
// changé (drapeau `_tapisSale`), jamais par frame au repos ; et pas au milieu
// d'une semaine étalée (on attend qu'elle soit entièrement appliquée).
// Le picking n'est pas touché : FindPlant itère tous les nœuds, dessinés ou non
// → cliquer dans un tapis sélectionne la plante la plus proche.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Levé par MajPlante, le retrait d'une plante et la pompe de palier.
		private bool _tapisSale;

		// Tampons réutilisés (pas d'allocation à chaque recalcul).
		private readonly Dictionary<(string Tile, int R, int C), Dictionary<string, (float Aire, Color Somme)>>
			_tapisParPlot = new();
		private readonly List<CouvertureLayer.Petites> _tapisPetites = new();

		private void MajTapisSiSale()
		{
			if (!_tapisSale || _etale != null || _couvertureLayer == null) return;
			_tapisSale = false;
			_tapisParPlot.Clear();
			foreach (var node in _plantNodes.Values)
			{
				if (!IsInstanceValid(node) || !node.EnTapis) continue;
				string tile = node.GetMeta(LectureSnap.Meta("tile")).AsString();
				int c = Mathf.FloorToInt((float)node.GetMeta(LectureSnap.Meta("lx")).AsDouble() / PlotCm);
				int r = Mathf.FloorToInt((float)node.GetMeta(LectureSnap.Meta("ly")).AsDouble() / PlotCm);
				if (!_tapisParPlot.TryGetValue((tile, r, c), out var parEspece))
					_tapisParPlot[(tile, r, c)] = parEspece = new();
				// Somme des teintes PONDÉRÉE par l'aire : la couleur moyenne de
				// l'espèce dans ce plot (chaque pied a sa nuance d'automne).
				string esp = node.GetMeta(LectureSnap.Meta("species")).AsString();
				float aire = node.AireTapisCm2;
				parEspece.TryGetValue(esp, out var acc);
				parEspece[esp] = (acc.Aire + aire, acc.Somme + node.TeinteTapis * aire);
			}
			_tapisPetites.Clear();
			foreach (var kv in _tapisParPlot)
			{
				// Espèce DOMINANTE du plot (la plus grande aire cumulée) → sa teinte ;
				// la densité prend l'aire de TOUTES les petites plantes du plot.
				float total = 0f, best = -1f;
				Color teinte = default;
				foreach (var e in kv.Value.Values)
				{
					total += e.Aire;
					if (e.Aire > best) { best = e.Aire; teinte = e.Somme / e.Aire; }
				}
				teinte.A = 1f;
				_tapisPetites.Add(new CouvertureLayer.Petites(kv.Key.Tile, kv.Key.R, kv.Key.C,
					Mathf.Clamp(total / (PlotCm * PlotCm), 0f, 1f), teinte));
			}
			_couvertureLayer.SetPetites(_tapisPetites, _origins);
		}
	}
}
