// SYMBIOSE — PlantBaker.cs (sprint JARDIN VIVANT T2 — pré-cuisson par instance)
// Le CUISEUR d'une plante : transforme son dessin vectoriel en une image GPU,
// au palier de zoom courant, sans aucune lecture GPU→CPU.
//
// 📖 Technique retenue (mesurée, cf. 00_etat.md) : un SubViewport PAR PLANTE,
// enfant du PlantRenderer, contenant un PINCEAU (un PlantRenderer « IsBrush »
// qui a reçu une copie de l'état dessiné). On le rend UNE fois (UpdateMode.Once) :
// sa texture de rendu EST l'image cuite, affichée par DrawTextureRect. Rien ne
// remonte en RAM CPU (pas de GetImage() bloquant) ; un SubViewport au repos
// (Once déjà consommé) ne coûte plus rien par frame — seulement sa mémoire vidéo.
//
// 📖 Alignement pixel : le SubViewport du monde accroche transforms et sommets au
// pixel (snap_2d_*). Le pinceau est rendu avec la MÊME échelle (zoom), les mêmes
// accroches et un collet sur un pixel ENTIER ; l'image est posée sur un pixel
// entier. Résidu mesuré : arêtes de branches décalées d'1 px sur ~0,2 % de
// l'image (arrondis du rastériseur, 00_etat.md) — reporter la phase sous-pixel
// du collet a été essayé et fait PIRE (3 variantes mesurées).
//
// Atlas de POSES : l'image est une rangée de PoseCount cellules (une par pose).
// T2 = 1 pose (celle d'aujourd'hui) ; T3 portera PoseCount à 8 (flexion au vent).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	internal sealed class PlantBaker
	{
		/// <summary>Nombre de poses par plante (T2 : 1 ; T3 : 8 degrés de flexion).</summary>
		public const int PoseCount = 1;

		// Au-delà de ce côté (px du SubViewport monde), on ne cuit pas : la plante
		// reste en dessin direct (un grand arbre à ×8 ferait > 15 Mo d'image pour
		// un objet qui déborde déjà de l'écran — le vectoriel y est moins cher).
		public const int MaxSidePx = 2048;

		// Comptabilité mémoire vidéo de TOUTES les images cuites (rapport F4/log).
		public static long TotalBytes { get; private set; }
		public static int TotalImages { get; private set; }

		private readonly PlantRenderer _owner;

		// Image AFFICHÉE (_shown) et cuisson EN VOL (_next). Distinctes quand la
		// géométrie change (taille, zoom) : l'ancienne image reste à l'écran
		// jusqu'à ce que la nouvelle soit rendue (jamais de trou, jamais d'image
		// à moitié allouée). Même géométrie → on recuit sur place.
		private Cell _shown, _next;

		private sealed class Cell
		{
			public SubViewport Vp;
			public readonly List<PlantRenderer> Brushes = new();
			public Vector2I CellSize;    // px d'une pose
			public Vector2I Origin;      // px du collet dans une cellule
			public float Zoom;
			public long Bytes => 4L * Vp.Size.X * Vp.Size.Y;   // RGBA8
		}

		public PlantBaker(PlantRenderer owner) => _owner = owner;

		public bool HasImage => _shown != null;
		public bool InFlight => _next != null;

		/// <summary>Lance la cuisson au zoom `zoom` (rendue en fin de frame).
		/// false = rien à cuire ou trop grand → la plante reste en direct.</summary>
		public bool Begin(float zoom)
		{
			Rect2 b = _owner.LocalBounds();
			if (b.Size == Vector2.Zero) { Release(); return false; }
			// Décalage ENTIER du collet dans la cellule (+1 px de garde) et taille.
			var origin = new Vector2I(1 - Mathf.FloorToInt(b.Position.X * zoom),
									  1 - Mathf.FloorToInt(b.Position.Y * zoom));
			var size = new Vector2I(origin.X + Mathf.CeilToInt(b.End.X * zoom) + 1,
									origin.Y + Mathf.CeilToInt(b.End.Y * zoom) + 1);
			if (size.X * PoseCount > MaxSidePx || size.Y > MaxSidePx) { Release(); return false; }

			Cell cell = _shown != null && _shown.CellSize == size
						&& _shown.Origin == origin && _shown.Zoom == zoom
				? _shown : NewCell(size, origin, zoom);
			for (int k = 0; k < PoseCount; k++)
				_owner.CopyDrawStateTo(cell.Brushes[k]);
			cell.Vp.RenderTargetUpdateMode = SubViewport.UpdateMode.Once;
			if (_next != null && _next != cell && _next != _shown) Free(_next);
			_next = cell;
			return true;
		}

		/// <summary>Frame suivante : la cuisson est rendue → elle devient l'image
		/// affichée, l'ancienne (autre géométrie) est libérée.</summary>
		public void Commit()
		{
			if (_next == null) return;
			if (_shown != null && _shown != _next) Free(_shown);
			_shown = _next;
			_next = null;
		}

		/// <summary>Libère toutes les images (plante retirée, hors champ, ou trop
		/// grande) → retour au dessin direct.</summary>
		public void Release()
		{
			if (_next != null && _next != _shown) Free(_next);
			if (_shown != null) Free(_shown);
			_shown = _next = null;
		}

		/// <summary>Affiche la pose `pose` de l'image cuite, en coordonnées
		/// LOCALES du PlantRenderer (un px cuit = 1/zoom px canvas).</summary>
		public void DrawImage(int pose = 0)
		{
			Cell c = _shown;
			var rect = new Rect2(-(Vector2)c.Origin / c.Zoom, (Vector2)c.CellSize / c.Zoom);
			var src = new Rect2(c.CellSize.X * pose, 0, c.CellSize.X, c.CellSize.Y);
			_owner.DrawTextureRectRegion(c.Vp.GetTexture(), rect, src);
		}

		private Cell NewCell(Vector2I size, Vector2I origin, float zoom)
		{
			var c = new Cell { CellSize = size, Origin = origin, Zoom = zoom };
			c.Vp = new SubViewport
			{
				Size = new Vector2I(size.X * PoseCount, size.Y),
				TransparentBg = true,
				Disable3D = true,
				GuiDisableInput = true,
				HandleInputLocally = false,
				// Mêmes accroches au pixel que le SubViewport du monde (WorldView.tscn).
				Snap2DTransformsToPixel = true,
				Snap2DVerticesToPixel = true,
				CanvasItemDefaultTextureFilter = Viewport.DefaultCanvasItemTextureFilter.Nearest,
				RenderTargetUpdateMode = SubViewport.UpdateMode.Disabled,
			};
			for (int k = 0; k < PoseCount; k++)
			{
				// Une pose = une cellule décalée d'un nombre ENTIER de px cuits.
				var brush = new PlantRenderer
				{
					IsBrush = true,
					Position = new Vector2(size.X * k / zoom, 0f),
				};
				c.Vp.AddChild(brush);
				c.Brushes.Add(brush);
			}
			_owner.AddChild(c.Vp);
			// Échelle = zoom du monde, collet posé sur un pixel ENTIER (le canvas
			// du SubViewport n'existe qu'une fois dans l'arbre → après AddChild).
			c.Vp.CanvasTransform = new Transform2D(0f, new Vector2(zoom, zoom), 0f, origin);
			TotalBytes += c.Bytes;
			TotalImages++;
			return c;
		}

		private static void Free(Cell c)
		{
			TotalBytes -= c.Bytes;
			TotalImages--;
			if (GodotObject.IsInstanceValid(c.Vp)) c.Vp.QueueFree();
		}
	}
}
