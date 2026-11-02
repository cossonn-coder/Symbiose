// SYMBIOSE — LeafFallLayer.cs (sprint AUTOMNE VISIBLE ⑤)
// La CHUTE des feuilles : pendant les semaines où la couronne d'un caduc se vide
// (`feuillage` du snapshot baisse), des feuilles de sa couleur descendent en
// oscillant depuis la couronne jusqu'au sol, poussées par le vent réel. Le reste de
// l'année ce calque est À L'ARRÊT : l'animation signale un état (philo DA, §3.4).
//
// Ce que la vue montre, et seulement ça : QUAND et COMBIEN la couronne perd sa
// masse sont décidés par Python (`feuillage_visible`, 1 → 0 en CHUTE_SEMAINES). Une
// feuille en l'air n'a aucun effet : celles qui comptent sont dans `litiere`.
//
// 📖 Pédagogie — pas d'état par feuille, comme ForagerLayer : la position d'une
// feuille se RECALCULE de l'horloge. i-ᵉ feuille + n° de son cycle → hash → point de
// départ ; temps écoulé dans le cycle → hauteur, oscillation, dérive. Côté embarqué :
// une fonction pure du temps plutôt qu'un tableau de particules à faire évoluer. Zéro
// Random, zéro allocation par feuille, et la rotation de vue D35 est gratuite.
//
// 📖 Pédagogie — l'horloge `_t` n'avance que si le temps du jeu court (TempsCourt) :
// en pause ou en planification les feuilles restent suspendues, elles ne repartent
// pas de zéro. Tout part en UN lot (LotTriangles = un draw call), redessiné à
// AnimHz ; le pan et le zoom ne redessinent que le cadre et le palier.
//
// Couleurs littérales : un lot sans texture ne peut pas passer par le shader indexé.
// Ce sont les tons d'automne de l'espèce, ceux de la couronne (`OrganPalette.Automne`).

