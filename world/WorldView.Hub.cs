// SYMBIOSE — WorldView.Hub.cs (partial de WorldView, sprint UI voix ②)
// La MAISON NORMANDE comme HUB VIVANT cliquable (décision Q2). Un clic sur
// l'empreinte de la maison ouvre un petit menu des 5 fonctions du hub :
// Atelier · Semis intérieur · Magazine · Carnet · Foyer (CLAUDE.md). Ici, 4
// entrées VOIX (Carnet / Encyclopédie / Magazine / Pages du grenier) ouvrent un
// VoicePanel ; les 3 entrées non-voix (Atelier / Semis intérieur / Foyer) sont
// affichées mais GRISÉES « à venir » (micro-décision A → dette D54). On
// n'invente pas leur comportement.
//
// 📖 Pédagogie Godot/C# :
//  - Détection du clic maison : on convertit la souris (espace caméra du
//    SubViewport, via WorldMouseCanvas) en cm MONDE (ScreenToWorld), puis on
//    teste l'appartenance au rectangle d'empreinte [_hx0,_hy0]→[_hx1,_hy1]. Pas
//    besoin d'Area2D/collision : l'empreinte est un simple rectangle au sol.
//  - Le menu est un CanvasLayer éphémère (comme le sélecteur ⑤) : il se libère
//    au clic d'une entrée ou en cliquant à côté.
//  - Button.Disabled = true grise le bouton ET l'inerte (aucun signal émis) —
//    la façon native de dire « à venir » sans câbler de comportement.
//
// INVARIANT « Godot bête » : ce partial ne fabrique aucun texte de voix. Il
// route seulement vers le bon VoicePanel ; le contenu viendra du pont en ③④.

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Un seul menu / un seul panneau voix actifs à la fois (le clic maison
		// route vers le bon contenu). Champs pour pouvoir les fermer/remplacer.
		private CanvasLayer _hubMenu;
		private VoicePanel _voicePanel;

		// -------------------------------------------------------------------
		// DÉTECTION DU CLIC MAISON
		// -------------------------------------------------------------------

		/// <summary>
		/// La souris (clic gauche) tombe-t-elle sur la maison ? Appelé AVANT
		/// TryAction : un clic sur la maison ouvre le hub au lieu d'exécuter un
		/// geste sur le sol.
		/// </summary>
		private bool ClicSurMaison(Vector2 mouseCanvas)
		{
			// _house n'existe qu'une fois le monde construit (BuildHouse).
			if (_house == null) return false;

			// 📖 Picking iso : la maison est DESSINÉE comme un volume (empreinte
			// au sol + murs qui montent + toit jusqu'au faîte, cf. BuildHouse).
			// Tester l'empreinte au sol via ScreenToWorld(z=0) raterait tout clic
			// sur les façades/toit (ils se reprojettent au sol PLUS AU NORD que
			// l'empreinte → hors rectangle). On teste donc la SILHOUETTE ÉCRAN
			// complète : enveloppe convexe des 4 coins au sol + leurs hauts de
			// murs + le faîte. WorldToScreen applique déjà l'orientation → le
			// test suit la rotation de vue (D35) sans effort. Généreux aux
			// avant-toits, ce qui aide la visée.
			Vector2 up   = new(0f, -_hWallCm * PxPerCmZ);
			Vector2 apex = WorldToScreen((_hx0 + _hx1) / 2f, (_hy0 + _hy1) / 2f)
						 - new Vector2(0f, _hHeightCm * PxPerCmZ);
			Vector2[] b =
			{
				WorldToScreen(_hx0, _hy0), WorldToScreen(_hx1, _hy0),
				WorldToScreen(_hx1, _hy1), WorldToScreen(_hx0, _hy1),
			};
			Vector2[] silhouette = Geometry2D.ConvexHull(new[]
			{
				b[0], b[1], b[2], b[3],
				b[0] + up, b[1] + up, b[2] + up, b[3] + up, apex,
			});
			return Geometry2D.IsPointInPolygon(mouseCanvas, silhouette);
		}

		// -------------------------------------------------------------------
		// MENU HUB — 5 fonctions (4 voix actives + Foyer/Atelier/Semis grisés)
		// -------------------------------------------------------------------

		private void OuvrirHubMaison()
		{
			FermerHubMenu();   // jamais deux menus superposés

			_hubMenu = new CanvasLayer { Name = "HubMenu", Layer = 8 };
			AddChild(_hubMenu);

			// Voile qui referme le menu si on clique à côté (hors du panneau).
			var voile = new ColorRect
			{
				Color = new Color(0f, 0f, 0f, 0.25f),
				MouseFilter = Control.MouseFilterEnum.Stop,
			};
			voile.SetAnchorsPreset(Control.LayoutPreset.FullRect);
			voile.GuiInput += ev =>
			{
				if (ev is InputEventMouseButton mb && mb.Pressed
					&& mb.ButtonIndex == MouseButton.Left)
					FermerHubMenu();
			};
			_hubMenu.AddChild(voile);

			var panneau = new PanelContainer();
			panneau.SetAnchorsPreset(Control.LayoutPreset.Center);
			panneau.CustomMinimumSize = new Vector2(280, 0);
			_hubMenu.AddChild(panneau);

			var vbox = new VBoxContainer();
			panneau.AddChild(vbox);

			vbox.AddChild(new Label
			{
				Text = "Maison",
				HorizontalAlignment = HorizontalAlignment.Center,
			});

			// Entrées VOIX (actives) — chacune ouvre le VoicePanel adéquat. ③ a
			// branché Carnet et Encyclopédie sur le pont ; Magazine / Pages
			// restent des VoicePanel de base (« à venir ») jusqu'au tronçon ④.
			AjouterEntreeVoix(vbox, "Carnet",       "Carnet",       "carnet");
			AjouterEntreeVoix(vbox, "Encyclopédie", "Encyclopédie", "encyclopedie");
			AjouterEntreeVoix(vbox, "Magazine",     "Magazine de botanique", "magazine");
			AjouterEntreeVoix(vbox, "Pages du grenier", "Pages du grenier", "pages");

			// Atelier (acquisition des moyens d'agir ④) : 5ᵉ fonction du hub, ACTIVE.
			// Même patron que les voix (un VoicePanel spécialisé, AtelierPanel), mais
			// c'est une VITRINE d'acquisition (outils + matériaux contre Vigueur), pas
			// une voix narrative. Elle route par la même mécanique OuvrirVoicePanel.
			AjouterEntreeVoix(vbox, "Atelier", "Atelier", "atelier");

			// Entrées NON-VOIX restantes (grisées « à venir » → dette D54).
			AjouterEntreeGrisee(vbox, "Semis intérieur");
			AjouterEntreeGrisee(vbox, "Foyer");

			GD.Print("[WorldView] hub-maison ouvert (5 fonctions, Atelier + 4 voix actives).");
		}

		// Une entrée active : clic → ferme le menu, ouvre le VoicePanel de la
		// voix (`fonction` sélectionne la spécialisation ; titre = libellé affiché).
		private void AjouterEntreeVoix(VBoxContainer parent, string libelle,
			string titre, string fonction)
		{
			var b = new Button { Text = libelle };
			b.Pressed += () =>
			{
				FermerHubMenu();
				OuvrirVoicePanel(titre, fonction);
			};
			parent.AddChild(b);
		}

		// Une entrée grisée : visible, inerte (aucun signal). « à venir » (D54).
		private void AjouterEntreeGrisee(VBoxContainer parent, string libelle)
		{
			parent.AddChild(new Button
			{
				Text = $"{libelle}  (à venir)",
				Disabled = true,
			});
		}

		private void FermerHubMenu()
		{
			if (_hubMenu == null) return;
			_hubMenu.QueueFree();
			_hubMenu = null;
		}

		// -------------------------------------------------------------------
		// VOICE PANEL — un seul actif à la fois
		// -------------------------------------------------------------------

		private void OuvrirVoicePanel(string titre, string fonction)
		{
			if (_voicePanel != null && IsInstanceValid(_voicePanel))
				_voicePanel.Fermer();

			// Une voix = une spécialisation de VoicePanel (③ : Carnet /
			// Encyclopédie ; ④ : Magazine / Pages). Le pont est injecté AVANT
			// Ouvrir (les spécialisations lisent leur voix dès le peuplement).
			_voicePanel = fonction switch
			{
				"carnet"       => new CarnetPanel(),
				"encyclopedie" => new EncyclopediePanel(),
				"magazine"     => new MagazinePanel(),
				"pages"        => new PagesPanel(),
				"atelier"      => new AtelierPanel(),   // acquisition des moyens d'agir ④
				_              => new VoicePanel(),
			};
			_voicePanel.InjecterPont(_bridge);
			AddChild(_voicePanel);
			_voicePanel.Ouvrir(titre, onFerme: () => _voicePanel = null);
		}
	}
}
