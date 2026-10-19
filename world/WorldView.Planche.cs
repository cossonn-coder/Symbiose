// SYMBIOSE — WorldView.Planche.cs (partial de WorldView, sprint RENDU VISIBLE T7)
// BANC F5 « planche des paliers » : touche L (comme « loupe ») = la caméra
// descend ×0,5 → ×32 sur UNE plante (celle sous le curseur, sinon la plus proche
// du centre de l'écran), PlancheStepSec secondes par palier, avec un encart
// « palier ×N · information » (le tableau D4 de la conception). Re-L = arrêt :
// la caméra revient exactement où elle était (position + palier). Molette pendant
// la planche = défilé arrêté, plante verrouillée au centre, palier à la main.
//
// C'est un OUTIL D'OBSERVATION (comme le défilé F12) : il ne fait que poser
// l'état caméra, puis refait ce que StepZoom fait après coup (pompe de redraw +
// culling). La question qu'il sert : « zoomer = voir plus ? » à chaque cran.
// Banc VM équivalent : `tools/capture_vm.sh -l SEC` (une PNG par palier).
//
// 📖 Pédagogie Godot/C# : même mécanique que le défilé (WorldView.Defile.cs) —
// une SceneTreeTimer à usage unique par étape, et un compteur de « génération »
// (_plancheGen) qui périme les minuteries d'une planche arrêtée en vol.

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private const float PlancheStepSec = 3f;
		private const float PlancheRayonCm = 60f;   // « sous le curseur » (≈ un plot)

		// Le tableau D4 (conception_rendu_visible.md §4) : palier → information AJOUTÉE.
		private static readonly (float Zoom, string Info)[] Planche =
		{
			(0.5f, "présence + saison"),
			(1f,   "port"),
			(2f,   "santé globale"),
			(4f,   "architecture (bois + masses)"),
			(8f,   "organes"),
			(16f,  "symptômes fins"),
			(32f,  "intime"),
		};

		private int _plancheStep = -1;   // -1 = planche arrêtée
		private int _plancheGen;
		private PlantRenderer _plancheCible;
		private Vector2 _plancheCamAvant;
		private int _plancheZoomAvant;
		private Label _plancheLabel;

		private bool PlancheActive => _plancheStep >= 0;

		// Touche L : lance / arrête la planche. `pasSec` = durée d'un palier
		// (le banc VM la raccourcit : le temps de capture coûte cher).
		// `parSouris` = false : la plante la plus proche du centre seulement (banc VM,
		// où le pointeur Xvfb n'a pas de position utile).
		private void TogglePlanche(float pasSec = PlancheStepSec, bool parSouris = true)
		{
			_plancheGen++;
			if (PlancheActive) { ArreterPlanche(); return; }
			if (_camera == null) return;
			_plancheCible = (parSouris ? FindPlant(_sourisMonde, PlancheRayonCm) : null)
				?? FindPlant(ScreenToWorld(_camera.Position), 1e5f);
			if (_plancheCible == null) { GD.Print("[Planche] aucune plante."); return; }
			_plancheCamAvant = _camera.Position;
			_plancheZoomAvant = _zoomIndex;
			PlancheEtape(0, _plancheGen, pasSec);
		}

		private void PlancheEtape(int step, int gen, float pasSec)
		{
			if (gen != _plancheGen) return;   // planche arrêtée entre-temps
			if (step >= Planche.Length || !IsInstanceValid(_plancheCible))
			{
				_plancheGen++;
				ArreterPlanche();
				return;
			}
			AfficherPalier(step, "");
			var zoom = Planche[step].Zoom;
			GD.Print($"[Planche] début ×{zoom} — frame {Engine.GetFramesDrawn()}");
			GetTree().CreateTimer(pasSec).Timeout += () =>
			{
				if (gen != _plancheGen) return;
				GD.Print($"[Planche] fin ×{zoom} — frame {Engine.GetFramesDrawn()}");
				PlancheEtape(step + 1, gen, pasSec);
			};
		}

		// Cadre la cible au palier `step` (caméra centrée sur elle) + encart.
		private void AfficherPalier(int step, string suffixe)
		{
			_plancheStep = step;
			var (zoom, info) = Planche[step];
			PoserCamera(System.Array.IndexOf(ZoomSteps, zoom),
				_plancheCible.EmpriseCanvas.GetCenter());
			string espece = _plancheCible.GetMeta(LectureSnap.Meta("species"), "?").AsString();
			EncartPlanche($"palier ×{zoom} · {info}   —   {espece} "
				+ $"({step + 1}/{Planche.Length}){suffixe}");
		}

		// Molette pendant la planche (demande Nico F5 2026-10-19) : la plante reste
		// VERROUILLÉE au centre — le défilé automatique s'arrête (génération périmée)
		// et chaque cran monte/descend d'un palier sur elle. Re-L sort comme avant.
		private void PlancheMolette(int dir)
		{
			_plancheGen++;   // périme la minuterie du défilé en cours
			if (!IsInstanceValid(_plancheCible)) { ArreterPlanche(); return; }
			int step = Mathf.Clamp(_plancheStep + dir, 0, Planche.Length - 1);
			AfficherPalier(step, "   ·   molette = palier, L = sortir");
		}

		private void ArreterPlanche()
		{
			_plancheStep = -1;
			_plancheCible = null;
			if (_plancheLabel != null) _plancheLabel.Visible = false;
			if (_camera != null) PoserCamera(_plancheZoomAvant, _plancheCamAvant);
			GD.Print("[Planche] arrêt, caméra restaurée.");
		}

		// Pose palier + position, puis ce que StepZoom fait après coup : la pompe de
		// redraw (le LOD dépend du palier) et le culling (l'étendue visible change).
		private void PoserCamera(int zoomIndex, Vector2 position)
		{
			_zoomIndex = zoomIndex;
			_camera.Zoom = Vector2.One * ZoomSteps[zoomIndex];
			CurrentZoom = ZoomSteps[zoomIndex];
			_camera.Position = ClampToWorld(position);
			RedrawAllPlants();
			CullPlants();
		}

		// Encart texte (écran, CanvasLayer "Hud") — créé à la première planche.
		private void EncartPlanche(string texte)
		{
			if (_plancheLabel == null)
			{
				var hud = GetNodeOrNull<CanvasLayer>("Hud");
				if (hud == null) return;
				// Au-dessus de la légende F1 (bas d'écran, y = 984).
				_plancheLabel = new Label { Position = new Vector2(16f, 940f) };
				_plancheLabel.AddThemeFontSizeOverride("font_size", 26);
				_plancheLabel.AddThemeColorOverride("font_color", new Color(1f, 0.95f, 0.7f));
				_plancheLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
				_plancheLabel.AddThemeConstantOverride("outline_size", 8);
				hud.AddChild(_plancheLabel);
			}
			_plancheLabel.Text = texte;
			_plancheLabel.Visible = true;
		}
	}
}