using Godot;
using System;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class LeafFallLayer : Node2D
	{
		private const float MinZoom = 1f;        // zoom de jeu du joueur
		private const float ZoomFeuille = 4f;    // en dessous : un grain, au-dessus : une feuille
		private const float AnimHz = 24f;
		private const float CullMarginPx = 16f;
		private const float FonduSec = 1.5f;     // le filet de feuilles monte et s'éteint
		private const float VChuteCmS = 70f;     // vitesse de descente (F5 : « sans gêner »)
		private const float DureeMinSec = 1.5f;  // un arbuste bas ne crépite pas
		private const float PartActive = 0.7f;   // reste du cycle : feuille absente (irrégularité)
		private const float CmParFeuille = 12f;  // une feuille en l'air par 12 cm de rayon
		private const int MinFeuilles = 2, MaxFeuilles = 32;
		private const float OscillationCm = 14f;
		private const float OscillationRadS = 2.4f;
		private const float DeriveCmS = 90f;     // à force de vent 1
		private const float VentLissageS = 1f;   // le vent change à la semaine : pas de saut
		private const float GrainPx = 1.5f;
		private const float FeuilleDemiPx = 2.6f;
		private const float FeuilleLargePx = 1.2f;
		private static readonly float[] HTons = { 0.17f, 0.5f, 0.83f };   // tons de l'espèce

		// Un caduc suivi : semaine vue, part de couronne vue, et s'il perd ses feuilles.
		private sealed class Emetteur
		{
			public PlantRenderer Noeud;
			public float X, Y, RayonCm, HauteurCm;
			public float Feuillage = 1f;
			public int Semaine;
			public bool Tombe;
			public float Fondu;
			public uint Hash;
			public Color[] Tons;
			public bool Eteint => !Tombe || !IsInstanceValid(Noeud);
		}

		/// <summary>Le temps du jeu court-il ? (posé par WorldView, Saison seulement).</summary>
		public Func<bool> TempsCourt;
		/// <summary>Semaine absolue du snapshot en cours d'application.</summary>
		public int Semaine;

		private readonly Dictionary<string, Emetteur> _emetteurs = new();
		private readonly List<string> _aRetirer = new();
		private readonly LotTriangles _lot = new();
		private double _t;
		private float _accum;
		private Vector2 _vent;   // dérive courante (cm/s, monde)
		private Transform2D _canvasVu;
		private Vector2 _projVue = new(float.NaN, float.NaN);
		private float _zoomVu = -1f;
		private bool _dessinVide = true;

		public override void _Ready() => SetProcess(false);

		/// <summary>Une plante vient d'être appliquée. Coût nul pour une plante dont la
		/// couronne est pleine et qui n'est pas suivie, soit presque toutes.
		/// Même semaine (geste, rotation) : rien ne change, la chute continue.</summary>
		public void Noter(string cle, PlantRenderer noeud, float wx, float wy, float feuillage)
		{
			if (!_emetteurs.TryGetValue(cle, out var e))
			{
				if (feuillage >= 1f) return;
				e = new Emetteur { Hash = HashKey(cle), Semaine = Semaine };
				// Première vue : chargé en pleine chute si la couronne est entamée en automne.
				// Au printemps, 0 < feuillage < 1 veut dire qu'elle se regarnit.
				e.Tombe = feuillage > 0f && WorldView.CurrentSeason == "automne";
				_emetteurs[cle] = e;
			}
			else if (e.Semaine != Semaine)
			{
				e.Tombe = feuillage < e.Feuillage;
				e.Semaine = Semaine;
			}
			e.Feuillage = feuillage;
			e.Noeud = noeud;
			e.X = wx; e.Y = wy;
			e.RayonCm = noeud.OmbreSpreadCm;
			e.HauteurCm = noeud.OmbreHeightCm;
			if (e.Tombe)
			{
				e.Tons ??= new[] { noeud.TonChute(HTons[0]), noeud.TonChute(HTons[1]), noeud.TonChute(HTons[2]) };
				SetProcess(true);
			}
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			bool court = TempsCourt?.Invoke() ?? true;
			if (court) Avancer((float)delta);

			float z = WorldView.CurrentZoom;
			Transform2D canvas = GetCanvasTransform();
			Vector2 proj = WorldView.WorldToScreen(0f, 0f);
			bool vue = z != _zoomVu || canvas != _canvasVu || proj != _projVue;
			if (vue) { _zoomVu = z; _canvasVu = canvas; _projVue = proj; }
			bool anime = court && _accum >= 1f / AnimHz;
			if (anime) _accum = 0f;
			if (z >= MinZoom ? vue || anime : vue && !_dessinVide) QueueRedraw();
		}

		// Horloge, vent lissé, fondu des émetteurs. Le calque s'arrête quand plus rien ne tombe.
		private void Avancer(float dt)
		{
			_t += dt;
			_accum += dt;
			_vent = _vent.Lerp(WindWave.Downwind * WindWave.Force * DeriveCmS,
							   1f - Mathf.Exp(-dt / VentLissageS));
			bool actif = false;
			_aRetirer.Clear();
			foreach (var kv in _emetteurs)
			{
				var e = kv.Value;
				e.Fondu = Mathf.MoveToward(e.Fondu, e.Eteint ? 0f : 1f, dt / FonduSec);
				if (e.Fondu > 0f || !e.Eteint) { actif = true; continue; }
				// Plus rien en l'air : on oublie l'arbre mort ou refeuillé. Nu en hiver,
				// on le garde : sa part vue (0) dit qu'il ne faut pas rejouer sa chute.
				if (!IsInstanceValid(e.Noeud) || e.Feuillage >= 1f) _aRetirer.Add(kv.Key);
			}
			foreach (string k in _aRetirer) _emetteurs.Remove(k);
			if (actif) return;
			SetProcess(false);
			if (!_dessinVide) QueueRedraw();   // efface les dernières feuilles
		}

		public override void _Draw()
		{
			_lot.Vider();
			float z = WorldView.CurrentZoom;
			if (z >= MinZoom)
			{
				Rect2 vis = (GetCanvasTransform().AffineInverse()
							 * GetViewportRect()).Grow(CullMarginPx);
				foreach (var e in _emetteurs.Values)
					if (e.Fondu > 0f) DessinerEmetteur(e, vis, z >= ZoomFeuille);
			}
			_dessinVide = _lot.Sommets == 0;
			_lot.Dessiner(this);
		}

		private void DessinerEmetteur(Emetteur e, Rect2 vis, bool feuille)
		{
			int n = Mathf.Clamp(Mathf.RoundToInt(e.RayonCm / CmParFeuille), MinFeuilles, MaxFeuilles);
			for (int i = 0; i < n; i++)
			{
				uint hi = Melange(e.Hash + (uint)i * 0x9e3779b1u);
				float hauteurDep = e.HauteurCm * (0.45f + 0.55f * Fr(hi));
				float duree = Mathf.Max(DureeMinSec, hauteurDep / VChuteCmS) / PartActive;
				double cycles = _t / duree + Fr(hi >> 8);
				double num = Math.Floor(cycles);
				float u = (float)(cycles - num);
				if (u >= PartActive) continue;
				float v = u / PartActive;   // 0 = quitte la couronne, 1 = touche le sol

				// Chaque cycle a son point de départ : pas deux fois la même trajectoire.
				uint hc = Melange(hi ^ (uint)(long)num);
				float ang = Fr(hc) * Mathf.Tau;
				float rad = e.RayonCm * Mathf.Sqrt(Fr(hc >> 8));
				float sec = u * duree;
				float osc = OscillationRadS * sec + Fr(hc >> 16) * Mathf.Tau;
				float balance = OscillationCm * Mathf.Sin(osc);
				float x = e.X + rad * Mathf.Cos(ang) + _vent.X * sec - balance * Mathf.Sin(ang);
				float y = e.Y + rad * Mathf.Sin(ang) + _vent.Y * sec + balance * Mathf.Cos(ang);
				Vector2 p = WorldView.WorldToScreen(x, y)
					- new Vector2(0f, hauteurDep * (1f - v) * WorldView.PxPerCmZ);
				if (!vis.HasPoint(p)) continue;

				Color col = e.Tons[(hc >> 24) % (uint)e.Tons.Length];
				// La feuille naît dans la couronne et se fond dans le tapis.
				col.A = e.Fondu * Mathf.Min(1f, Mathf.Min(v, 1f - v) * 10f);
				if (feuille) Feuille(p, osc, col);
				else _lot.Grain(p, GrainPx, col);
			}
		}

		// Deux triangles, un côté plus sombre. La largeur suit l'oscillation : la feuille
		// se retourne, elle ne glisse pas.
		private void Feuille(Vector2 p, float osc, Color col)
		{
			float angle = 0.6f * Mathf.Sin(osc) + osc * 0.15f;
			Vector2 d = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * FeuilleDemiPx;
			Vector2 l = d.Orthogonal().Normalized()
				* (FeuilleLargePx * (0.35f + 0.65f * Mathf.Abs(Mathf.Cos(osc))));
			_lot.Triangle(p - d, p + l, p + d, col);
			Color sombre = col.Darkened(0.2f);
			sombre.A = col.A;
			_lot.Triangle(p - d, p + d, p - l, sombre);
		}

		private static float Fr(uint h) => (h & 0xff) / 256f;

		/// <summary>Mélange d'un entier (finaliseur de type murmur) : des voisins donnent
		/// des valeurs sans rapport, sinon un semis fait des alignements visibles.</summary>
		internal static uint Melange(uint h)
		{
			h ^= h >> 16; h *= 0x7feb352du;
			h ^= h >> 15; h *= 0x846ca68bu;
			return h ^ (h >> 16);
		}

		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s) h = ((h << 5) + h) ^ ch;
			return h;
		}
	}
}
