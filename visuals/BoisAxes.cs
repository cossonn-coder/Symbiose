// SYMBIOSE — BoisAxes.cs (sprint BOIS & ARBRES ① — axes et tube lissé)
// LA GÉOMÉTRIE UNIQUE DU BOIS : à partir des segments du moteur (40-50 cm, la charpente),
// relie chaque segment à son porteur (`Segment.Parent`) en AXES, puis fait passer par TOUS
// les nœuds une courbe lisse. Le dessin du tube (PlantRenderer.Tube.cs) ET tous les lecteurs
// de la géométrie (rameaux dérivés, feuilles, fruits, clic, sécateur, surbrillance, neige)
// lisent CE fichier : un fruit ne flotte jamais à côté de sa branche, la coupe tombe où l'on vise.
//
// Indépendant de PlantRenderer (aucun champ de rendu, aucune projection) : du 3D en cm, repère
// de la tuile, comme `Segment`. Zéro Random : même structure → mêmes axes, octet pour octet.
//
// 📖 Pédagogie — trois idées.
//  1. AXE. À chaque nœud, le bois « continue » sur l'enfant le plus ALIGNÉ (à égalité : le plus
//     épais, puis le plus petit index) ; les autres enfants ouvrent un axe neuf (une branche).
//     Un tronc = un axe, une charpentière = un axe : c'est ce qui se dessine d'un seul tenant.
//  2. COURBE. Catmull-Rom CENTRIPÈTE (Barry & Goldman) : passe exactement par chaque nœud, ne fait
//     ni boucle ni dépassement sur les coudes serrés (la variante « uniforme » boucle). Aux bouts
//     d'un axe on prolonge en ligne droite (point miroir) → pas d'invention de courbure.
//  3. MÉMOÏSATION par RÉFÉRENCE de la structure (ConditionalWeakTable) : un nouveau snapshot = une
//     nouvelle PlantStructure = une clé neuve ; l'ancienne table part avec le ramasse-miettes. Le
//     pinceau de cuisson partage la même référence que la plante du monde → calcul fait UNE fois.
//     Comme une table dérivée en embarqué : reconstruite quand la source change, jamais par image.

using Godot;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

namespace Symbiose
{
	public sealed class BoisAxes
	{
		/// <summary>Un morceau de tube = le segment `Index` échantillonné le long de la courbe
		/// (points en cm, largeur en cm d'épaisseur, `V` = longueur d'arc en cm depuis la base de
		/// l'axe — la coordonnée de texture du ②). `Axe` = n° d'axe, `RangAxe` = rang dans l'axe.</summary>
		public sealed class Morceau
		{
			public int Index, Axe, RangAxe;
			public Vector3[] Points;
			public float[] LargeurCm;
			public float[] V;
		}

		// Échantillonnage : un point tous les ~5 cm de bois (un segment de 45 cm = 9 pas), borné.
		private const float PasCm = 5f;
		private const int PasMax = 12;
		// Bout d'un axe sans suite (apex, coupe) : il s'affine un peu au lieu de finir carré.
		private const float AffinementBout = 0.75f;
		// Pied (empattement) du tronc : évasé sur max(PiedMinCm, PiedParEpaisseur × épaisseur).
		private const float PiedEvase = 0.8f, PiedMinCm = 6f, PiedParEpaisseur = 2f, PiedSolCm = 1f;
		// Col de branche : l'axe enfant naît DANS le porteur (à mi-rayon) et s'y renfle.
		private const float ColRenfle = 0.45f, ColEntreeRayon = 0.5f;

		private static readonly ConditionalWeakTable<PlantStructure, BoisAxes> _memo = new();

		/// <summary>Les axes de `ps` (mémoïsés par référence : jamais recalculés pour la même structure).</summary>
		public static BoisAxes De(PlantStructure ps) => _memo.GetValue(ps, static p => new BoisAxes(p.Segments));

		private readonly List<Segment> _segs;
		private readonly int[] _prec, _suiv;
		private readonly Dictionary<Segment, int> _index = new();
		/// <summary>Morceaux[i] = le tube du segment i (même ordre que la structure).</summary>
		public readonly Morceau[] Morceaux;

