// SYMBIOSE — WorldView.Camera.cs (partial de WorldView, SS⑥ refactor global)
// La caméra JOUABLE (D35, tranche 4) : pan aux flèches, zoom molette par
// paliers entiers, rotation de la vue par quarts de tour. La rotation passe
// par RebuildWorld (tout ce qui a été posé via WorldToScreen a une Position
// figée → on reconstruit sol + maison + plantes sous la nouvelle orientation).

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Palier de zoom courant (t6·B2) — lu par MacroLife pour son LOD
		// (les bestioles n'apparaissent qu'en zoomant). Mis à jour par
		// FrameCamera et StepZoom, les deux seuls écrivains du zoom.
		public static float CurrentZoom { get; private set; } = 0.5f;

		// Paliers de zoom (molette). Les paliers < 4 sont PROVISOIRES (vue
		// d'ensemble sur placeholders vectoriels, aucun artefact possible) ;
		// la règle projet « ×4-×32, jamais de fraction » redeviendra stricte
		// quand les sprites pixel art remplaceront les Polygon2D (D34).
		private static readonly float[] ZoomSteps = { 0.5f, 1f, 2f, 4f, 8f, 16f, 32f };
		private int _zoomIndex;
		private Camera2D _camera;

		// -------------------------------------------------------------------
		// CAMÉRA — jouable depuis la tranche 4 (D35) : pan flèches, zoom
		// molette par paliers, rotation par quarts de tour (re-projection).
		// -------------------------------------------------------------------

		private void FrameCamera()
		{
			// Recherche via _worldVp (le SubViewport) plutôt qu'un chemin absolu
			// depuis le root : robuste si la scène bouge. La caméra est l'enfant
			// direct "Camera" du SubViewport (cf. WorldView.tscn).
			_camera = _worldVp.GetNodeOrNull<Camera2D>("Camera");
			if (_camera == null) return;
			// Palier initial = le plus proche du CameraZoom exporté (0.5 cadre
			// le monde entier) — _zoomIndex et Zoom ne divergent jamais.
			_zoomIndex = 0;
			for (int i = 1; i < ZoomSteps.Length; i++)
				if (Mathf.Abs(ZoomSteps[i] - CameraZoom)
					< Mathf.Abs(ZoomSteps[_zoomIndex] - CameraZoom))
					_zoomIndex = i;
			// Centre du monde (1000,1000) cm → écran ; remonté d'un demi-toit pour
			// que la maison ne tasse pas le cadrage (échelle INTERNE du SubViewport,
			// moitié du plein écran d'avant → ~50 px au lieu de ~100).
			_camera.Position = WorldToScreen(WorldCm / 2f, WorldCm / 2f)
				- new Vector2(0f, 50f);
			_camera.Zoom = Vector2.One * ZoomSteps[_zoomIndex];
			CurrentZoom = ZoomSteps[_zoomIndex];
			_camera.MakeCurrent();
		}

		private void UpdateCameraPan(float delta)
		{
			if (_camera == null) return;
			// Polling (Input.IsKeyPressed) et non événement : un MAINTIEN de
			// touche est un état continu, échantillonné chaque frame — comme
			// lire un GPIO dans la boucle plutôt que compter les IRQ de front.
			var dir = Vector2.Zero;
			if (Input.IsKeyPressed(Key.Left))  dir.X -= 1f;
			if (Input.IsKeyPressed(Key.Right)) dir.X += 1f;
			if (Input.IsKeyPressed(Key.Up))    dir.Y -= 1f;
			if (Input.IsKeyPressed(Key.Down))  dir.Y += 1f;
			if (dir == Vector2.Zero) return;
			// PanSpeedPx est en px ÉCRAN/s ; la Position caméra vit en canvas
			// → diviser par le zoom donne un ressenti identique à tout palier.
			_camera.Position = ClampToWorld(_camera.Position
				+ dir.Normalized() * (PanSpeedPx / _camera.Zoom.X) * delta);
		}

		// Borne la caméra à la boîte englobante du monde projeté + marge 10 %
		// (kickoff A·1 : on ne se perd pas dans le gris). Les 4 coins du carré
		// 0..2000 cm projettent x ∈ [−halfW, halfW], y ∈ [0, h] — IDENTIQUE à
		// toute orientation : le quart de tour remappe le carré sur lui-même.
		private static Vector2 ClampToWorld(Vector2 pos)
		{
			float halfW = WorldCm * PxPerCmX;        // 780 px internes
			float h     = WorldCm * PxPerCmY * 2f;   // 780 px internes
			float margin = 0.1f * h;
			pos.X = Mathf.Clamp(pos.X, -halfW - margin, halfW + margin);
			pos.Y = Mathf.Clamp(pos.Y, -margin, h + margin);
			return pos;
		}

		private void StepZoom(int dir)
		{
			if (_camera == null) return;
			int idx = Mathf.Clamp(_zoomIndex + dir, 0, ZoomSteps.Length - 1);
			if (idx == _zoomIndex) return;   // déjà au palier extrême
			float oldZ = ZoomSteps[_zoomIndex];
			float newZ = ZoomSteps[idx];
			_zoomIndex = idx;
			// Zoom centré souris (kickoff A·2) : le point canvas sous le
			// curseur doit y RESTER. WorldMouseCanvas rend la souris en canvas du
			// SubViewport (fenêtre → px internes → caméra défaite) ; il suffit de
			// glisser la caméra vers/depuis ce point au ratio des zooms :
			// m = cam + d/oldZ = cam' + d/newZ  ⇒  cam' = m + (cam−m)·oldZ/newZ.
			Vector2 mouse = WorldMouseCanvas();
			_camera.Position = ClampToWorld(
				mouse + (_camera.Position - mouse) * (oldZ / newZ));
			_camera.Zoom = Vector2.One * newZ;
			CurrentZoom = newZ;
			GD.Print($"[WorldView] zoom ×{newZ}.");
		}

		private void RotateView(int dir)
		{
			if (_lastSnap == null) return;   // monde pas encore construit
			_orientation = (_orientation + dir + 4) % 4;
			GD.Print($"[WorldView] rotation vue → orientation {_orientation} "
					 + $"({_orientation * 90}° anti-horaire).");
			RebuildWorld();
		}

		// Reconstruit sol + maison + plantes avec l'orientation courante : tout
		// ce qui a été posé via WorldToScreen a une Position FIGÉE, la
		// re-projection passe donc par une reconstruction (kickoff, pédagogie 2).
		// 1188 polygones + ~170 plantes = instantané, pas d'optimisation.
		// SANS fondu : même semaine vue d'un autre coin, pas des naissances.
		// La caméra ne bouge pas (défaut sobre) : la boîte du monde projeté est
		// la même à toute orientation — suivre le MÊME point monde pendant la
		// rotation (ScreenToWorld existe depuis le volet B) reste une finition
		// pour le sprint UI si le besoin se confirme à l'usage.
		private void RebuildWorld()
		{
			_ground.QueueFree();
			_objects.QueueFree();   // emporte maison, plantes, structures et fondus
			_plantNodes.Clear();
			_structs.Clear();       // nœuds libérés avec _objects → ApplyStructures recrée
			_supportNodes.Clear();  // idem → ApplySupports recrée (supports de grimpe ⑥)
			_containers.Clear();    // idem → ApplyContainers recrée (conteneurs ⑥a)

			BuildGround(_world);
			_objects = new Node2D { Name = "Objects", ZIndex = 10, YSortEnabled = true };
			AddWorld(_objects);
			BuildHouse(_world);
			ApplySnapshot(_lastSnap, fade: false);
			// La heatmap se re-projette au _Draw : un redraw suffit (t6·C).
			_fieldOverlay?.QueueRedraw();
		}
	}
}
