// SYMBIOSE — PetalLayer.cs (sprint VERGER VIVANT ④)
// Les PÉTALES AU SOL sous un arbre qui défleurit : quand `floraison` redescend de son pic, des
// pétales de la couleur de la fleur s'accumulent sous la couronne, puis fondent avec la fin de la
// floraison, en quelques semaines. Vue seule : un pétale n'a aucun effet moteur, et aucune litière
// n'est créée (le moteur ne trace pas la fleur comme tissu).
//
// La quantité vient de l'arbre (`PlantRenderer.PetalesAuSol`, FleursArbre.cs) : la part déjà
// défleurie depuis le pic, éteinte quand la floraison s'achève.
//
// 📖 Pédagogie — un semis STATIQUE et EMBOÎTÉ. Le i-ᵉ pétale d'un arbre a toujours la même place
// (hash de l'arbre et de i) ; on en dessine les N premiers, N ∝ la quantité. Quand la quantité
// baisse, les derniers disparaissent et les autres ne bougent pas : rien ne « saute » d'une semaine
// à l'autre. Pas d'animation (philo DA : l'animation signale un état ; ici, l'état est au sol).
// Le calque ne se redessine qu'au snapshot et au changement de cadre, en UN lot (un draw call).
//
// Couleurs littérales : un lot sans texture ne passe pas par le shader indexé (comme LeafFallLayer).
// Zéro Random (philo #3) ; golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PetalLayer : Node2D
	{
		private const float MinZoom = 1f;
		private const float ZoomPetale = 4f;     // en dessous : un grain, au-dessus : un pétale
		private const float CmParPetale = 1.2f;  // au plus fort, un pétale par 1,2 cm de rayon de couronne [choix]
		private const int MaxPetales = 260;
		private const float CullMarginPx = 8f;
		private const float GrainPx = 1.4f;
		private const float PetaleDemiPx = 1.4f, PetaleLargePx = 0.9f;

		private sealed class Tapis
		{
			public PlantRenderer Noeud;
			public float X, Y, RayonCm, Part;
			public uint Hash;
			public Color Ton;
		}

		private readonly Dictionary<string, Tapis> _tapis = new();
		private readonly List<string> _aRetirer = new();
		private readonly LotTriangles _lot = new();
		private Transform2D _canvasVu;
		private Vector2 _projVue = new(float.NaN, float.NaN);
		private float _zoomVu = -1f;

		public override void _Ready() => SetProcess(false);

		/// <summary>Une plante vient d'être appliquée (après SetStructure). Coût nul hors défloraison.</summary>
		public void Noter(string cle, PlantRenderer noeud, float wx, float wy)
		{
			float part = noeud.PetalesAuSol;
			if (part <= 0f)
			{
				if (_tapis.Remove(cle)) QueueRedraw();
				return;
			}
			if (!_tapis.TryGetValue(cle, out var t)) _tapis[cle] = t = new Tapis { Hash = HashKey(cle) };
			t.Noeud = noeud;
			t.X = wx; t.Y = wy;
			t.RayonCm = noeud.OmbreSpreadCm;
			t.Part = part;
			t.Ton = noeud.TonPetale;
			SetProcess(true);
			QueueRedraw();
		}

		// Redessine si le cadre change ; s'arrête quand plus aucun arbre ne défleurit.
		public override void _Process(double delta)
		{
			if (_tapis.Count == 0) { SetProcess(false); QueueRedraw(); return; }
			float z = WorldView.CurrentZoom;
			Transform2D canvas = GetCanvasTransform();
			Vector2 proj = WorldView.WorldToScreen(0f, 0f);
			if (z == _zoomVu && canvas == _canvasVu && proj == _projVue) return;
			_zoomVu = z; _canvasVu = canvas; _projVue = proj;
			QueueRedraw();
		}

		public override void _Draw()
		{
			_lot.Vider();
			float z = WorldView.CurrentZoom;
			if (z >= MinZoom)
			{
				Rect2 vis = (GetCanvasTransform().AffineInverse() * GetViewportRect()).Grow(CullMarginPx);
				_aRetirer.Clear();
				foreach (var kv in _tapis)
				{
					if (!IsInstanceValid(kv.Value.Noeud)) { _aRetirer.Add(kv.Key); continue; }
					Semer(kv.Value, vis, z >= ZoomPetale);
				}
				foreach (string k in _aRetirer) _tapis.Remove(k);
			}
			_lot.Dessiner(this);
		}

		private void Semer(Tapis t, Rect2 vis, bool petale)
		{
			int n = Mathf.RoundToInt(t.Part * Mathf.Min(t.RayonCm / CmParPetale, MaxPetales));
			Color sombre = t.Ton.Darkened(0.12f);
			for (int i = 0; i < n; i++)
			{
				uint h = LeafFallLayer.Melange(t.Hash + (uint)i * 0x9e3779b1u);
				// Plus dense près du tronc : le rayon suit le hash sans racine carrée.
				float ang = Fr(h) * Mathf.Tau, rad = t.RayonCm * (0.15f + 0.85f * Fr(h >> 8));
				Vector2 p = WorldView.WorldToScreen(t.X + rad * Mathf.Cos(ang), t.Y + rad * Mathf.Sin(ang));
				if (!vis.HasPoint(p)) continue;
				Color col = (h >> 16) % 3 == 0 ? sombre : t.Ton;
				if (!petale) { _lot.Grain(p, GrainPx, col); continue; }
				float a = Fr(h >> 24) * Mathf.Pi;
				Vector2 d = new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.5f) * PetaleDemiPx;
				Vector2 l = new Vector2(-d.Y, d.X).Normalized() * PetaleLargePx * 0.5f;
				_lot.Triangle(p - d, p + l, p + d, col);
				_lot.Triangle(p - d, p + d, p - l, col);
			}
		}

		private static float Fr(uint h) => (h & 0xff) / 256f;

		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s) h = ((h << 5) + h) ^ ch;
			return h;
		}
	}
}