		private BoisAxes(List<Segment> segs)
		{
			_segs = segs;
			int n = segs.Count;
			_prec = new int[n];
			_suiv = new int[n];
			System.Array.Fill(_prec, -1);
			System.Array.Fill(_suiv, -1);
			Morceaux = new Morceau[n];
			for (int i = 0; i < n; i++) _index.TryAdd(segs[i], i);
			ChoisirSuites();
			ConstruireMorceaux();
		}

		/// <summary>Index d'un segment de la structure (−1 s'il n'en fait pas partie).</summary>
		public int IndexDe(in Segment s) => _index.TryGetValue(s, out int i) ? i : -1;

		/// <summary>Le segment porteur valide de `i` (−1 = racine : collet, parent hors liste, ou
		/// flux sans `parent`).</summary>
		private int Porteur(int i)
		{
			int p = _segs[i].Parent;
			return p >= 0 && p < _segs.Count && p != i ? p : -1;
		}

		// Pour chaque nœud, la suite de l'axe : l'enfant le plus aligné, puis le plus épais, puis le
		// plus petit index (ordre total → déterministe).
		private void ChoisirSuites()
		{
			for (int c = 0; c < _segs.Count; c++)
			{
				int p = Porteur(c);
				if (p < 0) continue;
				int a = _suiv[p];
				if (a < 0 || Meilleur(p, c, a)) _suiv[p] = c;
			}
			for (int p = 0; p < _segs.Count; p++)
				if (_suiv[p] >= 0) _prec[_suiv[p]] = p;
		}

		private bool Meilleur(int p, int c, int a)
		{
			float dc = _segs[p].Dir.Dot(_segs[c].Dir), da = _segs[p].Dir.Dot(_segs[a].Dir);
			if (Mathf.Abs(dc - da) > 1e-4f) return dc > da;
			float tc = _segs[c].ThicknessCm, ta = _segs[a].ThicknessCm;
			if (Mathf.Abs(tc - ta) > 1e-4f) return tc > ta;
			return c < a;
		}

		private static Vector3 Bout(in Segment s) => s.Base + s.Dir * s.LengthCm;

		/// <summary>LE point du bois : segment `i`, `t` ∈ [0,1] de sa base à son bout, sur la COURBE.
		/// t = 0 et t = 1 sont les nœuds du moteur, exactement.</summary>
		public Vector3 Point(int i, float t)
		{
			var s = _segs[i];
			Vector3 p1 = s.Base, p2 = Bout(s);
			if (p1.DistanceSquaredTo(p2) < 1e-8f) return p1;
			Vector3 p0 = _prec[i] >= 0 ? _segs[_prec[i]].Base : p1 * 2f - p2;
			Vector3 p3 = _suiv[i] >= 0 ? Bout(_segs[_suiv[i]]) : p2 * 2f - p1;
			return CatmullRom(p0, p1, p2, p3, Mathf.Clamp(t, 0f, 1f));
		}

		/// <summary>Le point du segment `s` (même règle que `Point`) ; repli segment droit si `s`
		/// n'appartient pas à la structure.</summary>
		public Vector3 PointDe(in Segment s, float t)
		{
			int i = IndexDe(s);
			return i >= 0 ? Point(i, t) : s.Base + s.Dir * (s.LengthCm * t);
		}

		// Épaisseur continue le long d'un axe : de celle du segment à celle de sa suite (sans marche).
		private float Epaisseur(int i, float t)
		{
			float e0 = _segs[i].ThicknessCm;
			float e1 = _suiv[i] >= 0 ? _segs[_suiv[i]].ThicknessCm : e0 * AffinementBout;
			return Mathf.Lerp(e0, e1, t);
		}

		// Catmull-Rom centripète (α = ½), forme de Barry & Goldman : pyramide d'interpolations.
		private static Vector3 CatmullRom(Vector3 p0, Vector3 p1, Vector3 p2, Vector3 p3, float u)
		{
			float t0 = 0f;
			float t1 = t0 + Noeud(p0, p1);
			float t2 = t1 + Noeud(p1, p2);
			float t3 = t2 + Noeud(p2, p3);
			float t = Mathf.Lerp(t1, t2, u);
			Vector3 a1 = Mix(p0, p1, t0, t1, t), a2 = Mix(p1, p2, t1, t2, t), a3 = Mix(p2, p3, t2, t3, t);
			Vector3 b1 = Mix(a1, a2, t0, t2, t), b2 = Mix(a2, a3, t1, t3, t);
			return Mix(b1, b2, t1, t2, t);
		}

