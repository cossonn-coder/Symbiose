// SYMBIOSE — PlantRenderer.Prairie.cs (partial, sprint TRÈFLE DOMINANT ④, D126)
// La FORME de la prairie : trèfle, dactyle, fétuque, plantain. Ces quatre espèces ne
// passent plus par le chemin commun « segments + organes », qui en faisait des tiges
// isolées : le moteur fait pousser leurs segments en hauteur (un trèfle atteint ~40 cm
// de bois, pour une `height_cm` de 14), ce qui sert sa simulation mais ne ressemble pas
// à un couvre-sol. La vue garde ce que dit le moteur (espèce, hauteur, densité, floraison,
// santé, mort, quatre feuilles) et dessine un port authored, à TOUS les paliers.
//
// Ce fichier : la table des ports, le dispatch, le trèfle. Les trois autres espèces sont
// dans PlantRenderer.Graminees.cs. Zéro écologie, zéro Random : positions au hash de
// l'individu (GraineIndividu), donc stables d'une cuisson à l'autre (philo #3).
//
// 📖 Pédagogie (perf-first) : tout part en UN lot de triangles (LotTriangles) par plante.
// À l'affichage rien ne change : la plante reste un quad d'atlas cuit. À la cuisson, un
// seul envoi au lieu d'un DrawColoredPolygon par foliole. Le coût se paie côté CPU en
// sommets accumulés, pas en draw calls. Comme les couleurs posées passent par `Ton`, le
// pinceau écrit des CODES de palette et le shader éclaire la feuille selon le vrai soleil.
//
// 📖 Le TAPIS sort de la géométrie, sans couche neuve : un pied adulte couvre un disque
// (RayonTrefleCm) plus large que la distance entre ramets d'une colonie dense. Les disques
// se recouvrent, les quads se trient en Y comme toutes les plantes.
//
// Échelle cumulative conservée (conception_rendu_visible.md §4 D4) : santé dès ×2, fleurs
// dès ×2, feuille à folioles dès ×4, pétiole dès ×8, marque claire et nervure dès ×16.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private enum PortPrairie { Aucun, Trefle, Dactyle, Fetuque, Plantain }

		// Clé = nom de CLASSE Python, comme les autres tables d'espèces.
		private static readonly Dictionary<string, PortPrairie> PortsPrairie = new()
		{
			["Clover"] = PortPrairie.Trefle,
			["Dactyle"] = PortPrairie.Dactyle,
			["FetuqueRouge"] = PortPrairie.Fetuque,
			["PlantainLanceole"] = PortPrairie.Plantain,
		};

		private PortPrairie PortDeLaPlante =>
			_structure != null && PortsPrairie.TryGetValue(_structure.SpeciesName, out var p)
				? p : PortPrairie.Aucun;

		// Trèfle : rayon couvert par un pied adulte, feuilles au rayon plein.
		private const float RayonTrefleCm = 19f;
		// Couverture ~55 % du disque : c'est la SILHOUETTE d'une feuille isolée qui permet de
		// compter ses folioles (3 ou 4). Plus de feuilles, elles se recouvrent et le tapis
		// ne montre plus que des cœurs (essayé à 34 et 28, captures ×8). La sous-couche ferme le reste.
		private const int FeuillesTrefle = 22;
		// Hauteur des feuilles : 80 % de `height_cm`, plafonnée (tapis, pas buisson).
		private const float HauteurTrefleCm = 9f;
		private const float TailleFolioleCm = 3f;
		// `foliage_density` du trèfle : au-dessus, le feuillage est au complet.
		private const float DensitePleineTrefle = 0.4f;
		private const int PomponsMax = 5;
		private const float RayonPomponCm = 2.3f;
		// Plancher des feuilles d'un pied dormant ou mort : la couronne reste lisible.
		private const float DensitePlancher = 0.15f;
		private const int PosesMaxTapis = 2;
		// Au palier ×1, moins de feuilles : on n'y lit qu'une texture.
		private const float PartFeuillesLoin = 0.6f;

		// Contour d'une foliole en éventail depuis la base (star-shaped, donc pas de
		// triangulation native) : obovale, sommet échancré. (long, large) relatifs.
		// Base étroite et décollée du centre : l'ombre entre deux folioles les sépare à ×8,
		// où une foliole ne fait que ~9×5 px internes.
		private static readonly Vector2[] ProfilFoliole =
		{
			new(0.08f, 0f), new(0.30f, 0.15f), new(0.62f, 0.40f), new(0.92f, 0.38f), new(1f, 0.14f),
			new(0.88f, 0f), new(1f, -0.14f), new(0.92f, -0.38f), new(0.62f, -0.40f), new(0.30f, -0.15f),
		};

		// Lot de cette plante : gardé tant que le pinceau vit (le maillage doit survivre
		// jusqu'au rendu de la page).
		private LotTriangles _lotPrairie;
		// Tampon de projection réutilisé. Un pinceau dessine à la fois.
		private readonly List<Vector2> _contourPrairie = new();
		// Feuilles de devant, où posent marques fines et météo une fois le lot envoyé.
		private readonly List<(Vector2 C, float R, int I, float Z)> _sitesPrairie = new();

		// Taille d'un pied (0..1) : hauteur moteur, et âge du collet pour le trèfle.
		private float CroissancePrairie(PortPrairie port)
		{
			float h = _structure.HeightCm;
			return port switch
			{
				PortPrairie.Trefle => Mathf.Clamp(h / 10f, 0.2f, 1f) * Mathf.Lerp(0.55f, 1f, EtablissementTrefle()),
				PortPrairie.Plantain => Mathf.Clamp(h / 20f, 0.2f, 1f),
				PortPrairie.Fetuque => Mathf.Clamp(h / 15f, 0.25f, 1f),
				_ => Mathf.Clamp(h / 60f, 0.15f, 1f),
			};
		}

		// (rayon au sol, hauteur) du port dessiné, en cm. Remplace la mesure des segments
		// pour le tapis, l'ombre, le picking, le vent et la boîte de cuisson.
		private (float R, float H) MesurePrairie(PortPrairie port)
		{
			float h = _structure.HeightCm, g = CroissancePrairie(port);
			return AvecTaille(port switch
			{
				PortPrairie.Trefle => (RayonTrefleCm * g, Mathf.Clamp(h * 0.8f, 1f, HauteurTrefleCm)),
				PortPrairie.Dactyle => (Mathf.Clamp(h * 0.42f, 3f, 34f), Mathf.Clamp(h, 4f, 100f)),
				PortPrairie.Fetuque => (Mathf.Clamp(h * 0.6f, 2f, 16f), Mathf.Clamp(h, 2f, 30f)),
				_ => (RayonPlantainCm * g, Mathf.Clamp(h, 3f, 36f)),
			});
		}

		/// <summary>Appelé par MesurerPort : les mesures de port et d'ombre suivent ce
		/// qui est dessiné, pas le bois du moteur.</summary>
		private void MesurerPrairie()
		{
			PortPrairie port = PortDeLaPlante;
			if (port == PortPrairie.Aucun) return;
			(_rayonReelCm, _hauteurReelCm) = MesurePrairie(port);
			_spreadCm = _rayonReelCm;
			_heightCm = _hauteurReelCm;
		}

		/// <summary>Ce pied à quatre feuilles couvre-t-il un point à `d2` cm² de son collet ?
		/// Sert au picking seulement : rien ne le signale à l'écran.</summary>
		internal bool QuatreFeuillesSous(float d2) =>
			_structure != null && _structure.QuatreFeuilles && d2 <= _rayonReelCm * _rayonReelCm;

		/// <summary>Boîte de cuisson du port dessiné (false : autre espèce). Marge étroite :
		/// rien ne déborde du port, et une colonie entière à marge pleine gonflerait l'atlas.</summary>
		private bool BoitePrairie(out Rect2 r)
		{
			r = default;
			PortPrairie port = PortDeLaPlante;
			if (port == PortPrairie.Aucun) return false;
			var (rayon, h) = MesurePrairie(port);
			r = new Rect2(Vector2.Zero, Vector2.Zero);
			foreach (float z in new[] { 0f, h * MargeHauteurPrairie })
			{
				r = r.Expand(Iso(rayon, -rayon, z)).Expand(Iso(-rayon, rayon, z))
					 .Expand(Iso(rayon, rayon, z)).Expand(Iso(-rayon, -rayon, z));
			}
			r = r.Grow(MargePrairiePx);
			return true;
		}
		private const float MargeHauteurPrairie = 1.3f;   // pompons, épis au-dessus du port
		private const float MargePrairiePx = 2f;

		/// <summary>Dessine la plante si elle est de la prairie (appelé par DrawVector).
		/// Morte : même port, gris bois, clairsemé. Retourne false pour les autres.</summary>
		private bool DessinerPrairie()
		{
			PortPrairie port = PortDeLaPlante;
			if (port == PortPrairie.Aucun) return false;
			_lotPrairie ??= new LotTriangles();
			_lotPrairie.Vider();
			_sitesPrairie.Clear();
			Color col = TeintePrairie();
			switch (port)
			{
				case PortPrairie.Trefle: DessinerTrefle(col); break;
				case PortPrairie.Plantain: DessinerPlantain(col); break;
				case PortPrairie.Dactyle: DessinerDactyle(col); break;
				default: DessinerFetuque(col); break;
			}
			_lotPrairie.DessinerSansMaille(this);
			PoserDetailsPrairie(col);
			return true;
		}

		// Teinte du pied : espèce, automne, santé dès ×2, givre. Sans le « bois qui
		// transparaît » de TeinteSaison, qui lit `foliage_density` et ternirait tout tapis.
		private Color TeintePrairie()
		{
			if (MortPrairie) return DeadWoodColor;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			Color c = LeafColor(pal, Mathf.Clamp(_structure.Automne, 0f, 1f), _swayPhase);
			if (WorldView.CurrentZoom >= PalierSanteZoom) c = SymptomTint(c);
			c = Frosted(c);
			c.A = 1f;
			return c;
		}

		private bool MortPrairie => !string.IsNullOrEmpty(_deadStade);
		// Écrase les hauteurs d'un pied mort couché, comme le squelette commun.
		private float AplatMort => _deadStade == "couchee" ? CoucheeFlatten : 1f;
		private bool FleuriPrairie(float seuil) =>
			!MortPrairie && AuPalier(PalierSanteZoom) && _structure.Floraison >= seuil;

		// ---------------------------------------------------------------------------
		// TRÈFLE
		// ---------------------------------------------------------------------------

		private void DessinerTrefle(Color col)
		{
			var (rayon, h) = MesurePrairie(PortPrairie.Trefle);
			float g = CroissancePrairie(PortPrairie.Trefle), zoom = WorldView.CurrentZoom;
			float dens = MortPrairie ? DensitePlancher
				: Mathf.Clamp(_structure.DensiteVisible / DensitePleineTrefle, DensitePlancher, 1f);
			float loin = zoom < PalierSanteZoom ? PartFeuillesLoin : 1f;
			int n = Mathf.Max(1, Mathf.RoundToInt(FeuillesTrefle * g * dens * loin));
			int folioles = _structure.QuatreFeuilles ? 4 : 3;
			int ig = GraineIndividu;
			float taille = TailleFolioleCm * Mathf.Lerp(0.6f, 1f, g);

			// Disposition en tournesol (angle d'or) : couvre le disque sans trou ni rangée.
			var feuilles = new List<(float Prof, Vector3 P, float A, int K)>(n);
			float phase = Mathf.Tau * Hash01(201, ig, 0);
			for (int k = 0; k < n; k++)
			{
				float a = k * 2.39996f + phase;
				float d = rayon * Mathf.Sqrt((k + 0.5f) / n) * Mathf.Lerp(0.92f, 1.03f, Hash01(203, ig, k));
				float x = d * Mathf.Cos(a), y = d * Mathf.Sin(a);
				float centre = 1f - 0.6f * d / Mathf.Max(rayon, 1f);   // dôme : plus haut au centre
				float lz = h * centre * Mathf.Lerp(0.6f, 1f, Hash01(205, ig, k));
				lz = Mathf.Max(0.5f, lz - LeafDropCm(lz)) * AplatMort;
				feuilles.Add((WorldView.WorldToScreenOffset(x, y).Y, new Vector3(x, y, lz),
					Mathf.Tau * Hash01(207, ig, k), k));
			}
			feuilles.Sort((a, b) => a.Prof.CompareTo(b.Prof));   // du fond vers l'avant
			PoserSousCouche(rayon, col, ig);

			for (int f = 0; f < feuilles.Count; f++)
			{
				var (_, p, a0, k) = feuilles[f];
				// Ton 3 ou 2 : une feuille à contre-soleil perd un ton, et ne doit pas se fondre
				// dans la sous-couche (ton 1).
				int ton = 3 - (Hash01(209, ig, k) < 0.3f ? 1 : 0);
				if (zoom < PaliersHautsMinZoom) PoserTacheFeuille(p, taille * 1.05f, col, ton);
				// Une seule face par FEUILLE (`teinte`) : le soleil réel l'éclaire entière. Une face
				// par foliole n'en allumait qu'une, et la feuille se lisait comme un cœur isolé.
				// Quatre folioles : calées en X. En + les deux horizontales, écrasées par
				// l'iso, se confondraient. Un petit écart garde le pied naturel.
				else PoserFeuille(p, taille, folioles, folioles == 4 ? Mathf.Pi * 0.25f + (a0 - Mathf.Pi) * 0.04f : a0, col,
					Ton(col, ton, (int)(a0 / Mathf.Tau * 8f) & 7));
				if (f >= feuilles.Count * 2 / 3)
					_sitesPrairie.Add((Iso(p.X, p.Y, p.Z), taille * 0.7f * WorldView.PxPerCmX, k, p.Z));
			}
			if (FleuriPrairie(FloraisonSeuil * 0.4f)) PoserPompons(rayon, h, g, ig);
		}

		// Sous les feuilles, le feuillage qu'on ne détaille pas : une tache sombre au bord
		// irrégulier. Elle ferme le tapis entre les feuilles, sans en ajouter.
		private void PoserSousCouche(float rayon, Color col, int ig)
		{
			const int N = 24;
			Color c = Ton(col, 1);
			Vector2 centre = Iso(0f, 0f, 0f);
			Vector2 prem = default, prec = default;
			for (int i = 0; i <= N; i++)
			{
				int k = i % N;
				float a = k * Mathf.Tau / N;
				float d = rayon * Mathf.Lerp(0.72f, 0.98f, Hash01(221, ig, k));
				Vector2 cour = Iso(d * Mathf.Cos(a), d * Mathf.Sin(a), 0f);
				if (i == 0) prem = cour;
				else _lotPrairie.Triangle(centre, prec, i == N ? prem : cour, c);
				prec = cour;
			}
		}

		// Loin (×0,5-×2) : une feuille = une tache hexagonale. Les folioles n'y feraient
		// pas 2 px, et le ton au hash donne le grain du tapis.
		private void PoserTacheFeuille(Vector3 p, float r, Color col, int ton)
		{
			Color c = Ton(col, ton);
			Vector2 prem = Iso(p.X + r, p.Y, p.Z), prec = Iso(p.X, p.Y + r, p.Z);
			// Hexagone en éventail, projeté en iso comme le reste.
			for (int i = 2; i <= 5; i++)
			{
				float a = i * Mathf.Tau / 6f;
				Vector2 cour = Iso(p.X + r * Mathf.Cos(a), p.Y + r * Mathf.Sin(a), p.Z);
				_lotPrairie.Triangle(prem, prec, cour, c);
				prec = cour;
			}
		}

		// Près (×4+) : pétiole, ombre portée de chaque foliole, foliole, marque claire en V.
		private void PoserFeuille(Vector3 p, float taille, int folioles, float a0, Color col, Color teinte)
		{
			float zoom = WorldView.CurrentZoom, pix = PixelInterne;
			Vector2 centre = Iso(p.X, p.Y, p.Z);
			if (zoom >= PalierOrganesZoom)
				_lotPrairie.Ligne(Iso(p.X, p.Y, 0f), centre, Ton(col, 1), pix);
			var sud = new Vector2(0f, pix);
			// Quatre folioles, légèrement plus étroites : elles se touchent sans se couvrir.
			float large = folioles == 4 ? 0.9f : 1f;
			for (int f = 0; f < folioles; f++)
			{
				var (u, v) = AxesFoliole(a0, f, folioles);
				ContourFoliole(p, u, v, taille, large);
				PoserEventail(_contourPrairie, sud, Ton(col, 0));
			}
			for (int f = 0; f < folioles; f++)
			{
				var (u, v) = AxesFoliole(a0, f, folioles);
				ContourFoliole(p, u, v, taille, large);
				PoserEventail(_contourPrairie, Vector2.Zero, teinte);
				if (zoom >= PalierSymptomesZoom) PoserMarqueFoliole(p, u, v, taille, col);
			}
		}

		private static (Vector2 U, Vector2 V) AxesFoliole(float a0, int f, int folioles)
		{
			float a = a0 + Mathf.Tau * f / folioles;
			var u = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
			return (u, new Vector2(-u.Y, u.X));
		}

		private void ContourFoliole(Vector3 p, Vector2 u, Vector2 v, float taille, float large)
		{
			_contourPrairie.Clear();
			foreach (Vector2 q in ProfilFoliole)
				_contourPrairie.Add(PointFoliole(p, u, v, taille, q.X, q.Y * large));
		}

		private Vector2 PointFoliole(Vector3 p, Vector2 u, Vector2 v, float taille, float lg, float lr)
		{
			Vector2 m = u * (lg * taille) + v * (lr * taille);
			return Iso(p.X + m.X, p.Y + m.Y, p.Z);
		}

		// La marque claire en V du trèfle blanc et la nervure centrale.
		private void PoserMarqueFoliole(Vector3 p, Vector2 u, Vector2 v, float taille, Color col)
		{
			float pix = PixelInterne;
			Color clair = Ton(col, 4);
			Vector2 pointe = PointFoliole(p, u, v, taille, 0.38f, 0f);
			_lotPrairie.Ligne(PointFoliole(p, u, v, taille, 0.68f, 0.28f), pointe, clair, pix);
			_lotPrairie.Ligne(PointFoliole(p, u, v, taille, 0.68f, -0.28f), pointe, clair, pix);
			_lotPrairie.Ligne(PointFoliole(p, u, v, taille, 0.08f, 0f),
				PointFoliole(p, u, v, taille, 0.86f, 0f), Ton(col, 1), pix);
		}

		// Boules blanches sur tige nue, au-dessus des feuilles.
		private void PoserPompons(float rayon, float h, float g, int ig)
		{
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			int n = Mathf.Clamp(Mathf.CeilToInt(_structure.Floraison * g * PomponsMax), 1, PomponsMax);
			Color tige = Ton(pal.Leaf, 3);
			for (int k = 0; k < n; k++)
			{
				float a = Mathf.Tau * Hash01(211, ig, k), d = rayon * 0.75f * Mathf.Sqrt(Hash01(213, ig, k));
				float x = d * Mathf.Cos(a), y = d * Mathf.Sin(a);
				float z = h * Mathf.Lerp(1.05f, 1.25f, Hash01(215, ig, k));
				Vector2 c = Iso(x, y, z);
				_lotPrairie.Ligne(Iso(x, y, 0f), c, tige, PixelInterne);
				PoserBoule(c, RayonPomponCm * WorldView.PxPerCmX, pal.Flower, ig + k);
			}
		}

		// Une boule : base ombrée, calotte, puis grain de fleurons dès ×8.
		private void PoserBoule(Vector2 c, float r, Color col, int graine)
		{
			float pix = PixelInterne;
			r = Mathf.Max(r, pix);
			// Tons d'une fleur claire : le ton de base est la couleur d'espèce, le blanc d'un
			// pompon ne descend jamais jusqu'à son ombre dérivée vers le bleu.
			PoserDisque(c, r, Ton(col, PaletteIndexee.TonBase));
			PoserDisque(c - new Vector2(0f, r * 0.2f), r * 0.78f, Ton(col, 3));
			if (!AuPalier(PalierOrganesZoom)) return;
			Color eclat = Ton(col, 4), creux = Ton(col, 1);
			for (int k = 0; k < 7; k++)
			{
				float a = Mathf.Tau * Hash01(217, graine, k), d = r * 0.8f * Mathf.Sqrt(Hash01(219, graine, k));
				var q = c + new Vector2(d * Mathf.Cos(a), d * Mathf.Sin(a) * 0.9f);
				PoserDisque(q, Mathf.Max(pix, r * 0.12f), k % 3 == 0 ? creux : eclat);
			}
		}

		private void PoserDisque(Vector2 c, float r, Color col)
		{
			int N = CotesPour(r, 8);
			Vector2 prem = c + new Vector2(r, 0f), prec = prem;
			for (int i = 1; i < N; i++)
			{
				float a = i * Mathf.Tau / N;
				Vector2 cour = c + new Vector2(r * Mathf.Cos(a), r * Mathf.Sin(a));
				if (i > 1) _lotPrairie.Triangle(prem, prec, cour, col);
				prec = cour;
			}
		}

		// Éventail depuis le contour[0] : suffit aux formes étoilées depuis la base.
		private void PoserEventail(List<Vector2> contour, Vector2 dec, Color col)
		{
			for (int i = 1; i + 1 < contour.Count; i++)
				_lotPrairie.Triangle(contour[0] + dec, contour[i] + dec, contour[i + 1] + dec, col);
		}

		// ---------------------------------------------------------------------------
		// DÉTAILS — sémiologie et météo des paliers hauts, par-dessus le lot
		// ---------------------------------------------------------------------------

		// Les marques (morsures, gel, taches, reflet, neige) gardent leur code commun et
		// se posent sur les feuilles de devant : ce sont les seules qu'on voit entières.
		private void PoserDetailsPrairie(Color col)
		{
			if (MortPrairie) return;
			_limbeCourant = col;
			bool organes = AuPalier(PalierOrganesZoom);
			foreach (var (c, r, i, z) in _sitesPrairie)
			{
				if (organes)
				{
					DrawDetailsFeuille(c, r, i, 0);
					DrawWetGlint(c, r, i, 0);
					DrawColdLeaf(c, r, i, 0, z);
				}
				else if (_snow > 0f && Hash01(47, i, GraineIndividu) < _snow)
					DrawSnowCrown(c, r, r * 0.6f);
			}
		}
	}
}
