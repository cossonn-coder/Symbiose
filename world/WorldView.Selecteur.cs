// SYMBIOSE — WorldView.Selecteur.cs
// Écran de SÉLECTION DE MONDE (sprint « bancs d'essai », tronçon ⑤). Partial de
// WorldView : au lancement de la scène, au lieu de démarrer directement la
// `config` de l'Export, on présente un menu pour choisir full / smoke / un banc
// d'essai À L'ÉCRAN, sans éditer d'argument dans l'inspecteur.
//
// 📖 Pédagogie Godot/C# (Nico apprend le frontend) :
//  - CanvasLayer : une couche d'UI qui flotte AU-DESSUS du monde, en coordonnées
//    ÉCRAN (indifférente à la caméra/zoom 2D). C'est le bon parent pour un menu.
//  - OptionButton : la liste déroulante native (un « combo box »). AddItem ajoute
//    une entrée ; Selected = index courant ; GetItemText(i) = son libellé.
//  - Button.Pressed += () => {…} : on branche un lambda C# sur le SIGNAL Godot du
//    bouton (équivalent d'un connect()). Au clic, il lance la simulation.
//  - QueueFree() : libère le nœud à la fin de la frame (on retire tout le menu une
//    fois le monde lancé — il ne doit plus capter le moindre clic).
//
// La LISTE des bancs vient du serveur (SimBridge.ListBancs → commande list_bancs),
// pas d'une copie codée en dur ici : le registre Python `BANCS` reste la source
// unique (un menu périmé serait exactement le faux signal que ce sprint combat).

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		// La couche entière du menu — libérée d'un bloc au lancement.
		private CanvasLayer _selecteur;

		private void BuildSelecteur()
		{
			_selecteur = new CanvasLayer { Name = "Selecteur" };
			AddChild(_selecteur);

			// Panneau centré (PanelContainer = fond + marges ; preset Center le
			// place au milieu de l'écran sans calcul manuel d'ancrage).
			var panneau = new PanelContainer();
			panneau.SetAnchorsPreset(Control.LayoutPreset.Center);
			_selecteur.AddChild(panneau);

			var vbox = new VBoxContainer { CustomMinimumSize = new Vector2(260, 0) };
			panneau.AddChild(vbox);

			vbox.AddChild(new Label
			{
				Text = "Choisir un monde",
				HorizontalAlignment = HorizontalAlignment.Center,
			});

			var liste = new OptionButton();
			vbox.AddChild(liste);
			// full / smoke d'abord (les deux mondes canon : la démo et le golden),
			// puis les bancs d'essai dans l'ordre du registre Python (source unique).
			liste.AddItem("full");
			liste.AddItem("smoke");
			// « propre » = banc « monde propre » (équilibre invasion ①/⑧, D69) : mêmes
			// tuiles + cultivées + démo paillée sud, mais succession férale COUPÉE →
			// observer les cultivées seules (levier paillage lisible sans l'invasion).
			// Config d'init côté serveur (pas un banc du registre) → ajoutée à la main.
			liste.AddItem("propre");
			foreach (string nom in _bridge.ListBancs())
				liste.AddItem(nom);
			// Présélection = la `config` de l'Export (défaut « full ») si elle est
			// dans la liste → l'inspecteur garde son rôle de défaut, le menu n'est
			// qu'un moyen d'en changer à la volée.
			for (int i = 0; i < liste.ItemCount; i++)
				if (liste.GetItemText(i) == Config) { liste.Select(i); break; }

			var bouton = new Button { Text = "Lancer" };
			vbox.AddChild(bouton);
			bouton.Pressed += () =>
			{
				string config = liste.GetItemText(liste.Selected);
				GD.Print($"[WorldView] sélecteur → lancement config « {config} ».");
				_selecteur.QueueFree();   // le menu disparaît (plus aucun clic capté)
				_selecteur = null;
				StartSimulation(config);
			};
		}
	}
}
