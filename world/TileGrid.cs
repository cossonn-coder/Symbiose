// SYMBIOSE — TileGrid.cs
// Affiche une grille de tuiles isométriques en quinconce.
// Attach ce script sur un Node2D dans la scène principale.

using Godot;
using System.Collections.Generic;
using Symbiose;

public partial class TileGrid : Node2D
{
	// Dimensions tuile isométrique (losange 96×48)
	private const float TileW = 96f;
	private const float TileH = 48f;

	// Grille de la tuile (6 lignes × 8 colonnes = 48 plots)
	private const int GridRows = 6;
	private const int GridCols = 8;

	// Type de sol affiché (à rendre dynamique plus tard)
	[Export] public string SoilType = "terre";

	// Décalage global pour centrer la grille à l'écran
	[Export] public Vector2 GridOffset = new Vector2(200f, 100f);

	// Référence aux sprites des tuiles (un Sprite2D par plot)
	private readonly List<Sprite2D> _tileSprites = new();

	// ---------------------------------------------------------------------------
	// INITIALISATION
	// ---------------------------------------------------------------------------

	public override void _Ready()
	{
		BuildGrid();
	}

	private void BuildGrid()
	{
		// Nettoyer si rebuild
		foreach (var s in _tileSprites) s.QueueFree();
		_tileSprites.Clear();

		var texture = SpriteLoader.Instance?.GetTile(SoilType);
		if (texture == null)
		{
			GD.PrintErr($"[TileGrid] Texture introuvable pour sol='{SoilType}'");
			return;
		}

		for (int row = 0; row < GridRows; row++)
		{
			for (int col = 0; col < GridCols; col++)
			{
				var sprite = new Sprite2D();
				sprite.Texture  = texture;
				sprite.Position = HexToScreen(row, col) + GridOffset;

				// Pixel art — pas d'interpolation
				// L'ancrage par défaut est centre — on garde ça pour les tuiles
				// (le losange isométrique est centré sur son plot)

				// Tri Z : les tuiles du bas passent devant celles du haut
				sprite.ZIndex = row;

				AddChild(sprite);
				_tileSprites.Add(sprite);
			}
		}

		GD.Print($"[TileGrid] {_tileSprites.Count} tuiles affichées ({SoilType}).");
	}

	// ---------------------------------------------------------------------------
	// GÉOMÉTRIE QUINCONCE
	// Identique à Tile.HexToScreen() dans TileData.cs
	// ---------------------------------------------------------------------------

	public static Vector2 HexToScreen(int row, int col)
	{
		float x = col * TileW * 0.75f;
		float y = row * TileH * 0.5f;
		if (col % 2 == 1)
			y += TileH * 0.25f;
		return new Vector2(x, y);
	}

	// ---------------------------------------------------------------------------
	// CHANGEMENT DE SOL EN COURS DE JEU
	// ---------------------------------------------------------------------------

	public void SetSoilType(string soilType)
	{
		SoilType = soilType;
		BuildGrid();
	}

	// ---------------------------------------------------------------------------
	// CONVERSION ÉCRAN → PLOT (pour le clic joueur)
	// Retourne (-1,-1) si hors grille.
	// ---------------------------------------------------------------------------

	public (int row, int col) ScreenToHex(Vector2 screenPos)
	{
		Vector2 local = screenPos - GridOffset;

		// Approximation colonne
		int col = Mathf.RoundToInt(local.X / (TileW * 0.75f));
		col = Mathf.Clamp(col, 0, GridCols - 1);

		// Approximation ligne avec décalage quinconce
		float yOffset = (col % 2 == 1) ? TileH * 0.25f : 0f;
		int row = Mathf.RoundToInt((local.Y - yOffset) / (TileH * 0.5f));
		row = Mathf.Clamp(row, 0, GridRows - 1);

		// Valider que le point est bien dans le losange du plot trouvé
		Vector2 plotCenter = HexToScreen(row, col) + GridOffset;
		Vector2 delta      = screenPos - plotCenter;

		// Test losange isométrique : |dx|/TileW*2 + |dy|/TileH < 0.5
		float lozTest = Mathf.Abs(delta.X) / TileW + Mathf.Abs(delta.Y) / (TileH * 0.5f);
		if (lozTest > 1.0f)
			return (-1, -1);

		return (row, col);
	}

	// ---------------------------------------------------------------------------
	// DEBUG — affiche les coordonnées au survol (à retirer plus tard)
	// ---------------------------------------------------------------------------

	public override void _Input(InputEvent @event)
	{
		if (@event is InputEventMouseMotion motion)
		{
			var (row, col) = ScreenToHex(motion.Position);
			if (row >= 0)
				GD.Print($"[TileGrid] Survol plot ({row},{col})");
		}
	}
}
