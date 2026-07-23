// SYMBIOSE — WorldView.Selecteur.cs
// Écran de SÉLECTION DE MONDE (sprint « bancs d'essai » ⑤, refondu au sprint
// « fenêtrage UI » T1). Au lancement de la scène, au lieu de démarrer la `config`
// de l'Export, on présente un menu pour choisir full / smoke / propre / un banc
// d'essai À L'ÉCRAN. T1 : panneau ancré EN HAUT À GAUCHE, liste DÉFILANTE (au lieu
// d'un dropdown) et barre de FILTRE (par nom + par catégorie).
//
// 📖 Pédagogie Godot/C# (Nico apprend le frontend) :
//  - CanvasLayer : couche d'UI qui flotte AU-DESSUS du monde, en coordonnées
//    ÉCRAN (indifférente à la caméra/zoom). Le bon parent pour un menu.
//  - LayoutPreset.TopLeft + Position : on ancre le panneau au coin haut-gauche
//    puis on le décale d'une marge (16 px). Pas de calcul de centrage.
//  - ScrollContainer (via UiScroll.Envelopper) : la liste défile si elle déborde.
//  - ButtonGroup : un groupe de boutons TOGGLE dont un SEUL reste enfoncé —
//    c'est notre « sélection courante » visible (le banc choisi reste pressé).
//  - LineEdit.TextChanged / OptionButton.ItemSelected : signaux de filtre. Ils
//    recomposent la liste depuis la source MÉMORISÉE (`_bancs`), sans jamais
//    ré-interroger le pont (le registre ne change pas en cours d'écran).
//
// La LISTE des bancs vient du serveur (SimBridge.ListBancs → commande list_bancs),
// jamais d'une copie codée en dur : le registre Python `BANCS` reste la source
// unique (un menu périmé serait le faux signal que ce sprint combat, D47).

using Godot;
using System.Collections.Generic;
using System.Linq;

namespace Symbiose
{
	public partial class WorldView
	{
		// La couche entière du menu — libérée d'un bloc au lancement.
		private CanvasLayer _selecteur;

		// Entrées fixes (mondes canon) présentées en tête, hors registre de bancs.
		// « propre » = banc « monde propre » (équilibre invasion, D69) monté par une
		// config d'init côté serveur, pas par le registre → ajouté à la main ici.
		private static readonly (string Nom, string Categorie)[] EntreesCanon =
		{
			("full", "monde"), ("smoke", "monde"), ("propre", "monde"),
		};

		// Source COMPLÈTE mémorisée (canon + bancs) : le filtre travaille dessus,
		// jamais sur le pont.
		private (string Nom, string Categorie)[] _bancs;

		// Widgets de filtre + réceptacle de la liste (rebâtie à chaque filtrage).
		private LineEdit _filtreNom;
		private OptionButton _filtreCat;
		private VBoxContainer _liste;
		private ButtonGroup _groupeBancs;   // sélection courante (un toggle actif)

