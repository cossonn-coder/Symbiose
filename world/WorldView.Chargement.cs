// SYMBIOSE — WorldView.Chargement.cs (partial de WorldView, sprint HOUPPIER ④ ; mycélium :
// LISIÈRE & CHARGEMENT ④)
// L'ÉCRAN DE CHARGEMENT, entre le choix du monde et le jeu : atlas de gerbes, init du moteur
// (+ warmup), montage du monde, puis cuisson du cadre de départ. Le jeu s'ouvre sur des
// plantes déjà cuites, plus sur un dessin direct qui se remplace sous les yeux.
//
// Ce qu'on voit (L3) : une coupe de sol où un MYCÉLIUM pousse depuis une spore, gagne la
// racine d'une plantule et la gaine (mycorhize), puis sort un petit carpophore à 100 %. Il
// SERT de barre de progression (permise ici, E2 : la philo #5 — pas de barre — vaut pendant
// le jeu). Deux textures cuites (tools/splat/cuire_mycelium.js), un shader qui révèle les
// pixels d'âge ≤ progression (visuals/chargement_mycelium.gdshader). Aucun chiffre à l'écran.
//
// L'écran VIT pendant tout le chargement (L5) : le calcul de l'atlas de gerbes et le PONT
// (init + warmup) partent hors du fil principal (`Task.Run`) ; seuls l'envoi de l'atlas au
// GPU et le MONTAGE (arbre de scène, que Godot réserve au fil principal) gèlent l'image.
//
// 📖 Pédagogie — `await` dans Godot. `await Task.Run(...)` rend la main au moteur : les
// images continuent (le mycélium pousse), et la suite de la méthode reprend SUR LE FIL
// PRINCIPAL quand la tâche finit (Godot installe un contexte de synchronisation qui y
// renvoie les continuations). C'est l'équivalent d'une tâche de fond d'un RTOS qui poste
// un message à la boucle principale au lieu de toucher elle-même aux périphériques.
// Le pont n'a qu'UN tube : pendant l'init en fond, personne d'autre ne lui parle (`_Process`
// et les entrées sont coupés tant que `_started` est faux, le sélecteur est déjà libéré) ;
// le verrou d'I/O de SimBridge reste le filet.

