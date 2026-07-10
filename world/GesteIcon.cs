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

using Godot;

namespace Symbiose
{
	public partial class GesteIcon : Button
	{
		public const int Taille = 44;      // côté du bouton (px écran)
		private const float Marge = 9f;    // marge intérieure du pictogramme

		public string Verb { get; private set; }
		private char _kind;
		private bool _actif;
		private bool _verrouille;

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

		public override void _Draw()
		{
			var rect = new Rect2(0f, 0f, Taille, Taille);
			// Plaque de fond : sombre au repos, éclaircie si c'est le geste actif.
			Color fond = _actif ? new Color(0.30f, 0.42f, 0.30f, 0.95f)
								 : new Color(0.14f, 0.16f, 0.18f, 0.85f);
			DrawRect(rect, fond, filled: true);
			if (_actif)   // cadre lumineux autour du geste sélectionné
				DrawRect(rect, new Color(0.7f, 1f, 0.7f), filled: false, width: 2f);

			// Le pictogramme, dans la teinte de la famille — estompé si verrouillé.
			Color c = CouleurFamille(_verrouille ? '·' : PictoKind());
			if (_verrouille) c = c.Darkened(0.5f) with { A = 0.55f };
			DessinerPicto(PictoKind(), c);
		}

		// La famille de pictogramme : privilégie le VERBE (glyphe spécifique) puis
		// retombe sur le Kind de cible. Un caractère-clé pilote forme ET couleur.
		private char PictoKind() => Verb switch
		{
			"arroser" => 'o',            // goutte (bleu)
			"planter" or "planter_conteneur" => 'n',   // graine/pousse (vert)
			"tailler" => 'i',            // ciseaux (gris)
			"recolter" or "manger" => 'f',   // fruit/récolte (rouge)
			"ecraser" => 'x',            // croix (rouge sombre)
			"becher" => 'a',             // fourche/ameublir (brun)
			"pailler" => 'u',            // trait de mulch (paille)
			"bouturer" => 'b',           // tige piquée (vert clair)
			"greffer" => 'g',            // jonction en T (vert-brun)
			"favoriser_auxiliaire" => 'w',   // insecte (jaune)
			"broyer" => 'd',             // éclats de bois (brun)
			"composter" or "empiler_bois" or "retourner" or "epandre"
				or "poser_bac" or "poser_pile" => 't',   // tas (brun compost)
			"poser_pot" or "poser_bac_culture" or "deplacer_pot" => 'p',   // pot (terracotta)
			"poser_tuteur" or "poser_treillis" or "poser_pergola" or "palisser"
				=> 's',                  // support (gris clair)
			"poser_ruche" or "recolter_miel" => 'h',   // ruche (miel)
			"deraciner" => 'r',          // racine arrachée (brun)
			_ => _kind,                  // repli par famille de cible
		};

		// Couleur par famille de pictogramme — cohérence visuelle à l'écran.
		private static Color CouleurFamille(char k) => k switch
		{
			'o' => new Color(0.45f, 0.75f, 1f),      // eau
			'n' => new Color(0.5f, 0.85f, 0.4f),     // planter
			'i' => new Color(0.8f, 0.82f, 0.85f),    // taille
			'f' => new Color(0.9f, 0.4f, 0.4f),      // récolte/manger
			'x' => new Color(0.85f, 0.3f, 0.3f),     // écraser
			'a' => new Color(0.7f, 0.55f, 0.35f),    // ameublir
			'u' => new Color(0.85f, 0.75f, 0.45f),   // paillage
			'b' => new Color(0.6f, 0.9f, 0.55f),     // bouture
			'g' => new Color(0.65f, 0.8f, 0.4f),     // greffe
			'w' => new Color(0.95f, 0.85f, 0.35f),   // auxiliaire
			'd' => new Color(0.65f, 0.5f, 0.3f),     // broyer
			't' => new Color(0.55f, 0.42f, 0.28f),   // compost/tas
			'p' => new Color(0.8f, 0.45f, 0.3f),     // pot
			's' => new Color(0.75f, 0.75f, 0.78f),   // support
			'h' => new Color(0.95f, 0.75f, 0.3f),    // ruche
			'r' => new Color(0.6f, 0.45f, 0.35f),    // déraciner
			_ => new Color(0.7f, 0.7f, 0.7f),        // neutre
		};

