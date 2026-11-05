// SYMBIOSE — WorldView.Chargement.cs (partial de WorldView, sprint HOUPPIER ④)
// L'ÉCRAN DE CHARGEMENT, entre le choix du monde et le jeu : génération de l'atlas de gerbes,
// montage du monde, puis cuisson du cadre de départ. Le jeu s'ouvre sur des plantes déjà cuites,
// plus sur un dessin direct qui se remplace sous les yeux. Sans chiffre ni barre (philo #5).
//
// Le vent : rien de spécial ici. `PlantBaker.Begin` ne peint que les poses atteignables
// (`BakePosesUtiles`) : on cuit ce que le cadre peut montrer, pas 8 poses par plante.
//
// 📖 Pédagogie — pourquoi attendre deux images. `_bridge.Init` et le montage BLOQUENT le fil
// principal, et une image se dessine en fin de boucle. Si on enchaînait dans le même appel, l'écran
// serait créé mais jamais affiché. `await ToSignal(..., ProcessFrame)` rend la main au moteur et
// reprend à l'image suivante, comme céder au scheduler d'un RTOS avant une tâche longue.

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly bool CaptureChargement = ArgCapture("chargement") == "1";
		// Filet : passé ce délai, le jeu s'ouvre quand même ; le reste cuira en jouant.
		private const ulong ChargementMaxMs = 30000;
		// La file doit avoir tourné après le montage avant qu'on la croie au repos.
		private const int ChargementImagesMin = 3;

		private CanvasLayer _ecranChargement;
		private ulong _chargementT0, _cuissonDepartT0;
		private long _cuissonsAvant;
		private int _chargementImages;

		private async void LancerAvecChargement(string config)
		{
			_chargementT0 = Time.GetTicksMsec();
			AfficherEcranChargement();
			for (int i = 0; i < 2; i++) await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
			PlantRenderer.AssurerGerbes();
			StartSimulation(config);
		}

		private void AfficherEcranChargement()
		{
			_ecranChargement = new CanvasLayer { Layer = 100 };
			AddChild(_ecranChargement);
			var racine = new Control { Size = new Vector2(1920f, 1080f), MouseFilter = Control.MouseFilterEnum.Stop };
			racine.AddChild(new ColorRect { Color = Palette16.SolTerre, Size = racine.Size });
			_ecranChargement.AddChild(racine);
			var image = PlantRenderer.TouffeChargement();
			var pousse = ImageTexture.CreateFromImage(image);
			Vector2 taille = pousse.GetSize() * 8f;
			Piece(racine, pousse, (racine.Size - taille) * 0.5f - new Vector2(0f, 40f), 8f);
			var texte = new Label
			{
				Text = "Le jardin se prépare",
				HorizontalAlignment = HorizontalAlignment.Center,
				Position = new Vector2(0f, racine.Size.Y * 0.5f + 40f),
				Size = new Vector2(racine.Size.X, 40f),
			};
			texte.AddThemeFontSizeOverride("font_size", 24);
			racine.AddChild(texte);
		}

		// Fin de StartSimulation : le monde est monté, la caméra posée. La file cuit le cadre.
		private void DebuterCuissonDepart()
		{
			CullPlants();   // sans lui, tout le jardin serait « dans la marge »
			BakeQueue.ModeChargement = true;
			_cuissonDepartT0 = Time.GetTicksMsec();
			_cuissonsAvant = PlantBaker.Cuissons;
			_chargementImages = 0;
		}

		// Appelé par _Process tant que le jeu n'est pas ouvert.
		private void AvancerChargement()
		{
			if (_ecranChargement == null || !BakeQueue.ModeChargement) return;
			ulong maintenant = Time.GetTicksMsec();
			bool delai = maintenant - _cuissonDepartT0 > ChargementMaxMs;
			if (++_chargementImages < ChargementImagesMin || (!BakeQueue.AuRepos && !delai)) return;
			BakeQueue.ModeChargement = false;
			GD.Print($"[Chargement] montage {_cuissonDepartT0 - _chargementT0} ms, cuisson du cadre "
				+ $"{maintenant - _cuissonDepartT0} ms, {PlantBaker.Cuissons - _cuissonsAvant} cuissons, "
				+ $"{_chargementImages} images{(delai ? ", délai dépassé" : "")}.");
			_ecranChargement.QueueFree();
			_ecranChargement = null;
			_started = true;
		}
	}
}
