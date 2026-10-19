// SYMBIOSE — PerfPostes.cs (sprint PERF VUE ①, banc d'étalonnage)
// Chronomètres CPU par POSTE de la vue : combien de millisecondes, par seconde
// de jeu, chaque famille de travail coûte au fil principal (vie macro, ombres,
// soleil, vent, cuisson, dessin des plantes, application de semaine, tapis).
// Le rapport du banc (touche E, WorldView.Etalonnage.cs) les met à côté du
// temps d'image total : ce qui reste « non attribué » est le rendu lui-même
// (envoi au pilote OpenGL, remplissage GPU) et le reste du moteur Godot.
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
//    vrai coût de rendu de ces commandes tombe plus tard, dans le « non attribué ».

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
		}

		// Libellés du rapport, dans l'ordre de l'enum.
		private static readonly string[] Noms =
		{
			"vie macro _Process", "vie macro _Draw", "ombres _Draw", "soleil (UpdateSun)",
			"vent (poses)", "cuisson (file)", "plantes _Draw", "semaine (étalement)",
			"attente (marge)", "tapis/sol",
		};

		private static readonly int N = Noms.Length;
		private static readonly long[] _ticks = new long[N];
		private static readonly int[] _appels = new int[N];

		public static long Debut() => Stopwatch.GetTimestamp();

		public static void Fin(Poste p, long t0)
		{
			_ticks[(int)p] += Stopwatch.GetTimestamp() - t0;
			_appels[(int)p]++;
		}

		public static void Reset()
		{
			System.Array.Clear(_ticks);
			System.Array.Clear(_appels);
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
					+ $"· {_appels[i] / secondes,7:F0} appels/s"));
			}
		}
	}
}
