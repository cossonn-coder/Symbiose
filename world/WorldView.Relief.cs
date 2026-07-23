// SYMBIOSE — WorldView.Relief.cs (partial de WorldView, D57 ② — épaisseur de sol)
// Le RELIEF du sol : chaque plot est extrudé verticalement d'une hauteur ∝ son
// épaisseur de sol (champ `epaisseur_sol`, cm, exposé au snapshot 0.5.16). On
// VOIT le sol monter (l'humus s'accumule au fil des ans) et descendre (décompo,
// tassement, érosion) — le pendant visible du cycle de la matière organique.
//
// 📖 Modèle iso : le « dessus » du plot (le losange texturé de BuildGround) est
// remonté de `rise` px ; un FLANC vertical (Polygon2D sombre) comble la bande
// entre le dessus remonté et le niveau du sol de base. Les objets enracinés
// (plantes) suivent le MÊME `rise` → ils restent plantés dans la terre, pas
// suspendus (Partie C, helper UNIQUE `ReliefRisePx`).
//
// ⚠️ POINTS F5 (Nico) — cf. kickoff 02_rendu_relief.md §Points F5 :
//   · ReliefExaggeration : les épaisseurs jeunes sont sub-pixel (<1 cm) → un
//     facteur d'exagération rend le relief lisible. Valeur de départ à calibrer
//     à l'œil (trop bas = plat, trop haut = 60 cm d'humus mûr paraît une falaise).
//   · Recalage des AUTRES couches (litière, vie macro, structures, carpophores,
//     conteneurs) : NON branché ici (voie incrémentale du kickoff : « relief
//     d'abord, puis le recalage »). Extension mécanique via ReliefRisePx quand
//     l'exagération est calée au F5 — sinon tout « volerait » avant calibrage.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Facteur d'exagération visuelle du relief (F5-tunable EN LIVE via
		// l'inspecteur Godot — [Export]). 1.0 = échelle physique (1 cm de sol →
		// PxPerCmZ px) ; un sol mûr (~20 cm, EPAISSEUR_NORM_REF) fait alors
		// ~20·PxPerCmZ·facteur px de relief. À 0.5 (défaut), 20 cm ≈ 4 px internes
		// (~8 à l'écran) — discret. ⚠️ L'effet ne se voit qu'au PROCHAIN snapshot
		// (avance d'une semaine / mode Turbo) : UpdateRelief relit la valeur alors.
		[Export] public float ReliefExaggeration = 0.5f;

		// Un plot du relief : le losange « dessus » (déjà créé par BuildGround),
		// son flanc vertical, sa position écran de BASE (niveau sol 0) et son
		// identité tuile/plot pour lire l'épaisseur. baseScreen = WorldToScreen du
		// centre au niveau du sol : le dessus s'en écarte de `rise` vers le haut.
		private readonly struct ReliefPlot
		{
			public readonly string Tile;
			public readonly int R, C;
			public readonly Vector2 BaseScreen;
			public readonly Sprite2D Top;
			public readonly Polygon2D Flanc;
			public ReliefPlot(string tile, int r, int c, Vector2 baseScreen,
							  Sprite2D top, Polygon2D flanc)
			{ Tile = tile; R = r; C = c; BaseScreen = baseScreen; Top = top; Flanc = flanc; }
		}

		// Plots du relief, reconstruits par BuildGround (donc à chaque rotation).
		private readonly List<ReliefPlot> _reliefPlots = new();
		// Épaisseur courante par tuile (grille dense cm), lue au dernier snapshot.
		private Dictionary<string, float[,]> _epaisseurCm;
		// Altitude (micro-relief topographique FIXE, hydrologie ①, snapshot 0.5.17)
		// par tuile (grille dense cm). SOCLE géométrique du terrain, DISTINCT de
		// l'humus : la surface hydraulique du moteur est `altitude + epaisseur_sol`
		// (cf. tick_ruissellement) → on extrude le MÊME empilement pour que la vue
		// coïncide avec l'eau (les creux d'altitude captent les flaques ②/⑧). Lu au
		// snapshot par ApplyAltitude, sommé à l'épaisseur dans EpaisseurPxAt.
		private Dictionary<string, float[,]> _altitudeCm;

		// Vidé en tête de BuildGround (le sol est reconstruit sur rotation) : les
		// vieux ReliefPlot pointaient des nœuds désormais libérés.
		private void ResetRelief() => _reliefPlots.Clear();

		// Enregistre un plot pour le relief + crée son FLANC (sous le dessus).
		// Appelé par BuildGround pour chaque plot, APRÈS l'ajout du dessus `top`
		// (le flanc, ajouté ensuite, se dessine par-dessus les DESSUS des plots
		// nord déjà posés mais SOUS son propre dessus — non : le flanc doit passer
		// SOUS son dessus). On l'ajoute donc AVANT le dessus : voir BuildGround.
		private void RegisterReliefPlot(Node2D ground, string soilName, string tile,
										int r, int c, Vector2 baseScreen, Sprite2D top)
		{
			var flanc = new Polygon2D { Color = SoilColor(soilName).Darkened(0.4f) };
			ground.AddChild(flanc);   // sous le dessus (ajouté juste après par BuildGround)
			_reliefPlots.Add(new ReliefPlot(tile, r, c, baseScreen, top, flanc));
		}

		// SOURCE UNIQUE de l'offset vertical (kickoff §C : « un seul point de
		// vérité »). SURFACE du plot (tuile, r, c) → px de relief, où
		// surface = altitude (socle topo FIXE ①) + epaisseur_sol (humus foisonnant
		// D57). C'est le MÊME empilement que la surface hydraulique du moteur
		// (tick_ruissellement) → les creux d'altitude coïncident avec les flaques ⑧.
		// Chaque terme est TOLÉRANT (champ absent ou hors grille → 0) : un terrain
		// plat sans humus (démo, binaire ancien) reste au niveau du sol, aucun crash.
		private float EpaisseurPxAt(string tile, int r, int c)
			=> (GridCmAt(_altitudeCm, tile, r, c) + GridCmAt(_epaisseurCm, tile, r, c))
			   * PxPerCmZ * ReliefExaggeration;

		// Lecture bornée d'une grille dense cm par tuile (altitude ou épaisseur) :
		// 0 si le champ n'est pas encore connu ou (r,c) hors grille (repli plat).
		private static float GridCmAt(Dictionary<string, float[,]> grids,
									   string tile, int r, int c)
		{
			if (grids == null || !grids.TryGetValue(tile, out var g))
				return 0f;
			if (r < 0 || r >= g.GetLength(0) || c < 0 || c >= g.GetLength(1))
				return 0f;
			return g[r, c];
		}

		// Recalage d'un objet enraciné : de combien remonter (px) un objet posé à
		// la position LOCALE (lx, ly) cm dans `tile`. Résout le plot-foyer
		// (floor(/PlotCm)), comme le moteur. Partie C — même conversion que le sol.
		private float ReliefRisePx(string tile, float lxCm, float lyCm)
			=> EpaisseurPxAt(tile, (int)(lyCm / PlotCm), (int)(lxCm / PlotCm));

		/// <summary>Offset de relief (px, vers le HAUT) au plot (r,c) d'une tuile —
		/// accesseur public pour les calques de sol qui doivent se poser SUR la
		/// surface extrudée (flaque/marais ⑧). Même source unique que les plantes
		/// (surface = altitude + épaisseur × exagération). 0 si tuile/plot inconnu.</summary>
		public float ReliefRiseAtPlot(string tile, int r, int c)
			=> EpaisseurPxAt(tile, r, c);

		// Lit le bloc `epaisseur` du snapshot (grille 2D dense par tuile, cm) et
		// remonte le relief. Tolérant : bloc absent (binaire pré-0.5.16) → relief
		// laissé plat, aucun crash. Appelé par ApplySnapshot.
		private void ApplyEpaisseur(Godot.Collections.Dictionary epaisseur)
		{
			_epaisseurCm = ParseDenseGrid(epaisseur);
			UpdateRelief();
		}

		// Lit le bloc `altitude` du snapshot (grille 2D dense par tuile, cm,
		// hydrologie ①, 0.5.17) : socle topographique FIXE. Même format que
		// `epaisseur` → même parseur. Tolérant : bloc absent (binaire pré-0.5.17) →
		// altitude nulle → terrain plat (l'épaisseur seule fait le relief, comme avant).
		// Appelé par ApplySnapshot AVANT ApplyEpaisseur (qui déclenche UpdateRelief).
		private void ApplyAltitude(Godot.Collections.Dictionary altitude)
			=> _altitudeCm = ParseDenseGrid(altitude);

		// Convertit un bloc snapshot « grille 2D dense par tuile » (rows × cols de
		// doubles cm) en Dictionary<tuile, float[,]>. Partagé par altitude et
		// épaisseur (même contrat de sérialisation, serialize.py).
		private static Dictionary<string, float[,]> ParseDenseGrid(
			Godot.Collections.Dictionary bloc)
		{
			var res = new Dictionary<string, float[,]>();
			foreach (var kv in bloc)
			{
				var rows = kv.Value.AsGodotArray();
				int nr = rows.Count;
				if (nr == 0) { res[kv.Key.AsString()] = new float[0, 0]; continue; }
				int nc = rows[0].AsGodotArray().Count;
				var grid = new float[nr, nc];
				for (int r = 0; r < nr; r++)
				{
					var row = rows[r].AsGodotArray();
					for (int c = 0; c < nc && c < row.Count; c++)
						grid[r, c] = (float)row[c].AsDouble();
				}
				res[kv.Key.AsString()] = grid;
			}
			return res;
		}

		// Applique l'épaisseur courante à la géométrie : dessus remonté + flanc
		// redessiné. Une passe sur les plots (une fois par snapshot ≈ 60 s) — le
		// coût est celui de BuildGround, jugé trivial à cette cadence.
		private void UpdateRelief()
		{
			const float hw = TileWPx / 2f, hh = TileHPx / 2f;
			foreach (var p in _reliefPlots)
			{
				float rise = EpaisseurPxAt(p.Tile, p.R, p.C);
				p.Top.Position = p.BaseScreen - new Vector2(0f, rise);
				// Flanc = bande verticale sous le losange remonté : arête basse du
				// dessus (ouest/sud/est remontés de `rise`) jusqu'à l'arête basse
				// au niveau du sol. Dégénéré (invisible) quand rise = 0.
				Vector2 b = p.BaseScreen;
				p.Flanc.Polygon = new[]
				{
					b + new Vector2(-hw, -rise),    // ouest, dessus remonté
					b + new Vector2(0f, hh - rise),  // sud,   dessus remonté
					b + new Vector2(hw, -rise),      // est,   dessus remonté
					b + new Vector2(hw, 0f),         // est,   niveau sol
					b + new Vector2(0f, hh),         // sud,   niveau sol
					b + new Vector2(-hw, 0f),        // ouest, niveau sol
				};
			}
		}
	}
}
