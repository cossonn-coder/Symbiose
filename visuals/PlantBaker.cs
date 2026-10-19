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
// Atlas de POSES : l'image est une rangée de cellules, une par degré de flexion
// au vent (T3) : 1 au calme, jusqu'à 8 (PlantRenderer.MaxPoses) sous le vent —
// un port raide (arbre) n'en cuit que 3-4, il ne se couche jamais.
// PLANTE ASSEMBLÉE ② (D109 d) : l'image n'est plus un SubViewport PAR PLANTE
// mais un rectangle réservé dans une PAGE d'atlas commune (AtlasPages.cs) — les
// plantes voisines lisent la même texture, Godot les envoie en un seul lot. Les
// pinceaux vivent dans la page, à la position du rectangle, visibles le seul
// temps de leur cuisson.
// D106 T6 : chaque pose a SA cellule SERRÉE (sa boîte + son ancrage du collet)
// au lieu de l'union de la pose droite et de la plus couchée répétée 8 fois
// (116 Mo au vent vs 12,8 Mo au calme [×8, 51 plantes, n=1]). La plante ne
// « saute » pas d'une pose à l'autre : DrawImage pose chaque cellule à partir
// de SON ancrage, le collet reste sur le même pixel.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	internal sealed class PlantBaker
	{
		// Au-delà de ce côté (px du SubViewport monde), on ne cuit pas : la plante
		// reste en dessin direct (un grand arbre à ×8 ferait > 15 Mo d'image pour
		// un objet qui déborde déjà de l'écran — le vectoriel y est moins cher).
		public const int MaxSidePx = 2048;
		// T3 : largeur max de l'ATLAS (toutes poses côte à côte). Garde la mémoire
		// d'une plante ≤ 4096 × 2048 × 4 o = 32 Mo et sous la limite GPU (16384).
		public const int MaxAtlasPx = 4096;

		// Comptabilité mémoire vidéo de TOUTES les images cuites (rapport F4/log) :
		// depuis ② ce sont les pages communes (une « image » = une page).
		public static long TotalBytes => AtlasPages.TotalBytes;
		public static int TotalImages => AtlasPages.Pages;
		// Banc PERF VUE ④ : cuissons lancées et poses cuites (moyenne poses/cuisson).
		public static long Cuissons, PosesCuites;

		private readonly PlantRenderer _owner;

		// Image AFFICHÉE (_shown) et cuisson EN VOL (_next). Distinctes quand la
		// géométrie change (taille, zoom) : l'ancienne image reste à l'écran
		// jusqu'à ce que la nouvelle soit rendue (jamais de trou, jamais d'image
		// à moitié allouée). Même géométrie → on recuit sur place.
		private Cell _shown, _next;
		private int _nextUtiles = 1;   // cellules peintes par la cuisson en vol (D109 c)

		private sealed class Cell
		{
			public AtlasSlot Slot;       // rectangle réservé dans une page commune (②)
			public readonly List<PlantRenderer> Brushes = new();
			public Rect2I[] Cells;       // par pose : x dans le rectangle (y = 0) + taille
			public Vector2I[] Origins;   // par pose : px du collet dans SA cellule
			public float Zoom;
			public int Utiles = 1;       // cellules peintes (≤ Poses), D109 c
			public int Poses => Cells.Length;

			// Même découpage (tailles, ancrages, zoom) → on recuit sur place, sauf
			// si la page est en vidange (la plante migre vers une page plus pleine).
			public bool Matches(Rect2I[] cells, Vector2I[] origins, float zoom) =>
				Zoom == zoom && !Slot.Page.Vidange && Cells.Length == cells.Length
				&& System.Linq.Enumerable.SequenceEqual(Cells, cells)
				&& System.Linq.Enumerable.SequenceEqual(Origins, origins);
		}

		public PlantBaker(PlantRenderer owner) => _owner = owner;

		public bool HasImage => _shown != null;
		public bool InFlight => _next != null;

		/// <summary>Lance la cuisson au zoom `zoom` (rendue en fin de frame).
		/// false = rien à cuire ou trop grand → la plante reste en direct.</summary>
		public bool Begin(float zoom)
		{
			int poses = _owner.BakePoseCount;
			var cells = new Rect2I[poses];
			var origins = new Vector2I[poses];
			int x = 0, h = 0;
			for (int k = 0; k < poses; k++)
			{
				// Boîte SERRÉE de la pose k (T6) : la plante droite ne paie plus la
				// largeur de sa pose la plus couchée.
				Rect2 b = _owner.PoseBounds(k);
				if (b.Size == Vector2.Zero) { Release(); return false; }
				// Décalage ENTIER du collet dans la cellule (+1 px de garde) et taille.
				var origin = new Vector2I(1 - Mathf.FloorToInt(b.Position.X * zoom),
										  1 - Mathf.FloorToInt(b.Position.Y * zoom));
				var size = new Vector2I(origin.X + Mathf.CeilToInt(b.End.X * zoom) + 1,
										origin.Y + Mathf.CeilToInt(b.End.Y * zoom) + 1);
				if (size.X > MaxSidePx || size.Y > MaxSidePx) { Release(); return false; }
				cells[k] = new Rect2I(x, 0, size.X, size.Y);
				origins[k] = origin;
				x += size.X;
				h = Mathf.Max(h, size.Y);
			}
			if (x > MaxAtlasPx) { Release(); return false; }

			Cell cell = _shown != null && _shown.Matches(cells, origins, zoom)
				? _shown : NewCell(cells, origins, new Vector2I(x, h), zoom);
			// D109 (c) : seules les poses ATTEIGNABLES sont peintes ; les cellules
			// au-delà restent vides (pinceau masqué), jamais affichées (DrawImage).
			// Recuisson SUR PLACE : jusqu'au Commit, on n'affiche que les cellules
			// peintes à la fois avant et après (jamais une cellule vidée cette frame).
			_nextUtiles = _owner.BakePosesUtiles;
			cell.Utiles = cell == _shown ? Mathf.Min(cell.Utiles, _nextUtiles) : _nextUtiles;
			for (int k = 0; k < poses; k++)
			{
				bool peinte = k < _nextUtiles;
				cell.Brushes[k].Visible = peinte;
				if (!peinte) continue;
				_owner.CopyDrawStateTo(cell.Brushes[k]);
				cell.Brushes[k].SetBrushPose(k);   // cellule k = flexion k/7
			}
			// ② : la page ne s'efface pas seule → on gomme NOTRE rectangle, puis la
			// page est rendue une fois avec nos seuls pinceaux visibles.
			AtlasPage page = cell.Slot.Page;
			page.Gomme.Effacer(cell.Slot.Rect);
			page.Vp.RenderTargetUpdateMode = SubViewport.UpdateMode.Once;
			Cuissons++;
			PosesCuites += _nextUtiles;
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
			_shown.Utiles = _nextUtiles;
			_next = null;
			// Rendu fait : les pixels restent dans la page, les pinceaux se taisent
			// (sinon le prochain rendu de la page les rejouerait pour rien).
			foreach (var b in _shown.Brushes) b.Visible = false;
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
		/// LOCALES du PlantRenderer (un px cuit = 1/zoom px canvas). Une pose
		/// absente de l'atlas (cuit au calme, vent levé depuis) ou non peinte (vent
		/// qui vient de forcir, recuisson en file) → la plus couchée PEINTE.</summary>
		public void DrawImage(int pose = 0)
		{
			Cell c = _shown;
			pose = Mathf.Min(pose, c.Utiles - 1);
			Rect2I cell = c.Cells[pose];
			// Ancrage PROPRE à la pose : le collet tombe toujours au même endroit.
			var rect = new Rect2(-(Vector2)c.Origins[pose] / c.Zoom, (Vector2)cell.Size / c.Zoom);
			var src = new Rect2I(cell.Position + c.Slot.Rect.Position, cell.Size);
			_owner.DrawTextureRectRegion(c.Slot.Page.Vp.GetTexture(), rect, (Rect2)src);
		}

		private Cell NewCell(Rect2I[] cells, Vector2I[] origins, Vector2I atlas, float zoom)
		{
			var c = new Cell { Cells = cells, Origins = origins, Zoom = zoom };
			c.Slot = AtlasPages.Allouer(atlas, zoom, _owner);
			Vector2I o = c.Slot.Rect.Position;
			for (int k = 0; k < cells.Length; k++)
			{
				// Pinceau k : son collet sur un pixel ENTIER de la page (coin du
				// rectangle + x de la cellule + ancrage), en px canvas (÷ zoom).
				var brush = new PlantRenderer
				{
					IsBrush = true,
					Visible = false,
					Position = new Vector2(o.X + cells[k].Position.X + origins[k].X,
										   o.Y + origins[k].Y) / zoom,
				};
				c.Slot.Page.Vp.AddChild(brush);
				c.Brushes.Add(brush);
			}
			return c;
		}

		private static void Free(Cell c)
		{
			foreach (var b in c.Brushes)
				if (GodotObject.IsInstanceValid(b)) b.QueueFree();
			AtlasPages.Liberer(c.Slot);
		}
	}
}
