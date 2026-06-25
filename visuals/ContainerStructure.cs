// SYMBIOSE — ContainerStructure.cs (sprint pots/bacs ⑥a, vue Godot)
// Le PLACEHOLDER procédural d'un CONTENEUR de culture posé par le joueur : un
// POT (tronc-cône iso, mobile) ou un BAC (caisse N×M iso, immobile). Comme les
// structures de compost (cf. CompostStructure.cs), il VIT dans la couche YSort
// des objets (`_objects`) → il s'occulte correctement en profondeur avec les
// plantes et la maison. Reconstruction pleine à chaque snapshot (la forme ne
// change pas, pas de fondu à tenir).
//
// 📖 Pédagogie — décisions tranchées (Nico, AskUserQuestion 2026-06-25) :
//  · PLACEHOLDER procédural pixel-art (pas de PNG sur la VM, cohérent SS²/D34) ;
//  · le SUBSTRAT se lit à la TEINTE de la SURFACE (le dessus du conteneur), une
//    couleur par recette puisée dans Palette16 (cohérence chromatique). Repli
//    neutre si la clé de substrat est inconnue (lecture tolérante du snapshot).
// La hauteur (Z) projette toujours en vertical écran (comme la maison/les
// plantes) ; l'empreinte au sol, elle, tourne avec la vue (WorldToScreenOffset)
// → le placeholder reste cohérent sous les 4 orientations.
//
// Ce placeholder est de la VUE PURE : aucune logique métier (effet nain, couplage
// fond ouvert…) n'est CALCULÉE ici — le moteur Python l'a déjà résolue (height_cm
// réduit, drainage, couplage arrivent dans le snapshot). On ne fait que LIRE et
// DESSINER.
//
// 📖 Pédagogie ⑥c — INDICES DIÉGÉTIQUES du couplage (philo #5 : indices visuels,
// pas de chiffres). Deux faits écologiques que le moteur simule déjà reçoivent
// une marque DISCRÈTE sur le placeholder (aucun recalcul, on SIGNALE la cause) :
//  · A. FOND OUVERT vs FERMÉ — un bac `fond_ouvert` communique avec le sol (⑤) :
//    on dessine de fines RACINES qui débordent sous la caisse vers la tuile.
//    Le pot (ou un bac fermé) reçoit un FOND PLEIN (liseré d'arête bas continu).
//  · B. EFFET NAIN — un petit volume confiné (root-bound, calculé en amont par
//    la vue à partir de volume + fond_ouvert + présence de plante) reçoit des
//    RACINES TASSÉES affleurant la lèvre du pot. Grand volume / bac couplé (nain
//    levé) → pas de marque. L'indice suggère la cause, il ne l'explique pas (#6).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class ContainerStructure : Node2D
	{
		// --- Géométrie placeholder (cm, calibrage post-F5 par ces SEULES const) ---
		// Demi-empreinte d'un POT : il occupe le cœur d'un plot (50 cm) sans déborder.
		private const float PotHalfCm = 16f;
		// Demi-empreinte d'une cellule de BAC (en cm autour du centre de chaque plot).
		private const float BacCellHalfCm = 22f;
		// Hauteur de la paroi d'un BAC (extrudée vers le haut de l'écran).
		private const float BacWallCm = 28f;
		// Hauteur d'un POT à volume de RÉFÉRENCE (75 L ≈ pleine terre, cf. moteur
		// VOLUME_REF). La hauteur dessinée croît mollement avec le volume (racine)
		// pour qu'un grand pot reste lisible sans écraser l'écran.
		private const float PotHeightRefCm = 30f;
		private const float PotVolumeRefL  = 75f;

		// --- Teintes du conteneur (terre cuite du pot, bois clair du bac) ---------
		private static readonly Color PotTerreCuite = new Color("b5703f"); // flanc du pot
		private static readonly Color PotOmbre      = new Color("8a4f28"); // flanc à l'ombre
		private static readonly Color PotArete      = new Color("5e3318"); // arêtes sombres
		private static readonly Color BacBoisClair  = new Color("9a6f44"); // planches (≡ compost)
		private static readonly Color BacBoisOmbre  = new Color("6f4d2c");
		private static readonly Color BacArete      = new Color("523619");
		// Racines de l'indice de couplage : pâle (débordent du fond, ⑥c.A) et
		// brun-roux tassées (root-bound au bord du pot, ⑥c.B).
		private static readonly Color RacineFond   = new Color("c9b48a"); // chevelu pâle vers le sol
		private static readonly Color RacineTassee = new Color("a07a4a"); // racines serrées au bord

		// --- Teinte de SUBSTRAT (surface) par recette (CONCEPTION §2) -------------
		// Une couleur de surface par clé de substrat du registre Python
		// (world/substrat.py). Repli neutre `SolInconnu` si la clé est absente
		// (lecture tolérante : un snapshot futur peut nommer un substrat inconnu).
		private static readonly Dictionary<string, Color> SubstratTeinte = new()
		{
			["terreau"]      = new Color("4a3526"), // terreau brun foncé, riche
			["compost"]      = new Color("3c2c1c"), // compost très sombre, humifié
			// ⑥c — clé alignée sur le registre moteur (world/substrat.py :
			// "drainant_mineral", pas "drainant") → la teinte s'applique vraiment.
			["drainant_mineral"] = new Color("9a9486"), // mélange drainant gris clair (sable/pouzzolane)
			["lasagnes"]     = new Color("5b4a2e"), // strates brun-olive (litière en couches)
			["terre_jardin"] = Palette16.SolTerre,  // terre du jardin (même teinte que le sol)
			["mycelium_use"] = new Color("c8bda6"), // substrat de champignon clair (paille colonisée)
		};

		private readonly string _kind;     // "pot" | "bac"
		private readonly string _substrat; // clé de recette
		private readonly float _volume;    // litres (pilote la hauteur du pot)
		private readonly int _rows, _cols; // géométrie du mini-sol (bac N×M)
		private readonly bool _fondOuvert; // ⑥c.A : communique avec la tuile dessous
		private readonly bool _rootBound;  // ⑥c.B : nain non levé (petit volume confiné)

		public ContainerStructure(string kind, string substrat, float volume,
								  int rows, int cols,
								  bool fondOuvert = false, bool rootBound = false)
		{
			_kind = kind;
			_substrat = substrat;
			_volume = volume;
			_rows = Mathf.Max(1, rows);
			_cols = Mathf.Max(1, cols);
			_fondOuvert = fondOuvert;
			_rootBound = rootBound;
		}

		// Teinte de surface du substrat (repli neutre si clé inconnue).
		private Color Surface()
		{
			return SubstratTeinte.TryGetValue(_substrat, out var col)
				? col : Palette16.SolInconnu;
		}

		// Les 4 coins d'une empreinte carrée (demi-côté halfCm) projetés en OFFSET
		// (vecteur) autour d'un CENTRE déjà projeté — tournent avec la vue. Ordre
		// nw→ne→se→sw (identique à CompostStructure.Footprint, mais recentrable).
		private static Vector2[] Footprint(Vector2 center, float halfCm)
		{
			return new[]
			{
				center + WorldView.WorldToScreenOffset(-halfCm, -halfCm),
				center + WorldView.WorldToScreenOffset( halfCm, -halfCm),
				center + WorldView.WorldToScreenOffset( halfCm,  halfCm),
				center + WorldView.WorldToScreenOffset(-halfCm,  halfCm),
			};
		}

		public override void _Draw()
		{
			if (_kind == "bac") DrawBac();
			else DrawPot();
		}

		// POT : tronc-cône iso (la base plus ÉTROITE que la surface, comme un pot
		// de fleurs évasé). On dessine la base, on extrude vers le haut, on évase la
		// lèvre, puis on remplit la surface de la teinte de substrat. Empreinte 1 plot.
		private void DrawPot()
		{
			// Hauteur ∝ √(volume/ref) : croissance molle (un pot de 200 L n'est pas
			// 2,7× plus haut qu'un 75 L mais ~1,6×). Plancher pour rester visible.
			float h = PotHeightRefCm * Mathf.Sqrt(Mathf.Max(0.05f, _volume / PotVolumeRefL));
			Vector2 up = new Vector2(0f, -h * WorldView.PxPerCmZ);

			// Base étroite (au sol) et lèvre évasée (au sommet) : deux empreintes
			// concentriques de demi-côté différent → silhouette de tronc-cône.
			Vector2[] baseR = Footprint(Vector2.Zero, PotHalfCm * 0.72f);
			Vector2[] lipR  = Footprint(up, PotHalfCm);

			// Coin avant (le plus bas à l'écran) = ses 2 faces sont visibles.
			int front = 0;
			for (int i = 1; i < 4; i++) if (lipR[i].Y > lipR[front].Y) front = i;
			int right = (front + 3) % 4, left = front;

			foreach (int w in new[] { right, left })
			{
				var face = new[] { baseR[w], baseR[(w + 1) % 4],
								   lipR[(w + 1) % 4], lipR[w] };
				DrawColoredPolygon(face, w == left ? PotTerreCuite : PotOmbre);
				DrawPolyline(new[] { baseR[w], lipR[w], lipR[(w + 1) % 4] },
							 PotArete, 1.5f);
			}
			// Surface (le dessus du pot) = teinte de substrat, lue d'en haut.
			DrawColoredPolygon(lipR, Surface());
			DrawPolyline(new[] { lipR[0], lipR[1], lipR[2], lipR[3], lipR[0] },
						 PotArete, 1.5f);

			// ⑥c.B — indice « effet nain » : si la plante est root-bound (petit
			// volume, fond fermé), de courtes racines TASSÉES affleurent la lèvre
			// avant. Le pot est toujours fond FERMÉ → pas de racine vers le sol.
			if (_rootBound)
				DrawRootBoundFringe(new[] { lipR[front], lipR[(front + 1) % 4] });
		}

		// Racines tassées (⑥c.B) : un court chevelu vertical le long de l'arête
		// avant de la lèvre, signe d'un système racinaire à l'étroit (root-bound).
		// Discret : 3 brins de 5 cm vers le bas, brun-roux.
		private void DrawRootBoundFringe(Vector2[] frontEdge)
		{
			Vector2 down = new Vector2(0f, 5f * WorldView.PxPerCmZ);
			for (int i = 0; i <= 3; i++)
			{
				Vector2 a = frontEdge[0].Lerp(frontEdge[1], i / 3f);
				DrawLine(a, a + down, RacineTassee, 1.2f);
			}
		}

		// BAC : caisse N×M iso. On dessine chaque cellule du mini-sol comme un
		// caisson (faces avant + surface de substrat) ; le tout couvre cols×rows
		// plots. Mêmes 2 faces avant + dessus que DrawBac de CompostStructure.
		private void DrawBac()
		{
			Vector2 up = new Vector2(0f, -BacWallCm * WorldView.PxPerCmZ);
			Color surface = Surface();
			// On parcourt les cellules du plus LOIN au plus PROCHE pour que les
			// caissons avant se peignent par-dessus (tri en profondeur grossier au
			// sein du nœud ; le YSort global gère le tri avec plantes/maison).
			var cells = new List<(int R, int C, Vector2 Center)>();
			for (int r = 0; r < _rows; r++)
				for (int c = 0; c < _cols; c++)
				{
					// Centre de la cellule (r,c) en OFFSET monde depuis le coin du bac.
					// Le conteneur est ancré à son centre → on décale de la demi-grille.
					float dx = (c + 0.5f) * WorldView.PlotCm - _cols * WorldView.PlotCm / 2f;
					float dy = (r + 0.5f) * WorldView.PlotCm - _rows * WorldView.PlotCm / 2f;
					cells.Add((r, c, WorldView.WorldToScreenOffset(dx, dy)));
				}
			cells.Sort((a, b) => a.Center.Y.CompareTo(b.Center.Y)); // loin → proche

			Vector2[] frontEdge = null;   // arête basse avant de la cellule la PLUS proche
			foreach (var (r, c, center) in cells)
			{
				Vector2[] g = Footprint(center, BacCellHalfCm);
				Vector2[] top = { g[0] + up, g[1] + up, g[2] + up, g[3] + up };
				int front = 0;
				for (int i = 1; i < 4; i++) if (g[i].Y > g[front].Y) front = i;
				int right = (front + 3) % 4, left = front;

				// Surface de substrat (dessus de la caisse, vue d'en haut).
				DrawColoredPolygon(top, surface);

				foreach (int w in new[] { right, left })
				{
					var face = new[] { g[w], g[(w + 1) % 4],
									   top[(w + 1) % 4], top[w] };
					DrawColoredPolygon(face, w == left ? BacBoisClair : BacBoisOmbre);
					DrawPolyline(new[] { g[w], top[w], top[(w + 1) % 4] },
								 BacArete, 1.5f);
				}
				DrawPolyline(new[] { top[0], top[1], top[2], top[3], top[0] },
							 BacArete, 1.5f);
				// La dernière cellule peinte (tri loin→proche) est la plus AVANT :
				// on retient son arête basse pour l'indice de fond (⑥c.A).
				frontEdge = new[] { g[(front + 3) % 4], g[front], g[(front + 1) % 4] };
			}

			// ⑥c.A — indice « fond ouvert / fermé » sur l'arête avant la plus proche.
			if (frontEdge != null)
			{
				if (_fondOuvert) DrawOpenBottomRoots(frontEdge);
				else DrawClosedBottom(frontEdge);
			}
		}

		// ⑥c.A — FOND OUVERT : de fines racines pâles débordent sous l'arête avant
		// du bac vers la tuile (le bac couplé communique avec le sol, ⑤). Quelques
		// brins de longueurs irrégulières (déterministes : modulés par l'index).
		private void DrawOpenBottomRoots(Vector2[] frontEdge)
		{
			for (int i = 0; i <= 6; i++)
			{
				Vector2 a = frontEdge[0].Lerp(frontEdge[2], i / 6f);
				float len = 6f + (i % 3) * 3f;   // 6/9/12 cm, motif déterministe
				DrawLine(a, a + new Vector2(0f, len * WorldView.PxPerCmZ),
						 RacineFond, 1.1f);
			}
		}

		// ⑥c.A — FOND FERMÉ : un liseré d'arête bas PLEIN et continu (le pot/bac
		// fermé retient — aucune racine ne descend vers le sol).
		private void DrawClosedBottom(Vector2[] frontEdge)
		{
			DrawPolyline(frontEdge, BacArete, 2.4f);
		}
	}
}