using Godot;
using System.Threading.Tasks;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly bool CaptureChargement = ArgCapture("chargement") == "1";
		// Filet : passé ce délai, le jeu s'ouvre quand même ; le reste cuira en jouant.
		private const ulong ChargementMaxMs = 30000;
		// La file doit avoir tourné après le montage avant qu'on la croie au repos.
		private const int ChargementImagesMin = 3;
		private const string DossierChargement = "res://assets/chargement/";
		private const string ShaderChargement = "res://visuals/chargement_mycelium.gdshader";
		private const float EchelleChargement = 4f;   // 480×270 → 1920×1080, pixel entier

		private CanvasLayer _ecranChargement;
		private ShaderMaterial _matChargement;
		private ProgressionChargement _progression = new();
		private Task<(Godot.Collections.Dictionary World, Godot.Collections.Dictionary Snap)> _pontChargement;
		private ulong _chargementT0, _cuissonDepartT0, _phaseT0;
		private long _cuissonsAvant;
		private int _chargementImages, _fileMax;
		private readonly System.Text.StringBuilder _durees = new();

		private async void LancerAvecChargement(string config)
		{
			_chargementT0 = _phaseT0 = Time.GetTicksMsec();
			_progression = new ProgressionChargement();
			_durees.Clear();
			AfficherEcranChargement();
			for (int i = 0; i < 2; i++) await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
			Marquer(PhaseChargement.Gerbes);
			await Task.Run(PlantRenderer.PreparerGerbes);
			PlantRenderer.EnvoyerGerbes();
			Marquer(PhaseChargement.Pont);
			_pontChargement = Task.Run(() => PreparerMonde(config));
			var pret = await _pontChargement;
			if (pret.World == null) return;   // moteur tombé : l'erreur est en console, l'écran reste
			Marquer(PhaseChargement.Montage);
			await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);   // l'écran montre la phase
			ulong m0 = Time.GetTicksMsec();
			MonterMonde(config, pret.World, pret.Snap);   // finit par DebuterCuissonDepart
			GD.Print($"[Chargement] gel du montage : {Time.GetTicksMsec() - m0} ms (fil principal).");
		}

		// Clôt la phase en cours dans le journal et passe à `ph`.
		private void Marquer(PhaseChargement ph)
		{
			ulong t = Time.GetTicksMsec();
			if (ph != PhaseChargement.Gerbes) _durees.Append($"{_progression.Courante} {t - _phaseT0} ms, ");
			_phaseT0 = t;
			_progression.Entrer(ph, t / 1000.0);
		}

		private void AfficherEcranChargement()
		{
			_ecranChargement = new CanvasLayer { Layer = 100 };
			AddChild(_ecranChargement);
			var racine = new Control { Size = new Vector2(1920f, 1080f), MouseFilter = Control.MouseFilterEnum.Stop };
			racine.AddChild(new ColorRect { Color = Palette16.SolTerre, Size = racine.Size });
			_ecranChargement.AddChild(racine);
			var couleur = LireTextureChargement("mycelium_couleur.png");
			var ages = LireTextureChargement("mycelium_ages.png");
			if (couleur != null && ages != null)
			{
				_matChargement = new ShaderMaterial { Shader = GD.Load<Shader>(ShaderChargement) };
				_matChargement.SetShaderParameter("ages", ages);
				racine.AddChild(new TextureRect
				{
					Texture = couleur, Material = _matChargement, TextureFilter = CanvasItem.TextureFilterEnum.Nearest,
					ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
					Size = ages.GetSize() * EchelleChargement,
					Position = (racine.Size - ages.GetSize() * EchelleChargement) * 0.5f,
				});
			}
			var texte = new Label
			{
				Text = "Le jardin se prépare",
				HorizontalAlignment = HorizontalAlignment.Center,
				Position = new Vector2(0f, racine.Size.Y - 110f),
				Size = new Vector2(racine.Size.X, 40f),
			};
			texte.AddThemeFontSizeOverride("font_size", 24);
			racine.AddChild(texte);
		}

		// Les deux images cuites, lues en octets (comme les planches de splats, SplatPlanches.LireImage).
		// Absentes → pas de mycélium, l'écran garde fond et texte (jamais de crash).
		private static ImageTexture LireTextureChargement(string fichier)
		{
			var img = SplatPlanches.LireImage(DossierChargement + fichier);
			return img == null ? null : ImageTexture.CreateFromImage(img);
		}

		// Fin de MonterMonde : le monde est monté, la caméra posée. La file cuit le cadre.
		private void DebuterCuissonDepart()
		{
			CullPlants();   // sans lui, tout le jardin serait « dans la marge »
			BakeQueue.ModeChargement = true;
			Marquer(PhaseChargement.Cuisson);
			_cuissonDepartT0 = Time.GetTicksMsec();
			_cuissonsAvant = PlantBaker.Cuissons;
			_chargementImages = 0;
			_fileMax = 0;
		}

		// Appelé par _Process tant que le jeu n'est pas ouvert : fait pousser le mycélium et,
		// la cuisson finie, attend que le carpophore soit sorti (progression = 1) pour ouvrir.
		private void AvancerChargement(double delta)
		{
			if (_ecranChargement == null) return;
			ulong maintenant = Time.GetTicksMsec();
			float fraction = -1f;
			if (_progression.Courante == PhaseChargement.Cuisson)
			{
				_fileMax = Mathf.Max(_fileMax, BakeQueue.FileEligibles);
				fraction = _fileMax == 0 ? 0f : 1f - BakeQueue.FileEligibles / (float)_fileMax;
				bool delai = maintenant - _cuissonDepartT0 > ChargementMaxMs;
				if (++_chargementImages >= ChargementImagesMin && (BakeQueue.AuRepos || delai))
				{
					BakeQueue.ModeChargement = false;
					GD.Print($"[Chargement] cuisson du cadre {maintenant - _cuissonDepartT0} ms, "
						+ $"{PlantBaker.Cuissons - _cuissonsAvant} cuissons (file max {_fileMax}), "
						+ $"{_chargementImages} images{(delai ? ", délai dépassé" : "")}.");
					Marquer(PhaseChargement.Fini);
				}
			}
			_progression.Avancer(maintenant / 1000.0, delta, fraction);
			_matChargement?.SetShaderParameter("progression", _progression.Valeur);
			if (_progression.Courante != PhaseChargement.Fini || _progression.Valeur < 0.999f) return;
			GD.Print($"[Chargement] phases : {_durees}total {maintenant - _chargementT0} ms.");
			_ecranChargement.QueueFree();
			_ecranChargement = null;
			_matChargement = null;
			_started = true;
		}
	}
}
