// SYMBIOSE — AllelopathieLayer.cs
// Le HALO DE SOL PELÉ de l'allélopathie racinaire (sprint ALLÉLOPATHIE ⑥). Le champ
// souterrain `allelopathie` du moteur — concentration d'allélochimiques exsudés par
// les racines (juglone du noyer, artémisinine de l'armoise…) qui INHIBENT la levée
// et bride la croissance des voisines — est exposé au snapshot (bloc `allelopathie`
// = liste creuse `[[r, c, concentration], …]`, protocole 0.5.29). On en tire un
// INDICE DIÉGÉTIQUE (philo #5) : là où le sol est chargé, la terre reste NUE/pelée
// (rien ne lève), un halo de terre grisâtre qui s'ouvre plus la charge est forte.
// Le pendant NÉGATIF du tapis de couverture : là où CouvertureLayer verdit le sol
// tapissé, ici on « déshabille » le sol empoisonné. La donnée vient du moteur
// (source de vérité) : on ne recalcule RIEN, on rend `allelo` tel quel. Pas de
// chiffre, pas de barre — juste une zone morte qu'on APPREND à reconnaître.
//
// 📖 Pédagogie — MÊME patron que CouvertureLayer/LitterLayer : UN seul CanvasItem
// redessine tout dans son _Draw (les taches partent en lot, pas un Node2D chacun),
// la rotation D35 est gratuite (re-projection par WorldToScreen/Offset à chaque
// dessin), et le jitter est STABLE (hash, zéro Random — philo #3) : le halo ne
// frétille pas. Le halo est inerte entre deux snapshots → on ne QueueRedraw qu'à
// l'arrivée d'un snapshot et au basculement de LOD.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class AllelopathieLayer : Node2D
	{
		// Terre pelée : brun-gris terne, un poil violacé (le pôle « inhibé » de la
		// heatmap F6 `allelopathie`) — on lit « ici rien ne pousse », pas un signal
		// UI. Sous les rares plantes qui survivent, la teinte reste discrète.
		private static readonly Color PeleColor = new Color("7a6a68");

		// LOD : le halo est un détail de sol qu'on lit en s'approchant (comme la
		// litière/couverture) — invisible en vue d'ensemble. Palier réglable au F5.
		private const float MinZoom = 1f;
		// Marge de culling (px canvas) : couvre l'étalement du jitter d'un plot.
		private const float CullMarginPx = 48f;
		// Étalement du semis DANS le plot (un plot = 50 cm) : on reste dans le losange.
		private const float SpreadCm = 20f;
		// Opacité d'une tache : plancher (un début de charge se voit à peine) + part ∝
		// charge normalisée. Volontairement DISCRET (indice, pas alerte).
		private const float AlphaFloor = 0.08f;
		private const float AlphaSpan  = 0.32f;
		// Nombre de taches à charge pleine (densité du sol pelé) — norm module de 1 à ce max.
		private const int SpecksMax = 6;
		// Normalisation de la concentration : ALLELO_MAX côté moteur = 3.0 (borne
		// GridField, ≡ échelle n/p/k). On borne à cette échelle pour que l'intensité
		// visuelle soit comparable d'une semaine à l'autre (miroir des bornes fixes F6).
		private const float AlleloMax = 3f;

		// Un plot pelé. Position MONDE du centre (cm) ; `Norm` ∈ ]0,1] (charge / MAX)
		// pilote densité et opacité ; `Hash` = graine déterministe du jitter.
		private struct Patch
		{
			public float Cx, Cy;
			public float Norm;
			public uint Hash;
		}

		private readonly List<Patch> _patches = new();
		private bool _lastZoomOk;
		private int _margeVersion = -1;   // cadre commun déjà dessiné (MargeVue, T4)

		// Hash djb2-xor (même choix que CouvertureLayer/LitterLayer : jamais
		// GetHashCode pour du visuel stable, jamais de Random).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s)
				h = ((h << 5) + h) ^ ch;
			return h;
		}

		/// <summary>
		/// Applique le bloc `allelopathie` d'un snapshot (liste creuse par tuile,
		/// 0.5.29). `origins` = origin_cm par tuile (le même cache que plantes/litière).
		/// Reconstruction simple : le halo est inerte (pas de diff/fondu à tenir) et un
		/// snapshot ne tombe qu'à la semaine — pas de churn.
		/// </summary>
		public void SetAllelopathie(GDict allelo, Dictionary<string, Vector2> origins)
		{
			_patches.Clear();
			foreach (var tileKv in allelo)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				foreach (var pv in tileKv.Value.AsGodotArray())
				{
					// Format compact 0.5.29 : [r, c, concentration].
					var e = pv.AsGodotArray();
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					float norm = Mathf.Clamp((float)e[2].AsDouble() / AlleloMax, 0f, 1f);
					if (norm <= 0f) continue;   // sous le plancher : pas de halo
					_patches.Add(new Patch
					{
						// x = est (colonnes), y = sud (lignes) — convention
						// WorldToScreen, jamais une 2ᵉ (leçon D2).
						Cx = o.X + (c + 0.5f) * WorldView.PlotCm,
						Cy = o.Y + (r + 0.5f) * WorldView.PlotCm,
						Norm = norm,
						Hash = HashKey(tileId + "|" + r + "|" + c),
					});
				}
			}
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			if (!Visible) return;
			// Le halo ne s'anime pas : on ne redessine qu'au basculement de LOD.
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk || _margeVersion != MargeVue.Version)
			{
				_lastZoomOk = zoomOk;
				_margeVersion = MargeVue.Version;   // pan/zoom : cadre ré-ancré
				QueueRedraw();
			}
		}

		// PLANTE ASSEMBLÉE ① : les primitives partent en UN lot (LotTriangles,
		// ordre des anciens appels conservé) → un seul draw call pour la couche.
		private readonly LotTriangles _lot = new();

		public override void _Draw()
		{
			_lot.Vider();
			Peindre();
			_lot.Dessiner(this);
		}

		private void Peindre()
		{
			if (_patches.Count == 0 || WorldView.CurrentZoom < MinZoom) return;
			// Culling (T4) : cadre de marge COMMUN et stable (world/MargeVue.cs),
			// + notre marge d'objet ; redessiné au ré-ancrage (pan/zoom), pas par frame.
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			foreach (var p in _patches)
			{
				Vector2 center = WorldView.WorldToScreen(p.Cx, p.Cy);
				if (!vis.HasPoint(center)) continue;   // hors cadre : rien
				Color col = PeleColor;
				col.A = AlphaFloor + AlphaSpan * p.Norm;
				int specks = 1 + Mathf.RoundToInt((SpecksMax - 1) * p.Norm);
				for (int i = 0; i < specks; i++)
				{
					// Jitter déterministe (même schéma que CouvertureLayer) : deux
					// tirages du hash (déphasés par i) → angle + distance dans le plot.
					// Projeté en OFFSET → le semis pivote avec la vue sans glisser (D35).
					uint hi = p.Hash * 2654435761u + (uint)(i * 40503);
					float ang = (hi & 0xffff) * (Mathf.Tau / 65536f);
					float dist = SpreadCm * ((hi >> 16 & 0xff) / 255f);
					Vector2 off = WorldView.WorldToScreenOffset(
						dist * Mathf.Cos(ang), dist * Mathf.Sin(ang));
					// Tache un poil plus large que la couverture (plaque de terre nue,
					// pas un brin d'herbe).
					_lot.Cercle(center + off, 3.0f, col);
				}
			}
		}
	}
}