		// Un pictogramme MINIMAL par famille : formes primitives suffisantes à
		// distinguer les gestes d'un coup d'œil (calibrage F5 : sprites dédiés plus
		// tard). Le cadre utile est [Marge, Taille-Marge] pour laisser respirer.
		private void DessinerPicto(char k, Color c)
		{
			float lo = Marge, hi = Taille - Marge, mid = Taille / 2f;
			switch (k)
			{
				case 'o':   // goutte : triangle + arc bas
					DrawColoredPolygon(new[]
					{
						new Vector2(mid, lo), new Vector2(hi, hi), new Vector2(lo, hi),
					}, c);
					DrawCircle(new Vector2(mid, hi - 3f), 6f, c);
					break;
				case 'n':   // pousse : tige verticale + 2 feuilles
					DrawLine(new Vector2(mid, hi), new Vector2(mid, lo + 4f), c, 3f);
					DrawCircle(new Vector2(mid - 6f, mid), 5f, c);
					DrawCircle(new Vector2(mid + 6f, mid - 4f), 5f, c);
					break;
				case 'i':   // ciseaux : deux lames en X + anneaux
					DrawLine(new Vector2(lo, lo), new Vector2(hi, hi), c, 2.5f);
					DrawLine(new Vector2(hi, lo), new Vector2(lo, hi), c, 2.5f);
					DrawCircle(new Vector2(lo + 3f, hi - 3f), 4f, c);
					DrawCircle(new Vector2(hi - 3f, hi - 3f), 4f, c);
					break;
				case 'f':   // fruit : disque + petite queue
					DrawCircle(new Vector2(mid, mid + 3f), (hi - lo) / 2.6f, c);
					DrawLine(new Vector2(mid, lo + 2f), new Vector2(mid + 4f, lo - 2f), c, 2f);
					break;
				case 'x':   // écraser : grosse croix
					DrawLine(new Vector2(lo, lo), new Vector2(hi, hi), c, 4f);
					DrawLine(new Vector2(hi, lo), new Vector2(lo, hi), c, 4f);
					break;
				case 'a':   // ameublir : fourche à 3 dents
					DrawLine(new Vector2(mid, lo), new Vector2(mid, mid), c, 3f);
					for (int i = 0; i < 3; i++)
					{
						float x = lo + i * (hi - lo) / 2f;
						DrawLine(new Vector2(x, mid), new Vector2(x, hi), c, 2.5f);
					}
					DrawLine(new Vector2(lo, mid), new Vector2(hi, mid), c, 2.5f);
					break;
				case 'u':   // paillage : trois traits horizontaux
					for (int i = 0; i < 3; i++)
					{
						float y = lo + 4f + i * 7f;
						DrawLine(new Vector2(lo, y), new Vector2(hi, y), c, 3f);
					}
					break;
				case 'b':   // bouture : tige oblique piquée dans un trait de sol
					DrawLine(new Vector2(lo + 4f, hi), new Vector2(hi - 6f, lo + 4f), c, 3f);
					DrawLine(new Vector2(lo, hi), new Vector2(hi, hi), c, 2f);
					DrawCircle(new Vector2(hi - 6f, lo + 4f), 4f, c);
					break;
				case 'g':   // greffe : jonction en T (scion sur porte-greffe)
					DrawLine(new Vector2(mid, hi), new Vector2(mid, mid), c, 4f);
					DrawLine(new Vector2(mid, mid), new Vector2(hi - 4f, lo + 4f), c, 3f);
					DrawLine(new Vector2(lo + 3f, mid - 2f), new Vector2(hi - 3f, mid - 2f), c, 1.5f);
					break;
				case 'w':   // auxiliaire : corps + 2 antennes (insecte)
					DrawCircle(new Vector2(mid, mid + 2f), 6f, c);
					DrawLine(new Vector2(mid - 3f, mid - 3f), new Vector2(mid - 7f, lo), c, 2f);
					DrawLine(new Vector2(mid + 3f, mid - 3f), new Vector2(mid + 7f, lo), c, 2f);
					break;
				case 'd':   // broyer : éclats (traits éparpillés)
					DrawLine(new Vector2(lo, mid), new Vector2(mid, lo + 3f), c, 2.5f);
					DrawLine(new Vector2(mid, hi - 3f), new Vector2(hi, mid), c, 2.5f);
					DrawLine(new Vector2(lo + 4f, hi - 4f), new Vector2(hi - 4f, lo + 4f), c, 2f);
					break;
				case 't':   // tas : triangle plein (compost)
					DrawColoredPolygon(new[]
					{
						new Vector2(mid, lo + 2f), new Vector2(hi, hi), new Vector2(lo, hi),
					}, c);
					break;
				case 'p':   // pot : trapèze (large en haut)
					DrawColoredPolygon(new[]
					{
						new Vector2(lo, mid - 4f), new Vector2(hi, mid - 4f),
						new Vector2(hi - 5f, hi), new Vector2(lo + 5f, hi),
					}, c);
					break;
				case 's':   // support : treillis (croix quadrillée)
					DrawLine(new Vector2(mid - 6f, lo), new Vector2(mid - 6f, hi), c, 2f);
					DrawLine(new Vector2(mid + 6f, lo), new Vector2(mid + 6f, hi), c, 2f);
					DrawLine(new Vector2(lo, mid - 6f), new Vector2(hi, mid - 6f), c, 2f);
					DrawLine(new Vector2(lo, mid + 6f), new Vector2(hi, mid + 6f), c, 2f);
					break;
				case 'h':   // ruche : deux arcs empilés
					DrawArc(new Vector2(mid, mid + 4f), 10f, Mathf.Pi, Mathf.Tau, 20, c, 3f);
					DrawArc(new Vector2(mid, hi), 12f, Mathf.Pi, Mathf.Tau, 20, c, 3f);
					break;
				case 'r':   // déraciner : Y renversé (racines arrachées)
					DrawLine(new Vector2(mid, lo), new Vector2(mid, mid), c, 3f);
					DrawLine(new Vector2(mid, mid), new Vector2(lo, hi), c, 2.5f);
					DrawLine(new Vector2(mid, mid), new Vector2(hi, hi), c, 2.5f);
					break;
				default:    // repli : pastille pleine (le geste existe, forme neutre)
					DrawCircle(new Vector2(mid, mid), (hi - lo) / 3f, c);
					break;
			}
		}
	}
}
