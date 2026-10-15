// SYMBIOSE — WorldView.Capture.cs (sprint JARDIN VIVANT, T0 — banc de capture VM)
// Mode CAPTURE : lancé par `tools/capture_vm.sh` (Godot sous Xvfb + Movie Maker),
// il saute l'écran de sélection, monte directement un monde/banc et cadre la
// caméra à un palier de zoom donné. Les PNG eux-mêmes sont écrits par le Movie
// Maker de Godot (`--write-movie`), pas par ce code. Sert d'« yeux » à l'agent
// sur la VM sans écran — ce n'est PAS un livrable joueur.
//
// 📖 Pédagogie Godot/C# :
//  - OS.GetCmdlineUserArgs() rend les arguments placés APRÈS `--` sur la ligne
//    de commande Godot (ceux que le moteur ne consomme pas). Comme argv en C,
//    mais déjà filtré des options moteur.
//  - INACTIF PAR DÉFAUT : sans `--capture-banc=…`, `CaptureBanc` reste null et
//    rien ne change (le F5 de Nico, lancé sans argument, est intact).
//
// Arguments reconnus (après `--`) :
//   --capture-banc=<nom>     monde/banc à monter (full, smoke, propre, ou un banc
//                            du registre Python `BANCS`) — active le mode
//   --capture-zoom=<z>       palier de zoom (0.5 1 2 4 8 16 32) ; défaut = cadrage
//   --capture-centre=<x>,<y> point visé en cm monde (défaut = centre 1000,1000)
//   --capture-souris=<x>,<y> souris posée en px ÉCRAN (survol : losange, étiquette)
//   --capture-geste=<n>      slot de geste armé (0..9) — losange qui « respire »

using Godot;
using System.Globalization;

namespace Symbiose
{
	public partial class WorldView
	{
		// Parsés UNE fois au chargement de la classe (les arguments ne changent pas
		// pendant l'exécution). null / NaN = option absente.
		private static readonly string CaptureBanc = ArgCapture("banc");
		private static readonly float CaptureZoom = ParseFloat(ArgCapture("zoom"));
		private static readonly string CaptureCentre = ArgCapture("centre");
		private static readonly string CaptureSouris = ArgCapture("souris");
		private static readonly float CaptureGeste = ParseFloat(ArgCapture("geste"));

		// Vrai quand le jeu est lancé par le banc de capture (WorldView._Ready
		// saute alors le sélecteur de monde).
		private static bool CaptureActive => CaptureBanc != null;

		private static string ArgCapture(string cle)
		{
			string prefixe = $"--capture-{cle}=";
			foreach (string a in OS.GetCmdlineUserArgs())
				if (a.StartsWith(prefixe)) return a.Substring(prefixe.Length);
			return null;
		}

		private static float ParseFloat(string s) =>
			s != null && float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out float v)
				? v : float.NaN;

		// Appelé APRÈS FrameCamera (monde construit) : impose le palier de zoom et
		// le point visé. On n'utilise pas StepZoom (zoom centré SOURIS — sous Xvfb
		// la souris n'a pas de position utile) : on pose directement l'état caméra,
		// puis on refait ce que StepZoom fait après coup (redraw LOD + culling).
		private void AppliquerCapture()
		{
			if (!CaptureActive || _camera == null) return;
			GD.Print($"[Capture] banc « {CaptureBanc} », zoom {CaptureZoom}, centre {CaptureCentre ?? "monde"}.");

			if (CaptureCentre != null)
			{
				string[] xy = CaptureCentre.Split(',');
				if (xy.Length == 2)
					_camera.Position = ClampToWorld(WorldToScreen(ParseFloat(xy[0]), ParseFloat(xy[1])));
			}
			if (!float.IsNaN(CaptureZoom))
			{
				int idx = System.Array.IndexOf(ZoomSteps, CaptureZoom);
				if (idx < 0)
					GD.PushWarning($"[Capture] zoom {CaptureZoom} hors paliers {string.Join(" ", ZoomSteps)} — ignoré.");
				else
				{
					_zoomIndex = idx;
					_camera.Zoom = Vector2.One * CaptureZoom;
					CurrentZoom = CaptureZoom;
				}
			}
			// Xvfb a un vrai pointeur X : WarpMouse le déplace, GetMousePosition le relit.
			if (CaptureSouris != null)
			{
				string[] s = CaptureSouris.Split(',');
				if (s.Length == 2)
					Input.WarpMouse(new Vector2(ParseFloat(s[0]), ParseFloat(s[1])));
			}
			if (!float.IsNaN(CaptureGeste)) SelectSlot((int)CaptureGeste);
			RedrawAllPlants();
			CullPlants();
		}
	}
}
