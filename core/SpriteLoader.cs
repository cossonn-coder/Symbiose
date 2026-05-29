// SYMBIOSE — SpriteLoader.cs v2
// Chargement récursif — supporte les sous-dossiers par espèce.
//
// Structure attendue :
//   assets/sprites/tiles/tile_terre.png
//   assets/sprites/plants/tomate/tomato_1_semis.png
//   assets/sprites/plants/basilic/basil_1_semis.png
//   assets/sprites/rondelles/rond_maladie.png
//   assets/sprites/icons/icon_mort.png

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class SpriteLoader : Node
	{
		public static SpriteLoader Instance { get; private set; }

		private readonly Dictionary<string, Texture2D> _textures = new();

		// Dossiers racines — chacun est parcouru récursivement
		private static readonly string[] RootPaths = new[]
		{
			"res://assets/sprites/tiles/",
			"res://assets/sprites/plants/",
			"res://assets/sprites/rondelles/",
			"res://assets/sprites/icons/",
		};

		public override void _Ready()
		{
			Instance = this;
			foreach (var root in RootPaths)
				LoadRecursive(root);

			GD.Print($"[SpriteLoader] {_textures.Count} sprites chargés.");

			// Debug — liste tout ce qui est chargé
			foreach (var key in _textures.Keys)
				GD.Print($"  · {key}");
		}

		// ---------------------------------------------------------------------------
		// CHARGEMENT RÉCURSIF
		// ---------------------------------------------------------------------------

		private void LoadRecursive(string path)
		{
			if (!DirAccess.DirExistsAbsolute(path))
			{
				GD.PrintErr($"[SpriteLoader] Dossier introuvable : {path}");
				return;
			}

			using var dir = DirAccess.Open(path);
			if (dir == null) return;

			dir.ListDirBegin();
			string entry = dir.GetNext();

			while (entry != "")
			{
				// Ignorer fichiers cachés et imports Godot
				if (!entry.StartsWith(".") && !entry.EndsWith(".import"))
				{
					string fullPath = path + entry;

					if (dir.CurrentIsDir())
					{
						// Sous-dossier → descendre récursivement
						LoadRecursive(fullPath + "/");
					}
					else if (entry.EndsWith(".png"))
					{
						// Clé = nom de fichier sans extension
						string key     = entry.Replace(".png", "");
						var    texture = GD.Load<Texture2D>(fullPath);

						if (texture != null)
							_textures[key] = texture;
						else
							GD.PrintErr($"[SpriteLoader] Échec : {fullPath}");
					}
				}
				entry = dir.GetNext();
			}

			dir.ListDirEnd();
		}

		// ---------------------------------------------------------------------------
		// ACCÈS
		// ---------------------------------------------------------------------------

		/// <summary>Retourne une texture par nom de fichier sans extension.</summary>
		public Texture2D Get(string spriteName)
		{
			if (_textures.TryGetValue(spriteName, out var tex))
				return tex;

			GD.PrintErr($"[SpriteLoader] Introuvable : '{spriteName}'");
			return null;
		}

		public Texture2D GetTile(string soilType)     => Get($"tile_{soilType}");
		public Texture2D GetPlant(string spriteName)  => Get(spriteName);
		public Texture2D GetRondelle(string variable) => Get($"rond_{variable}");
		public Texture2D GetIcon(string iconName)     => Get($"icon_{iconName}");

		public bool Has(string spriteName)            => _textures.ContainsKey(spriteName);
		public IEnumerable<string> AllKeys()          => _textures.Keys;
	}
}
