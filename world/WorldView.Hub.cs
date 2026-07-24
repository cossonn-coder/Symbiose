// SYMBIOSE — WorldView.Hub.cs (partial de WorldView ; refactor fenêtrage UI T3)
// La MAISON NORMANDE comme HUB VIVANT cliquable. Depuis T3, le clic maison n'ouvre
// PLUS un menu intermédiaire des 5 fonctions (A8) : il ouvre DIRECTEMENT le
// conteneur de consultation à onglets (`ConsultationPanel`), positionné au tiers
// droit (D59 absorbée), sur l'onglet Carnet. Les surfaces d'information (Carnet ·
// Encyclopédie · Magazine · Pages · Atelier) sont des ONGLETS ; l'Automate s'ajoute
// en dernier, DEV-GATED (touche A). Foyer / Semis intérieur redeviendront des
// onglets à leur implémentation (A9 → dette D54) — pas d'onglet mort en v1.
//
// 📖 Pédagogie Godot/C# :
//  - Détection du clic maison : on convertit la souris en cm MONDE (ScreenToWorld)
//    et on teste l'appartenance à la SILHOUETTE ÉCRAN du volume (empreinte + murs
//    + faîte). Pas d'Area2D : géométrie pure, qui suit la rotation de vue (D35).
//  - Chaque onglet est un `Control` (VoicePanel-dérivé ou AutomateContent) construit
//    UNE fois puis confié au `TabContainer` : masqué/affiché, jamais reconstruit.
//
// INVARIANT « Godot bête » : ce partial ne fabrique aucun texte de voix. Il route
// vers le conteneur ; le contenu verbatim vient du pont dans chaque onglet.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Un seul conteneur de consultation actif à la fois (le clic maison / la
		// touche A route vers le bon onglet). Champ pour pouvoir le fermer/remplacer.
		private ConsultationPanel _consultation;

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

			// 📖 Picking iso : la maison est DESSINÉE comme un volume (empreinte au
			// sol + murs + toit). Tester la seule empreinte au sol raterait les clics
			// sur façades/toit (ils se reprojettent PLUS AU NORD). On teste donc la
			// SILHOUETTE ÉCRAN complète : enveloppe convexe des 4 coins au sol + leurs
			// hauts de murs + le faîte. WorldToScreen applique déjà l'orientation → le
			// test suit la rotation de vue (D35). Généreux aux avant-toits (aide la visée).
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
		// CONTENEUR DE CONSULTATION — onglets Carnet…Atelier (+ Automate dev-gated)
		// -------------------------------------------------------------------

		/// <summary>
		/// Ouvre (ou ré-ouvre) le conteneur de consultation sur l'onglet nommé.
		/// Reconstruit la fenêtre entière — bon marché : les contenus sont légers, et
		/// seul le CHANGEMENT D'ONGLET reste sans reconstruction (perf, garanti par le
		/// TabContainer). Un seul conteneur actif à la fois.
		/// </summary>
		private void OuvrirConsultation(string ongletInitial)
		{
			if (_consultation != null && IsInstanceValid(_consultation))
				_consultation.Fermer();

			// Onglets VOIX : chacun met la sim en PAUSE (on lit en pause, A2).
			var onglets = new List<ConsultationPanel.Onglet>
			{
				OngletVoix("Carnet",       new CarnetPanel()),
				OngletVoix("Encyclopédie", new EncyclopediePanel()),
				OngletVoix("Magazine",     new MagazinePanel()),
				OngletVoix("Pages",        new PagesPanel()),
				OngletVoix("Courrier",     new CourrierPanel()),
				OngletVoix("Atelier",      new AtelierPanel()),
			};

			// Onglet AUTOMATE dev-gated (A6) : présent uniquement s'il a été branché
			// (touche A). Il NE met PAS en pause (on regarde la sim jouer, A2). On le
			// « seed » avec le dernier bloc connu pour éviter un onglet vide à l'ouverture.
			if (_automateOn)
			{
				_automateContent = new AutomateContent();
				_automateContent.Construire();
				if (_automateBlock != null) _automateContent.Rendre(_automateBlock);
				onglets.Add(new ConsultationPanel.Onglet("Automate", _automateContent, false));
			}

			_consultation = new ConsultationPanel();
			AddChild(_consultation);
			_consultation.Ouvrir(onglets, IndexOnglet(onglets, ongletInitial),
				onFerme: () => { _consultation = null; _automateContent = null; });

			GD.Print($"[WorldView] consultation ouverte (onglet {ongletInitial}).");
		}

		// Construit un onglet VOIX : injecte le pont, bâtit le contenu (Remplir lit
		// via Bridge), et le marque « met en pause ».
		private ConsultationPanel.Onglet OngletVoix(string nom, VoicePanel contenu)
		{
			contenu.InjecterPont(_bridge);
			contenu.Construire();
			return new ConsultationPanel.Onglet(nom, contenu, MetEnPause: true);
		}

		// Index de l'onglet nommé (défaut 0 = Carnet si introuvable).
		private static int IndexOnglet(List<ConsultationPanel.Onglet> onglets, string nom)
		{
			for (int i = 0; i < onglets.Count; i++)
				if (onglets[i].Nom == nom) return i;
			return 0;
		}
	}
}
