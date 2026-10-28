// SYMBIOSE — AtlasPages.cs (sprint PLANTE ASSEMBLÉE ② — pages d'atlas communes, D109 d)
// Le GESTIONNAIRE DE PAGES des plantes cuites. Avant ②, chaque plante cuisait
// dans SA texture (un SubViewport par plante) : deux plantes voisines à l'écran
// = deux textures = deux envois GPU, Godot ne peut rien regrouper. Ici les
// cuissons partagent des PAGES (grands SubViewport communs) : des plantes
// consécutives dans l'ordre de dessin qui lisent la même page forment UN envoi.
//
// 📖 Pédagogie (analogie embarqué) : c'est un allocateur mémoire. Une page est un
// tas de pixels ; chaque plante y réserve un rectangle (malloc) et le rend à sa
// mort ou quand sa taille change (free). Empaquetage par ÉTAGÈRES : la page est
// découpée en bandes horizontales de hauteur arrondie (classe de taille), chaque
// bande garde la liste de ses trous libres (first-fit, trous voisins fusionnés).
// Simple, O(nombre d'étagères), et la fragmentation reste bornée par classe.
//
// 📖 Une page ne se REDESSINE PAS en entier à chaque cuisson (ce serait rejouer
// le dessin vectoriel de toutes ses plantes) : elle ne s'efface jamais seule
// (ClearMode.Never après le tout premier rendu). Une cuisson efface SON rectangle
// (gomme en mélange désactivé = écrit du transparent pur) puis y peint ses
// pinceaux, seuls visibles pendant ce rendu ; les pixels des autres plantes
// restent tels quels en mémoire vidéo.
//
// Une page = un zoom (son CanvasTransform, comme le SubViewport par plante
// d'avant) : changer de palier remplit de nouvelles pages, les anciennes se
// vident à mesure que les plantes recuisent et sont libérées vides.
// Une plante plus grande qu'une page reçoit une page DÉDIÉE à sa taille exacte.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	/// <summary>Un rectangle réservé dans une page (px de la page).</summary>
	internal sealed class AtlasSlot
	{
		public AtlasPage Page;
		public Rect2I Rect;
		public PlantRenderer Owner;
	}

	internal sealed class AtlasPage
	{
		public SubViewport Vp;
		public float Zoom;
		public bool Dediee;
		public bool Vidange;           // trop creuse : plus d'allocation, ses plantes migrent
		public long Occupe;            // px réservés (aire des rectangles)
		public readonly List<AtlasSlot> Slots = new();
		public readonly List<Etagere> Etageres = new();
		public int BasY;               // première ligne libre sous la dernière étagère
		public Gomme Gomme;
		public long Bytes => 4L * Vp.Size.X * Vp.Size.Y;   // RGBA8

		internal sealed class Etagere
		{
			public int Y, H;
			public readonly List<Vector2I> Trous = new();   // (x, largeur)
		}
	}

	/// <summary>Efface les rectangles recuits ce rendu-ci (écrit (0,0,0,0) tel quel).</summary>
	internal sealed partial class Gomme : Node2D
	{
		private static readonly ShaderMaterial Remplace = new()
		{
			Shader = new Shader { Code = "shader_type canvas_item;\nrender_mode blend_disabled;\n" },
		};
		private readonly List<Rect2I> _rects = new();
		private ulong _frame = ulong.MaxValue;

		public Gomme(float zoom)
		{
			Material = Remplace;
			ZIndex = -1;                                   // avant tous les pinceaux
			Scale = new Vector2(1f / zoom, 1f / zoom);     // dessine en px de page
		}

		public void Effacer(Rect2I r)
		{
			// Une nouvelle image = un nouveau rendu de page : on oublie les rectangles
			// du rendu précédent (leurs pinceaux sont masqués, les gommer les viderait).
			ulong f = Engine.GetProcessFrames();
			if (f != _frame) { _rects.Clear(); _frame = f; AtlasPages.Rendus++; }
			_rects.Add(r);
			QueueRedraw();
		}

		public override void _Draw()
		{
			foreach (var r in _rects) DrawRect((Rect2)r, new Color(0, 0, 0, 0));
		}
	}

	internal static class AtlasPages
	{
		// Côté d'une page partagée (px) : 2048² × 4 o = 16 Mo de mémoire vidéo.
		public const int PageSide = 2048;
		// Arrondi des hauteurs d'étagère (classe de taille) et garde entre rectangles.
		private const int PasEtagere = 16;
		private const int Garde = 1;
		// Fragmentation : une page partagée occupée à moins de ce ratio, alors qu'une
		// autre page du même zoom existe, passe en vidange (ses plantes recuisent
		// ailleurs). Mesuré au banc (00_etat.md, ②).
		private const float SeuilVidange = 0.25f;

		private static readonly List<AtlasPage> _pages = new();
		/// <summary>Parent des pages dans l'arbre (BakeQueue, posé à son entrée).</summary>
		public static Node Hote;

		public static long TotalBytes { get; private set; }
		public static int Pages => _pages.Count;
		public static int Vidanges { get; private set; }   // compteur (log de cuisson)

		/// <summary>Réserve un rectangle de `taille` px pour `owner` au zoom donné.</summary>
		public static AtlasSlot Allouer(Vector2I taille, float zoom, PlantRenderer owner)
		{
			var t = taille + new Vector2I(Garde, Garde);
			AtlasSlot s = null;
			if (t.X > PageSide || t.Y > PageSide)
			{
				// Page dédiée à la taille exacte : un seul rectangle, en (0,0).
				AtlasPage d = NouvellePage(taille, zoom, dediee: true);
				s = new AtlasSlot { Page = d, Rect = new Rect2I(Vector2I.Zero, taille) };
				d.Slots.Add(s);
				d.Occupe = (long)taille.X * taille.Y;
			}
			else
			{
				foreach (var p in _pages)
				{
					if (p.Dediee || p.Vidange || p.Zoom != zoom) continue;
					s = Placer(p, taille, t);
					if (s != null) break;
				}
				s ??= Placer(NouvellePage(new Vector2I(PageSide, PageSide), zoom, false), taille, t);
			}
			s.Owner = owner;
			return s;
		}

		/// <summary>Rend le rectangle ; une page vide est libérée.</summary>
		public static void Liberer(AtlasSlot s)
		{
			AtlasPage p = s.Page;
			if (!p.Slots.Remove(s)) return;
			p.Occupe -= (long)s.Rect.Size.X * s.Rect.Size.Y;
			if (p.Slots.Count == 0) { Detruire(p); return; }
			if (!p.Dediee)
			{
				RendreTrou(p, s);
				if (!p.Vidange && p.Occupe < SeuilVidange * PageSide * PageSide && AutrePage(p))
				{
					p.Vidange = true;
					Vidanges++;
					foreach (var o in p.Slots)
						if (GodotObject.IsInstanceValid(o.Owner)) BakeQueue.MarkDirty(o.Owner);
				}
			}
		}

		private static bool AutrePage(AtlasPage p)
		{
			foreach (var q in _pages)
				if (q != p && !q.Dediee && !q.Vidange && q.Zoom == p.Zoom) return true;
			return false;
		}

		// First-fit dans une étagère de même classe de hauteur, sinon nouvelle
		// étagère sous les autres (ou une étagère vide réutilisée), sinon null.
		private static AtlasSlot Placer(AtlasPage p, Vector2I taille, Vector2I t)
		{
			int h = (t.Y + PasEtagere - 1) / PasEtagere * PasEtagere;
			int largeur = p.Vp.Size.X;
			AtlasPage.Etagere e = null;
			int iTrou = -1;
			foreach (var et in p.Etageres)
			{
				bool vide = et.Trous.Count == 1 && et.Trous[0].Y == largeur;
				if (et.H != h && !(vide && et.H >= h)) continue;
				iTrou = et.Trous.FindIndex(tr => tr.Y >= t.X);
				if (iTrou >= 0) { e = et; break; }
			}
			if (e == null)
			{
				if (p.BasY + h > p.Vp.Size.Y) return null;
				e = new AtlasPage.Etagere { Y = p.BasY, H = h };
				e.Trous.Add(new Vector2I(0, largeur));
				p.Etageres.Add(e);
				p.BasY += h;
				iTrou = 0;
			}
			Vector2I trou = e.Trous[iTrou];
			if (trou.Y == t.X) e.Trous.RemoveAt(iTrou);
			else e.Trous[iTrou] = new Vector2I(trou.X + t.X, trou.Y - t.X);
			var s = new AtlasSlot { Page = p, Rect = new Rect2I(trou.X, e.Y, taille) };
			p.Slots.Add(s);
			p.Occupe += (long)taille.X * taille.Y;
			return s;
		}

		// Remet la largeur du rectangle (+ garde) dans les trous de son étagère,
		// fusionne avec les voisins ; les étagères vides du bas sont rendues.
		private static void RendreTrou(AtlasPage p, AtlasSlot s)
		{
			var e = p.Etageres.Find(et => et.Y == s.Rect.Position.Y);
			int x = s.Rect.Position.X, w = s.Rect.Size.X + Garde;
			int i = 0;
			while (i < e.Trous.Count && e.Trous[i].X < x) i++;
			e.Trous.Insert(i, new Vector2I(x, w));
			if (i + 1 < e.Trous.Count && x + w == e.Trous[i + 1].X)
			{
				e.Trous[i] = new Vector2I(x, w + e.Trous[i + 1].Y);
				e.Trous.RemoveAt(i + 1);
			}
			if (i > 0 && e.Trous[i - 1].X + e.Trous[i - 1].Y == x)
			{
				e.Trous[i - 1] = new Vector2I(e.Trous[i - 1].X, e.Trous[i - 1].Y + e.Trous[i].Y);
				e.Trous.RemoveAt(i);
			}
			int largeur = p.Vp.Size.X;
			while (p.Etageres.Count > 0)
			{
				var bas = p.Etageres[^1];
				if (!(bas.Trous.Count == 1 && bas.Trous[0].Y == largeur)) break;
				p.Etageres.RemoveAt(p.Etageres.Count - 1);
				p.BasY = bas.Y;
			}
		}

		// Diagnostic FLUIDITÉ AN 2 ④ : temps passé à créer des pages (remis à zéro
		// par BakeQueue à chaque image, imprimé avec une image de cuisson lente).
		public static long CreationUs;
		public static int Creees;
		// Compteurs CUMULÉS, jamais remis à zéro (FLUIDITÉ PC PARTAGE ③, rapport Z) :
		// le journal de zoom en fait des deltas par image. « Rendus » = pages rendues
		// (une page rendue une fois par image où au moins une cuisson l'a touchée).
		// « Dédiées » = pages à la taille exacte d'une grande plante (jamais en réserve).
		public static long CreeesTotal, CreationUsTotal, ReutiliseesTotal, DetruitesTotal, Rendus;
		public static long DedieesCreeesTotal, DedieesDetruitesTotal;

		private static AtlasPage NouvellePage(Vector2I taille, float zoom, bool dediee)
		{
			ulong t0 = Time.GetTicksUsec();
			try { return CreerPage(taille, zoom, dediee); }
			finally
			{
				long us = (long)(Time.GetTicksUsec() - t0);
				CreationUs += us; Creees++;
				CreationUsTotal += us; CreeesTotal++;
			}
		}

		// RÉSERVE de pages vides (FLUIDITÉ AN 2 ④). Mesuré au banc E VM : créer une
		// page 2048² (SubViewport + cible de rendu) coûte 33-87 ms d'UN bloc
		// [n=12 créations, 1 run] — c'était LA cuisson « unique de 60-74 ms » : le
		// budget ne peut rien contre un seul appel. Or le jardin crée et détruit des
		// pages en continu (une recuisson double l'occupation le temps du Commit, les
		// pages trop creuses se vident). Une page devenue vide est donc GARDÉE (au
		// plus ReserveMax) et resservie, remise à zéro, au lieu d'être recréée.
		// Pas de trou : ses anciens pixels ne sont jamais affichés — chaque cuisson
		// gomme son rectangle avant de peindre (Gomme), et seule la cellule
		// cuite est lue. Mémoire vidéo : la réserve reste comptée dans TotalBytes.
		private const int ReserveMax = 2;
		private static readonly List<AtlasPage> _reserve = new();

		private static AtlasPage CreerPage(Vector2I taille, float zoom, bool dediee)
		{
			if (!dediee && _reserve.Count > 0)
			{
				var r = _reserve[^1];
				_reserve.RemoveAt(_reserve.Count - 1);
				r.Zoom = zoom;
				r.Gomme.Scale = new Vector2(1f / zoom, 1f / zoom);
				r.Vp.CanvasTransform = new Transform2D(0f, new Vector2(zoom, zoom), 0f, Vector2.Zero);
				_pages.Add(r);
				ReutiliseesTotal++;
				return r;
			}
			var p = new AtlasPage { Zoom = zoom, Dediee = dediee };
			if (dediee) DedieesCreeesTotal++;
			p.Vp = new SubViewport
			{
				Size = taille,
				TransparentBg = true,
				Disable3D = true,
				GuiDisableInput = true,
				HandleInputLocally = false,
				// Mêmes accroches au pixel que le SubViewport du monde (WorldView.tscn).
				Snap2DTransformsToPixel = true,
				Snap2DVerticesToPixel = true,
				CanvasItemDefaultTextureFilter = Viewport.DefaultCanvasItemTextureFilter.Nearest,
				RenderTargetUpdateMode = SubViewport.UpdateMode.Disabled,
				// Effacée au premier rendu, plus jamais ensuite : chaque cuisson
				// gomme puis repeint SON rectangle (cf. en-tête).
				RenderTargetClearMode = SubViewport.ClearMode.Once,
			};
			p.Gomme = new Gomme(zoom);
			p.Vp.AddChild(p.Gomme);
			Hote.AddChild(p.Vp);
			// Échelle = zoom du monde (le canvas n'existe qu'une fois dans l'arbre).
			p.Vp.CanvasTransform = new Transform2D(0f, new Vector2(zoom, zoom), 0f, Vector2.Zero);
			_pages.Add(p);
			TotalBytes += p.Bytes;
			return p;
		}

		private static void Detruire(AtlasPage p)
		{
			_pages.Remove(p);
			if (!p.Dediee && _reserve.Count < ReserveMax && GodotObject.IsInstanceValid(p.Vp))
			{
				// Remise à zéro de la comptabilité ; la cible de rendu est gardée.
				p.Vidange = false;
				p.Occupe = 0;
				p.Slots.Clear();
				p.Etageres.Clear();
				p.BasY = 0;
				_reserve.Add(p);
				return;
			}
			TotalBytes -= p.Bytes;
			DetruitesTotal++;
			if (p.Dediee) DedieesDetruitesTotal++;
			if (GodotObject.IsInstanceValid(p.Vp)) p.Vp.QueueFree();
		}
	}
}
