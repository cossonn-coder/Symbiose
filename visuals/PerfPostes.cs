// SYMBIOSE — PerfPostes.cs (sprint PERF VUE ①, banc d'étalonnage)
// Chronomètres CPU par POSTE de la vue : combien de millisecondes, par seconde
// de jeu, chaque famille de travail coûte au fil principal (vie macro, ombres,
// soleil, vent, cuisson, dessin des plantes, application de semaine, tapis).
// Le rapport du banc (touche E, WorldView.Etalonnage.cs) les met à côté du
// temps d'image total et du rendu CPU mesuré par Godot : ce qui reste est
// « inexpliqué » (reste du moteur Godot, pilote, ou CPU volé — FLUIDITÉ PC ①).
//
// 📖 Pédagogie (côté embarqué) : c'est l'équivalent d'un compteur de cycles
// (DWT->CYCCNT sur Cortex-M) lu en entrée et en sortie de chaque routine, puis
// accumulé par routine. `Stopwatch.GetTimestamp()` lit l'horloge haute
// résolution du système (quelques dizaines de ns) : le coût de la mesure est
// négligeable devant celui des routines mesurées.
//  - Classe STATIQUE : les appelants (MacroLife, PlantShadow, WindWave…) n'ont
//    aucune référence à WorldView ; un état global de mesure évite de câbler.
//  - Toujours actif (quelques additions par appel) ; `Reset()` ouvre une
//    fenêtre de mesure, `Ligne(...)` la résume.
//  - Les `_Draw` mesurés ne font qu'ENREGISTRER des commandes de dessin : le
//    vrai coût de rendu de ces commandes tombe plus tard, dans le « rendu CPU ».

using System.Diagnostics;
using System.Globalization;
using System.Text;

namespace Symbiose
{
	public static class PerfPostes
	{
		public enum Poste
		{
			MacroProcess, MacroDraw, OmbreDraw, Soleil, Vent,
			CuissonFile, PlanteDraw, Etalement, Attente, Tapis,
			ForagerProcess, ForagerDraw,   // butineurs (banc accéléré, PLANTE ASSEMBLÉE ③)
			PlanteVecteur,   // plantes SANS image, tracé vectoriel direct (LEVIERS ③)
		}

		// Libellés du rapport, dans l'ordre de l'enum.
		private static readonly string[] Noms =
		{
			"vie macro _Process", "vie macro _Draw", "ombres _Draw", "soleil (UpdateSun)",
			"vent (poses)", "cuisson (file)", "plantes _Draw", "semaine (étalement)",
			"attente (marge)", "tapis/sol", "butineurs _Process", "butineurs _Draw",
			"plantes vectoriel",
		};

		private static readonly int N = Noms.Length;
		public static int Nombre => Noms.Length;   // taille des tableaux de Copier (PERF VUE ④)
		private static readonly long[] _ticks = new long[N];
		private static readonly int[] _appels = new int[N];

		// Octets alloués (tas managé) par poste — PERF VUE ④ : le ramasse-miettes
		// .NET suspend le jeu ~35-45 ms par collecte [VM] ; qui le nourrit ?
		// `GetAllocatedBytesForCurrentThread` = compteur du thread appelant (le fil
		// principal ici) : quelques ns, pas d'allocation. Postes jamais imbriqués.
		private static readonly long[] _octets = new long[N];
		private static long _allocT0;

		public static long Debut()
		{
			_allocT0 = System.GC.GetAllocatedBytesForCurrentThread();
			return Stopwatch.GetTimestamp();
		}

		public static void Fin(Poste p, long t0)
		{
			_ticks[(int)p] += Stopwatch.GetTimestamp() - t0;
			_octets[(int)p] += System.GC.GetAllocatedBytesForCurrentThread() - _allocT0;
			_appels[(int)p]++;
		}

		/// <summary>Copie les compteurs bruts (ticks cumulés) dans `dst` (taille Nombre),
		/// sans allocation : le diagnostic des à-coups en fait des deltas par image.</summary>
		public static void Copier(long[] dst) => System.Array.Copy(_ticks, dst, N);

		/// <summary>Postes d'un delta de ticks au-dessus de `seuilMs`, « nom x ms », le plus
		/// lourd d'abord ; « — » si aucun (le temps est alors du rendu ou hors postes).</summary>
		public static string Detail(long[] delta, double seuilMs)
		{
			var l = new System.Collections.Generic.List<(double ms, string nom)>();
			for (int i = 0; i < N; i++)
			{
				double ms = delta[i] * 1000.0 / Stopwatch.Frequency;
				if (ms >= seuilMs) l.Add((ms, Noms[i]));
			}
			if (l.Count == 0) return "postes —";
			l.Sort((a, b) => b.ms.CompareTo(a.ms));
			var sb = new StringBuilder("postes ");
			foreach (var (ms, nom) in l)
				sb.Append(string.Create(CultureInfo.InvariantCulture, $"{nom} {ms:F1} ms, "));
			return sb.ToString(0, sb.Length - 2);
		}

		public static void Reset()
		{
			System.Array.Clear(_ticks);
			System.Array.Clear(_appels);
			System.Array.Clear(_octets);
		}

		/// <summary>Somme des postes, en ms sur la fenêtre (pour le « non attribué »).</summary>
		public static double TotalMs()
		{
			long t = 0;
			foreach (long v in _ticks) t += v;
			return t * 1000.0 / Stopwatch.Frequency;
		}

		/// <summary>Une ligne par poste : ms par image (moyenne), part du temps
		/// d'image, appels par seconde. `frames`/`secondes` = la fenêtre mesurée.</summary>
		public static void Ecrire(StringBuilder sb, int frames, double secondes, double msImage)
		{
			if (frames <= 0 || secondes <= 0) return;
			for (int i = 0; i < N; i++)
			{
				double ms = _ticks[i] * 1000.0 / Stopwatch.Frequency / frames;
				sb.AppendLine(string.Create(CultureInfo.InvariantCulture,
					$"    {Noms[i],-22} {ms,7:F2} ms/image ({100 * ms / msImage,4:F1} %) "
					+ $"· {_appels[i] / secondes,7:F0} appels/s · {_octets[i] / 1024.0 / secondes,7:F0} Ko alloués/s"));
			}
		}
	}
}
