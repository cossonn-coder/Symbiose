// SYMBIOSE — LeafLitterLayer.cs
// La LITIÈRE DE FEUILLES au sol (rendu feuillage ⑥, E5bis, doc RENDU_FEUILLAGE
// §6.3). Sœur de `LitterLayer` (qui pose des AMAS abstraits, tissu confondu),
// mais SPÉCIALISÉE feuille : ici une feuille tombée est rendue comme une vraie
// SILHOUETTE de feuille MORTE posée à plat — un semis déterministe de calottes
// aplaties au sol, sur la parcelle, à la manière de `MacroLife`/`LitterLayer`
// (échantillonnage STABLE par hash, zéro Random — philo #3, condition du golden).
//
// AUTOMNE VISIBLE ⑤ : on lit la MASSE DE FEUILLES du plot (9ᵉ champ de `litiere`, pont
// 0.6.3), même si un autre tissu domine : un tapis sous un arbre ne s'interrompt
// plus là où l'herbe morte pèse davantage. Repli sans ce champ : les seuls plots à
// tissu dominant `"feuille"`, comme avant. Le tapis est un SEMIS EN LOT : un grain
// aux paliers bas (×1, ×2, zoom de jeu), une petite feuille à deux tons dès ×4 ; les
// silhouettes ne s'y ajoutent qu'aux gros plans (ZoomSilhouette), où peu de plots sont à
// l'écran. Il fond tout seul : le moteur décompose la masse, le semis s'éclaircit.
// Couleurs littérales : un lot sans texture ne passe pas par le shader indexé, et ces
// tons sont plats (ils ne suivent pas le soleil), donc rien n'est perdu.
//
// L'espèce d'origine N'EST PAS traçable côté moteur, D50 (la
// parcelle est typée par TISSU, pas par espèce) → repli `Elliptique` assumé
// (§6.3) : on passe une espèce vide à `DrawLitterLeaf`, qui retombe sur le profil
// par défaut. Une litière de pommier perd donc sa silhouette de pommier — limite
// connue, levée le jour où le moteur tracera l'espèce de la nécromasse.
//
// 📖 Pédagogie — POURQUOI ce nœud EST-il un PlantRenderer ?
// Les primitives de tracé d'une feuille (`DrawLitterLeaf` → `DrawShapeBySpecies`
// → `DrawVolumeEllipse`, nervures…) sont des méthodes d'INSTANCE de
// `PlantRenderer`, et un `DrawCircle`/`DrawLine` de Godot ne « peint » que sur le
// CanvasItem qui l'émet, et SEULEMENT pendant son propre `_Draw`. Pour réutiliser
// ce vocabulaire de tracé sans le dupliquer, le calque HÉRITE de `PlantRenderer`
// et l'utilise comme « stylo » : il émet les feuilles mortes depuis SON `_Draw`.
// On neutralise les deux comportements « plante vivante » du parent : `_Ready`
// (qui crée une ombre-capsule) → no-op, et `_Draw` (qui exige une `_structure`)
// → remplacé par notre semis de litière. `_structure` reste null : `DrawLitterLeaf`
// prend l'espèce en ARGUMENT et ne la lit jamais.
//
// 📖 Pédagogie — MÊME patron batché que `LitterLayer`/`MacroLife` : UN seul
// CanvasItem redessine toute la litière de feuilles dans son `_Draw` (pas un
// Node2D par feuille), et le semis part en un seul envoi. La litière est INERTE (matière morte) : on ne QueueRedraw
// qu'à l'arrivée d'un snapshot et au basculement de LOD — le canvas dort sinon.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class LeafLitterLayer : PlantRenderer
	{
		// Le tissu de SURFACE qui nous concerne (TISSU_ORDER côté moteur) : repli
		// d'un pont pré-0.6.3, qui n'expose pas la masse de feuilles à part.
		private const string TissuFeuille = "feuille";

		// LOD : visible dès ×1, le zoom de jeu du joueur. Dès ZoomFeuille le grain devient
		// une feuille, dès ZoomSilhouette s'y ajoutent les silhouettes DrawLitterLeaf
		// (plusieurs envois par feuille, tenable seulement quand peu de plots sont à l'écran).
		private const float MinZoom = 1f;
		private const float ZoomFeuille = 4f;
		private const float ZoomSilhouette = 16f;
		// Marge de culling (px canvas) : couvre l'étalement du semis dans le plot.
		private const float CullMarginPx = 64f;

		// Référence de masse pour saturer la densité. Le moteur dépose FEUILLE_PAR_PLOT
		// (0,30) étalé sur 4 semaines pendant que ça se décompose : le pic réel d'un plot
		// est plus bas, ~0,20 (mesures/apres_tapis.md). Au-delà, le tapis est plein.
		private const float MasseRef = 0.20f;
		// En deçà, plus rien à voir : le tapis a fondu (sinon un grain par plot resterait
		// toute l'année, la moindre feuille d'herbacée en poserait un).
		private const float MasseMin = 0.01f;
		// Semis du tapis par plot à saturation. Un plot fait 380 px² à ×1 : 60 grains de
		// 2 px² en couvrent ~32 %. Dès ZoomFeuille, 40 feuilles suffisent, elles sont plus grandes.
		private const int MaxGrains = 60, MaxFeuilles = 40;
		// Le semis couvre tout le plot (un plot = 50 cm) pour que le tapis soit continu.
		private const float SemisDemiCm = 25f;
		private const float GrainPx = 1f;
		// Feuille à plat : demi-longueur et demi-largeur en cm, projetées par la vue.
		private const float FeuilleDemiCm = 7f, FeuilleLargeCm = 3f;
		// Bornes du nombre de SILHOUETTES par plot (∝ masse, comme la pop macro) :
		// au moins 1 (une trace se voit), au plus MaxLeaves (densité plafonnée).
		private const int MinLeaves = 1;
		private const int MaxLeaves = 6;
		// Étalement du semis dans le plot, en cm (un plot = 50 cm) : on reste DANS
		// le losange (±18 cm autour du centre, comme LitterLayer.SpreadCm).
		private const float SpreadCm = 18f;

		// Taille d'une feuille morte à l'écran, en px MONDE projeté (calotte). On
		// la POSE À PLAT : ry < rx (aplatissement) → une feuille au sol n'a pas le
		// relief d'une feuille dressée, mais garde ≥ 2 valeurs (DrawVolumeEllipse,
		// invariant §1). Ajustable F5.
		private const float LeafRadiusPx = 5f;
		private const float FlatRatio = 0.45f;   // ry = rx × ce ratio → calotte aplatie

		// Dérive vers le sol (§6.3) : la litière de feuilles fraîche est brun-roux
		// VIF ; en vieillissant elle s'assombrit et se désature jusqu'à FONDRE dans
		// l'humus. `age_sem` (proxy de décompo, pont 0.5.6) pilote l'interpolation.
		private static readonly Color FreshLeaf = new Color("a86a32");   // brun-roux sec vif
		private static readonly Color HumusLeaf = new Color("5a4630");   // brun sombre désaturé = humus
		// Âge (semaines) au-delà duquel la feuille a entièrement fondu dans l'humus
		// (teinte = HumusLeaf pleine). En deçà, interpolation linéaire. Calibrage F5.
		private const float AgeFullDecompSem = 16f;
		// Tons chauds du semis, du plus jaune au plus brun : l'œil lit un mélange de feuilles,
		// pas une teinte unie. Ils virent à l'humus par paliers (TonsSemis), pas en continu.
		private static readonly Color[] TonsFrais =
		{
			new("d3a23a"), new("c98a2e"), new("b5622a"), new("8f4a24"),
		};
		private const int NbStades = 4;
		private static readonly Color[,] TonsSemis = CalculerTonsSemis();
		private static Color[,] CalculerTonsSemis()
		{
			var t = new Color[NbStades, TonsFrais.Length];
			for (int s = 0; s < NbStades; s++)
				for (int i = 0; i < TonsFrais.Length; i++)
					t[s, i] = TonsFrais[i].Lerp(HumusLeaf, s / (NbStades - 1f));
			return t;
		}
		// Opacité des silhouettes : plancher (une trace ténue se voit) + part ∝ masse, comme
		// LitterLayer — la litière fraîche dense est plus présente que deux feuilles.
		private const float AlphaFloor = 0.55f;
		private const float AlphaSpan  = 0.45f;

		// Un plot porteur de litière de FEUILLES. Position MONDE du centre (cm) ;
		// `Count` feuilles à semer, `Col` la teinte morte dérivée de l'âge, `Hash`
		// la graine déterministe du semis (stable inter-frames et inter-sessions).
		private struct Patch
		{
			public float Cx, Cy;
			public Color Col;
			public int Count;
			public float Sat;    // masse / MasseRef ∈ [0, 1], règle la densité du semis
			public int Stade;    // 0 fraîche → NbStades − 1 humus
			public float Alpha;
			public uint Hash;
		}

		private readonly List<Patch> _patches = new();
		private bool _lastZoomOk;
		private int _margeVersion = -1;   // cadre commun déjà dessiné (MargeVue, T4)
		private readonly LotTriangles _lot = new();

		// Hash djb2-xor (même choix que LitterLayer/MacroLife : jamais GetHashCode
		// pour du visuel stable, jamais de Random — philo #3).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s)
				h = ((h << 5) + h) ^ ch;
			return h;
		}

		// Le parent crée une ombre-capsule en _Ready (rendu d'une plante vivante) :
		// inutile et trompeur pour un calque de litière → on neutralise. `_structure`
		// reste null, on ne dessine jamais de segments.
		public override void _Ready() { }

		/// <summary>
		/// Applique le bloc `litiere` d'un snapshot (liste creuse par tuile), en ne
		/// retenant QUE les plots qui portent des feuilles. `origins` =
		/// origin_cm par tuile (le même cache que plantes/macro/LitterLayer).
		/// Reconstruction simple : la litière est inerte (pas de diff/fondu à tenir)
		/// et un snapshot ne tombe qu'à la semaine — pas de churn.
		/// </summary>
		public void SetLitiere(GDict litiere, Dictionary<string, Vector2> origins)
		{
			_patches.Clear();
			foreach (var tileKv in litiere)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				using var plots = tileKv.Value.AsGodotArray();
				for (int i = 0; i < plots.Count; i++)
				{
					// Format compact : [r, c, tissu_dominant, masse, age_sem, bois × 3,
					// masse_feuille (0.6.3)].
					using var e = LectureSnap.Tab(plots, i);   // PERF VUE ④ : sans finaliseur
					float masse;
					if (e.Count > 8) masse = (float)e[8].AsDouble();
					else if (LectureSnap.S(e, 2) == TissuFeuille) masse = (float)e[3].AsDouble();
					else continue;   // pont pré-0.6.3, autre tissu dominant → LitterLayer
					if (masse < MasseMin) continue;
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					float ageSem = AgeHorsBois(e);

					float sat = Mathf.Clamp(masse / MasseRef, 0f, 1f);
					float decomp = Mathf.Clamp(ageSem / AgeFullDecompSem, 0f, 1f);
					_patches.Add(new Patch
					{
						// x = est (colonnes), y = sud (lignes) — convention
						// FindPlot/WorldToScreen, pas une 2ᵉ (leçon D2).
						Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
						Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
						// Dérive vers l'humus ∝ âge : fraîche = brun-roux vif,
						// vieillie = brun sombre désaturé qui fond dans le sol.
						Col = FreshLeaf.Lerp(HumusLeaf, decomp),
						Count = Mathf.Clamp(
							MinLeaves + Mathf.RoundToInt((MaxLeaves - MinLeaves) * sat),
							MinLeaves, MaxLeaves),
						Sat = sat,
						Stade = Mathf.RoundToInt(decomp * (NbStades - 1)),
						Alpha = AlphaFloor + AlphaSpan * sat,
						Hash = HashKey(tileId + "|" + r + "|" + c),
					});
				}
			}
			QueueRedraw();
		}

		// age_sem (5ᵉ champ, pont 0.5.6) = âge moyen de TOUTE la surface du plot : le bois
		// mort y pèse lourd et vieux (médiane 54 semaines en s37, la feuille de l'automne
		// semblait déjà humus [n=1 run, VM]). On retire la part du bois, connue (index
		// 5-6) ; reste l'âge feuilles + herbacées (médiane 2,3 semaines en s37). Lecture
		// TOLÉRANTE : pré-0.5.6 → 0 (fraîche), pré-0.5.51 → l'âge moyen tel quel.
		private static float AgeHorsBois(Godot.Collections.Array e)
		{
			if (e.Count <= 4) return 0f;
			float age = (float)e[4].AsDouble();
			if (e.Count <= 6) return age;
			float total = (float)e[3].AsDouble(), bois = (float)e[5].AsDouble();
			if (total - bois <= 1e-6f) return age;
			return Mathf.Max(0f, (total * age - bois * (float)e[6].AsDouble()) / (total - bois));
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// La litière ne s'anime pas : on ne redessine qu'au basculement de LOD
			// (zoom franchit MinZoom) et au ré-ancrage, qu'un changement de palier
			// déclenche aussi (la taille du cadre change) — sinon le canvas dort.
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk || _margeVersion != MargeVue.Version)
			{
				_lastZoomOk = zoomOk;
				_margeVersion = MargeVue.Version;   // pan/zoom : cadre ré-ancré
				QueueRedraw();
			}
		}

		// Remplace le _Draw « plante vivante » du parent (qui exige _structure) par
		// le semis de litière de feuilles. Même patron batché que LitterLayer.
		public override void _Draw()
		{
			_lot.Vider();
			if (_patches.Count == 0 || WorldView.CurrentZoom < MinZoom) return;
			// Culling (T4) : cadre de marge COMMUN et stable (world/MargeVue.cs),
			// + notre marge d'objet ; redessiné au ré-ancrage (pan/zoom), pas par frame.
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			DessinerSemis(vis);
			if (WorldView.CurrentZoom >= ZoomSilhouette) DessinerSilhouettes(vis);
		}

		// Le tapis, en un seul envoi. Offsets calculés sur la base projetée de la vue
		// (une combinaison linéaire suffit) : il pivote avec elle sans glisser (D35).
		private void DessinerSemis(Rect2 vis)
		{
			bool feuille = WorldView.CurrentZoom >= ZoomFeuille;
			int max = feuille ? MaxFeuilles : MaxGrains;
			Vector2 bx = WorldView.WorldToScreenOffset(1f, 0f);
			Vector2 by = WorldView.WorldToScreenOffset(0f, 1f);
			foreach (var p in _patches)
			{
				Vector2 center = WorldView.WorldToScreen(p.Cx, p.Cy);
				if (!vis.HasPoint(center)) continue;
				int semis = Mathf.Max(1, Mathf.RoundToInt(max * p.Sat));
				for (int i = 0; i < semis; i++)
				{
					uint h = LeafFallLayer.Melange(p.Hash + (uint)i * 0x9e3779b1u);
					float dx = SemisDemiCm * ((h & 0xff) / 127.5f - 1f);
					float dy = SemisDemiCm * ((h >> 8 & 0xff) / 127.5f - 1f);
					Vector2 c = center + bx * dx + by * dy;
					Color col = TonsSemis[p.Stade, (h >> 16) % (uint)TonsFrais.Length];
					if (!feuille) { _lot.Grain(c, GrainPx, col); continue; }
					float a = (h >> 18 & 0xff) * (Mathf.Tau / 256f);
					float cs = Mathf.Cos(a), sn = Mathf.Sin(a);
					Vector2 d = (bx * cs + by * sn) * FeuilleDemiCm;
					Vector2 l = (by * cs - bx * sn) * FeuilleLargeCm;
					_lot.Triangle(c - d, c + l, c + d, col);
					_lot.Triangle(c - d, c + d, c - l, col.Darkened(0.2f));
				}
			}
			_lot.Dessiner(this);
		}

		// Gros plan : la vraie forme de feuille, par-dessus le semis.
		private void DessinerSilhouettes(Rect2 vis)
		{
			foreach (var p in _patches)
			{
				Vector2 center = WorldView.WorldToScreen(p.Cx, p.Cy);
				if (!vis.HasPoint(center)) continue;   // hors cadre : rien
				Color col = p.Col;
				col.A = p.Alpha;
				for (int i = 0; i < p.Count; i++)
				{
					// Semis déterministe : deux tirages du hash (déphasés par i)
					// → angle + distance dans le plot. Projeté en OFFSET (vecteur)
					// → le semis pivote avec la vue sans glisser de 20 m (D35).
					uint hi = p.Hash * 2654435761u + (uint)(i * 40503);
					float ang = (hi & 0xffff) * (Mathf.Tau / 65536f);
					float dist = SpreadCm * ((hi >> 16 & 0xff) / 255f);
					Vector2 off = WorldView.WorldToScreenOffset(
						dist * Mathf.Cos(ang), dist * Mathf.Sin(ang));
					// POSE À PLAT : ry = rx × FlatRatio (calotte aplatie, ≥ 2 valeurs
					// conservées par DrawVolumeEllipse sous-jacent). Espèce vide →
					// repli Elliptique assumé (§6.3). `seed` = hash du plot dérivé
					// du rang i → deux feuilles d'un amas diffèrent, stable.
					int seed = (int)(hi & 0x7fffffff);
					DrawLitterLeaf("", center + off,
								   LeafRadiusPx, LeafRadiusPx * FlatRatio, col, seed);
				}
			}
		}
	}
}
