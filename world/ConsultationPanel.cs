// SYMBIOSE — ConsultationPanel.cs (sprint fenêtrage UI, T3 — Volet B)
// Le CONTENEUR À ONGLETS de consultation in-game (décisions A2/A4/A6/A8). Une
// seule fenêtre, ancrée au TIERS DROIT (emplacement de l'ancien panneau automate,
// D59 absorbée), réunit toutes les surfaces d'information : Carnet · Encyclopédie ·
// Magazine · Pages · Atelier, plus l'onglet Automate DEV-GATED. Remplace l'ancien
// « menu hub » intermédiaire : clic maison → cette fenêtre directement.
//
// Ce conteneur est AGNOSTIQUE du contenu : on lui passe une liste d'onglets
// {nom, Control, met-en-pause}. Il pose le chrome (voile, cadre, bouton fermer),
// gère la PAUSE PAR ONGLET (A2) et restaure l'état de pause d'avant ouverture à
// la fermeture. Il ne connaît ni les voix, ni l'automate — juste des Control.
//
// 📖 Pédagogie Godot/C# :
//  - TabContainer : un Control dont chaque enfant `Control` direct devient une
//    PAGE, son `Name` servant de libellé d'onglet. Il masque/affiche les pages
//    (jamais de reconstruction) → parfait pour garder les contenus vivants (perf).
//  - PAUSE PAR ONGLET : un onglet « voix » gèle la sim (on lit en pause) ; l'onglet
//    Automate la laisse tourner (on le regarde jouer). On lit le flag « met en
//    pause » de l'onglet actif à chaque changement (`TabChanged`).
//  - VOILE : plein écran, il gèle ET assombrit le monde derrière une voix (capte
//    les clics pour qu'aucun geste ne parte par erreur). Sur l'onglet Automate,
//    on l'EFFACE : le monde reste visible et interactif (la sim joue).
//  - ProcessMode = Always : la fenêtre et ses boutons restent vivants même quand
//    l'arbre est en pause (sinon « Fermer » gèlerait). Exception UI standard.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class ConsultationPanel : CanvasLayer
	{
		/// <summary>Un onglet à afficher : libellé, contenu, et s'il met la sim en pause.</summary>
		public readonly record struct Onglet(string Nom, Control Contenu, bool MetEnPause);

		// État de pause de l'arbre AVANT ouverture — restauré à la fermeture (on ne
		// « dépause » pas aveuglément : le monde pouvait déjà être figé).
		private bool _pauseAvant;

		private TabContainer _tabs;
		private ColorRect _voile;
		private System.Action _onFerme;

		// Flag « met en pause » par index d'onglet (parallèle aux pages du TabContainer).
		private readonly List<bool> _pauseParOnglet = new();

		/// <summary>Index de l'onglet actif (−1 si non ouvert).</summary>
		public int OngletActif => _tabs?.CurrentTab ?? -1;

		/// <summary>
		/// Construit le chrome (voile, cadre à droite, bouton fermer) et empile les
		/// onglets. Mémorise l'état de pause puis applique celui de l'onglet initial.
		/// `onFerme` (optionnel) est rappelé à la fermeture.
		/// </summary>
		public void Ouvrir(IList<Onglet> onglets, int ongletInitial, System.Action onFerme = null)
		{
			_onFerme = onFerme;
			Layer = 10;                 // au-dessus du HUD et du monde
			ProcessMode = Node.ProcessModeEnum.Always;

			_pauseAvant = GetTree().Paused;

			// Voile plein écran : capte les clics et assombrit le décor sur une voix.
			_voile = new ColorRect
			{
				Color = new Color(0f, 0f, 0f, 0.55f),
				MouseFilter = Control.MouseFilterEnum.Stop,
			};
			_voile.SetAnchorsPreset(Control.LayoutPreset.FullRect);
			AddChild(_voile);

			// Cadre ancré au tiers droit (aligné sur l'ancienne zone automate).
			var panneau = new PanelContainer
			{
				Position = new Vector2(1142f, 100f),
				CustomMinimumSize = new Vector2(772f, 872f),
			};
			AddChild(panneau);

			var vbox = new VBoxContainer();
			panneau.AddChild(vbox);

			// En-tête : bouton « Fermer » à droite (les onglets tiennent lieu de titre).
			var entete = new HBoxContainer();
			vbox.AddChild(entete);
			entete.AddChild(new Control { SizeFlagsHorizontal = Control.SizeFlags.ExpandFill });
			var fermer = new Button { Text = "Fermer  ✕" };
			fermer.Pressed += Fermer;
			entete.AddChild(fermer);

			_tabs = new TabContainer
			{
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
				SizeFlagsVertical = Control.SizeFlags.ExpandFill,
				CustomMinimumSize = new Vector2(752f, 812f),
			};
			vbox.AddChild(_tabs);

			foreach (var o in onglets)
			{
				o.Contenu.Name = o.Nom;      // le Name = libellé de l'onglet
				_tabs.AddChild(o.Contenu);
				_pauseParOnglet.Add(o.MetEnPause);
			}

			_tabs.TabChanged += OnTabChanged;
			_tabs.CurrentTab = Mathf.Clamp(ongletInitial, 0, onglets.Count - 1);
			AppliquerEtat(_tabs.CurrentTab);

			GD.Print($"[ConsultationPanel] ouvert ({onglets.Count} onglets, "
				+ $"onglet {_tabs.CurrentTab}).");
		}

		// Changement d'onglet → (dé)pause + voile selon le nouvel onglet actif.
		private void OnTabChanged(long idx) => AppliquerEtat((int)idx);

		// Applique l'état lié à l'onglet `idx` : pause de la sim + présence du voile.
		// Onglet voix → sim en pause + voile (lecture) ; onglet Automate → sim qui
		// tourne + pas de voile (monde visible et vivant).
		private void AppliquerEtat(int idx)
		{
			bool pause = _pauseParOnglet[idx];
			GetTree().Paused = pause;
			_voile.Visible = pause;
			_voile.MouseFilter = pause
				? Control.MouseFilterEnum.Stop : Control.MouseFilterEnum.Ignore;
		}

		/// <summary>Ferme la fenêtre et restaure l'état de pause d'avant ouverture.</summary>
		public void Fermer()
		{
			GetTree().Paused = _pauseAvant;
			_onFerme?.Invoke();
			GD.Print("[ConsultationPanel] fermé (état de pause restauré).");
			QueueFree();
		}
	}
}
