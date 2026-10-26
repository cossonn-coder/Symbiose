// SYMBIOSE — PollenLot.cs (PLANTE ASSEMBLÉE ③, extrait de ForagerLayer.cs)
// Le POLLEN DÉPOSÉ par les butineurs (décision Nico 2026-06-18) : à chaque
// atterrissage d'un butineur porteur, un point ambré s'ajoute sur la fleur, capé,
// accumulé toute la saison. C'est un ressenti de VUE (on compte les atterrissages,
// pas le `pollen_recu` exact du moteur) ; vidé au passage de saison.
//
// Pourquoi un nœud à part : mesuré au banc accéléré (×8, 3 s/semaine, VM), le
// pollen faisait l'essentiel du `_Draw` des butineurs — ~700 points redessinés à
// CHAQUE image (le vol des butineurs exige 24 Hz, le pollen, lui, est immobile).
// Ici, le pollen n'est redessiné que sur SIGNAL :
//  - un dépôt / un élagage / la remise à zéro → « sale », redessiné au plus
//    RedessinHz fois par seconde (un point qui apparaît 250 ms plus tard ne se
//    voit pas : l'atterrissage lui-même dure ~1 s) ;
//  - un pan / un zoom / une rotation de vue (le tracé est culé au cadre et
//    projeté par WorldToScreen) → redessin immédiat, comme avant.
//
// 📖 Pédagogie (côté embarqué) : c'est un afficheur à rafraîchissement sur
// changement (« dirty flag ») plutôt qu'à balayage continu — on ne réécrit la
// mémoire d'image que quand la donnée a bougé, et pas plus vite que l'œil.
// Dessiné SOUS les butineurs : enfant de ForagerLayer avec ShowBehindParent.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PollenLot : Node2D
	{
		private const int MaxParFleur = 8;
		private const float PointPx = 1.3f;
		private const float PasSpiraleCm = 2.2f;   // pas de la spirale de points
		private const float RedessinHz = 4f;
		private const float MinZoom = 4f;           // LOD identique aux butineurs
		private const float MargeCullPx = 160f;
		private static readonly Color Couleur = new("fff2a8");

		// Clé = position MONDE de la fleur arrondie au cm (les sauts des butineurs
		// sont des copies exactes des positions de l'index plantes) → nb de points.
		private readonly Dictionary<(int X, int Y), int> _pollen = new();
		private bool _sale;
		private float _accum;
		private Transform2D _canvasVu;
		private Vector2 _projVue = new(float.NaN, float.NaN);
		private bool _zoomVu;

		public PollenLot() { ShowBehindParent = true; }

		public int Fleurs => _pollen.Count;   // rapport de banc (FLUIDITÉ PC ①)

		public static (int, int) Cle(Vector2 p) =>
			((int)Mathf.Round(p.X), (int)Mathf.Round(p.Y));

		/// <summary>Un atterrissage porteur sur la fleur `cle` : +1 point (capé).</summary>
		public void Deposer((int, int) cle)
		{
			int cur = _pollen.TryGetValue(cle, out int v) ? v : 0;
			if (cur >= MaxParFleur) return;
			_pollen[cle] = cur + 1;
			_sale = true;
		}

		/// <summary>Passage de saison : ardoise vierge.</summary>
		public void Vider()
		{
			if (_pollen.Count == 0) return;
			_pollen.Clear();
			_sale = true;
		}

		// Oublie le pollen posé sur une fleur qui n'existe plus (plante morte/retirée
		// entre deux semaines) : les points restent collés aux fleurs VIVANTES.
		public void Elaguer(Dictionary<string, List<Vector2>> plantsByName)
		{
			if (_pollen.Count == 0) return;
			var valid = new HashSet<(int, int)>();
			if (plantsByName != null)
				foreach (var kv in plantsByName)
					foreach (var p in kv.Value)
						valid.Add(Cle(p));
			List<(int, int)> drop = null;
			foreach (var k in _pollen.Keys)
				if (!valid.Contains(k)) (drop ??= new()).Add(k);
			if (drop == null) return;
			foreach (var k in drop) _pollen.Remove(k);
			_sale = true;
		}

		public override void _Process(double delta)
		{
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			// Cadre ou projection changés (pan, zoom, rotation D35) → tout de suite.
			Transform2D canvas = GetCanvasTransform();
			Vector2 proj = WorldView.WorldToScreen(0f, 0f);
			if (zoomOk != _zoomVu || canvas != _canvasVu || proj != _projVue)
			{
				_zoomVu = zoomOk; _canvasVu = canvas; _projVue = proj;
				Redessiner();
				return;
			}
			if (!_sale) return;
			_accum += (float)delta;
			if (_accum >= 1f / RedessinHz) Redessiner();
		}

		private void Redessiner()
		{
			_sale = false;
			_accum = 0f;
			QueueRedraw();
		}

		// n points par fleur, en spirale serrée sur la corolle (angle d'or →
		// répartition régulière sans grille). Offsets en cm MONDE
		// (WorldToScreenOffset) pour tourner avec la vue (D35). Culé par fleur.
		public override void _Draw()
		{
			long t0 = PerfPostes.Debut();   // compté avec les butineurs (banc accéléré)
			Dessiner();
			PerfPostes.Fin(PerfPostes.Poste.ForagerDraw, t0);
		}

		private void Dessiner()
		{
			if (WorldView.CurrentZoom < MinZoom || _pollen.Count == 0) return;
			Rect2 vis = (GetCanvasTransform().AffineInverse()
						 * GetViewportRect()).Grow(MargeCullPx);
			foreach (var kv in _pollen)
			{
				Vector2 c = WorldView.WorldToScreen(kv.Key.X, kv.Key.Y);
				if (!vis.HasPoint(c)) continue;
				for (int i = 0; i < kv.Value; i++)
				{
					float a = i * 2.39996f;                  // angle d'or (rad)
					float rad = PasSpiraleCm * Mathf.Sqrt(i);
					Vector2 off = WorldView.WorldToScreenOffset(
						rad * Mathf.Cos(a), rad * Mathf.Sin(a));
					DrawCircle(c + off, PointPx, Couleur);
				}
			}
		}
	}
}
