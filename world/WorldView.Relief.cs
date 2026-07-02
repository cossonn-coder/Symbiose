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
		// Facteur d'exagération visuelle du relief (F5-tunable). 1.0 = échelle
		// physique (1 cm de sol → PxPerCmZ px) ; >1 pour rendre lisibles les
		// premiers millimètres d'humus. Un sol mûr (~20 cm, EPAISSEUR_NORM_REF)
		// fait alors ~20·PxPerCmZ·facteur px de relief.
		private const float ReliefExaggeration = 2.0f;

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
		// vérité »). Épaisseur du plot (tuile, r, c) → px de relief. 0 si le champ
		// n'est pas encore connu ou hors grille → repli plat (tolérance pré-0.5.16).
		private float EpaisseurPxAt(string tile, int r, int c)
		{
			if (_epaisseurCm == null || !_epaisseurCm.TryGetValue(tile, out var g))
				return 0f;
			if (r < 0 || r >= g.GetLength(0) || c < 0 || c >= g.GetLength(1))
				return 0f;
			return g[r, c] * PxPerCmZ * ReliefExaggeration;
		}

		// Recalage d'un objet enraciné : de combien remonter (px) un objet posé à
		// la position LOCALE (lx, ly) cm dans `tile`. Résout le plot-foyer
		// (floor(/PlotCm)), comme le moteur. Partie C — même conversion que le sol.
		private float ReliefRisePx(string tile, float lxCm, float lyCm)
			=> EpaisseurPxAt(tile, (int)(lyCm / PlotCm), (int)(lxCm / PlotCm));

		// Lit le bloc `epaisseur` du snapshot (grille 2D dense par tuile, cm) et
		// remonte le relief. Tolérant : bloc absent (binaire pré-0.5.16) → relief
		// laissé plat, aucun crash. Appelé par ApplySnapshot.
		private void ApplyEpaisseur(Godot.Collections.Dictionary epaisseur)
		{
			_epaisseurCm = new Dictionary<string, float[,]>();
			foreach (var kv in epaisseur)
			{
				var rows = kv.Value.AsGodotArray();
				int nr = rows.Count;
				if (nr == 0) { _epaisseurCm[kv.Key.AsString()] = new float[0, 0]; continue; }
				int nc = rows[0].AsGodotArray().Count;
				var grid = new float[nr, nc];
				for (int r = 0; r < nr; r++)
				{
					var row = rows[r].AsGodotArray();
					for (int c = 0; c < nc && c < row.Count; c++)
						grid[r, c] = (float)row[c].AsDouble();
				}
				_epaisseurCm[kv.Key.AsString()] = grid;
			}
			UpdateRelief();
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
