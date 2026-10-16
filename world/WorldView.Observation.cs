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

		// Vie macro (D60 ②) : clés d'espèce animale + "champignon" déjà consignées.
		// Set SÉPARÉ des plantes — les clés sont d'un autre espace (clé de maîtrise
		// directe, pas un nom de classe) : pas de collision, dédup propre.
		private readonly HashSet<string> _especesMacroObservees = new();

		// Zoom en deçà duquel la vie macro n'est pas affichée (aligné sur
		// MacroLife/ForagerLayer/CarpophoreLayer.MinZoom = ×4) : on ne peut observer
		// que ce qui est VISIBLE (kickoff ② — pas de découverte au dézoom).
		private const float MacroObserveMinZoom = 4f;

		// Appelée chaque frame (_Process) : si une plante est sous le curseur et que
		// son espèce n'a jamais été observée, on la consigne au pont (survol = appris).
		private void ObserveHoveredPlant()
		{
			if (_bridge == null || _plantNodes.Count == 0 || !_survolSale) return;
			var node = FindPlant(_sourisMonde, HoverRadiusCm);
			if (node == null || !IsInstanceValid(node)) return;
			string species = node.GetMeta("species", "").AsString();
			if (species.Length == 0 || !_especesObservees.Add(species)) return;
			// 1er survol de cette espèce → découverte côté Python (idempotent).
			_bridge.Observer(species);
			GD.Print($"[WorldView] survol → espèce observée : {species}.");
		}

		// Survol de la VIE MACRO (D60 ②) : porter la posture naturaliste des plantes
		// à toute la vie macro. On observe l'espèce animale (nuage MacroLife OU
		// butineur ForagerLayer) ou le champignon (carpophore) sous le curseur, à la
		// 1ʳᵉ fois. On RÉUTILISE le picking déjà présent (SpeciesNear / HasNear,
		// lecture des ancres en mémoire — zéro requête pipe, zéro nouveau balayage).
		// Gaté au zoom ≥ ×4 : on ne découvre que ce qui est AFFICHÉ (au dézoom la vie
		// macro est masquée — on n'observe pas l'invisible).
		private void ObserveHoveredMacroLife()
		{
			// Les ancres macro ne bougent qu'au snapshot → clé de survol (T3).
			if (_bridge == null || !_survolSale) return;
			if (CurrentZoom < MacroObserveMinZoom) return;
			Vector2 w = _sourisMonde;

			// Espèce animale sous le curseur : d'abord le nuage trophique, sinon un
			// butineur (les deux exposent la MÊME clé d'espèce que le pont attend).
			string espece = _macroLife?.SpeciesNear(w, MacroPickRadiusCm)
							?? _foragerLayer?.SpeciesNear(w, MacroPickRadiusCm);
			// À défaut d'animal, un carpophore → la clé fongique générique unique.
			if (espece == null && _carpophoreLayer != null
				&& _carpophoreLayer.HasNear(w, MacroPickRadiusCm))
				espece = "champignon";

			if (espece == null || !_especesMacroObservees.Add(espece)) return;
			_bridge.Observer(espece);
			GD.Print($"[WorldView] survol → vie macro observée : {espece}.");
		}
	}
}
