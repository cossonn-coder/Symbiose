// SYMBIOSE — WorldView.Macros.cs (partial de WorldView, palette de gestes ⑤)
// LES MACROS JOUEUR (D1/D5) : une SÉQUENCE de gestes REJOUÉE sur le MÊME point
// cliqué (planter → pailler → arroser ICI, en un clic). Pas de « pinceau »
// balayé (rejeté, D5) : un seul point, N gestes appliqués dessus. Chaque
// sous-geste PAIE sa Vigueur (philo #1) — la macro n'est qu'un CONFORT
// d'enchaînement, aucune remise moteur. La DÉFINITION d'une macro est une
// DONNÉE persistée côté Python (game_state["palette"][player]["macros"]) ; la
// vue la LIT du snapshot (bloc player.palette) et la REJOUE comme N envois
// `action` NORMAUX, séquentiels (le pont reste 1↔1, un geste par réponse).
//
// 📖 Pédagogie Godot/C# :
//  - ENREGISTREMENT (touche K) : on bascule `_recording`. Tant qu'il est ON,
//    sélectionner un geste (palette/1..9/Tab) l'AJOUTE à la macro au lieu de
//    l'activer. Re-K = clôt + PERSISTE via SimBridge.Palette(macros:…).
//  - REJEU (touche J puis clic) : un clic capture le POINT, puis on enfile les
//    indices des gestes de la macro ; _Process les DÉPILE un par un dès que le
//    pipe est libre (comme _queuedIntent), en réutilisant TryAction — donc la
//    désignation par famille de cible (plante/plot/point) marche telle quelle.
//  - COHÉRENCE : les macros persistées par ce même client sont déjà validées
//    « même famille de cible » côté Python (definir_palette). On rejoue en
//    confiance ; un sous-geste qui ne trouve pas sa cible se refuse seul (NAK),
//    sans casser la file (le serveur reste stateless).

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Macros connues de l'avatar, lues du snapshot (player.palette.macros).
		// Chacune = un nom + la liste ORDONNÉE des verbes à rejouer. Vide tant que
		// le joueur n'a rien enregistré (bloc palette par défaut = slots/macros []).
		private readonly List<(string Nom, List<string> Gestes)> _macros = new();

		// Enregistrement en cours (touche K) : la séquence de verbes captés.
		private bool _recording;
		private readonly List<string> _macroRec = new();

		// Rejeu en cours : file des INDICES Gestes[] restant à appliquer, au MÊME
		// point capturé au clic. _macroArmed = un clic va lancer le rejeu (touche J).
		private bool _macroArmed;
		private readonly Queue<int> _macroReplay = new();
		private Vector2 _macroPoint;
		private bool _macroShift;

		// -------------------------------------------------------------------
		// LECTURE DU SNAPSHOT — player.palette.macros (⑤, 0.5.26).
		// -------------------------------------------------------------------

		// Reçoit le bloc `palette` du joueur (ou null si absent = binaire pré-0.5.26
		// → aucune macro). Reconstruit la liste locale telle quelle : le serveur est
		// la source de vérité de la DÉFINITION (les slots ④ pilotent déjà la palette).
		private void ApplyPalette(GDict palette)
		{
			_macros.Clear();
			if (palette == null || !palette.ContainsKey("macros")) return;
			foreach (var mv in palette["macros"].AsGodotArray())
			{
				var m = mv.AsGodotDictionary();
				var gestes = new List<string>();
				foreach (var g in m["gestes"].AsGodotArray()) gestes.Add(g.AsString());
				_macros.Add((m["nom"].AsString(), gestes));
			}
		}

		// -------------------------------------------------------------------
		// ENREGISTREMENT — touche K bascule ; les gestes sélectionnés s'ajoutent.
		// -------------------------------------------------------------------

		// Démarre / clôt un enregistrement. À la clôture, si la séquence n'est pas
		// vide, on la PERSISTE via le pont (SimBridge.Palette) : Python valide la
		// cohérence de cible et l'écrit dans le save. Le snapshot suivant la relira.
		private void ToggleMacroRecord()
		{
			if (!_recording)
			{
				_recording = true;
				_macroRec.Clear();
				_lastActionMsg = "macro : enregistrement ON — enchaînez des gestes, K pour finir";
				GD.Print("[WorldView] macro : REC ON.");
			}
			else
			{
				_recording = false;
				if (_macroRec.Count == 0)
					_lastActionMsg = "macro : enregistrement vide, rien de retenu";
				else
					PersistMacro();
				GD.Print($"[WorldView] macro : REC OFF ({_macroRec.Count} gestes).");
			}
			UpdateActionHud();
		}

		// Appelée par SelectGeste quand _recording : ajoute le verbe à la séquence
		// au lieu d'activer le geste. Retourne true si l'appel a été « consommé »
		// par l'enregistrement (SelectGeste s'arrête alors là).
		private bool RecordGesteSiEnCours(int idx)
		{
			if (!_recording) return false;
			string verb = Gestes[idx].Verb;
			_macroRec.Add(verb);
			_lastActionMsg = $"macro : +{verb} ({_macroRec.Count}) — K pour finir";
			GD.Print($"[WorldView] macro : capté {verb} ({_macroRec.Count}).");
			UpdateActionHud();
			return true;
		}

		// Envoie la macro courante au pont. Nom auto « macro N » (l'ordre de
		// création) ; on remplace toute macro homonyme en réémettant TOUTE la
		// liste connue + la nouvelle (definir_palette écrit macros en bloc). Le
		// serveur refuse une séquence incohérente (familles de cible mêlées) →
		// message relayé, aucune écriture (transactionnel côté Python).
		private void PersistMacro()
		{
			if (_bridge == null) return;
			var macros = new Godot.Collections.Array();
			foreach (var m in _macros)
				macros.Add(MacroDict(m.Nom, m.Gestes));
			var gestes = new Godot.Collections.Array();
			foreach (var v in _macroRec) gestes.Add(v);
			macros.Add(new GDict { ["nom"] = $"macro {_macros.Count + 1}",
								   ["gestes"] = gestes });

			var reponse = _bridge.Palette(macros: macros);
			if (reponse != null && reponse.ContainsKey("ok") && reponse["ok"].AsBool())
			{
				_lastActionMsg = $"macro « macro {_macros.Count + 1} » enregistrée "
					+ $"({_macroRec.Count} gestes)";
				GD.Print("[WorldView] macro persistée.");
			}
			else
			{
				string err = reponse != null && reponse.ContainsKey("error")
					? reponse["error"].AsString() : "refus du pont";
				_lastActionMsg = $"macro refusée : {err}";
				GD.Print($"[WorldView] macro refusée : {err}.");
			}
		}

		private static GDict MacroDict(string nom, List<string> gestes)
		{
			var arr = new Godot.Collections.Array();
			foreach (var v in gestes) arr.Add(v);
			return new GDict { ["nom"] = nom, ["gestes"] = arr };
		}

		// -------------------------------------------------------------------
		// REJEU — touche J arme ; le prochain clic capture le point et enfile.
		// -------------------------------------------------------------------

		// Arme le rejeu de la PREMIÈRE macro connue (calibrage F5 : une seule macro
		// suffit au proto ; un sélecteur multi-macro viendra si Nico le demande).
		// Rien à armer si aucune macro n'existe (message clair).
		private void ArmerMacro()
		{
			if (_macros.Count == 0)
			{
				_lastActionMsg = "aucune macro (K pour en enregistrer une)";
				UpdateActionHud();
				return;
			}
			_macroArmed = true;
			_lastActionMsg = $"macro « {_macros[0].Nom} » armée — cliquez le point à traiter";
			GD.Print($"[WorldView] macro : « {_macros[0].Nom} » armée.");
			UpdateActionHud();
		}

		// Un clic alors que la macro est armée : capture le POINT + Maj, résout la
		// suite de gestes en indices Gestes[], et remplit la file. Le rejeu réel se
		// fait dans _Process (DrainMacro) au rythme du pipe — chaque sous-geste part
		// comme un `action` normal, paie sa Vigueur, applique son snapshot.
		private bool LancerMacroSiArmee(Vector2 canvas, bool shift)
		{
			if (!_macroArmed) return false;
			_macroArmed = false;
			_macroReplay.Clear();
			_macroPoint = canvas;
			_macroShift = shift;
			foreach (string verb in _macros[0].Gestes)
			{
				int idx = IndexDuVerbe(verb);
				if (idx >= 0) _macroReplay.Enqueue(idx);
			}
			GD.Print($"[WorldView] macro : rejeu de {_macroReplay.Count} gestes au point cliqué.");
			DrainMacro();   // lance le 1er tout de suite si le pipe est libre
			return true;
		}

		// Dépile le prochain sous-geste de la macro et le lance au point capturé,
		// via TryAction (donc la désignation par famille de cible est réutilisée).
		// N'agit QUE si le pipe est libre et qu'aucune intention n'est déjà en file
		// (on ne double jamais un envoi) — appelée par _Process à chaque frame.
		private void DrainMacro()
		{
			if (_macroReplay.Count == 0) return;
			if (!PipeFree || _queuedIntent != null) return;
			int idx = _macroReplay.Dequeue();
			_gesteIndex = idx;                 // TryAction lit le geste courant
			UpdatePaletteSelection();
			TryAction(_macroPoint, _macroShift);
		}

		// Annule tout enregistrement/rejeu (appelé par SelectGeste hors macro).
		private void ResetMacroState()
		{
			_macroArmed = false;
			_macroReplay.Clear();
		}

		private static int IndexDuVerbe(string verb)
		{
			for (int i = 0; i < Gestes.Length; i++)
				if (Gestes[i].Verb == verb) return i;
			return -1;
		}
	}
}
