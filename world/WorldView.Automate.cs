// SYMBIOSE — WorldView.Automate.cs (partial de WorldView ; refactor fenêtrage UI T3)
// GLUE du JARDINIER AUTOMATE : brancher/débrancher l'automate déterministe côté
// serveur (pont 0.5.30), gérer l'onglet Automate du conteneur de consultation
// (DEV-GATED, A6) et lui pousser le bloc `automate` du snapshot tant qu'il est
// VISIBLE. Toute la MISE EN PAGE (profil/objectifs/journal/filtre) a migré dans
// `AutomateContent` (T3) — ce partial ne fait plus que router les intentions.
//
// Depuis T3 : plus de CanvasLayer autonome. L'onglet Automate n'apparaît que
// lorsque la touche A l'a branché ; il vit dans `ConsultationPanel` (tiers droit),
// à côté des voix. La sim TOURNE quand cet onglet est actif (pause par onglet, A2)
// → on regarde l'automate jouer le jardin ENTRE deux ticks (invariant H2).

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private bool _automateOn;             // automate branché côté serveur ?
		private AutomateContent _automateContent;  // contenu de l'onglet (null si absent)
		private GDict _automateBlock;         // dernier bloc snapshot (seed à l'ouverture)

		// Touche A : brancher/débrancher l'automate ET ouvrir/fermer son onglet.
		//  - panneau ouvert sur l'onglet Automate ACTIF → débrancher + fermer (A8) ;
		//  - sinon → brancher (si besoin) puis ouvrir/basculer sur l'onglet Automate.
		private void ToggleAutomate()
		{
			if (_bridge == null) return;

			// Cas fermeture (A8) : l'onglet Automate est celui affiché → on coupe.
			if (_consultation != null && IsInstanceValid(_consultation)
				&& _automateContent != null && _automateContent.IsVisibleInTree())
			{
				_bridge.Automate(false, null);
				_automateOn = false;
				_consultation.Fermer();       // onFerme remet _consultation/_automateContent à null
				GD.Print("[WorldView] A → jardinier automate OFF (onglet fermé).");
				return;
			}

			// Cas ouverture : brancher si pas déjà, puis (ré)ouvrir sur l'onglet Automate.
			if (!_automateOn)
			{
				// Profil par défaut = LIBRE + désherbage curatif (l'automate ne paie
				// pas sa Vigueur → il joue chaque tick, retour visuel dense pour le F5).
				var profil = new GDict { ["desherbage"] = "curatif" };
				var resp = _bridge.Automate(true, profil);
				if (resp == null)
				{
					GD.PrintErr("[WorldView] automate indisponible (moteur pré-0.5.30 ?).");
					return;
				}
				_automateOn = true;
				int cultivees = resp.ContainsKey("cultivees") ? resp["cultivees"].AsInt32() : 0;
				GD.Print($"[WorldView] A → jardinier automate ON ({cultivees} cultivées sous tutelle).");
			}
			OuvrirConsultation("Automate");
		}

		// Maj+A : pousse un OBJECTIF démo (récolter 5 tomates) pour valider l'onglet
		// objectifs en F5 (sans lui, aucun objectif n'existe → l'onglet reste vide).
		// Instrument debug — les vrais objectifs diégétiques = système de quêtes (D79).
		private void InjecterObjectifDemo()
		{
			if (_bridge == null || !_automateOn) return;
			_bridge.AutomateObjectif("recolter", 5, "tomate");
			GD.Print("[WorldView] Maj+A → objectif démo poussé (récolter 5 tomate).");
		}

		// Touche F / Maj+F (⑤) : filtre du log automate. Délégué au contenu de
		// l'onglet, et seulement quand celui-ci est VISIBLE (sinon inerte).
		private void CycleAutomateCat()
		{
			if (_automateContent != null && IsInstanceValid(_automateContent)
				&& _automateContent.IsVisibleInTree())
				_automateContent.CyclerCategorie();
		}

		private void ToggleAutomateCat()
		{
			if (_automateContent != null && IsInstanceValid(_automateContent)
				&& _automateContent.IsVisibleInTree())
				_automateContent.BasculerCategorie();
		}

		// Bloc `automate` du snapshot (appelé depuis ApplySnapshot SI présent, donc
		// seulement quand l'automate est branché). On mémorise TOUJOURS le bloc (seed
		// à l'ouverture de l'onglet) ; on ne (re)construit le texte QUE si l'onglet
		// Automate est l'onglet visible — sinon aucune mise en page (perf, T3).
		private void ApplyAutomate(GDict block)
		{
			_automateBlock = block;
			if (_automateContent != null && IsInstanceValid(_automateContent)
				&& _automateContent.IsVisibleInTree())
				_automateContent.Rendre(block);
		}
	}
}
