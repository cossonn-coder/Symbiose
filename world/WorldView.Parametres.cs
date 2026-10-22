// SYMBIOSE — WorldView.Parametres.cs
// Sous-panneau PARAMÈTRES du launcher (sprint « fenêtrage UI » T2). Ouvert par le
// bouton « Paramètres… » du sélecteur (WorldView.Selecteur.cs), il regroupe les
// réglages qui ont un SENS AVANT de monter un monde (décision D-A7 : Paramètres =
// launcher UNIQUEMENT en v1). Deux familles :
//   1. CONFORT (vue) appliqué à la simulation à venir :
//      - Vitesse de sim → écrit `SecondsPerWeek` (champ de démarrage, plage 30-180 s) ;
//      - Ombres → bascule `ShadowsOn` (état persistant honoré chaque frame par le
//        soleil) via la MÊME méthode que la touche O (`ToggleShadows`, aucune
//        duplication de logique).
//   2. INIT passées à `cmd_init` au lancement (mémorisées ici, lues par
//      StartSimulation → SimBridge.Init) :
//      - Encyclopédie de démarrage (vierge / amorcée / fournie) ;
//      - Carnet interprétatif anticipé (OUI / NON) ;
//      - Vigueur infinie (réglage de TEST, défaut OUI pendant la phase de test).
//
// ⚠️ Périmètre volontairement RESTREINT (Simplicity First + D-A7) : les overlays
// debug PUREMENT runtime (heatmaps F6, température sol F7, vie macro I, LOD F9)
// dépendent de couches construites APRÈS le lancement — ils n'ont pas de cible au
// launcher et RESTENT sur leurs touches in-game (D-A7). Seuls les réglages honorés
// dès le démarrage (vitesse, ombres) + les options d'init sont exposés ici. Le
// détail est consigné dans 00_etat.md pour Nico.
//
// 📖 Pédagogie Godot/C# :
//  - Le sous-panneau est un PanelContainer enfant du MÊME CanvasLayer que le
//    sélecteur (`_selecteur`) → il disparaît avec lui au « Lancer » (QueueFree
//    récursif), rien à démonter à la main.
//  - HSlider.ValueChanged / OptionButton.ItemSelected / CheckButton.Toggled :
//    signaux d'UI ; chaque handler écrit directement le champ concerné.
//  - UiScroll.Envelopper : patron transversal du sprint (défile si débordement).

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		// Choix d'INIT mémorisés par le panneau, transmis à `cmd_init` au lancement
		// (StartSimulation → _bridge.Init). Défauts = réglages d'aide de CLAUDE.md
		// (encyclopédie « amorcée », carnet interprétatif NON anticipé).
		private string _encycloDemarrage = "amorcee";
		private bool _carnetAnticipe = false;
		// Réglage de TEST « Vigueur infinie » : les gestes ne coûtent plus rien.
		// Défaut ON tant que dure la phase de test (demande Nico 2026-10-22) — à
		// repasser à false avant de distribuer le jeu.
		private bool _vigueurInfinie = true;

		// Le sous-panneau lui-même (caché par défaut) + le label de la vitesse (mis
		// à jour au fil du slider).
		private PanelContainer _parametres;
		private Label _vitesseLabel;

		// Codes d'encyclopédie dans l'ordre des items de l'OptionButton.
		private static readonly string[] EncycloCodes = { "vierge", "amorcee", "fournie" };

		private void BuildParametres()
		{
			_parametres = new PanelContainer { Visible = false };
			// Ancré à DROITE du panneau launcher (320 de large + marge) pour ne pas
			// le recouvrir ; défile si le contenu déborde en hauteur.
			_parametres.SetAnchorsPreset(Control.LayoutPreset.TopLeft);
			_parametres.Position = new Vector2(352, 16);
			_parametres.CustomMinimumSize = new Vector2(300, 0);
			_selecteur.AddChild(_parametres);

			// Contenu enveloppé dans un ScrollContainer borné (patron T1
			// `UiScroll.Envelopper`) : défile SI le panneau déborde en hauteur.
			var vbox = new VBoxContainer { CustomMinimumSize = new Vector2(300, 0) };
			_parametres.AddChild(UiScroll.Envelopper(vbox, 420f));

			vbox.AddChild(new Label
			{
				Text = "Paramètres",
				HorizontalAlignment = HorizontalAlignment.Center,
			});

			// --- Confort : vitesse de simulation (écrit SecondsPerWeek) ---
			_vitesseLabel = new Label();
			vbox.AddChild(_vitesseLabel);
			var vitesse = new HSlider
			{
				MinValue = 30, MaxValue = 180, Step = 1, Value = SecondsPerWeek,
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
			};
			vitesse.ValueChanged += v =>
			{
				SecondsPerWeek = (float)v;
				MajVitesseLabel();
			};
			vbox.AddChild(vitesse);
			MajVitesseLabel();

			// --- Confort : ombres (même bascule que la touche O) ---
			var ombres = new CheckButton { Text = "Ombres", ButtonPressed = ShadowsOn };
			ombres.Toggled += on =>
			{
				// ToggleShadows FLIPPE l'état ; on ne l'appelle que si le nouvel état
				// voulu diffère de l'actuel (évite un double-flip). Réutilise la
				// logique existante (WorldView.Controls.cs), zéro duplication.
				if (on != ShadowsOn) ToggleShadows();
			};
			vbox.AddChild(ombres);

			vbox.AddChild(new HSeparator());

			// --- Init : encyclopédie de démarrage ---
			vbox.AddChild(new Label { Text = "Encyclopédie de démarrage" });
			var encyclo = new OptionButton { SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
			encyclo.AddItem("vierge");
			encyclo.AddItem("amorcée");
			encyclo.AddItem("fournie");
			encyclo.Selected = 1;   // défaut : amorcée (réglage d'aide CLAUDE.md)
			encyclo.ItemSelected += idx => _encycloDemarrage = EncycloCodes[idx];
			vbox.AddChild(encyclo);

			// --- Init : carnet interprétatif anticipé ---
			var carnet = new CheckButton
			{
				Text = "Carnet interprétatif anticipé",
				ButtonPressed = _carnetAnticipe,
			};
			carnet.Toggled += on => _carnetAnticipe = on;
			vbox.AddChild(carnet);

			// --- Init : Vigueur infinie (réglage de test) ---
			var vigueur = new CheckButton
			{
				Text = "Vigueur infinie (test)",
				ButtonPressed = _vigueurInfinie,
			};
			vigueur.Toggled += on => _vigueurInfinie = on;
			vbox.AddChild(vigueur);
		}

		private void MajVitesseLabel()
		{
			_vitesseLabel.Text = $"Vitesse de sim : {SecondsPerWeek:0} s / semaine";
		}

		// Ouvre/ferme le sous-panneau (bouton « Paramètres… » du sélecteur).
		private void ToggleParametres()
		{
			if (_parametres != null) _parametres.Visible = !_parametres.Visible;
		}
	}
}
