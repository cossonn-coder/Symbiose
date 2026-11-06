// SYMBIOSE — PlantRenderer.CleStable.cs (partial, sprint HOUPPIER ④)
// Deux clés qui disent ce qu'un arbre EST, indépendamment de sa place dans une liste :
//  · CleSegment : l'identité d'un segment, pour les présences et positions tirées au hash ;
//  · CleArbre + signature du bois : ce qu'on dessine, pour ne recuire que si le dessin change assez.
//
// 📖 Pédagogie — pourquoi pas l'indice. `_rebuild` (sim/growth/geometrie.py) réindexe la liste à
// chaque coupe : le segment 42 devient le 37, et son hash change avec son indice. Couper une
// branche faisait donc sauter les feuilles de TOUTES les autres, comme une table indexée par une
// position qui glisse. La base et la direction, elles, ne bougent plus après la création :
// `base` et `dir` sont des tuples posés une fois (`_mk`, phases.py), seul `length_cm` grandit
// (vérifié au code : aucune affectation `.base =` ni `.dir =` dans le moteur). Il faut les deux :
// deux segments frères partent du même point, seule leur direction les sépare.
//
// 📖 Pourquoi l'automne et la santé sont DANS la clé. La palette indexée sépare la LUMIÈRE (shader)
// de la TEINTE : le n° de palette de la teinte est écrit dans les pixels à la cuisson
// (`DrawPlanteAssemblee`, `PaletteIndexee.Palette(c)`). Une teinte qui change exige donc une
// recuisson, immédiate : ces champs comparés à l'échelon près évitent de refaire l'image pour une
// nuance que la palette ne montrerait pas.
//
// Vue pure, zéro Random (philo #3), golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Échelle de la base (0,1 cm) et de la direction (celle du pont, 1e-3, segments_pont.py).
		private const float CleBaseEchelle = 10f, CleDirEchelle = 1000f;
		// Une teinte (0..1) vue en 10 échelons chez un arbre : ~20 semaines de saison = ~10 recuissons.
		private const float EchelonsTeinte = 10f;
		// Bois : passage du tendre au lignifié et de la brindille à l'écorce, en 8 échelons.
		private const float EchelonsBois = 8f;

		private static int Melange(int h, int v) { unchecked { return (h ^ v) * 16777619; } }

		private static int Echelon(float v) => Mathf.RoundToInt(v * EchelonsTeinte);

		// Relative au collet : un pied déplacé (pot) garde ses feuilles. Positive : les appelants
		// s'en servent comme un indice, `(i + j) % 2` compris.
		private int CleSegment(in Segment s)
		{
			Vector3 c = _structure.ColletCm;
			int h = unchecked((int)2166136261);
			h = Melange(h, Mathf.RoundToInt((s.Base.X - c.X) * CleBaseEchelle));
			h = Melange(h, Mathf.RoundToInt((s.Base.Y - c.Y) * CleBaseEchelle));
			h = Melange(h, Mathf.RoundToInt((s.Base.Z - c.Z) * CleBaseEchelle));
			h = Melange(h, Mathf.RoundToInt(s.Dir.X * CleDirEchelle));
			h = Melange(h, Mathf.RoundToInt(s.Dir.Y * CleDirEchelle));
			h = Melange(h, Mathf.RoundToInt(s.Dir.Z * CleDirEchelle));
			return h & 0x7FFFFFFF;
		}

		// ---------------------------------------------------------------------------
		// RECUISSON D'UN ARBRE
		// ---------------------------------------------------------------------------

		// 📖 Pourquoi une TOLÉRANCE et pas une simple égalité. Un arbre change vraiment chaque semaine :
		// ses apex s'allongent, la cladoptose coupe, le plafond de segments en retire un quand un autre
		// pousse. Une clé exacte, même quantifiée, ratait 0,91 fois par arbre et par semaine [`houppiers_25`,
		// seed 42, 2 ans, modèle Python de la clé] : elle ne servait à rien. On compare donc le bois à celui
		// de la dernière cuisson, segment par segment, et il faut qu'assez de segments aient changé.
		// C'est un capteur à hystérésis : on ne réagit pas à chaque tic. Le délai borne ce qu'une image
		// peut garder de retard, et un geste du joueur recuit tout de suite (WorldView.cs, après l'action).
		// Valeurs [choix], à juger au F5 : c'est le retard visible contre le coût de cuisson.
		private const float ToleranceSegments = 0.15f;
		private const int SegmentsChangesMin = 2;
		private const int SemainesSansCuissonMax = 8;
		private const float LongueurPasCm = 10f;

		private readonly record struct CleArbre(int Densite, int Floraison, bool Fane, int Automne, int Fruits, string Stade);
		private CleArbre _cleArbre;
		private HashSet<int> _boisCuit = new(), _boisNeuf = new();
		private int _semainesSansCuisson;

		// Ce qui se voit d'un segment : sa place, sa longueur au pas, sa largeur comme DrawTigesAssemblees
		// la trace, le passage du tendre au lignifié, s'il porte des feuilles, si elles ont fini de grandir.
		private int SignatureSegment(in Segment seg)
		{
			int h = Melange(CleSegment(seg), Mathf.RoundToInt(seg.LengthCm / LongueurPasCm));
			h = Melange(h, Mathf.RoundToInt(seg.ThicknessCm * WorldView.PxPerCmX * WoodWidthFactor));
			h = Melange(h, Mathf.RoundToInt(Lignification(seg) * EchelonsBois));
			h = Melange(h, IsLeafy(seg) ? 1 : 0);
			return Melange(h, seg.AgeWeeks >= LeafMaturityWeeks ? 1 : 0);
		}

		// Ce que `SetStructure` apporte. Symptômes, vitalité, neige, pluie arrivent par leurs propres
		// portes : voir MemesSymptomesArbre, SetVitality et RefreshMeteo, à l'échelon près comme ici.
		private CleArbre CleDeLArbre()
		{
			var s = _structure;
			int fruits = s.Fruits.Count;
			foreach (var fr in s.Fruits)
			{
				fruits = Melange(fruits, fr.SegmentId);
				fruits = Melange(fruits, Echelon(fr.Maturite));
				fruits = Melange(fruits, Echelon(fr.Masse));
				fruits = Melange(fruits, fr.Nombre);   // une cerise mangée se voit (VERGER VIVANT ④)
			}
			return new CleArbre(Echelon(s.DensiteVisible), Echelon(s.Floraison), FloraisonFane, Echelon(s.Automne), fruits, s.StageName);
		}

		private bool ArbreInchange()
		{
			_boisNeuf.Clear();
			foreach (var seg in _structure.Segments) _boisNeuf.Add(SignatureSegment(seg));
			int disparus = 0;
			foreach (int sig in _boisCuit) if (!_boisNeuf.Contains(sig)) disparus++;
			int changes = System.Math.Max(disparus, _boisNeuf.Count - (_boisCuit.Count - disparus));
			int seuil = Mathf.Max(SegmentsChangesMin, Mathf.CeilToInt(_boisNeuf.Count * ToleranceSegments));
			_semainesSansCuisson++;
			CleArbre cle = CleDeLArbre();
			if (cle == _cleArbre && changes < seuil && (changes == 0 || _semainesSansCuisson < SemainesSansCuissonMax))
				return true;
			_cleArbre = cle;
			(_boisCuit, _boisNeuf) = (_boisNeuf, _boisCuit);
			_semainesSansCuisson = 0;
			return false;
		}

		// Deux listes de symptômes se valent à l'échelon près, et un symptôme à l'échelon 0 ne se voit pas :
		// qu'il apparaisse ou disparaisse de la liste ne change aucun dessin.
		private bool MemesSymptomesArbre(IReadOnlyList<(string Cause, float Intensite)> neufs)
		{
			return Inclus(neufs, _symptomes) && Inclus(_symptomes, neufs);

			static bool Inclus(IReadOnlyList<(string Cause, float Intensite)> a, IReadOnlyList<(string Cause, float Intensite)> b)
			{
				for (int i = 0; i < a.Count; i++)
				{
					if (Echelon(a[i].Intensite) == 0) continue;
					bool trouve = false;
					for (int j = 0; j < b.Count && !trouve; j++)
						trouve = a[i].Cause == b[j].Cause && Echelon(a[i].Intensite) == Echelon(b[j].Intensite);
					if (!trouve) return false;
				}
				return true;
			}
		}
	}
}
