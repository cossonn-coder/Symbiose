// SYMBIOSE — WorldView.Observation.cs (partial de WorldView, retour F5 voix 0.5.12)
// L'OBSERVATION par SURVOL. Retour de conception de Nico : une plante n'est
// « observée » (fiche encyclopédie N1) que si le joueur PASSE LA SOURIS dessus
// pour voir son nom — pas parce qu'elle pousse dans le jardin. C'est la posture
// naturaliste : on apprend ce qu'on REGARDE.
//
// 📖 Pédagogie — on réutilise EXACTEMENT le picking de survol des étiquettes
// (FindPlant sur la souris, WorldView.Etiquettes.cs) : là où l'étiquette AFFICHE
// le nom, ici on le CONSIGNE au pont. Appelé chaque frame, mais on n'envoie une
// commande `observer` qu'à la PREMIÈRE fois qu'une espèce est survolée (dédup par
// un HashSet de sessions) — le pont est idempotent, mais on lui épargne le spam.
// Indépendant du mode d'étiquette : on observe même si les étiquettes sont sur
// « Aucune » (regarder une plante suffit).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Espèces (noms de classe) déjà envoyées au pont cette session : dédup pour
		// ne pas ré-émettre `observer` à chaque frame de survol.
		private readonly HashSet<string> _especesObservees = new();

		// Appelée chaque frame (_Process) : si une plante est sous le curseur et que
		// son espèce n'a jamais été observée, on la consigne au pont (survol = appris).
		private void ObserveHoveredPlant()
		{
			if (_bridge == null || _plantNodes.Count == 0) return;
			var node = FindPlant(ScreenToWorld(WorldMouseCanvas()), HoverRadiusCm);
			if (node == null || !IsInstanceValid(node)) return;
			string species = node.GetMeta("species", "").AsString();
			if (species.Length == 0 || !_especesObservees.Add(species)) return;
			// 1er survol de cette espèce → découverte côté Python (idempotent).
			_bridge.Observer(species);
			GD.Print($"[WorldView] survol → espèce observée : {species}.");
		}
	}
}
