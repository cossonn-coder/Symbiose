// SYMBIOSE — WorldView.Controls.cs (partial de WorldView, SS⑥ refactor global)
// Les ENTRÉES clavier/souris (bindings provisoires — les vrais boutons = sprint
// UI) et les bascules d'état qu'elles déclenchent : phase (Espace), mode de
// simulation (M), étiquettes (F3), maison transparente (H), ombres (O), vie
// macro (I). Le zoom/rotation va à la caméra, les gestes 1..8 aux actions, la
// heatmap au HUD — _UnhandledInput ne fait qu'aiguiller (partial = même classe).

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private bool _houseGhost;             // maison transparente (H)

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
				// Gestes 1..8 en PhysicalKeycode (POSITION de la touche, pas son
				// étiquette) : en AZERTY la rangée des chiffres non-shiftée émet
				// &é"'(-è_ comme Keycode — le code physique, lui, reste Key1..8
				// quel que soit le layout. 📖 C'est la différence scancode/keysym.
				if (k.PhysicalKeycode >= Key.Key1 && k.PhysicalKeycode <= Key.Key9)
				{
					SelectGeste((int)(k.PhysicalKeycode - Key.Key1));
					return;
				}
				// Tab = geste suivant : UNE touche cycle toute la palette (retour
				// F5 Nico). Plus robuste que les chiffres pour atteindre les
				// derniers gestes ; le HUD montre toujours le geste courant.
				if (k.Keycode == Key.Tab) { CyclePalette(+1); return; }
				switch (k.Keycode)
				{
					case Key.Space:    TogglePhase();  break;
					case Key.S:        CycleSeed();    break;   // espèce pour planter
					case Key.B:        CycleSubstrat(); break;  // substrat (poser pot/bac)
					// Monde anti-horaire = la CAMÉRA orbite vers la droite
					// (ressenti validé par Nico au 1er F5 t4).
					case Key.Pageup:   RotateView(+1); break;
					case Key.Pagedown: RotateView(-1); break;
					case Key.M:        CycleSimMode();    break;
					case Key.F3:       ToggleLabels();    break;
					case Key.F4:       TogglePerf();      break;
					case Key.H:        ToggleHouseGhost(); break;
					case Key.O:        ToggleShadows();   break;
					case Key.I:        ToggleMacroLife(); break;
					case Key.F6:
						if (k.ShiftPressed) CycleField();
						else ToggleFieldOverlay();
						break;
					case Key.F7:       ToggleSoilTemp();   break;
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
					// Clic sur la maison = ouvrir le HUB (voix), pas un geste sol.
					var canvas = WorldMouseCanvas();
					bool surMaison = ClicSurMaison(canvas);
					// TRACE TEMPORAIRE (diagnostic F5 clic maison) : à retirer une
					// fois le picking confirmé. Dit si le clic touche la silhouette.
					GD.Print($"[WorldView] clic gauche canvas={canvas} → surMaison={surMaison}");
					if (surMaison) OuvrirHubMaison();
					else TryAction(canvas, mb.ShiftPressed);
				}
			}
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

		// Modulate = teinte × alpha appliquée au nœud ET ses enfants : un seul
		// réglage rend les 5 polygones de la maison fantomatiques. L'ombre
		// portée n'est PAS affectée (elle vit dans _ground) : une maison
		// transparente ombre toujours — c'est le moteur qui décide, pas la vue.
		private void ApplyHouseGhost()
		{
			if (_house != null)
				_house.Modulate = new Color(1f, 1f, 1f, _houseGhost ? 0.15f : 1f);
		}
	}
}