		private static float Noeud(Vector3 a, Vector3 b) => Mathf.Max(Mathf.Sqrt(a.DistanceTo(b)), 1e-3f);

		private static Vector3 Mix(Vector3 a, Vector3 b, float ta, float tb, float t) =>
			a * ((tb - t) / (tb - ta)) + b * ((t - ta) / (tb - ta));

		// Axes : chaque segment sans précédent ouvre un axe (ordre des index → n° d'axe stable),
		// qu'on suit de suite en suite en cumulant la longueur d'arc.
		private void ConstruireMorceaux()
		{
			int axe = 0;
			for (int r = 0; r < _segs.Count; r++)
			{
				if (_prec[r] >= 0) continue;
				float v = 0f;
				int rang = 0;
				for (int i = r; i >= 0; i = _suiv[i], rang++)
					Morceaux[i] = Echantillonner(i, axe, rang, ref v);
				axe++;
			}
			// Garde-fou : un cycle de parents (flux incohérent) n'a pas de racine → ses segments
			// deviennent chacun un axe isolé plutôt qu'un trou.
			for (int i = 0; i < _segs.Count; i++)
			{
				if (Morceaux[i] != null) continue;
				_prec[i] = _suiv[i] = -1;
				float v = 0f;
				Morceaux[i] = Echantillonner(i, axe++, 0, ref v);
			}
		}

		private Morceau Echantillonner(int i, int axe, int rang, ref float v)
		{
			var s = _segs[i];
			int n = Mathf.Clamp(Mathf.CeilToInt(s.LengthCm / PasCm), 1, PasMax);
			bool col = rang == 0 && Porteur(i) >= 0;
			int k0 = col ? 1 : 0;
			var m = new Morceau
			{
				Index = i, Axe = axe, RangAxe = rang,
				Points = new Vector3[n + 1 + k0], LargeurCm = new float[n + 1 + k0], V = new float[n + 1 + k0],
			};
			if (col)
			{
				// Entrée du col : à mi-rayon du porteur, en arrière le long de la tangente de départ.
				float r = _segs[Porteur(i)].ThicknessCm * 0.5f * ColEntreeRayon;
				Vector3 tan = (Point(i, Mathf.Min(1f, 0.1f)) - s.Base).Normalized();
				if (tan == Vector3.Zero) tan = s.Dir;
				m.Points[0] = s.Base - tan * r;
				m.V[0] = v;
				v += r;
			}
			for (int k = 0; k <= n; k++)
			{
				int j = k + k0;
				m.Points[j] = Point(i, k / (float)n);
				if (k > 0) v += m.Points[j].DistanceTo(m.Points[j - 1]);   // k = 0 : nœud (col déjà compté)
				m.V[j] = v;
			}
			for (int j = 0; j < m.Points.Length; j++)
			{
				float t = Mathf.Clamp((j - k0) / (float)n, 0f, 1f);
				m.LargeurCm[j] = Epaisseur(i, t) * Evasement(i, rang, m.V[j], col ? m.V[0] : 0f);
			}
			return m;
		}

		// Pied évasé (racine posée au sol) et col de branche (premier morceau d'un axe enfant) :
		// renflement qui retombe en douceur (carré de la distance) sur sa longueur.
		private float Evasement(int i, int rang, float v, float v0)
		{
			if (rang != 0) return 1f;
			var s = _segs[i];
			int p = Porteur(i);
			if (p < 0)
			{
				if (s.Base.Z > PiedSolCm) return 1f;
				float l = Mathf.Max(PiedMinCm, PiedParEpaisseur * s.ThicknessCm);
				float u = Mathf.Max(0f, 1f - v / l);
				return 1f + PiedEvase * u * u;
			}
			float ep = _segs[p].ThicknessCm, lc = Mathf.Max(ep, 1f);
			float w = Mathf.Max(0f, 1f - (v - v0) / lc);
			float f = 1f + ColRenfle * w * w;
			// Le col ne dépasse jamais le porteur : il s'y fond, il ne le déborde pas.
			return Mathf.Min(f, Mathf.Max(1f, ep / Mathf.Max(s.ThicknessCm, 1e-3f)));
		}
	}
}
