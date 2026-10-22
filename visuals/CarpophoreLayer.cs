// SYMBIOSE — CarpophoreLayer.cs
// Les CARPOPHORES visibles (sprint mycélium ④/⑥, §4) : les champignons qui
// PERCENT après la pluie, en automne, là où le réseau souterrain `mycelium` est
// dense et le sol humide. Ils sont la SEULE fenêtre directe sur l'acteur fongique
// (le réseau lui-même reste souterrain, invisible hors overlay debug F6). Indice
// diégétique de la santé fongique du sol (philo #5/#6 : laisser le sol couvert,
// non bêché → des champignons poussent).
//
// 📖 Pédagogie — MÊME modèle que MacroLife/FieldOverlay : UN seul CanvasItem
// batché redessine tous les chapeaux dans son _Draw, pas un Node2D par
// champignon. Les carpophores sont de la PERCEPTION pure échantillonnée par le
// serveur (sample_carpophores, zéro état moteur) → la vue ne fait que LIRE le
// bloc `carpophores` du snapshot et le dessiner. Ils sont SESSILES (pas d'errance
// comme les bestioles) : un fondu d'apparition/disparition suffit (ils poussent
// après la pluie, fanent ensuite). Positions déterministes (hash serveur) → la
// clé de diff (tile|r|c|x|y) survit d'une semaine à l'autre, comme MacroLife.

