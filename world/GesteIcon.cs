// SYMBIOSE — GesteIcon.cs (palette de gestes ④, D11)
// UN pictogramme MUET par geste (philo #5 : pas de texte en HUD primaire). Icône
// PROCÉDURALE — zéro asset à produire, comme les placeholders tuiles/maison de
// WorldView : chaque geste dessine une petite forme reconnaissable par famille
// (goutte = arroser, ciseaux = tailler, main = planter, tas = compost…). Le
// libellé n'apparaît qu'au SURVOL (TooltipText natif), jamais dessiné à l'écran.
//
// 📖 Pédagogie Godot/C# :
//  - On hérite de Button (pas de Control nu) pour récupérer GRATUITEMENT le clic,
//    le focus visuel, le survol/tooltip et l'état pressé — la palette n'a qu'à
//    brancher le signal Pressed. On masque le fond/texte par défaut du bouton
//    (Flat + thème transparent) et on DESSINE nous-mêmes le pictogramme dans
//    _Draw (QueueRedraw quand l'état Actif/Verrouillé change).
//  - `Actif` (le geste courant) → cadre lumineux ; `Verrouille` → grisé/estompé
//    (calibrage F5 : masquer OU griser — ici on grise, plus pédagogique).
//
// ICÔNES & CURSEUR ① : quand le geste possède une GRILLE dans `IconeGeste`
// (visuals/IconeGeste.cs), `_Draw` pose sa texture cuite — 16×16 logiques à ×2 =
// 32 px, centrés dans la case de 44 px. Sinon l'ancien pictogramme procédural
// (GesteIcon.Repli.cs) sert de repli, le temps que toutes les icônes existent.

using Godot;

namespace Symbiose
{
	public partial class GesteIcon : Button
	{
		public const int Taille = 44;      // côté du bouton (px écran)
		private const float Marge = 9f;    // marge intérieure du pictogramme
		// Icône cuite : ×2 est le plus grand multiple ENTIER de 16 px qui tient
		// dans la case (×3 = 48 px déborderait des 44 px).
		private const int EchelleIcone = 2;
		// Assombrissement d'un geste pressenti (plaque + ancien pictogramme).
		private static readonly Color TeintePressenti = new(0.42f, 0.46f, 0.50f);

		public string Verb { get; private set; }
		private char _kind;
		private bool _actif;
		private bool _verrouille;
		private bool _pressenti;

		// Callback d'ÉDITION (T1) : le clic DROIT sur un slot ouvre le menu
		// assigner/vider (branché par la palette, cf. WorldView.Palette.cs). On
		// passe par une Action C# plutôt qu'un signal Godot : la palette capture
		// déjà l'index de slot dans son lambda, rien à transporter.
		public System.Action OnRightClick;

		public bool Actif
		{
			get => _actif;
			set { if (_actif == value) return; _actif = value; QueueRedraw(); }
		}

		public bool Verrouille
		{
			get => _verrouille;
			set
			{
				if (_verrouille == value) return;
				_verrouille = value;
				// Un geste verrouillé reste VISIBLE mais inerte (aucun signal) et
				// estompé — le joueur devine qu'il existe sans pouvoir l'employer.
				Disabled = value;
				QueueRedraw();
			}
		}

		/// <summary>Geste PRESSENTI (palette & tiroir ③) : le joueur en a entrevu
		/// l'existence sans pouvoir l'employer. Une silhouette d'une seule teinte
		/// sombre, inerte ; au survol, la PHRASE d'ambiance du pont et rien d'autre
		/// (ni nom du geste, ni condition — philo #6). À appeler après Init.</summary>
		public void MarquerPressenti(string phrase)
		{
			_pressenti = true;
			Disabled = true;               // un Button désactivé n'émet plus `Pressed`
			// SelfModulate multiplie TOUT ce que ce nœud dessine : certains glyphes ont
			// leurs couleurs propres (une tige verte…), les assombrir d'un bloc donne
			// une vraie silhouette, d'une seule valeur.
			// Un geste à icône cuite a sa propre texture de silhouette, déjà dans sa
			// teinte finale : on ne l'assombrit pas une seconde fois (_Draw n'éteint
			// alors que la plaque).
			if (!IconeGeste.Existe(Verb)) SelfModulate = TeintePressenti;
			TooltipText = phrase;          // … mais garde son info-bulle
			QueueRedraw();
		}

		public void Init(string verb, string nom, char kind)
		{
			Verb = verb;
			_kind = kind;
			TooltipText = nom;             // libellé au survol seulement (philo #5)
			Flat = true;                   // pas de skin de bouton : on peint tout
			CustomMinimumSize = new Vector2(Taille, Taille);
			FocusMode = FocusModeEnum.None;
			// Rend le fond natif transparent : notre _Draw fournit tout le visuel.
			AddThemeStyleboxOverride("normal", new StyleBoxEmpty());
			AddThemeStyleboxOverride("hover", new StyleBoxEmpty());
			AddThemeStyleboxOverride("pressed", new StyleBoxEmpty());
			AddThemeStyleboxOverride("disabled", new StyleBoxEmpty());
			AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
		}

		// Le clic DROIT n'est pas un « appui » de Button (Pressed = gauche) : on
		// l'intercepte ici et on délègue à la palette (édition du slot). Les autres
		// événements repartent au Button (base) pour garder le clic gauche/survol.
		public override void _GuiInput(InputEvent ev)
		{
			if (ev is InputEventMouseButton mb && mb.Pressed
				&& mb.ButtonIndex == MouseButton.Right)
			{
				OnRightClick?.Invoke();
				AcceptEvent();
				return;
			}
			base._GuiInput(ev);
		}

		public override void _Draw()
		{
			var rect = new Rect2(0f, 0f, Taille, Taille);
			// Plaque de fond : sombre au repos, éclaircie si c'est le geste actif.
			Color fond = _actif ? new Color(0.30f, 0.42f, 0.30f, 0.95f)
								 : new Color(0.14f, 0.16f, 0.18f, 0.85f);
			ImageTexture icone = IconeGeste.Texture(Verb, EchelleIcone, silhouette: _pressenti);
			if (icone != null && _pressenti) fond *= TeintePressenti;
			DrawRect(rect, fond, filled: true);
			if (_actif)   // cadre lumineux autour du geste sélectionné
				DrawRect(rect, new Color(0.7f, 1f, 0.7f), filled: false, width: 2f);

			// Icône cuite (texture en cache, rien n'est recalculé ici) : centrée,
			// estompée si le geste est verrouillé. Sinon → ancien dessin, ci-dessous.
			if (icone != null)
			{
				float bord = (Taille - IconeGeste.Cote * EchelleIcone) / 2f;
				DrawTexture(icone, new Vector2(bord, bord),
							_verrouille ? new Color(0.5f, 0.5f, 0.5f, 0.55f) : Colors.White);
				return;
			}

			// Le pictogramme, dans la teinte de la famille — estompé si verrouillé.
			Color c = CouleurFamille(_verrouille ? '·' : PictoKind());
			if (_verrouille) c = c.Darkened(0.5f) with { A = 0.55f };
			// Pressenti : une seule teinte sombre, quelle que soit la famille.
			if (_pressenti) c = new Color(0.75f, 0.75f, 0.75f);   // gris, assombri par SelfModulate
			DessinerPicto(PictoKind(), c);
		}
	}
}
