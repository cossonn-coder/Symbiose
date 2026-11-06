// SYMBIOSE — PlantRenderer.FruitsArbre.cs (partial, sprint VERGER VIVANT ④)
// Les FRUITS D'UN ARBRE, par cohortes. Depuis le pont 0.6.9 (③), une entrée de `fruits` est une
// cohorte : `nombre` fruits nés ensemble sur un segment, de même maturité. Un cerisier en porte
// ~2 000 en 25 à 38 cohortes. La vue en dessine le nombre, plafonné pour la cuisson, en grappes
// réparties sur les brindilles du segment porteur, et le clic `manger` relit ces mêmes points.
//
// 📖 Pédagogie — pourquoi un PLAFOND proportionnel. Dessiner 2 000 cerises coûterait 2 000 globes
// par pose de vent. On garde la proportion entre cohortes (chacune garde au moins un fruit) et on
// réduit le tout à `FruitsArbreMax` : comme un sous-échantillonnage d'un signal, la forme reste,
// le débit baisse. Les points sont mémoïsés sur la référence du snapshot (clé auto-invalidante,
// comme les rameaux) : le dessin et le clic ne les recalculent pas.
//
// 📖 Pourquoi la taille vient de la FICHE et pas de la masse. Depuis ③, `masse` est celle d'UN fruit
// d'espèce (cerise 0,005, pomme 0,09) : rapportée à la masse nominale 0,15 des herbacées, une
// cerise tombait au pixel plancher. Un arbre à fiche prend le diamètre de sa fiche, qui grossit
// avec la maturité (nouaison à ~45 %) ; la masse ne sert plus qu'aux espèces sans fiche.
//
// Zéro Random (philo #3) : tout au hash de la clé stable du segment ; canaux 545, 563-569.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Plafond de dessin par arbre [choix, mesuré au bilan ④] : au-delà, la proportion est gardée.
		private const int FruitsArbreMax = 500;
		private const float FruitPenduCm = 1f;
		private const float FruitNoueTaille = 0.45f;   // rayon à la nouaison, part du rayon mûr
		private const float FruitEcartCm = 1.6f;       // écart des fruits d'une grappe autour du point d'attache
		// La fiche : pomme 6-8 cm, cerise 2 cm, figue 4-8 cm, noix ~4,5 cm de diamètre [odg].
		private static readonly Dictionary<string, FicheFruit> FruitsArbres = new()
		{
			["AppleTree"] = new(3.5f), ["CherryTree"] = new(1f), ["Fig"] = new(3f), ["WalnutTree"] = new(2.2f),
		};
		// Grappe : fruits au plus par point d'attache ; queue : longueur du pédoncule, en cm [odg].
		// Cerises par 2 ou 3 sur de longues queues, pommes par 1 ou 2, figue seule, noix par 1 ou 2.
		private static readonly Dictionary<string, (int Grappe, float QueueCm)> GrappesFruits = new()
		{
			["CherryTree"] = (3, 4f), ["AppleTree"] = (2, 2f), ["Fig"] = (1, 0.5f), ["WalnutTree"] = (2, 0.5f),
		};

		/// <summary>Un fruit dessiné : sa cohorte (index moteur, clé de `manger`), son point, son attache.</summary>
		private readonly record struct FruitPose(int Cohorte, Vector3 P, Vector3 Attache);

		private readonly List<FruitPose> _fruitsPoses = new();
		private readonly Dictionary<int, List<(int Rang, Vector3 B)>> _attachesParCle = new();
		private PlantStructure _fruitsPosesDe;
		private Vector2 _fruitsPosesAxe;

		private FicheFruit FicheFruitArbre =>
			FruitsArbres.TryGetValue(_structure.SpeciesName, out var f) ? f : FruitParDefaut;

		/// <summary>Combien de fruits dessiner pour une cohorte : sa part du plafond, au moins un.</summary>
		private static int FruitsDessines(int nombre, float garde) => Mathf.Max(1, Mathf.RoundToInt(nombre * garde));

		// Les fruits à dessiner, du premier de la cohorte 0 au dernier de la dernière. Reconstruits si
		// le snapshot ou la rotation D35 changent (mêmes clés que BoisDuHouppier).
		private List<FruitPose> FruitsPoses()
		{
			Vector2 axe = WorldView.WorldToScreenOffset(1f, 1f);
			if (_fruitsPosesDe == _structure && _fruitsPosesAxe == axe) return _fruitsPoses;
			_fruitsPosesDe = _structure;
			_fruitsPosesAxe = axe;
			_fruitsPoses.Clear();
			var fruits = _structure.Fruits;
			var segs = _structure.Segments;
			if (fruits.Count == 0 || segs.Count == 0) return _fruitsPoses;

			// Les bouts de brindille de chaque segment : là où pendent les fruits. Rangés par rang,
			// pas par profondeur : une rotation de vue ne déplace aucun fruit.
			foreach (var l in _attachesParCle.Values) l.Clear();
			foreach (var e in BoisDuHouppier())
			{
				if (e.EstRameau) continue;
				if (!_attachesParCle.TryGetValue(e.Cle, out var l)) _attachesParCle[e.Cle] = l = new();
				l.Add((e.Rang, e.B));
			}
			foreach (var l in _attachesParCle.Values) l.Sort(static (a, b) => a.Rang.CompareTo(b.Rang));
			int total = 0;
			foreach (var f in fruits) total += f.Nombre;
			float garde = Mathf.Min(1f, FruitsArbreMax / (float)Mathf.Max(total, 1));
			if (!GrappesFruits.TryGetValue(_structure.SpeciesName, out var grappe)) grappe = (1, 1f);

			for (int i = 0; i < fruits.Count; i++)
			{
				int id = Mathf.Clamp(fruits[i].SegmentId, 0, segs.Count - 1), rang = 0;
				for (int k = 0; k < i; k++)
					if (Mathf.Clamp(fruits[k].SegmentId, 0, segs.Count - 1) == id) rang++;
				Segment s = segs[id];
				int cle = CleSegment(s);
				_attachesParCle.TryGetValue(cle, out var attaches);
				int nb = attaches?.Count ?? 0;
				int depart = (int)(Hash01(545, cle, rang) * Mathf.Max(nb, 1)) + rang * 3;
				int n = FruitsDessines(fruits[i].Nombre, garde);
				for (int k = 0; k < n; k++)
				{
					int g = k / grappe.Grappe, j = k % grappe.Grappe, h = rang * 4096 + g;
					// Grappe suivante sur la brindille suivante ; au-delà, un peu plus loin sur la même.
					Vector3 attache = nb == 0 ? s.Base + s.Dir * s.LengthCm
						: attaches[(depart + g) % nb].B - new Vector3(0f, 0f, (g / nb) * 3f * Hash01(563, cle, h));
					float a = Mathf.Tau * (j / (float)grappe.Grappe + Hash01(565, cle, h));
					float ecart = grappe.Grappe == 1 ? 0f : FruitEcartCm * Mathf.Lerp(0.6f, 1f, Hash01(567, cle, h * 4 + j));
					float queue = FruitPenduCm + grappe.QueueCm * Mathf.Lerp(0.7f, 1f, Hash01(569, cle, h * 4 + j));
					_fruitsPoses.Add(new FruitPose(i, attache + new Vector3(ecart * Mathf.Cos(a), ecart * Mathf.Sin(a), -queue), attache));
				}
			}
			return _fruitsPoses;
		}

		// Le point du PREMIER fruit dessiné de la cohorte `i` : le banc de cueillette (-C) y clique.
		private Vector3 PointFruitArbre(int i)
		{
			foreach (var p in FruitsPoses())
				if (p.Cohorte == i) return p.P;
			return _structure.ColletCm;
		}

		/// <summary>Rayon d'un fruit d'arbre en px canvas : fiche × maturité ; espèce sans fiche : la masse.</summary>
		private float RayonFruitArbre(FicheFruit fr, in FruitData f) =>
			FruitsArbres.ContainsKey(_structure.SpeciesName)
				? Mathf.Max(fr.RayonCm * WorldView.PxPerCmX * Mathf.Lerp(FruitNoueTaille, 1f, Mathf.Clamp(f.Maturite, 0f, 1f)), PixelInterne)
				: RayonFruit(fr, f.Masse);

		/// <summary>Fruits d'un arbre, à leur taille en cm, à tous les paliers : au moins un point à ×1.
		/// Dès ×8, la queue de chaque fruit relie la grappe à sa brindille.</summary>
		private void DrawFruitsHouppier()
		{
			if (_structure.Fruits.Count == 0) return;
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			FicheFruit fr = FicheFruitArbre;
			Vector3 c = _structure.ColletCm;
			bool queues = AuPalier(PalierOrganesZoom);
			Color queue = Ton(pal.Leaf, 1);
			_lotPrairie ??= new LotTriangles();
			_lotPrairie.Vider();
			var poses = FruitsPoses();
			for (int k = 0; k < poses.Count; k++)
			{
				var p = poses[k];
				var f = _structure.Fruits[p.Cohorte];
				Vector2 pos = Iso(p.P.X - c.X, p.P.Y - c.Y, p.P.Z);
				if (queues) _lotPrairie.Ligne(Iso(p.Attache.X - c.X, p.Attache.Y - c.Y, p.Attache.Z), pos, queue, PixelInterne);
				PoserFruit(pos, RayonFruitArbre(fr, f), fr.Allonge, FruitColor(pal, f.Maturite), k);
			}
			_lotPrairie.DessinerSansMaille(this);
		}

		/// <summary>Cohorte du fruit dessiné le plus proche de `local` (px canvas locaux), et sa distance².</summary>
		private int FruitArbreProche(Vector2 local, out float d2, out float rayon)
		{
			int best = -1;
			d2 = float.MaxValue;
			rayon = 0f;
			Vector3 c = _structure.ColletCm;
			FicheFruit fr = FicheFruitArbre;
			foreach (var p in FruitsPoses())
			{
				float d = local.DistanceSquaredTo(Iso(p.P.X - c.X, p.P.Y - c.Y, p.P.Z));
				if (d >= d2) continue;
				d2 = d;
				best = p.Cohorte;
				rayon = RayonFruitArbre(fr, _structure.Fruits[p.Cohorte]) * fr.Allonge;
			}
			return best;
		}

		/// <summary>Comme DistanceFruitPort, sur les fruits dessinés d'un arbre.</summary>
		private float DistanceFruitArbre(Vector2 canvasPos)
		{
			if (_structure.Fruits.Count == 0) return float.PositiveInfinity;
			if (FruitArbreProche(ToLocal(canvasPos), out float d2, out float r) < 0) return float.PositiveInfinity;
			float tol = Mathf.Max(ToleranceFruitPx / WorldView.CurrentZoom, r);
			return d2 <= tol * tol ? d2 : float.PositiveInfinity;
		}
	}
}