using Godot;
using System.Collections.Generic;
using System.Globalization;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class CarpophoreLayer : Node2D
	{
		// Fondus calés sur le reste de la vue (plantes/macro) : un seul langage
		// visuel pour « apparaît / disparaît de l'écosystème ».
		private const float FadeInSec = 0.6f;
		private const float FadeOutSec = 0.9f;
		private const float BaseAlpha = 0.95f;
		// LOD (comme MacroLife) : les champignons sont petits, on ne les peint
		// qu'à partir du palier pixel-art ×4 — à la vue d'ensemble on lit le
		// paysage, pas les chapeaux. C'est aussi le garde-fou de perf (au-delà la
		// caméra ne cadre qu'une fraction du monde, on dessine peu).
		private const float MinZoom = 4f;

		// Teintes et silhouettes : PAR ESPÈCE depuis ⑧ (CarpophoreStyles.cs ; repli
		// = l'ancien champignon brun de sous-bois).

		// Un chapeau affiché. Position MONDE absolue (cm) ; densite ∝ taille.
		private class Entry
		{
			public float Wx, Wy, Densite;
			public string Role;           // b / r / h (pont ≥ 0.5.47), null : absent
			public string Espece;         // clé d'espèce (pont ≥ 0.5.52), null : absent
			public string Tile;           // désignation du geste `manger` (⑧) :
			public int R, C, Slot = -1;   // [r, c, slot] ; slot -1 = pont pré-0.5.56
			public StyleCarpo Style;      // portrait de l'espèce (résolu une fois)
			public uint Phase;            // hash de la clé → taille/inclinaison propres
			public float BornAt;
			public float DyingAt = -1f;   // < 0 : vivant
		}

		// Clé stable (tile|r|c|x|y) → chapeau (cf. MacroLife : le serveur arrondit
		// x/y de façon déterministe, la clé survit aux semaines).
		private readonly Dictionary<string, Entry> _entries = new();

		/// <summary>Carpophore VIVANT dont l'ANCRE est la plus proche du point MONDE
		/// (cm), dans `rayonCm`, ou null (D60 ② : survol → observation du
		/// champignon ; INFO-BULLE ③ : + rôle local et densité du réseau). Clé =
		/// l'ESPÈCE du carpophore (sol qui respire ⑤ : une fiche par espèce), repli
		/// « champignon » d'un pont pré-0.5.52. On teste
		/// l'ancre (position snapshot stable, les chapeaux sont sessiles). `role`
		/// non null : ne retient que ce rôle local (banc de capture ③).</summary>
		public MacroPick? Near(Vector2 wMonde, float rayonCm, string role = null)
		{
			float bestD = rayonCm * rayonCm;
			Entry best = null;
			foreach (var e in _entries.Values)
			{
				if (e.DyingAt >= 0f || (role != null && e.Role != role)) continue;
				float dx = e.Wx - wMonde.X, dy = e.Wy - wMonde.Y;
				float d = dx * dx + dy * dy;
				if (d <= bestD) { bestD = d; best = e; }
			}
			return best == null ? null
				: new MacroPick(best.Espece ?? "champignon", 1, -1f, best.Role, best.Densite,
								new Vector2(best.Wx, best.Wy));
		}

		/// <summary>Désignation `target.carpophore [r, c, slot]` du carpophore VIVANT
		/// le plus proche (geste `manger`, ⑧) : false si aucun dans le rayon ou si le
		/// pont ne donne pas le slot (pré-0.5.56). `distCm` = distance à l'ancre.</summary>
		public bool Cible(Vector2 wMonde, float rayonCm, out string tile, out int r,
						  out int c, out int slot, out float distCm)
		{
			tile = null; r = c = slot = -1; distCm = float.MaxValue;
			float bestD = rayonCm * rayonCm;
			Entry best = null;
			foreach (var e in _entries.Values)
			{
				if (e.DyingAt >= 0f || e.Slot < 0) continue;
				float dx = e.Wx - wMonde.X, dy = e.Wy - wMonde.Y;
				float d = dx * dx + dy * dy;
				if (d <= bestD) { bestD = d; best = e; }
			}
			if (best == null) return false;
			tile = best.Tile; r = best.R; c = best.C; slot = best.Slot;
			distCm = Mathf.Sqrt(bestD);
			return true;
		}

		private static float NowSec() => Time.GetTicksMsec() / 1000f;

		// Hash djb2-xor (déterministe inter-sessions — jamais GetHashCode pour du
		// visuel stable, leçon t6·A).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s) h = ((h << 5) + h) ^ ch;
			return h;
		}

		/// <summary>
		/// Applique le bloc `carpophores` d'un snapshot (diff doux, même patron que
		/// MacroLife) : format COMPACT par tuile `[r, c, x_frac, y_frac, densite,
		/// role]` (role b/r/h depuis 0.5.47, absent d'un pont plus ancien).
		/// Clé connue → maj de la densité ; nouvelle → fondu d'entrée ; disparue →
		/// fondu de sortie puis oubli. `origins` = origin_cm par tuile.
		/// </summary>
		public void SetCarpophores(GDict carpophores,
								   Dictionary<string, Vector2> origins, bool fade)
		{
			float now = NowSec();
			var seen = new HashSet<string>();
			foreach (var tileKv in carpophores)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				foreach (var kv in tileKv.Value.AsGodotArray())
				{
					var a = kv.AsGodotArray();
					int r = a[0].AsInt32(), c = a[1].AsInt32();
					double xf = a[2].AsDouble(), yf = a[3].AsDouble();
					float dens = (float)a[4].AsDouble();
					string role = a.Count > 5 ? a[5].AsString() : null;
					string espece = a.Count > 6 ? a[6].AsString() : null;
					int slot = a.Count > 7 ? a[7].AsInt32() : -1;   // pont ≥ 0.5.56
					string key = tileId + "|" + r + "|" + c
						+ "|" + xf.ToString("F3", CultureInfo.InvariantCulture)
						+ "|" + yf.ToString("F3", CultureInfo.InvariantCulture);
					seen.Add(key);
					if (_entries.TryGetValue(key, out var known))
					{
						known.Densite = dens;
						known.Role = role;
						known.Espece = espece;
						known.Slot = slot;
						known.Style = CarpophoreStyles.De(espece);
						if (known.DyingAt >= 0f)   // re-pousse pendant son fondu de mort
						{
							float alpha = Mathf.Clamp(
								1f - (now - known.DyingAt) / FadeOutSec, 0f, 1f);
							known.BornAt = now - FadeInSec * alpha;
							known.DyingAt = -1f;
						}
						continue;
					}
					_entries[key] = new Entry
					{
						Wx = o.X + (c + (float)xf) * WorldView.PlotCm,
						Wy = o.Y + (r + (float)yf) * WorldView.PlotCm,
						Densite = dens,
						Role = role,
						Espece = espece,
						Tile = tileId, R = r, C = c, Slot = slot,
						Style = CarpophoreStyles.De(espece),
						Phase = HashKey(key),
						BornAt = fade ? now : now - FadeInSec,
					};
				}
			}
			// Chapeaux disparus du snapshot (réseau qui s'est défait / saison
			// passée) → fondu de sortie.
			foreach (var kv in _entries)
				if (kv.Value.DyingAt < 0f && !seen.Contains(kv.Key))
					kv.Value.DyingAt = now;
			QueueRedraw();
		}

		// Le LOD vient de basculer (zoom franchit MinZoom) → UN redraw, puis silence.
		private bool _lastZoomOk;

		public override void _Process(double delta)
		{
			if (!Visible || _entries.Count == 0) return;
			// On ne redessine QUE quand le fondu d'un chapeau est en cours OU que le
			// LOD bascule — sinon les sprites sont immobiles (sessiles), aucun coût.
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk) { _lastZoomOk = zoomOk; QueueRedraw(); return; }
			if (!zoomOk) return;
			float now = NowSec();
			foreach (var e in _entries.Values)
			{
				bool fadingIn = now - e.BornAt < FadeInSec;
				bool fadingOut = e.DyingAt >= 0f;
				if (fadingIn || fadingOut) { QueueRedraw(); return; }
			}
		}

		// ⑧ : tous les chapeaux partent en UN lot de triangles (un draw call), comme
		// la litière — avant, chaque DrawCircle/DrawLine coûtait le sien.
		private readonly LotTriangles _lot = new();

		public override void _Draw()
		{
			_lot.Vider();
			Peindre();
			_lot.Dessiner(this);
		}

		private void Peindre()
		{
			if (_entries.Count == 0) return;
			if (WorldView.CurrentZoom < MinZoom) return;   // LOD : trop loin
			Rect2 vis = (GetCanvasTransform().AffineInverse()
						 * GetViewportRect()).Grow(40f);
			float now = NowSec();
			List<string> gone = null;
			foreach (var kv in _entries)
			{
				var e = kv.Value;
				float alpha = Mathf.Clamp((now - e.BornAt) / FadeInSec, 0f, 1f);
				if (e.DyingAt >= 0f)
				{
					float fade = 1f - (now - e.DyingAt) / FadeOutSec;
					if (fade <= 0f) { (gone ??= new List<string>()).Add(kv.Key); continue; }
					alpha = Mathf.Min(alpha, fade);
				}
				Vector2 scr = WorldView.WorldToScreen(e.Wx, e.Wy);
				if (!vis.HasPoint(scr)) continue;
				DrawChampignon(scr, e.Densite, e.Phase, alpha, e.Style);
			}
			if (gone != null)
				foreach (string k in gone) _entries.Remove(k);
		}

		// Gabarit commun à toutes les espèces : taille ∝ densité du réseau (un réseau
		// dense pousse de plus gros carpophores), ±20 % de variété déterministe par le
		// hash (un rond de sorcière n'est pas un clone) ; la silhouette et les
		// couleurs viennent du style de l'espèce. Le pied monte en VERTICAL écran
		// (comme les plantes/maison). Zéro Random.
		private void DrawChampignon(Vector2 baseScr, float densite, uint phase,
									float alpha, StyleCarpo style)
		{
			float d = Mathf.Clamp(densite, 0f, 1f);
			float varia = 0.8f + 0.4f * ((phase & 0xff) / 255f);
			float h = (5f + 7f * d) * varia * WorldView.PxPerCmZ;   // hauteur pied
			float cap = (2.5f + 4f * d) * varia;                    // rayon chapeau px
			CarpophoreStyles.Dessiner(_lot, style, baseScr, h, cap, phase, alpha);
		}
	}
}
