// SYMBIOSE — PlanteLue.cs (sprint FLUIDITÉ AN 2 ④ — lecture des plantes hors fil principal)
// Une plante du snapshot, LUE une fois en données C# pures : structure, symptômes,
// vitalité, strate… Tout ce que `MajPlante` (world/WorldView.Snapshot.cs) lisait
// dans le dictionnaire Godot sur le fil principal, ~1 ms/plante mesuré sur la VM.
//
// Où ça tourne : `SemaineRecue.Lire` est appelé DANS la tâche du step (thread du
// pool), juste après le parse JSON du pont. Le fil principal ne fait plus que
// poser des valeurs prêtes sur les nœuds.
//
// 📖 Pédagogie (règle de thread Godot, vue de l'embarqué) : l'arbre de scène est
// comme un périphérique partagé SANS verrou — seul le fil principal y touche. Ici
// on ne lit QUE le dictionnaire que la tâche vient elle-même de parser (personne
// d'autre ne le voit encore) et on fabrique des objets .NET ordinaires : aucun
// nœud, aucun état de WorldView, aucun appel RenderingServer. C'est l'équivalent
// d'une ISR qui remplit un tampon privé, consommé ensuite par la boucle principale.

using System.Collections.Generic;
using System.Globalization;
using GArray = Godot.Collections.Array;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public sealed class PlanteLue
	{
		public string Key, Tile, Species, Name, Tag;
		public float X, Y;
		public int NSegs;
		public bool Dead;
		public PlantStructure Structure;
		public string StadeMort, SupportKind, Strate, Silhouette;
		public float Vitalite = 1f, Abri = 1f;
		public bool Emitteur = true;
		public readonly List<(string Cause, float Intensite)> Symptomes = new();

		// Clé stable d'une plante = tuile + espèce + position. Culture INVARIANTE :
		// la clé est fabriquée sur deux fils (pool et principal) qui n'ont pas
		// forcément la même culture courante → « 12,3 » ≠ « 12.3 » casserait le diff.
		public static string Cle(string tile, string species, double x, double y) =>
			string.Create(CultureInfo.InvariantCulture, $"{tile}|{species}|{x:F1}|{y:F1}");

		/// <summary>Lit la plante `p` (lecture seule, aucun nœud touché). Une plante
		/// sans segments (germination) ne lit que l'identité : rien à dessiner.</summary>
		public static PlanteLue Lire(GDict p)
		{
			var l = new PlanteLue
			{
				Tile = LectureSnap.S(p, "tile"),
				Species = LectureSnap.S(p, "species"),
				Name = LectureSnap.S(p, "name"),
			};
			double x = LectureSnap.D(p, "x_cm"), y = LectureSnap.D(p, "y_cm");
			l.X = (float)x;
			l.Y = (float)y;
			l.Key = Cle(l.Tile, l.Species, x, y);
			if (LectureSnap.A(p, "segs_lus"))   // pont en delta (0.6.0, core/PontDelta.cs)
				l.NSegs = StructureLoader.SegsLus(p).Length / PontDelta.Pas;
			else
				using (var segs = LectureSnap.Tab(p, "segments")) l.NSegs = segs.Count;
			l.Dead = LectureSnap.A(p, "dead") && LectureSnap.B(p, "dead");
			if (l.NSegs == 0) return l;

			l.Structure = StructureLoader.FromSnapshot(p);
			l.Tag = $"{l.Species} · {LectureSnap.S(p, "stage_name")}";
			// Lectures TOLÉRANTES (clé absente = snapshot ancien → défaut neutre),
			// historique des clés dans MajPlante.
			if (l.Dead) l.StadeMort = LectureSnap.S(p, "stade_mort");
			if (LectureSnap.A(p, "leaf_symptoms"))
				using (var syms = LectureSnap.Tab(p, "leaf_symptoms"))
					LireSymptomes(syms, l.Symptomes);
			if (LectureSnap.A(p, "vitalite")) l.Vitalite = LectureSnap.F(p, "vitalite");
			if (LectureSnap.A(p, "support"))
				using (var sup = LectureSnap.Dico(p, "support")) l.SupportKind = LectureSnap.S(sup, "type");
			if (LectureSnap.A(p, "strate")) l.Strate = LectureSnap.S(p, "strate");
			if (LectureSnap.A(p, "silhouette")) l.Silhouette = LectureSnap.S(p, "silhouette");
			if (LectureSnap.A(p, "emitteur")) l.Emitteur = LectureSnap.B(p, "emitteur");
			if (LectureSnap.A(p, "abri")) l.Abri = LectureSnap.F(p, "abri");
			return l;
		}

		/// <summary>Liste `leaf_symptoms` ({cause, intensity}) → couples C#.</summary>
		public static void LireSymptomes(GArray syms, List<(string, float)> dest)
		{
			for (int i = 0; i < syms.Count; i++)
			{
				using var d = LectureSnap.Dico(syms, i);
				dest.Add((LectureSnap.S(d, "cause"), LectureSnap.F(d, "intensity")));
			}
		}
	}

	/// <summary>Résultat d'un step : le snapshot parsé + ses plantes déjà lues
	/// (même indice que `snap["plants"]`). Construit sur le thread du pool.</summary>
	public sealed class SemaineRecue
	{
		public GDict Snap;
		public PlanteLue[] Plantes;
		public double LectureMs;   // temps de lecture des plantes (thread du pool, banc)

		public static SemaineRecue Lire(GDict snap)
		{
			if (snap == null) return null;
			long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
			var r = new SemaineRecue { Snap = snap };
			if (LectureSnap.A(snap, "plants"))
				using (var arr = LectureSnap.Tab(snap, "plants"))
				{
					r.Plantes = new PlanteLue[arr.Count];
					for (int i = 0; i < arr.Count; i++)
						using (var p = LectureSnap.Dico(arr, i)) r.Plantes[i] = PlanteLue.Lire(p);
				}
			r.LectureMs = System.Diagnostics.Stopwatch.GetElapsedTime(t0).TotalMilliseconds;
			return r;
		}
	}
}
