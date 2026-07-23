// SYMBIOSE — VoicePanel.cs (refactor sprint fenêtrage UI, T3)
// Base des CONTENUS de voix (Carnet / Encyclopédie / Magazine / Pages / Atelier).
// Depuis T3, VoicePanel n'est PLUS un panneau autonome (CanvasLayer + voile +
// pause) : c'est un CONTENU D'ONGLET défilable. Le chrome (voile, cadre, bouton
// fermer, gestion de pause, emplacement) a été REMONTÉ dans `ConsultationPanel`,
// qui héberge tous ces contenus dans un `TabContainer`. Une seule fenêtre à
// onglets réunit désormais toutes les voix (Volet B, décisions A2/A4/A6/A8).
//
// 📖 Pédagogie Godot/C# (Nico apprend le frontend) :
//  - ScrollContainer : un cadre qui laisse défiler son unique enfant quand il
//    déborde en hauteur. En devenant nous-mêmes un ScrollContainer, chaque
//    contenu d'onglet défile tout seul (règle transversale du sprint « toute
//    fenêtre défile si débordement »), sans envelopper à la main.
//  - Une page de `TabContainer` = un enfant `Control` direct ; son `Name` sert de
//    LIBELLÉ d'onglet. Le conteneur (ConsultationPanel) nomme chaque contenu.
//  - `Construire()` est appelé par le conteneur APRÈS `InjecterPont` : les
//    spécialisations lisent leur voix (via `Bridge`) dès le peuplement. Le contenu
//    est bâti UNE FOIS ; le TabContainer masque/affiche, jamais ne reconstruit.
//
// INVARIANT « Godot bête » (§1) : ce nœud ne FABRIQUE aucun texte de voix. Il pose
// une mise en page ; le corpus verbatim arrive par SimBridge dans les
// spécialisations. Inchangé par le refactor : elles n'utilisent que `Contenu`,
// `Bridge`, `Remplir()` et `InjecterPont` — tous préservés à l'identique.

using Godot;

namespace Symbiose
{
	public partial class VoicePanel : ScrollContainer
	{
		// Zone de contenu défilante, exposée aux spécialisations (elles y ajoutent
		// leurs listes/fiches). Vide dans le contenu de base.
		protected VBoxContainer Contenu { get; private set; }

		// Pont vers le moteur Python, injecté par le conteneur AVANT `Construire`.
		// Les spécialisations lisent leurs voix par ce pont (read-only) et se
		// contentent de mettre en page — INVARIANT « Godot bête ».
		protected SimBridge Bridge { get; set; }

		/// <summary>
		/// Injecte le pont Python AVANT `Construire` (le conteneur le fournit).
		/// </summary>
		public void InjecterPont(SimBridge bridge) => Bridge = bridge;

		/// <summary>
		/// Construit la zone défilante puis la peuple via `Remplir()`. Appelé par
		/// le conteneur (ConsultationPanel) une fois le pont injecté. Bâti UNE fois.
		/// </summary>
		public void Construire()
		{
			SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
			SizeFlagsVertical = Control.SizeFlags.ExpandFill;
			// Nos listes débordent en hauteur, jamais en largeur : on coupe le
			// défilement horizontal (barre parasite qui gênerait la lecture).
			HorizontalScrollMode = ScrollMode.Disabled;

			Contenu = new VBoxContainer
			{
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
			};
			AddChild(Contenu);

			// Point d'extension : une spécialisation peuple `Contenu` en surchargeant
			// Remplir(). Le contenu de base pose un placeholder « à venir ».
			Remplir();
		}

		/// <summary>
		/// Peuplement de `Contenu`, appelé en fin de `Construire`. Le contenu de
		/// base pose un placeholder ; les spécialisations (Carnet, Encyclopédie…) le
		/// surchargent pour afficher le texte VERBATIM lu via `Bridge`. Aucun texte
		/// de voix n'est fabriqué ici — mise en page seulement.
		/// </summary>
		protected virtual void Remplir()
		{
			Contenu.AddChild(new Label { Text = "(contenu à venir)" });
		}
	}
}
