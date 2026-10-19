// SYMBIOSE — LectureSnap.cs (sprint PERF VUE ④ — lecture du snapshot SANS finaliseurs)
// Lire une valeur d'un Godot.Collections.Dictionary sans nourrir le ramasse-miettes.
//
// Mesuré au banc E (VM, turbo) : chaque collecte du GC .NET gelait le jeu
// ~35-45 ms, avec 26 000 à 64 000 objets en attente de FINALISATION par collecte.
// La source : l'API Godot C# elle-même. Un `Godot.Variant` qui porte une chaîne,
// un tableau ou un dictionnaire alloue un petit objet `Disposer` doté d'un
// FINALISEUR ; `AsGodotArray()` / `AsGodotDictionary()` créent un wrapper lui aussi
// finalisable. Or `dict["cle"]` en crée DEUX ou trois : la clé (chaîne → Variant),
// la valeur, et le wrapper. Une semaine = des dizaines de milliers d'accès.
//
// 📖 Pédagogie (.NET, vu de l'embarqué) : un objet à finaliseur, c'est une
// ressource native (ici une référence comptée côté moteur Godot) que le GC doit
// rendre « à la main ». Il survit à SA première collecte (mis en file pour le
// thread finaliseur), puis meurt à la suivante : il coûte deux passages et
// rallonge chaque pause. `Dispose()` libère la ressource TOUT DE SUITE et retire
// l'objet de la file (`GC.SuppressFinalize`) : il redevient un objet ordinaire,
// mort-né, gratuit pour le GC. C'est l'équivalent d'un `free()` explicite au lieu
// d'attendre un ramasse-miettes.
// Règles ici :
//  - les CLÉS sont des Variant créés une fois et gardés (cache) : zéro allocation ;
//  - la valeur lue est disposée aussitôt convertie (`using`) ;
//  - `Tab` / `Dico` rendent un wrapper que l'APPELANT dispose (`using var`), sauf
//    s'il le garde (index du dossier, métadonnées) — alors on ne le dispose pas.
// Lecture seule, aucune logique : la vue reste un consommateur passif (Option B).

using Godot;
using System.Collections.Concurrent;
using GArray = Godot.Collections.Array;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public static class LectureSnap
	{
		// Une clé = un Variant de chaîne, créé à la première lecture puis réutilisé.
		// Concurrent : le snapshot peut être lu hors fil principal (prudence).
		private static readonly ConcurrentDictionary<string, Variant> _cles = new();

		public static Variant Cle(string k) => _cles.GetOrAdd(k, s => s);

		// Noms de MÉTADONNÉES de nœud (`GetMeta("wx")`…) : une chaîne passée à l'API
		// Godot devient un `StringName` NEUF à chaque appel (finaliseur + référence
		// faible suivie). Mesuré : `FindPlant` (picking/survol, chaque image pendant
		// l'application d'une semaine) en créait ~540 par appel. Cache : un par nom.
		private static readonly ConcurrentDictionary<string, StringName> _metas = new();

		public static StringName Meta(string k) => _metas.GetOrAdd(k, s => new StringName(s));

		public static bool A(GDict d, string k) => d.ContainsKey(Cle(k));

		public static double D(GDict d, string k)
		{
			using Variant v = d[Cle(k)];
			return v.AsDouble();
		}

		public static float F(GDict d, string k) => (float)D(d, k);

		public static int I(GDict d, string k)
		{
			using Variant v = d[Cle(k)];
			return v.AsInt32();
		}

		public static bool B(GDict d, string k)
		{
			using Variant v = d[Cle(k)];
			return v.AsBool();
		}

		public static string S(GDict d, string k)
		{
			using Variant v = d[Cle(k)];
			return v.AsString();
		}

		/// <summary>Tableau sous `k` : wrapper NEUF, à disposer par l'appelant.</summary>
		public static GArray Tab(GDict d, string k)
		{
			using Variant v = d[Cle(k)];
			return v.AsGodotArray();
		}

		/// <summary>Dictionnaire sous `k` : wrapper NEUF, à disposer par l'appelant.</summary>
		public static GDict Dico(GDict d, string k)
		{
			using Variant v = d[Cle(k)];
			return v.AsGodotDictionary();
		}

		/// <summary>Élément i d'un tableau, en dictionnaire (à disposer par l'appelant).</summary>
		public static GDict Dico(GArray a, int i)
		{
			using Variant v = a[i];
			return v.AsGodotDictionary();
		}

		/// <summary>Élément i d'un tableau, en tableau (à disposer par l'appelant).</summary>
		public static GArray Tab(GArray a, int i)
		{
			using Variant v = a[i];
			return v.AsGodotArray();
		}

		/// <summary>Élément i d'un tableau, en chaîne.</summary>
		public static string S(GArray a, int i)
		{
			using Variant v = a[i];
			return v.AsString();
		}

		/// <summary>Élément i d'un tableau de nombres (aucun finaliseur pour un nombre,
		/// mais la lecture reste groupée ici).</summary>
		public static double D(GArray a, int i)
		{
			using Variant v = a[i];
			return v.AsDouble();
		}
	}
}
