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
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Espèces (noms de classe) déjà envoyées au pont cette session : dédup pour
		// ne pas ré-émettre `observer` à chaque frame de survol.
		private readonly HashSet<string> _especesObservees = new();

		// Vie macro (D60 ②) : "clé|saison" déjà consignés (clé d'espèce animale ou
		// "champignon"). Set SÉPARÉ des plantes — les clés sont d'un autre espace
		// (clé de maîtrise directe, pas un nom de classe). INFO-BULLE DU VIVANT ③ :
		// dédup par (clé, SAISON) et non plus « une fois par session » — Python
		// crédite +1 palier par saison neuve d'observation (le nom se révèle en 3
		// saisons) ; une dédup de session bloquerait tout crédit après le 1er survol.
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
			string species = node.GetMeta(LectureSnap.Meta("species"), "").AsString();
			if (species.Length == 0 || !_especesObservees.Add(species)) return;
			// 1er survol de cette espèce → découverte côté Python (idempotent).
			AppelObservation(() => _bridge.Observer(species));
			GD.Print($"[WorldView] survol → espèce observée : {species}.");
		}

		// Survol de la VIE MACRO (D60 ②) : porter la posture naturaliste des plantes
		// à toute la vie macro. On observe l'espèce animale (nuage MacroLife OU
		// butineur ForagerLayer) ou le champignon (carpophore) sous le curseur, à la
		// 1ʳᵉ fois. On RÉUTILISE le picking déjà présent (Near → MacroPick,
		// lecture des ancres en mémoire — zéro requête pipe, zéro nouveau balayage).
		// Gaté au zoom ≥ ×4 : on ne découvre que ce qui est AFFICHÉ (au dézoom la vie
		// macro est masquée — on n'observe pas l'invisible).
		private void ObserveHoveredMacroLife()
		{
			// Les ancres macro ne bougent qu'au snapshot → clé de survol (T3).
			if (_bridge == null || !_survolSale) return;
			string espece = BeteSousSouris()?.Cle;
			if (espece == null || !_especesMacroObservees.Add($"{espece}|{SaisonObservee}")) return;
			AppelObservation(() =>
			{
				var rep = _bridge.Observer(espece);
				// Pont ≥ 0.5.48 : la réponse porte `appris` (lecture pure) → si ce survol
				// vient de franchir le palier du nom, l'info-bulle nomme la bête TOUT DE
				// SUITE, sans attendre le snapshot de la semaine suivante.
				if (rep != null && rep.ContainsKey("appris"))
				{
					LireAppris(new GDict { ["appris"] = rep["appris"] });
					_cleVersion = -1;   // recalcul de l'info-bulle à la frame suivante
				}
			});
			GD.Print($"[WorldView] survol → vie macro observée : {espece}.");
		}

		// OBSERVATIONS DIFFÉRÉES (FLUIDITÉ AN 2 ④). Une observation est un appel
		// SYNCHRONE au pont : si un step est en vol, le fil principal attend le verrou
		// du pipe pendant tout le tick (~1 s) → image gelée. Mesuré au banc E VM : 3
		// survols pendant la mesure = 3 images de 0,6 à 1,4 s [n=1 run]. Depuis que le
		// step suivant part pendant l'application de la semaine (chevauchement), le
		// pipe est presque toujours occupé : l'appel attend donc son tour en file et
		// part dès que le pipe est libre (quelques images plus tard, invisible).
		// 📖 C'est le report d'une requête bloquante hors de la boucle temps réel :
		// on poste un message au lieu d'attendre la réponse sous interruption.
		private readonly Queue<System.Action> _observationsEnFile = new();

		private void AppelObservation(System.Action appel)
		{
			if (PipeFree) appel();
			else _observationsEnFile.Enqueue(appel);
		}

		/// <summary>Chaque frame (_Process), avant le lancement du step : vide la file
		/// tant que le pipe est libre.</summary>
		private void DrainObservations()
		{
			while (_observationsEnFile.Count > 0 && PipeFree) _observationsEnFile.Dequeue()();
		}

		// Saison d'observation, MÊME formule que la note Python (semaine consignée =
		// semaine moteur − 1, saisons de 13 semaines, semaine 0 ≡ semaine 1) : la
		// dédup vue des signes et de la vie macro tombe sur les saisons de Python.
		private int SaisonObservee => System.Math.Max(0, SemaineMoteur - 2) / 13;

		/// <summary>Bête sous le curseur (ou carpophore, clé "champignon"), null si
		/// rien ou si la vie macro n'est pas affichée (zoom &lt; ×4). Partagée par
		/// l'observation et l'info-bulle : un seul picking (cf. MacroPick).</summary>
		private MacroPick? BeteSousSouris()
		{
			if (CurrentZoom < MacroObserveMinZoom) return null;
			Vector2 w = _sourisMonde;
			// D'abord le nuage trophique, sinon un butineur (les deux exposent la
			// MÊME clé d'espèce que le pont attend), à défaut un carpophore.
			return _macroLife?.Near(w, MacroPickRadiusCm)
				?? _foragerLayer?.Near(w, MacroPickRadiusCm)
				?? _carpophoreLayer?.Near(w, MacroPickRadiusCm);
		}
	}
}
