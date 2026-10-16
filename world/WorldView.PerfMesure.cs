// SYMBIOSE — WorldView.PerfMesure.cs (partial de WorldView, sprint RENDU VISIBLE T1)
// Mesure COMPARABLE du coût d'une frame de rendu : envois GPU (draw calls),
// objets et primitives dessinés, temps de frame. Les FPS de la VM (llvmpipe,
// rendu logiciel) ne disent rien du PC de Nico (iGPU HD 4600) ; le nombre
// d'envois GPU par frame, lui, est le même sur les deux machines → c'est LA
// métrique de vérification des tronçons suivants (conception §2).
//
// 📖 Pédagogie Godot/C# :
//  - `Performance.GetMonitor(...)` lit les compteurs internes du moteur (comme
//    les registres de statistiques d'un périphérique en embarqué). Les moniteurs
//    `Render*InFrame` décrivent la DERNIÈRE frame dessinée.
//  - Un « draw call » = un envoi de commande de dessin au GPU. Godot regroupe
//    (batch) les items voisins de même texture/matériau en un seul envoi ;
//    alterner deux types de nœuds casse ce regroupement → le compteur grimpe.
//  - On moyenne sur une fenêtre d'~1 s (accumulateur + remise à zéro) : la
//    valeur d'une seule frame est trop bruitée pour comparer deux réglages.
//  - Le temps vient de l'HORLOGE MURALE (`Time.GetTicksUsec`), pas du `delta`
//    de _Process : mesuré sur la VM, le delta sous-estimait la frame (~7,5 FPS
//    affichés contre 5-6 par `--print-fps`) — Godot lisse/borne ce delta.
//  - Ligne `[perf]` en culture INVARIANTE (point décimal) : la culture FR du
//    poste écrirait « 133,5 » et casserait le parseur du script.
//
// Échantillonné à CHAQUE frame (quelques lectures de compteurs, coût nul),
// indépendamment de F4 : le mode capture (tools/perf_vm.sh) imprime une ligne
// `[perf]` par fenêtre sans afficher le HUD.

using Godot;
using System.Globalization;

namespace Symbiose
{
	public partial class WorldView
	{
		private const double PerfFenetreSec = 1.0;

		// Accumulateurs de la fenêtre en cours.
		private double _pmDraw, _pmObj, _pmPrim;
		private ulong _pmDebutUs;
		private int _pmFrames;
		// Gel (D106 T4, méthode 73a3f24) : frame la plus longue de la fenêtre et
		// nombre de frames > 250 ms — la moyenne seule masque l'à-coup hebdomadaire.
		private ulong _pmPrecUs;
		private double _pmMaxMs;
		private int _pmGels;
		// Moyennes de la dernière fenêtre close (−1 = pas encore mesuré).
		private double _pmFrameMs = -1, _pmDrawMoy = -1, _pmObjMoy = -1, _pmPrimMoy = -1;

		// Appelé chaque frame depuis _Process (toutes phases).
		private void MesurerPerfRendu()
		{
			ulong now = Time.GetTicksUsec();
			if (_pmDebutUs == 0) { _pmDebutUs = _pmPrecUs = now; return; }   // 1re frame : ouvre la fenêtre
			_pmFrames++;
			double frameMs = (now - _pmPrecUs) / 1000.0;
			_pmPrecUs = now;
			if (frameMs > _pmMaxMs) _pmMaxMs = frameMs;
			if (frameMs > 250.0) _pmGels++;
			_pmDraw += Performance.GetMonitor(Performance.Monitor.RenderTotalDrawCallsInFrame);
			_pmObj += Performance.GetMonitor(Performance.Monitor.RenderTotalObjectsInFrame);
			_pmPrim += Performance.GetMonitor(Performance.Monitor.RenderTotalPrimitivesInFrame);
			double temps = (now - _pmDebutUs) / 1e6;
			if (temps < PerfFenetreSec) return;

			_pmFrameMs = 1000.0 * temps / _pmFrames;
			_pmDrawMoy = _pmDraw / _pmFrames;
			_pmObjMoy = _pmObj / _pmFrames;
			_pmPrimMoy = _pmPrim / _pmFrames;
			// Banc temps réel (perf_vm.sh) : une ligne machine-lisible par fenêtre.
			if (CaptureActive)
				GD.Print(string.Create(CultureInfo.InvariantCulture,
					$"[perf] fps={1000.0 / _pmFrameMs:F1} ms={_pmFrameMs:F1} "
					+ $"draw={_pmDrawMoy:F0} obj={_pmObjMoy:F0} prim={_pmPrimMoy:F0} "
					+ $"max={_pmMaxMs:F0} gels={_pmGels} couches={NomCasCouches()}"));
			_pmDraw = _pmObj = _pmPrim = 0;
			_pmMaxMs = 0;
			_pmGels = 0;
			_pmDebutUs = now;
			_pmFrames = 0;
		}

		// Ligne « rendu » ajoutée à l'overlay F4 et au rapport presse-papier (C).
		private string LignePerfRendu()
		{
			if (_pmFrameMs < 0) return "rendu — mesure en cours… · couches : " + NomCasCouches();
			return $"rendu — frame {_pmFrameMs:F1} ms (moy. ~1 s) · draw calls "
				+ $"{_pmDrawMoy:F0} · objets {_pmObjMoy:F0} · primitives {_pmPrimMoy:F0} · "
				+ $"couches : {NomCasCouches()}";
		}
	}
}
