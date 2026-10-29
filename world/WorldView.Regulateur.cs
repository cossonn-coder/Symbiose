// SYMBIOSE — WorldView.Regulateur.cs (partial de WorldView, FLUIDITÉ PC PARTAGE ②)
// RÉGULATEUR DE CADENCE : quand la vue attend le moteur, elle lui rend la machine.
// Règle (décision Nico 2026-10-28, plancher 15 FPS accepté) : en Phase.Saison, si
// une semaine est DUE (`_timeAccum ≥ spw`) ET que le step précédent est encore en
// vol côté Python (`_pendingStep != null`), la vue plafonne à 15 images/s
// (`Engine.MaxFps`). Partout ailleurs, plafond d'origine (mémorisé à la première
// image) : Planification, Pause, semaine à l'heure, semaine en application
// (`VuePrete` faux : c'est la VUE qui est en retard, elle a besoin du CPU), et
// pendant ~1 s après toute interaction caméra (flèches, molette, quart de tour).
//
// Hypothèse servie (NON mesurée, conception §2) : sur le PC de Nico (Haswell mobile,
// iGPU HD 4600), cœurs et GPU partagent TDP et cache L3 ; une vue qui dessine sans
// plafond (~17 FPS, la vsync ne bride jamais) ralentit le moteur Python. Si elle est
// fausse, le régulateur reste inoffensif : il ne s'engage que quand le moteur est
// DÉJÀ en retard. Le banc de partage (WorldView.BancPartage.cs) tranche.
//
// Un seul propriétaire d'`Engine.MaxFps` à la fois : pendant la phase B du banc
// 3 phases (rendu coupé, WorldView.Banc3Phases.cs pose 60 puis restaure), le
// régulateur ne touche à rien. Phase C (moteur en pause) : aucune semaine due →
// jamais régulée.
//
// 📖 Pédagogie (côté embarqué) : c'est un gouverneur de fréquence — quand la tâche
// de calcul rate son échéance, on abaisse la cadence de la tâche d'affichage (moins
// de cycles, moins de chaleur, moins de bande passante mémoire partagée) au lieu de
// laisser les deux se battre ; dès que l'utilisateur interagit, on remonte.

using Godot;
using System.Globalization;

namespace Symbiose
{
	public partial class WorldView
	{
		private const int RegulateurFps = 15;           // plancher accepté par Nico
		private const double RegulateurCameraSec = 1.0; // plein régime après la caméra

		// Choix du joueur (case « Régulateur de cadence » de Paramètres). Défaut OFF
		// depuis le run PC du 2026-10-29 : son gain n'est pas démontré [n=1 run, PC]
		// et sans lui l'image est la plus fluide. `_regActif` = état effectif ; le
		// banc de partage le force par sous-phase puis le rend au choix du joueur.
		private bool _regChoix = false;
		private bool _regActif = false;
		private int _regOrigine = -1;           // plafond d'origine (première image)
		private bool _regEngage;                // état courant (overlay F4, rapport)
		private double _regCameraT = -1e9;      // dernière interaction caméra (s)
		private double _regSec;                 // temps régulé depuis RemettreRegulateur

		/// <summary>Cadence demandée en secondes réelles par semaine (même règle que
		/// le lancement du step dans _Process : turbo = 0, step dès que le pont répond).</summary>
		private float SpwCourant =>
			_simMode == SimMode.Turbo ? 0f
			: DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;

		/// <summary>Appelé par la caméra (pan, zoom, rotation) : plein régime ~1 s.</summary>
		private void NoterCameraBouge() => _regCameraT = Maintenant;

		/// <summary>Appelé à chaque image par _Process, après le banc (qui peut couper
		/// le rendu) et avant le lancement du step.</summary>
		private void RegulerCadence(double delta)
		{
			if (_b3RenduCoupe) return;   // phase B : Banc3Phases.cs possède MaxFps
			if (_regOrigine < 0) _regOrigine = Engine.MaxFps;
			_regEngage = _regActif
				&& _phase == Phase.Saison
				&& _pendingStep != null
				&& _timeAccum >= SpwCourant
				&& Maintenant - _regCameraT > RegulateurCameraSec;
			int cible = _regEngage ? RegulateurFps : _regOrigine;
			if (Engine.MaxFps != cible) Engine.MaxFps = cible;
			if (_regEngage) _regSec += delta;
		}

		/// <summary>Remet à zéro le temps régulé (début d'une fenêtre de banc).</summary>
		private void RemettreRegulateur() => _regSec = 0;

		/// <summary>Part du temps régulé depuis `debut` (horloge murale, s), en %.</summary>
		private double PartReguleePct(double debut)
		{
			double t = Maintenant - debut;
			return t > 0 ? 100.0 * _regSec / t : 0;
		}

		/// <summary>État court pour l'overlay F4.</summary>
		private string EtatRegulateur() =>
			!_regActif ? "régulateur coupé"
			: _regEngage ? $"régulé {RegulateurFps} FPS (moteur en retard)" : "libre";

		/// <summary>Ligne du rapport de banc (E, Maj+E, chaque phase du banc 3 phases).</summary>
		private string LigneRegulateur(double debut) => string.Create(CultureInfo.InvariantCulture,
			$"  régulateur {(_regActif ? "ON" : "OFF")} : {PartReguleePct(debut):F0} % du temps régulé à {RegulateurFps} FPS"
			+ $" · plafond d'origine {(_regOrigine <= 0 ? "aucun" : _regOrigine.ToString())}");
	}
}
