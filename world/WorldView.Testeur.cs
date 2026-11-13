// SYMBIOSE — WorldView.Testeur.cs (partial de WorldView, GESTES LISIBLES ⑤)
// LE MODE TESTEUR : un banc déclare un PLAN DE TEST (liste ordonnée de gestes et de
// cibles, `bancs/plan_test.py`) ; la touche B le déroule ici, geste par geste, PAR LE
// MÊME CHEMIN QU'UN CLIC DU JOUEUR : le geste est armé dans la palette, la souris est
// posée sur la cible, puis `TryAction` part comme un clic (désignation, pont, animation
// du curseur, réponse, traces au sol). Ce n'est pas l'automate : aucune décision ici.
//
// Le plan vient du pont (`plan_test`, 0.6.16), DÉJÀ résolu en points MONDE : la vue n'a
// aucune table de cibles. Un geste à deux temps porte deux clics (épandre : le tas, puis
// le plot). Rapport : une ligne par geste (verbe, cible, appliqué / refusé, message),
// affichée dans l'onglet Automate et écrite au journal Godot `[Testeur]` (capture VM :
// `tools/capture_vm.sh -b sol_canvas -R …`).
//
// 📖 Pédagogie Godot : pas de boucle bloquante — chaque étape programme la suivante par
// un minuteur de l'arbre (`GetTree().CreateTimer(s).Timeout`), le jeu continue d'afficher
// entre deux. Le verdict se lit sur la réponse du pont (le curseur joue « exécution » ou
// « refus », `_verdictGeste`) ; un refus de la VUE (aucune requête partie : pas de cible
// sous le clic) se lit tout de suite après le clic.

using System.Collections.Generic;
using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private const float TesteurPasSec = 3f;     // un geste toutes les ~3 s
		private const float TesteurClicSec = 1f;    // entre les deux clics d'un geste à deux temps

		private static readonly bool CaptureTesteur = ArgCapture("testeur") != null;
		private readonly List<string> _rapportTesteur = new();
		private bool _testeurEnCours;

		/// <summary>Touche B : demande le plan du monde monté au pont et le déroule.</summary>
		private void LancerTesteur()
		{
			if (_bridge == null || _world == null || _testeurEnCours) return;
			if (!PipeFree || _queuedIntent != null)   // une requête en vol : on réessaie
			{
				GetTree().CreateTimer(0.2f).Timeout += LancerTesteur;
				return;
			}
			var rep = _bridge.PlanTest(_configLancee);
			var plan = rep?["plan"].AsGodotArray();
			_rapportTesteur.Clear();
			if (plan == null || plan.Count == 0)
			{
				Rapporter($"aucun plan de test pour « {_configLancee} »");
				return;
			}
			_testeurEnCours = true;
			if (CaptureBanc != null && _curseurTemoin == null) PoserTemoinCurseur();
			GD.Print($"[Testeur] plan « {_configLancee} » : {plan.Count} gestes.");
			JouerEtapeTesteur(plan, 0);
		}

		private void JouerEtapeTesteur(Godot.Collections.Array plan, int i)
		{
			if (i >= plan.Count)
			{
				_testeurEnCours = false;
				GD.Print($"[Testeur] fin du plan ({plan.Count} gestes).");
				OuvrirConsultation("Automate");   // le rapport complet, sous les yeux
				return;
			}
			var e = plan[i].AsGodotDictionary();
			string entete = $"{i + 1}. {e["verbe"].AsString()} → {e["cible"].AsString()}";
			var clics = e["clics"].AsGodotArray();
			int g = IndexDuVerbe(e["geste"].AsString());
			string empeche = clics.Count == 0 ? "cible introuvable"
				: g < 0 ? "geste absent de la palette" : null;
			if (empeche != null)
			{
				Rapporter($"✗ {entete} : refusé « {empeche} »");
				GetTree().CreateTimer(TesteurClicSec).Timeout += () => JouerEtapeTesteur(plan, i + 1);
				return;
			}
			SelectGeste(g);
			CliquerTesteur(clics, 0, e["maj"].AsBool(), () =>
				GetTree().CreateTimer(TesteurPasSec).Timeout += () =>
				{
					Rapporter(_verdictGeste switch
					{
						AnimationGeste.Sorte.Execution => $"✓ {entete} : appliqué « {_lastActionMsg} »",
						AnimationGeste.Sorte.Refus => $"✗ {entete} : refusé « {_lastActionMsg} »",
						_ => $"? {entete} : sans réponse « {_lastActionMsg} »",
					});
					JouerEtapeTesteur(plan, i + 1);
				},
				() =>
				{
					Rapporter($"✗ {entete} : refusé par la vue « {_lastActionMsg} »");
					GetTree().CreateTimer(TesteurClicSec).Timeout += () => JouerEtapeTesteur(plan, i + 1);
				});
		}

		// Clic k du geste : la souris se pose sur le point (le curseur et son témoin y
		// jouent), puis TryAction comme un clic gauche. Au dernier clic, `envoye` si une
		// requête est partie (ou attend le pipe), sinon `refuse` (la vue n'a rien envoyé).
		private void CliquerTesteur(Godot.Collections.Array clics, int k, bool maj,
									System.Action envoye, System.Action refuse)
		{
			var p = clics[k].AsGodotArray();
			Vector2 canvas = WorldToScreen((float)p[0].AsDouble(), (float)p[1].AsDouble());
			Input.WarpMouse(CanvasVersSouris(canvas));
			bool dernier = k == clics.Count - 1;
			if (dernier) { _verdictGeste = null; _lastActionMsg = ""; }
			TryAction(canvas, maj);
			if (!dernier)
			{
				GetTree().CreateTimer(TesteurClicSec).Timeout += () => CliquerTesteur(clics, k + 1, maj, envoye, refuse);
				return;
			}
			if (_pendingAction != null || _queuedIntent != null) envoye();
			else refuse();
		}

		// Inverse de SourisVersCanvas (WorldView.cs) : canvas monde → px fenêtre.
		private Vector2 CanvasVersSouris(Vector2 canvas)
		{
			var container = _worldVp.GetParent<SubViewportContainer>();
			Vector2 scale = (Vector2)_worldVp.Size / container.Size;
			return container.GlobalPosition + _worldVp.GetCanvasTransform() * canvas / scale;
		}

		// Une ligne de rapport : journal Godot (capture VM) + onglet Automate s'il est ouvert.
		private void Rapporter(string ligne)
		{
			_rapportTesteur.Add(ligne);
			GD.Print($"[Testeur] {ligne}");
			if (_automateContent != null && IsInstanceValid(_automateContent))
				_automateContent.PoserTesteur(_rapportTesteur);
		}

		// Capture VM (`--capture-testeur`) : le plan part 4 s après le montage.
		private void LancerTesteurCapture()
		{
			if (CaptureTesteur) GetTree().CreateTimer(4f).Timeout += LancerTesteur;
		}
	}
}
