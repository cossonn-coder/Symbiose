// SYMBIOSE — PlantRenderer.Organs.cs
// Organes procéduraux (feuilles / fleurs / fruits) — partial de PlantRenderer.
// Portage de tools/render_structure.py §« ORGANES PROCÉDURAUX » (_draw_organs,
// validé visuellement en SVG). Extrait de PlantRenderer.cs au refactor SS⑦.
//
// Constantes et palette IDENTIQUES au prototype ; seul le hash diffère (local
// C#, pas de parité bit-à-bit requise : c'est de la décoration de vue, il faut
// juste la STABILITÉ inter-frames et inter-sessions).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		private const float LeafMaxThickCm = 1.6f; // au-delà = bois structurel, nu
		private const float LeafSpacingCm = 11f;   // une feuille tous les ~11 cm
		private const float LeafOffsetCm = 7f;     // déport latéral p/r à l'axe
		private const float LeafSizeCm = 7f;       // demi-grandeur d'une feuille
		private const int MaxFruits = 10;          // plafond anti-fouillis (proxy fleurs)
		private const float MaturiteChute = 1.3f;  // miroir MATURITE_CHUTE moteur : sur-mûr → chute
		// Brun fermenté d'un fruit sur-mûr (④) — vers quoi tire la couleur au-delà du mûr.
		private static readonly Color FruitRotten = new Color("6b4a2f");

		// Palette par espèce (= ORGAN_PALETTE du prototype) : feuille, fleur,
		// fruit vert, fruit mûr. Espèce inconnue → défaut.
		private readonly struct OrganPalette
		{
			public readonly Color Leaf, Flower, FruitUnripe, FruitRipe;
			public OrganPalette(string leaf, string flower, string unripe, string ripe)
			{
				Leaf = new Color(leaf); Flower = new Color(flower);
				FruitUnripe = new Color(unripe); FruitRipe = new Color(ripe);
			}
		}
		private static readonly System.Collections.Generic.Dictionary<string, OrganPalette>
			Palettes = new()
			{
				["Tomato"] = new OrganPalette("3f9e3a", "e8d24a", "5fae3f", "d8392a"),
				["AppleTree"] = new OrganPalette("3f8e3a", "f3e0e8", "82ae4f", "cc382e"),
			};
		private static readonly OrganPalette DefaultPalette =
			new OrganPalette("469a3f", "ead85a", "6fae45", "cf3a2e");
		private static readonly Color[] AutumnLeaves =
		{
			new Color("c9a23a"), new Color("c4762a"), new Color("a8392a"),
			new Color("b8902f"), new Color("9c5a22"),
		};
		private static readonly Color FlowerHeart = new Color("e8c63a");

		// Hash entier → [0,1) déterministe (mix multiplicatif xorshift). Remplace
		// le _hash_noise(SEED, canal, i, j) du prototype : mêmes ENTRÉES (canal,
		// index segment, index feuille) → même feuille au même endroit à chaque
		// frame ET à chaque session — zéro Random, philo #3.
		private static float Hash01(int channel, int i, int j)
		{
			uint h = (uint)channel * 0x9E3779B1u
				   ^ (uint)i * 0x85EBCA77u ^ (uint)j * 0xC2B2AE3Du;
			h ^= h >> 15; h *= 0x2C1B3C6Du;
			h ^= h >> 12; h *= 0x297A2D39u;
			h ^= h >> 15;
			return (h & 0xFFFFFF) / 16777216f;
		}

		// Couleur d'une feuille (= _leaf_color) : palette espèce + décalage
		// saisonnier — printemps clair (×1.25), été plein, automne tiré dans la
		// palette chaude au hash, hiver foncé (×0.7, atteint seulement si la
		// densité saisonnière n'est pas nulle, donc persistant).
		private static Color LeafColor(OrganPalette pal, string season, float h)
		{
			switch (season)
			{
				case "printemps": return Scaled(pal.Leaf, 1.25f);
				case "automne": return AutumnLeaves[(int)(h * AutumnLeaves.Length) % AutumnLeaves.Length];
				case "hiver": return Scaled(pal.Leaf, 0.7f);
				default: return pal.Leaf;   // été
			}
		}

		private static Color Scaled(Color c, float f) =>
			new Color(Mathf.Clamp(c.R * f, 0f, 1f), Mathf.Clamp(c.G * f, 0f, 1f),
					  Mathf.Clamp(c.B * f, 0f, 1f), c.A);

		// Un segment porte des feuilles s'il est jeune/fin (rameau) ou un apex —
		// le bois épais (tronc/charpente) reste nu (= _is_leafy).
		private static bool IsLeafy(Segment s) =>
			s.IsApex || s.ThicknessCm <= LeafMaxThickCm;

		// ---------------------------------------------------------------------------
		// ORGANES — feuilles / fleurs / fruits (t6·A, portage _draw_organs)
		// ---------------------------------------------------------------------------

		private void DrawOrgans(Vector3 collet)
		{
			string season = WorldView.CurrentSeason;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal))
				pal = DefaultPalette;

			// --- FEUILLES — densité saisonnière calculée côté Python (caduc
			// hiver → 0, on ne dessine rien). densité < 1 → SOUS-ÉCHANTILLONNAGE
			// au hash (canal 17) : un feuillage léger (0.35) garde ~1 feuille
			// sur 3, toujours LES MÊMES (stabilité inter-frames).
			float density = _structure.FoliageDensity;
			if (density > 0f)
			{
				for (int i = 0; i < _structure.Segments.Count; i++)
				{
					var s = _structure.Segments[i];
					if (!IsLeafy(s)) continue;
					int n = Mathf.Max(1, (int)(s.LengthCm / LeafSpacingCm));
					// Perpendiculaire HORIZONTALE à l'axe du rameau (plan sol) —
					// le déport latéral des feuilles, comme le prototype.
					float hmag = new Vector2(s.Dir.X, s.Dir.Y).Length();
					Vector2 perp = hmag > 1e-6f
						? new Vector2(-s.Dir.Y / hmag, s.Dir.X / hmag)
						: new Vector2(1f, 0f);
					for (int j = 0; j < n; j++)
					{
						if (Hash01(17, i, j) >= density) continue;
						float t = (j + 0.5f) / n;
						Vector3 p = s.Base + s.Dir * (s.LengthCm * t);
						float h1 = Hash01(7, i, j);
						float h2 = Hash01(11, i, j);
						float side = h1 < 0.5f ? 1f : -1f;
						float off = LeafOffsetCm * (0.5f + h2);
						float lx = p.X + perp.X * off * side;
						float ly = p.Y + perp.Y * off * side;
						float lz = p.Z + (h2 - 0.5f) * LeafOffsetCm;
						Vector2 c = Iso(lx - collet.X, ly - collet.Y, lz);
						Color col = LeafColor(pal, season, Hash01(13, i, j));
						col.A = 0.92f;
						float r = LeafSizeCm * WorldView.PxPerCmX;
						DrawEllipse(c, r * 1.15f, r * 0.65f, col);
					}
				}
			}

			// --- FLEURS — proxy saisonnier (REPRO_BY_SEASON, kickoff t6) : il
			// n'y a PAS d'état moteur de fleur, on garde le proxy. "flower" =
			// floraison de la saison, dessinée aux sites reproducteurs.
			if (_structure.Organ == "flower")
				foreach (Vector3 site in OrganSites())
					DrawFlower(Iso(site.X - collet.X, site.Y - collet.Y, site.Z), pal);

			// --- FRUITS — VRAI état moteur (plant.fruits, ③), plus le proxy : la
			// maturité (vert→mûr→brun) et la déplétion par `manger` deviennent
			// OBSERVABLES. Une espèce sans fruit moteur (herbacées) n'en montre
			// donc plus — c'est l'état réel, pas une décoration saisonnière.
			DrawFruits(collet, pal);
		}

		// Corolle de fleur = 5 pétales clairs + cœur (tailles px du prototype).
		private void DrawFlower(Vector2 c, OrganPalette pal)
		{
			for (int p = 0; p < 5; p++)
			{
				float a = Mathf.Tau * p / 5f;
				DrawCircle(c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 3.6f,
						   2.6f, pal.Flower);
			}
			DrawCircle(c, 2f, FlowerHeart);
		}

		// Fruits tracés : un disque par entrée de `_structure.Fruits`, ancré au
		// bout de son segment porteur, COULEUR ∝ maturité, TAILLE ∝ masse. Reflet
		// blanc haut-gauche comme le proxy d'avant — continuité visuelle.
		private void DrawFruits(Vector3 collet, OrganPalette pal)
		{
			foreach (var f in _structure.Fruits)
			{
				Vector3 p3 = FruitPoint(f);
				Vector2 c = Iso(p3.X - collet.X, p3.Y - collet.Y, p3.Z);
				// masse → rayon (FRUIT_MASSE=0.15 côté moteur → ~4.5 px ; borné).
				float rad = 3.0f + Mathf.Min(f.Masse, 0.3f) * 10f;
				DrawCircle(c, rad, FruitColor(pal, f.Maturite));
				DrawCircle(c - new Vector2(rad * 0.3f, rad * 0.3f),
						   rad * 0.3f, new Color(1f, 1f, 1f, 0.45f));
			}
		}

		// Couleur d'un fruit selon sa maturité : interpolation vert→mûr sur [0,1],
		// puis mûr→brun fermenté de 1.0 au seuil de chute (1.3 = MATURITE_CHUTE).
		private static Color FruitColor(OrganPalette pal, float mat)
		{
			if (mat <= 1f)
				return pal.FruitUnripe.Lerp(pal.FruitRipe, Mathf.Clamp(mat, 0f, 1f));
			float t = Mathf.Clamp((mat - 1f) / (MaturiteChute - 1f), 0f, 1f);
			return pal.FruitRipe.Lerp(FruitRotten, t);
		}

		// Point 3D (cm tuile-local) où ancrer un fruit = bout de son segment
		// porteur. `SegmentId` est un repère BEST-EFFORT (les indices glissent
		// avec la croissance, cf. moteur) → on borne à un segment valide.
		private Vector3 FruitPoint(FruitData f)
		{
			var segs = _structure.Segments;
			if (segs.Count == 0) return _structure.ColletCm;
			var s = segs[Mathf.Clamp(f.SegmentId, 0, segs.Count - 1)];
			return s.Base + s.Dir * s.LengthCm;
		}

		/// <summary>Index (= ordre du snapshot = clé `manger` moteur) du fruit le
		/// plus proche de `canvasPos`, ou −1 si la plante n'a aucun fruit. MÊME
		/// projection que DrawFruits → on cible exactement ce qu'on voit.</summary>
		public int FindFruitNear(Vector2 canvasPos)
		{
			if (_structure == null || _structure.Fruits.Count == 0) return -1;
			Vector2 local = ToLocal(canvasPos);
			Vector3 collet = _structure.ColletCm;
			int best = -1;
			float bestD = float.MaxValue;
			for (int i = 0; i < _structure.Fruits.Count; i++)
			{
				Vector3 p3 = FruitPoint(_structure.Fruits[i]);
				Vector2 c = Iso(p3.X - collet.X, p3.Y - collet.Y, p3.Z);
				float d = local.DistanceSquaredTo(c);
				if (d < bestD) { bestD = d; best = i; }
			}
			return best;
		}

		// Points 3D (cm, tuile-local) où naissent fleurs/fruits (= _organ_sites) :
		// bouts d'apex (`terminal`) ou bouts des latéraux HORS meneur (`lateral`,
		// le meneur = apex le plus haut, exclu → fructification latérale).
		// Plafonné à MaxFruits par sous-échantillonnage régulier (anti-fouillis).
		private List<Vector3> OrganSites()
		{
			var apex = new List<Segment>();
			foreach (var s in _structure.Segments)
				if (s.IsApex) apex.Add(s);
			if (apex.Count == 0) return new List<Vector3>();
			if (_structure.OrganSite == "lateral" && apex.Count > 1)
			{
				int leader = 0;
				float zMax = float.MinValue;
				for (int i = 0; i < apex.Count; i++)
				{
					float z = apex[i].Base.Z + apex[i].Dir.Z * apex[i].LengthCm;
					if (z > zMax) { zMax = z; leader = i; }
				}
				apex.RemoveAt(leader);
			}
			var tips = new List<Vector3>(apex.Count);
			foreach (var s in apex)
				tips.Add(s.Base + s.Dir * s.LengthCm);
			if (tips.Count > MaxFruits)
			{
				float step = (float)tips.Count / MaxFruits;
				var sampled = new List<Vector3>(MaxFruits);
				for (int i = 0; i < MaxFruits; i++)
					sampled.Add(tips[(int)(i * step)]);
				return sampled;
			}
			return tips;
		}

		// Ellipse pleine alignée écran (Godot n'a pas de DrawEllipse natif) :
		// petit polygone de 10 points — les feuilles se dessinent au SetStructure
		// seulement, le coût par redraw reste trivial (~10 vertices/feuille).
		private void DrawEllipse(Vector2 center, float rx, float ry, Color col)
		{
			const int n = 10;
			var pts = new Vector2[n];
			for (int i = 0; i < n; i++)
			{
				float a = Mathf.Tau * i / n;
				pts[i] = center + new Vector2(rx * Mathf.Cos(a), ry * Mathf.Sin(a));
			}
			DrawColoredPolygon(pts, col);
		}
	}
}
