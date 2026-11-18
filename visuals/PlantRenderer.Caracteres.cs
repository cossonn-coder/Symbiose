// SYMBIOSE — PlantRenderer.Caracteres.cs (partial de PlantRenderer, D139 caractères
// vivants ⑤ ⑥). Ce que la plante montre de ses CARACTÈRES HÉRITABLES (conception §4).
//
// ⑤ : la lignée vécue de l'année (fécondation, pollen donné, part autofécondée), relue
// par le survol G (WorldView.Genes.cs).
// ⑥ : les signes dessinés, lus dans `signes_car`, `rejets`, `sans_graines` (pont 0.6.20) :
//   · teinte des pétales sur l'axe de couleur de l'espèce, en DÉGRADÉ d'un pied à l'autre ;
//   · taille des fleurs (tête × √taille_fleur) ;
//   · guides à nectar : œil central plus sombre, puis lignes, selon le contraste ;
//   · feuille plus mate et plus sombre, ou plus luisante (coriacité) ;
//   · port en flèche (étroit) ou en buisson (large) (dominance apicale) ;
//   · rejets au pied d'une colonie mûre (vigueur clonale) ;
//   · têtes brunes et rabougries quand les fleurs ont fané SANS GRAINES.
// La taille des fruits n'est pas ici : la masse du pont la porte déjà (SignesCaracteres.cs).
//
// 📖 Pourquoi QUANTIFIER la teinte. Chaque teinte distincte coûte une palette indexée
// (PaletteIndexee : une rampe de 5 tons par couleur de base) et une cuisson à part. On
// arrondit la teinte à 10°, la saturation à 0,1, la matité au 1/8 : un nuancier fini de
// variantes précuites, et un dégradé encore visible d'une bourrache à l'autre.
//
// 📖 Pourquoi croiser « sans graines » avec la saison. Le moteur garde la fécondation
// posée jusqu'à la récolte d'automne : un trèfle qui fane après (s41) porterait le signe
// jusqu'à l'automne suivant. La vue ne le montre donc que si CE pied a été vu en fleur
// depuis le dernier hiver, et qu'il n'est plus en fleur : un loquet remis à zéro l'hiver.
//
// Vue pure, zéro Random (variations au hash), golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		/// <summary>Lignée vécue (pont 0.6.20) : [fécondation, pollen donné, part
		/// autofécondée ∈ [0,1]] ; null si absente (ancien serveur, plante morte).</summary>
		public float[] FecondationVecue { get; set; }

		// Nuancier [choix] : pas de teinte, de saturation, et part de saturation montrée (la
		// saturation 1 du moteur est un bleu pur, trop cru à côté des teintes d'espèce).
		private const float PasTeinteDeg = 10f, PasSaturation = 0.1f, SaturationVue = 0.75f;
		// Valeur d'une fleur blanche (saturation 0) : le blanc chaux de la palette maître.
		private const float ValeurBlanc = 0.95f;
		private const float PasMatite = 0.125f, AssombriParPas = 0.07f, EclairciParPas = 0.05f;
		// Port : rayon dessiné × (1 − PortEcart × port) ; ±1 → ×0,6 (flèche) … ×1,4 (buisson).
		private const float PortEcart = 0.4f;
		private const int RejetsMax = 5;
		// Tête fanée sans graines : terre 2 de la palette maître, rabougrie.
		private static readonly Color TeinteFanee = Palette16.Maitre[10];
		private const float EchelleFanee = 0.7f;

		private readonly record struct CleSignes(bool Fleur, int Teinte, int Sat, int Echelle, int Guides, int Matite, int Port);
		private CleSignes _cleSignes;
		private bool _aPalIndividu;
		private OrganPalette _palIndividu;
		private float _echelleFleur = 1f, _contrasteGuides = 0.5f, _portCar;
		private int _rejetsN;
		private bool _fleuriVu, _signeFane;

		/// <summary>Pose les signes des caractères ; recuit seulement si ce qui se voit change.
		/// À appeler APRÈS SetStructure (la floraison et l'espèce sont lues ici).</summary>
		public void SetCaracteres(SignesCaracteres s, float rejets, bool sansGraines)
		{
			bool sale = false;
			if (s != null && _structure != null)
			{
				var cle = new CleSignes(s.AFleur, Mathf.RoundToInt(s.TeinteDeg / PasTeinteDeg) % 36,
					Mathf.RoundToInt(s.Saturation / PasSaturation), Mathf.RoundToInt(s.EchelleFleur * 20f),
					Mathf.RoundToInt(s.ContrasteGuides * 10f), Mathf.RoundToInt((s.MatiteFeuille - 0.5f) / PasMatite),
					Mathf.RoundToInt(s.Port * 10f));
				if (!_aPalIndividu || cle != _cleSignes)
				{
					_cleSignes = cle;
					_palIndividu = PaletteDe(cle);
					_aPalIndividu = true;
					_echelleFleur = cle.Echelle / 20f;
					_contrasteGuides = cle.Guides / 10f;
					_portCar = cle.Port / 10f;
					RemesurerPort();
					sale = true;
				}
			}
			int n = Mathf.RoundToInt(Mathf.Clamp(rejets, 0f, 1f) * RejetsMax);
			if (n != _rejetsN) { _rejetsN = n; sale = true; }
			if (_structure != null)
			{
				if (WorldView.CurrentSeason == "hiver") _fleuriVu = false;
				else if (_structure.Floraison >= FloraisonSeuil) _fleuriVu = true;
			}
			bool fane = sansGraines && _fleuriVu && _structure != null && _structure.Floraison < FloraisonSeuil;
			if (fane != _signeFane) { _signeFane = fane; sale = true; }
			if (sale) Invalidate();
		}

		// La palette de l'individu : celle de l'espèce, limbe mati et fleur sur son axe.
		private OrganPalette PaletteDe(in CleSignes cle)
		{
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			Color feuille = cle.Matite >= 0 ? pal.Leaf.Darkened(AssombriParPas * cle.Matite)
				: pal.Leaf.Lightened(EclairciParPas * -cle.Matite);
			Color fleur = pal.Flower;
			if (cle.Fleur)
			{
				float sat = Mathf.Clamp(cle.Sat * PasSaturation, 0f, 1f);
				fleur = Color.FromHsv(cle.Teinte * PasTeinteDeg / 360f, sat * SaturationVue,
					Mathf.Lerp(ValeurBlanc, pal.Flower.V, sat));
			}
			return pal.Individu(feuille, fleur);
		}

		/// <summary>La palette à dessiner : celle de CE pied (signes reçus), sinon de l'espèce.</summary>
		private OrganPalette PaletteIndividu()
		{
			if (_aPalIndividu) return _palIndividu;
			return Palettes.TryGetValue(_structure.SpeciesName, out var pal) ? pal : DefaultPalette;
		}

		// Le port a changé de largeur : la mesure (ombre, picking, boîte) suit sans attendre la
		// semaine suivante. Sans LisserHauteur : la hauteur ne doit avancer qu'une fois par snapshot.
		private void RemesurerPort()
		{
			if (FicheDeLaPlante is not { } f || _hauteurLisseeCm < 0f) return;
			(_rayonReelCm, _hauteurReelCm) = MesurePort(f);
			_spreadCm = _rayonReelCm;
			_heightCm = _hauteurReelCm;
		}

		/// <summary>Largeur du port : seuls la tige et le buisson ont une dominance qui se voit.</summary>
		private float FacteurPort(FichePort f) =>
			f.Forme is FormePort.Tige or FormePort.Buisson ? 1f - PortEcart * _portCar : 1f;

		/// <summary>Tête fanée sans graines (couleur et rayon), ou la tête telle quelle si elle
		/// est encore en fleur.</summary>
		private void Faner(ref Color c, ref float r, bool enFleur)
		{
			if (!_signeFane || enFleur) return;
			c = TeinteFanee;
			r *= EchelleFanee;
		}

		/// <summary>Guides à nectar sur une fleur ouverte, de près : œil central pâle (pas de
		/// guide), moyen, ou sombre bordé de lignes (fort contraste).</summary>
		private void PoserGuides(Vector2 c, float r, Color col, FormeTete forme)
		{
			if (forme is not (FormeTete.Etoile or FormeTete.Corolle or FormeTete.Soleil
				or FormeTete.Capitule or FormeTete.Trompette) || !AuPalier(PalierOrganesZoom)) return;
			float k = _contrasteGuides, pix = PixelInterne;
			int ton = k < 0.35f ? 3 : k < 0.65f ? 1 : 0;
			if (k >= 0.65f)
				for (int i = 0; i < 5; i++)
				{
					float a = i * Mathf.Tau / 5f - Mathf.Pi * 0.5f + Mathf.Pi / 5f;
					var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.8f);
					_lotPrairie.Ligne(c + dir * r * 0.3f, c + dir * r * Mathf.Lerp(0.55f, 0.85f, k), Ton(col, 0), pix);
				}
			PoserDisque(c, Mathf.Max(r * Mathf.Lerp(0.24f, 0.4f, k), pix), Ton(col, ton));
		}

		/// <summary>Rejets d'une colonie mûre : petites pousses au pied, sous le rayon du port.</summary>
		private void PoserRejets(FichePort f, Color col)
		{
			if (_rejetsN == 0 || MortPrairie || !AuPalier(PaliersHautsMinZoom)) return;
			var (rayon, _) = MesurePort(f);
			int ig = GraineIndividu;
			float pix = PixelInterne, haut = Mathf.Clamp(f.HautFeuillesCm * 0.25f, 3f, 12f);
			float large = Mathf.Max(pix, 0.6f * WorldView.PxPerCmX);
			for (int k = 0; k < _rejetsN; k++)
			{
				float a = Mathf.Tau * Hash01(611, ig, k), d = rayon * Mathf.Lerp(0.55f, 0.9f, Hash01(613, ig, k));
				float x = d * Mathf.Cos(a), y = d * Mathf.Sin(a);
				Vector2 pied = Iso(x, y, 0f);
				for (int b = 0; b < 3; b++)
				{
					float e = (b - 1) * haut * 0.35f, z = haut * Mathf.Lerp(0.6f, 1f, Hash01(617, ig, k * 3 + b));
					_lotPrairie.Ligne(pied, Iso(x + e * Mathf.Sin(a), y - e * Mathf.Cos(a), z),
						Ton(col, b == 1 ? 3 : PaletteIndexee.TonBase), large);
				}
			}
		}

		/// <summary>Recopie les signes vers le pinceau de cuisson (Bake.cs).</summary>
		private void CopierCaracteres(PlantRenderer brush)
		{
			brush._aPalIndividu = _aPalIndividu;
			brush._palIndividu = _palIndividu;
			brush._cleSignes = _cleSignes;
			brush._echelleFleur = _echelleFleur;
			brush._contrasteGuides = _contrasteGuides;
			brush._portCar = _portCar;
			brush._rejetsN = _rejetsN;
			brush._signeFane = _signeFane;
		}
	}
}
