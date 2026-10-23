// SYMBIOSE — WorldView.Attente.cs (partial de WorldView, sprint RENDU VISIBLE T4)
// SEMAINE PARESSEUSE HORS CHAMP (décision D2) : une plante connue qui est HORS de
// la marge (world/MargeVue.cs) ne reçoit, à la famille 1 de l'étalement, que sa
// DONNÉE (payload stocké ici) ; le coût réel — parse des segments, setters,
// recuisson — attend qu'on en ait besoin :
//  · à son ENTRÉE dans la marge (pan, zoom, rotation) : file à budget, même
//    budget par frame que l'étalement, les plus proches du centre d'abord, et
//    AVANT leur cuisson (BakeQueue saute les plantes EnAttente) ;
//  · à sa CONSULTATION (clic du dossier F2, taille, recherche de segment) :
//    appliquée sur-le-champ (AppliquerSiEnAttente).
// Plusieurs semaines hors champ ne s'empilent pas : seule la DERNIÈRE donnée
// compte (le dictionnaire écrase). Les index (dossier, fleurs des butineurs,
// clés vues) restent tenus à jour par l'étalement : rien n'y est différé.
//
// 📖 Pédagogie (côté embarqué) : c'est l'évaluation PARESSEUSE d'un registre
// « shadow » — on mémorise la dernière valeur écrite et on ne la recopie dans le
// registre réel (coûteux) que quand quelqu'un va le lire.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Dernière donnée non appliquée (déjà LUE, FLUIDITÉ AN 2 ④), par plante hors marge.
		private readonly Dictionary<PlantRenderer, PlanteLue> _enAttente = new();
		// Plantes en attente entrées dans la marge, à appliquer (triées au centre).
		private readonly List<PlantRenderer> _fileEntree = new();

		private void MettreEnAttente(PlantRenderer node, PlanteLue l)
		{
			_enAttente[node] = l;   // écrase : seule la dernière semaine compte
			node.EnAttente = true;
		}

		private void SortirAttente(PlantRenderer node)
		{
			if (_enAttente.Remove(node)) node.EnAttente = false;
		}

		/// <summary>Rotation / reconstruction : les nœuds partent, le snapshot
		/// complet est ré-appliqué en naissances → plus rien n'attend.</summary>
		private void ViderAttente()
		{
			_enAttente.Clear();
			_fileEntree.Clear();
		}

		/// <summary>Appelé par CullPlants quand `node` entre dans la marge. Vrai si
		/// la plante attendait (la file devra être retriée).</summary>
		private bool EntreeDansMarge(PlantRenderer node)
		{
			if (!node.EnAttente) return false;
			_fileEntree.Add(node);
			return true;
		}

		// Les plus proches du centre de l'écran d'abord (~quelques centaines au
		// pire, à un dézoom : tri ponctuel, négligeable).
		private void TrierFileEntree()
		{
			Vector2 c = _camera.Position;
			_fileEntree.Sort((a, b) =>
				a.Position.DistanceSquaredTo(c).CompareTo(b.Position.DistanceSquaredTo(c)));
		}

		/// <summary>Chaque frame (_Process) : applique les plantes entrées dans la
		/// marge, dans le budget de l'étalement. Ne double pas une semaine en cours
		/// d'application (elle traite elle-même les plantes devenues visibles).</summary>
		private void AvancerAttente()
		{
			if (_fileEntree.Count == 0 || _etale != null) return;
			ulong t0 = Time.GetTicksUsec();
			int i = 0;
			while (i < _fileEntree.Count)
			{
				var node = _fileEntree[i++];
				// Ressortie de la marge entre-temps : reste en attente (CullPlants la
				// remettra en file à sa prochaine entrée).
				if (IsInstanceValid(node) && node.Visible
					&& _enAttente.TryGetValue(node, out var p))
					MajPlante(node, p);
				if ((long)(Time.GetTicksUsec() - t0) >= BudgetPlantesUs) break;
			}
			_fileEntree.RemoveRange(0, i);
			_survolVersion++;   // le monde affiché a changé → survol à recalculer (T3)
		}

		/// <summary>Consultation (clic, taille, dossier) : la plante concernée est
		/// mise à jour d'abord, de façon synchrone.</summary>
		private void AppliquerSiEnAttente(PlantRenderer node)
		{
			if (node != null && _enAttente.TryGetValue(node, out var p))
			{
				MajPlante(node, p);
				_survolVersion++;
			}
		}
	}
}
