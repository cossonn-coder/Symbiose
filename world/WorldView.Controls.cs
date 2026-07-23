// SYMBIOSE — WorldView.Controls.cs (partial de WorldView, SS⑥ refactor global)
// Les ENTRÉES clavier/souris (bindings provisoires — les vrais boutons = sprint
// UI) et les bascules d'état qu'elles déclenchent : phase (Espace), mode de
// simulation (M), étiquettes (F3), maison transparente (H), ombres (O), vie
// macro (I). Le zoom/rotation va à la caméra, les gestes 1..8 aux actions, la
// heatmap au HUD — _UnhandledInput ne fait qu'aiguiller (partial = même classe).

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private bool _houseGhost;             // maison transparente (H)
		// Overlay debug LOD des émetteurs d'ombre (D67, F9) : quand ON, les plantes
		// NON-émettrices (semis sous-seuil que le LOD écarte des boucles d'ombre) se
		// teintent — on VOIT qui le LOD retire. Statique : PlantRenderer.ApplyLodTint
		// le lit sans référence au nœud parent. OFF par défaut (« affichage technique »).
		public static bool LodDebugOn { get; private set; }
		private const int DebugSkipWeeks = 10; // touche T : semaines sautées d'un coup (debug)

		// -------------------------------------------------------------------
		// BOUCLE HYBRIDE — entrées (tranche 3)
		// -------------------------------------------------------------------

		public override void _UnhandledInput(InputEvent ev)
		{
			// Écran de sélection (⑤) : aucune commande monde tant que la sim n'est
			// pas lancée (le menu consomme ses propres clics via _gui_input).
			if (!_started) return;

			// Clavier provisoire (les vrais bindings/boutons = sprint UI) :
			// Espace = saison/pause ; PageUp/PageDown = pivoter la vue (touches
			// univoques en AZERTY).
			if (ev is InputEventKey k && k.Pressed && !k.Echo)
			{
				// SLOTS de la palette (T1) en PhysicalKeycode (POSITION de la touche, pas son
				// étiquette) : en AZERTY la rangée des chiffres non-shiftée émet
				// &é"'(-è_ comme Keycode — le code physique, lui, reste Key1..8
				// quel que soit le layout. 📖 C'est la différence scancode/keysym.
				if (k.PhysicalKeycode >= Key.Key1 && k.PhysicalKeycode <= Key.Key9)
				{
					SelectSlot((int)(k.PhysicalKeycode - Key.Key1));
					return;
				}
				if (k.PhysicalKeycode == Key.Key0) { SelectSlot(9); return; }
				// Échap (T2, item 5, D4) : retour à l'accueil, avec PRÉCÉDENCE. Si un
				// panneau de consultation (Carnet/Encyclopédie/… ou Automate) est
				// ouvert, Échap le ferme d'abord et s'arrête là ; sinon il recharge la
				// scène → _ExitTree ferme proprement le pont, re-_Ready reconstruit le
				// sélecteur (nouveau choix de monde). Le garde `_started` en tête de
				// méthode assure qu'on ne recharge pas pendant l'écran de sélection.
				if (k.Keycode == Key.Escape)
				{
					// Précédence (T3 s'insère AVANT la consultation) : le dossier de
					// plante debug se ferme d'abord, puis un panneau de consultation,
					// et seulement sinon → retour à l'accueil.
					if (_dossier != null && IsInstanceValid(_dossier))
						FermerDossier();
					else if (_consultation != null && IsInstanceValid(_consultation))
						_consultation.Fermer();
					else
					{
						GD.Print("[WorldView] Échap → retour à l'accueil (rechargement).");
						GetTree().ReloadCurrentScene();
					}
					return;
				}
				// Tab = slot suivant : UNE touche cycle les slots OCCUPÉS (retour
				// F5 Nico). Plus robuste que les chiffres pour atteindre les
				// derniers gestes ; le HUD montre toujours le geste courant.
				if (k.Keycode == Key.Tab) { CycleSlots(+1); return; }
				switch (k.Keycode)
				{
					case Key.Space:    TogglePhase();  break;
					case Key.S:        CycleSeed();    break;   // espèce pour planter
					case Key.B:        CycleSubstrat(); break;  // substrat (poser pot/bac)
					case Key.N:        CycleNature();  break;   // nature du mulch (pailler ⑧)
					// Monde anti-horaire = la CAMÉRA orbite vers la droite
					// (ressenti validé par Nico au 1er F5 t4).
					case Key.Pageup:   RotateView(+1); break;
					case Key.Pagedown: RotateView(-1); break;
					case Key.M:        CycleSimMode();    break;
					case Key.F1:       CycleHudText();    break;   // cycle texte HUD : Jeu → Nu → Aide (T4, item 6)
					case Key.F2:       ToggleInspectMode(); break; // dossier de plante debug (T3)
					case Key.F3:       ToggleLabels();    break;
					case Key.F4:       TogglePerf();      break;
					case Key.C:        CopyPerfReport();  break;  // presse-papier perf
					case Key.H:        ToggleHouseGhost(); break;
					case Key.O:        ToggleShadows();   break;
					case Key.I:        ToggleMacroLife(); break;
					case Key.F6:
						if (k.ShiftPressed) CycleField();
						else ToggleFieldOverlay();
						break;
					case Key.F7:       ToggleSoilTemp();   break;
					case Key.F9:       ToggleLodDebug();   break;  // LOD émetteurs d'ombre (D67)
					case Key.F10:      _decorLayer?.ToggleBanc(); break;  // banc décor : 4 motifs (lisibilité décor T4)
					case Key.G:        ToggleGenesHover(); break;  // survol gènes debug (diversité fondatrice ③)
					// Macros de gestes (⑤, palette perso) : K enregistre une
					// séquence (re-K pour finir + persister) ; J arme le rejeu de
					// la macro au prochain clic (mêmes gestes, même point).
					case Key.K:        ToggleMacroRecord(); break;
					case Key.J:        ArmerMacro();        break;
					// --- Raccourcis DEBUG voix (pont 0.5.12) : forcer la maîtrise
					//     pour tester magazine/pages/carnet sans jouer. LETTRES libres
					//     (⚠️ F5=Run, F8=Stop sont réservés par l'éditeur Godot et
					//     ferment/relancent le jeu — retour F5 Nico). ---
					case Key.P:        DebugMaitrise("palier3");       break;  // Palier 3
					case Key.V:        DebugMaitrise("observer_tout"); break;  // Voir tout
					case Key.R:        DebugMaitrise("reset");         break;  // Reset maîtrise
					// T = « temps » : sauter DebugSkipWeeks semaines d'un coup (debug).
					case Key.T:        SkipWeeks(DebugSkipWeeks);     break;
					// A = jardinier automate F5 (⑥) : brancher/débrancher l'automate
					// (panneau journal/impasses + onglet objectifs). Maj+A = pousser
					// un objectif démo (récolter 5 tomate) pour valider l'onglet.
					case Key.A:
						if (k.ShiftPressed) InjecterObjectifDemo();
						else ToggleAutomate();
						break;
					// F = filtre du log automate (⑤) : cycle la catégorie focus ;
					// Maj+F la (dé)coche. Inerte tant que l'automate n'est pas branché.
					case Key.F:
						if (k.ShiftPressed) ToggleAutomateCat();
						else CycleAutomateCat();
						break;
				}
			}
			// Molette = paliers de zoom (décision Nico 2026-06-10 : molette,
			// pas de touches). Clic gauche = exécuter le geste courant (volet B).
			else if (ev is InputEventMouseButton mb && mb.Pressed)
			{
				if (mb.ButtonIndex == MouseButton.WheelUp)   StepZoom(+1);
				if (mb.ButtonIndex == MouseButton.WheelDown) StepZoom(-1);
				if (mb.ButtonIndex == MouseButton.Left)
				{
					var canvas = WorldMouseCanvas();
					// Mode inspection (T3, touche F2) : le clic ouvre le dossier de la
					// plante pointée (ou referme) au lieu d'agir — priorité sur tout.
					if (InspecterAuClic(canvas))
						return;
					// Macro armée (⑤, touche J) : le clic capture le point et enfile
					// le rejeu — priorité sur tout le reste (ni hub, ni geste simple).
					if (LancerMacroSiArmee(canvas, mb.ShiftPressed))
						return;
					// Priorité de clic plante > maison : cliquer le corps visible d'une
					// plante exécute le geste, jamais le hub — même si la maison est
					// devant/derrière la plante. Le hub ne s'ouvre que sur un clic maison
					// SANS plante sous le curseur.
					if (!PointeUnePlante(canvas) && ClicSurMaison(canvas))
						OuvrirConsultation("Carnet");
					else
						TryAction(canvas, mb.ShiftPressed);
				}
			}
		}

		/// <summary>Une plante est-elle sous le curseur (corps visible) ? Sert la
		/// priorité de clic plante > maison. ~500 nœuds, balayage linéaire.</summary>
		private bool PointeUnePlante(Vector2 canvasMouse)
		{
			foreach (var node in _plantNodes.Values)
				if (IsInstanceValid(node) && node.Visible
					&& node.ContientCurseur(canvasMouse))
					return true;
			return false;
		}

		private void TogglePhase()
		{
			// Un print par appui : si RIEN n'apparaît en console en tapant
			// Espace, c'est que l'input ne parvient pas au jeu (focus).
			switch (_phase)
			{
				case Phase.Planification:
					_timeAccum = 0f;
					SetPhase(Phase.Saison);
					GD.Print("[WorldView] Espace → saison lancée.");
					break;
				case Phase.Saison:
					SetPhase(Phase.Pause);
					GD.Print("[WorldView] Espace → pause.");
					break;
				case Phase.Pause:
					SetPhase(Phase.Saison);
					GD.Print("[WorldView] Espace → reprise.");
					break;
			}
		}

		private void SetPhase(Phase phase)
		{
			_phase = phase;
			UpdateClock();
		}

		private void CycleSimMode()
		{
			_simMode = (SimMode)(((int)_simMode + 1) % 3);
			GD.Print($"[WorldView] M → mode simulation : {_simMode}.");
			UpdateClock();
		}

		private void ToggleLabels()
		{
			// Cycle Survol → Toutes → Aucune. L'affichage est entièrement géré
			// chaque frame par UpdatePlantLabels (WorldView.Etiquettes.cs) selon
			// ce mode — rien à basculer ici, juste l'état.
			_labelMode = (LabelMode)(((int)_labelMode + 1) % 3);
			GD.Print($"[WorldView] F3 → étiquettes : {_labelMode}.");
		}

		private void ToggleHouseGhost()
		{
			_houseGhost = !_houseGhost;
			ApplyHouseGhost();
			GD.Print($"[WorldView] H → maison {(_houseGhost ? "transparente" : "opaque")}.");
		}

		private void ToggleShadows()
		{
			ShadowsOn = !ShadowsOn;
			if (_houseShadow != null) _houseShadow.Visible = ShadowsOn;
			// Re-dessiner les nœuds d'ombre : OFF → _Draw vide les efface ;
			// ON → repartir d'un soleil « sale » force le recalcul immédiat.
			_lastSunH = float.NaN;
			foreach (var node in _plantNodes.Values)
				node.GetNodeOrNull<Node2D>("Shadow")?.QueueRedraw();
			GD.Print($"[WorldView] O → ombres {(ShadowsOn ? "ON" : "OFF")}.");
		}

		// Touche I (correctif t6·B2, demande Nico F5) : montre/cache la vie
		// macro. Visible=false court-circuite _Process ET le dessin (coût nul) ;
		// les données continuent de suivre les snapshots — rallumer est gratuit.
		private void ToggleMacroLife()
		{
			if (_macroLife == null) return;
			_macroLife.Visible = !_macroLife.Visible;
			GD.Print($"[WorldView] I → vie macro {(_macroLife.Visible ? "ON" : "OFF")}.");
		}

		// Touche F9 (LOD émetteurs d'ombre, D67) : teinte les plantes NON-émettrices
		// (semis sous-seuil écartés des boucles d'ombre par le LOD). On rebalaie tous
		// les nœuds pour (re)poser/retirer la teinte — coût trivial (~150 nœuds, un
		// SelfModulate chacun). « Affichage technique déconseillé en découverte »,
		// même esprit que les heatmaps F6/F7 (philo #5).
		private void ToggleLodDebug()
		{
			LodDebugOn = !LodDebugOn;
			foreach (var node in _plantNodes.Values) node.ApplyLodTint();
			GD.Print($"[WorldView] F9 → overlay LOD émetteurs {(LodDebugOn ? "ON" : "OFF")}.");
		}

		// Modulate = teinte × alpha appliquée au nœud ET ses enfants : un seul
		// réglage rend les 5 polygones de la maison fantomatiques. L'ombre
		// portée n'est PAS affectée (elle vit dans _ground) : une maison
		// transparente ombre toujours — c'est le moteur qui décide, pas la vue.
		private void ApplyHouseGhost()
		{
			if (_house != null)
				_house.Modulate = new Color(1f, 1f, 1f, _houseGhost ? 0.15f : 1f);
		}

		// --- Raccourcis DEBUG (retour F5 voix, pont 0.5.12) --------------------

		// F8/F9/F10 : force la maîtrise via le pont (palier3 / observer_tout /
		// reset) pour tester magazine/pages/carnet sans jouer jusqu'au palier 3.
		// Les panneaux de voix se rafraîchissent à leur prochaine ouverture.
		private void DebugMaitrise(string op)
		{
			if (_bridge == null) return;
			_bridge.Debug(op);
			// Reset : vider aussi la dédup de survol, sinon les espèces déjà
			// survolées ne se ré-observeraient plus (encyclopédie muette au survol).
			if (op == "reset") _especesObservees.Clear();
			GD.Print($"[WorldView] DEBUG maîtrise : {op}.");
		}

		// Touche T : avance N semaines d'un coup, SYNCHRONE (petit gel assumé ~N
		// ticks) — uniquement si le pipe est libre (pas de step/action en vol),
		// pour ne pas court-circuiter la boucle async. Applique le dernier snapshot.
		private void SkipWeeks(int n)
		{
			if (!PipeFree) { GD.Print("[WorldView] skip ignoré (pipe occupé)."); return; }
			GDict snap = null;
			for (int i = 0; i < n; i++)
			{
				snap = _bridge.StepWeek();
				if (snap == null) { GD.PrintErr("[WorldView] skip interrompu (step nul)."); break; }
			}
			if (snap != null)
			{
				ApplySnapshot(snap, fade: false);
				GD.Print($"[WorldView] DEBUG saut de {n} semaines.");
			}
		}
	}
}
