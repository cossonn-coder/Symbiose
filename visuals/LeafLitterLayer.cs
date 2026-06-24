// SYMBIOSE — LeafLitterLayer.cs
// La LITIÈRE DE FEUILLES au sol (rendu feuillage ⑥, E5bis, doc RENDU_FEUILLAGE
// §6.3). Sœur de `LitterLayer` (qui pose des AMAS abstraits, tissu confondu),
// mais SPÉCIALISÉE feuille : ici une feuille tombée est rendue comme une vraie
// SILHOUETTE de feuille MORTE posée à plat — un semis déterministe de calottes
// aplaties au sol, sur la parcelle, à la manière de `MacroLife`/`LitterLayer`
// (échantillonnage STABLE par hash, zéro Random — philo #3, condition du golden).
//
// On ne traite QUE les plots dont le tissu DOMINANT du snapshot `litiere` est
// `"feuille"` (les autres — herbacé, fruit, bois — restent à `LitterLayer`, qui
// pose ses amas terreux). L'espèce d'origine N'EST PAS traçable côté moteur (la
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
// Node2D par feuille). La litière est INERTE (matière morte) : on ne QueueRedraw
// qu'à l'arrivée d'un snapshot et au basculement de LOD — le canvas dort sinon.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class LeafLitterLayer : PlantRenderer
	{
		// Le tissu de SURFACE qui nous concerne (TISSU_ORDER côté moteur). Toute
		// autre valeur (herbace/fruit/bois/fleur) est laissée à LitterLayer.
		private const string TissuFeuille = "feuille";

		// LOD : aligné sur LitterLayer (un détail de sol qu'on lit en s'approchant).
		// Sous ce zoom, on n'affiche rien — et la forme de feuille (§2) retombe de
		// toute façon sur l'ellipse au repli LOD interne de DrawShapeBySpecies.
		private const float MinZoom = 2f;
		// Marge de culling (px canvas) : couvre l'étalement du semis dans le plot.
		private const float CullMarginPx = 64f;

		// Référence de masse pour saturer la densité (cf. LitterLayer.MasseRef) :
		// au-delà, l'amas est « plein » (nombre de feuilles plafonné). Calibrage F5.
		private const float MasseRef = 2.5f;
		// Bornes du nombre de feuilles par plot (∝ masse, comme la pop macro) :
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
		private const float AgeFullDecompSem = 12f;
		// Opacité : plancher (une trace ténue se voit) + part ∝ masse, comme
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
			public float Alpha;
			public uint Hash;
		}

		private readonly List<Patch> _patches = new();
		private bool _lastZoomOk;

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
		/// retenant QUE les plots dont le tissu dominant est `feuille`. `origins` =
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
				foreach (var pv in tileKv.Value.AsGodotArray())
				{
					// Format compact 0.5.6 : [r, c, tissu_dominant, masse, age_sem].
					var e = pv.AsGodotArray();
					string tissu = e[2].AsString();
					if (tissu != TissuFeuille) continue;   // herbacé/fruit/bois → LitterLayer
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					float masse = (float)e[3].AsDouble();
					// age_sem (5ᵉ champ, pont 0.5.6) : proxy de décompo. Lecture
					// TOLÉRANTE — un snapshot pré-0.5.6 n'a que 4 champs → âge 0
					// (litière fraîche, brun-roux vif), jamais de crash.
					float ageSem = e.Count > 4 ? (float)e[4].AsDouble() : 0f;

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
						Alpha = AlphaFloor + AlphaSpan * sat,
						Hash = HashKey(tileId + "|" + r + "|" + c),
					});
				}
			}
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// La litière ne s'anime pas : on ne redessine qu'au basculement de LOD
			// (zoom franchit MinZoom) — sinon le canvas dort.
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk)
			{
				_lastZoomOk = zoomOk;
				QueueRedraw();
			}
		}

		// Remplace le _Draw « plante vivante » du parent (qui exige _structure) par
		// le semis de litière de feuilles. Même patron batché que LitterLayer.
		public override void _Draw()
		{
			if (_patches.Count == 0 || WorldView.CurrentZoom < MinZoom) return;
			// Culling : la transform canvas→écran de Godot, inversée, ramène le
			// viewport en coordonnées canvas (notre espace de dessin).
			Rect2 vis = (GetCanvasTransform().AffineInverse()
						 * GetViewportRect()).Grow(CullMarginPx);
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