		private void BuildSelecteur()
		{
			_selecteur = new CanvasLayer { Name = "Selecteur" };
			AddChild(_selecteur);

			// Panneau ancré en HAUT À GAUCHE, largeur fixe raisonnable, décalé d'une
			// marge du coin. PanelContainer = fond + marges natifs.
			var panneau = new PanelContainer();
			panneau.SetAnchorsPreset(Control.LayoutPreset.TopLeft);
			panneau.Position = new Vector2(16, 16);
			panneau.CustomMinimumSize = new Vector2(320, 0);
			_selecteur.AddChild(panneau);

			var vbox = new VBoxContainer { CustomMinimumSize = new Vector2(320, 0) };
			panneau.AddChild(vbox);

			vbox.AddChild(new Label
			{
				Text = "Choisir un monde",
				HorizontalAlignment = HorizontalAlignment.Center,
			});

			// --- Barre de filtre : nom (sous-chaîne) + catégorie ---
			_filtreNom = new LineEdit
			{
				PlaceholderText = "Filtrer par nom…",
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
			};
			_filtreNom.TextChanged += _ => RebatirListe();
			vbox.AddChild(_filtreNom);

			_filtreCat = new OptionButton
			{
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
			};
			_filtreCat.ItemSelected += _ => RebatirListe();
			vbox.AddChild(_filtreCat);

			// --- Source mémorisée : canon en tête, puis les bancs du registre ---
			_bancs = EntreesCanon.Concat(_bridge.ListBancs()).ToArray();

			// Catégories distinctes → OptionButton du filtre. « toutes » en tête
			// (index 0 = pas de filtre catégorie), puis les catégories triées.
			_filtreCat.AddItem("toutes catégories");
			foreach (string cat in _bancs.Select(b => b.Categorie).Distinct().OrderBy(c => c))
				_filtreCat.AddItem(cat);

			// --- Liste défilante (un bouton toggle par banc) ---
			// Pleine hauteur (T2, item 3, D5) : la liste descend jusqu'en bas d'écran
			// au lieu de plafonner à 360 px. Hauteur max = écran (1080) − marge haute
			// (16) − marge basse (16) − widgets fixes du panneau (titre + 2 filtres +
			// 2 boutons ≈ 220 px). Le ScrollContainer défile toujours si la liste
			// dépasse cette hauteur (comportement inchangé), sinon rien ne bouge.
			const float hauteurListe = 1080f - 16f - 16f - 220f;   // ≈ 832 px
			_groupeBancs = new ButtonGroup();
			_liste = new VBoxContainer { SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
			vbox.AddChild(UiScroll.Envelopper(_liste, hauteurListe));

			// Bouton « Paramètres » : ouvre/ferme le sous-panneau d'options (T2).
			var params_ = new Button { Text = "Paramètres…" };
			params_.Pressed += ToggleParametres;
			vbox.AddChild(params_);

			var bouton = new Button { Text = "Lancer" };
			bouton.Pressed += Lancer;
			vbox.AddChild(bouton);

			BuildParametres();   // sous-panneau caché, révélé par le bouton ci-dessus
			RebatirListe();      // remplit la liste + applique la présélection
		}

		// Recompose la liste affichée depuis `_bancs` selon les deux filtres. La
		// sélection courante est préservée si l'entrée choisie reste visible ; sinon
		// on retombe sur la présélection (`Config`), puis sur la 1re entrée visible.
		private void RebatirListe()
		{
			string dejaChoisi = ConfigChoisie();
			foreach (Node enfant in _liste.GetChildren())
				enfant.QueueFree();

			string saisie = _filtreNom.Text.ToLower();
			string cat = _filtreCat.Selected <= 0 ? null : _filtreCat.GetItemText(_filtreCat.Selected);

			Button premier = null, aReselectionner = null;
			foreach (var (nom, categorie) in _bancs)
			{
				if (saisie.Length > 0 && !nom.ToLower().Contains(saisie)) continue;
				if (cat != null && categorie != cat) continue;

				var b = new Button
				{
					Text = categorie == "monde" ? nom : $"[{categorie}] {nom}",
					ToggleMode = true,
					ButtonGroup = _groupeBancs,
					Alignment = HorizontalAlignment.Left,
				};
				b.SetMeta("config", nom);
				_liste.AddChild(b);

				premier ??= b;
				if (nom == dejaChoisi || (aReselectionner == null && nom == Config))
					aReselectionner = b;
			}

			// Rétablir une sélection visible (choix courant > présélection Export >
			// 1re entrée) pour que « Lancer » ait toujours une cible.
			var cible = aReselectionner ?? premier;
			if (cible != null) cible.ButtonPressed = true;
		}

		// Config du banc actuellement sélectionné (bouton toggle enfoncé), ou null.
		private string ConfigChoisie()
		{
			var presse = _groupeBancs?.GetPressedButton();
			return presse != null ? (string)presse.GetMeta("config") : null;
		}

		private void Lancer()
		{
			string config = ConfigChoisie();
			if (config == null) return;   // liste vide (filtre trop strict) → rien à lancer
			GD.Print($"[WorldView] sélecteur → lancement config « {config} ».");
			_selecteur.QueueFree();   // le menu disparaît (plus aucun clic capté)
			_selecteur = null;
			StartSimulation(config);
		}
	}
}
