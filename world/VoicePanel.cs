// SYMBIOSE — VoicePanel.cs
// Panneau de CONSULTATION des voix narratives (sprint UI voix, tronçon ②).
// Ossature RÉUTILISABLE : un CanvasLayer plein écran (titre + zone défilante +
// bouton fermer) que les tronçons ③④ spécialisent (Carnet / Encyclopédie /
// Pages / Magazine). Ce tronçon ne remplit RIEN — les panneaux s'ouvrent vides
// (« à venir »). Le contenu verbatim viendra du pont Python en ③④.
//
// 📖 Pédagogie Godot/C# (Nico apprend le frontend) :
//  - CanvasLayer : couche d'UI en coordonnées ÉCRAN, au-dessus du monde 2D
//    (indifférente à la caméra/zoom). Le bon parent pour un panneau plein écran.
//  - PAUSE-AWARE : consulter un carnet arrête le temps (cohérent boucle hybride
//    « on lit la partie en pause »). On mémorise l'état de pause de l'arbre à
//    l'ouverture et on le RESTAURE à la fermeture — jamais on ne suppose l'état.
//  - ProcessMode = Always : le panneau et ses boutons doivent rester VIVANTS
//    même quand l'arbre est en pause (sinon le bouton « Fermer » gèlerait avec
//    le reste). C'est l'exception standard pour l'UI de pause.
//  - QueueFree() : libère le nœud en fin de frame — le panneau fermé ne capte
//    plus le moindre clic.
//
// INVARIANT « Godot bête » (§1) : ce nœud ne FABRIQUE aucun texte de voix. Il
// pose une mise en page vide ; le corpus verbatim arrivera par SimBridge en ③④.

using Godot;

namespace Symbiose
{
	public partial class VoicePanel : CanvasLayer
	{
		// État de pause de l'arbre AVANT ouverture — restauré à la fermeture
		// (on ne « dépause » pas aveuglément : le monde pouvait déjà être figé).
		private bool _pauseAvant;

		// Zone de contenu défilante, exposée aux spécialisations ③④ (elles y
		// ajouteront leurs listes/fiches). Vide dans ce tronçon.
		protected VBoxContainer Contenu { get; private set; }

		// Rappelé à la fermeture (pour que le hub réactive la maison, etc.).
		private System.Action _onFerme;

		/// <summary>
		/// Construit l'ossature : fond assombri plein écran, titre, zone
		/// défilante vide, bouton « Fermer ». Met la simulation en PAUSE et
		/// mémorise l'état précédent. `onFerme` (optionnel) rappelé à la fermeture.
		/// </summary>
		public void Ouvrir(string titre, System.Action onFerme = null)
		{
			_onFerme = onFerme;
			Layer = 10;                 // au-dessus du HUD et du monde
			ProcessMode = Node.ProcessModeEnum.Always;

			// Pause du temps figé — mémorisée puis restaurée (cf. en-tête).
			_pauseAvant = GetTree().Paused;
			GetTree().Paused = true;

			// Voile plein écran : capte les clics derrière le panneau (le monde
			// ne réagit plus tant qu'on consulte) et assombrit le décor.
			var voile = new ColorRect
			{
				Color = new Color(0f, 0f, 0f, 0.55f),
				MouseFilter = Control.MouseFilterEnum.Stop,
			};
			voile.SetAnchorsPreset(Control.LayoutPreset.FullRect);
			AddChild(voile);

			// Panneau central (marge intérieure via PanelContainer).
			var panneau = new PanelContainer();
			panneau.SetAnchorsPreset(Control.LayoutPreset.Center);
			panneau.CustomMinimumSize = new Vector2(720, 560);
			AddChild(panneau);

			var vbox = new VBoxContainer();
			panneau.AddChild(vbox);

			// En-tête : titre à gauche, bouton fermer à droite.
			var entete = new HBoxContainer();
			vbox.AddChild(entete);

			var lblTitre = new Label
			{
				Text = titre,
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
			};
			lblTitre.AddThemeFontSizeOverride("font_size", 28);
			entete.AddChild(lblTitre);

			var fermer = new Button { Text = "Fermer  ✕" };
			fermer.Pressed += Fermer;
			entete.AddChild(fermer);

			// Zone défilante : les spécialisations ③④ peupleront `Contenu`.
			var scroll = new ScrollContainer
			{
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
				SizeFlagsVertical = Control.SizeFlags.ExpandFill,
				CustomMinimumSize = new Vector2(700, 480),
			};
			vbox.AddChild(scroll);

			Contenu = new VBoxContainer
			{
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
			};
			scroll.AddChild(Contenu);

			// Placeholder « à venir » — retiré par ③④ quand ils remplissent
			// `Contenu`. Marque clairement qu'aucun texte n'est encore branché.
			Contenu.AddChild(new Label { Text = "(contenu à venir)" });

			GD.Print($"[VoicePanel] ouvert : « {titre} » (simulation en pause).");
		}

		/// <summary>Ferme le panneau et restaure l'état de pause précédent.</summary>
		public void Fermer()
		{
			GetTree().Paused = _pauseAvant;
			_onFerme?.Invoke();
			GD.Print("[VoicePanel] fermé (état de pause restauré).");
			QueueFree();
		}
	}
}
