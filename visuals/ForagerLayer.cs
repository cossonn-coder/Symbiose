// SYMBIOSE — ForagerLayer.cs
// Vol des BUTINEURS de fleur en fleur (arc pollinisation, vue du bloc `foragers`
// du snapshot, protocole 0.3.9). Là où MacroLife dessine un NUAGE de densité
// ancré (un quantum qui erre autour d'un point fixe), le butineur est un AGENT :
// il saute de fleur en fleur, et seulement de fleurs de SON espèce-cible — la
// constance florale du moteur (un agent ne dépose que sur l'espèce qu'il porte)
// se LIT visuellement. Les guildes abeille/syrphe/papillon vivent ICI, plus dans
// MacroLife (décision Nico 2026-06-18 : pas de double affichage).
//
// 📖 Pédagogie — pourquoi un layer batché comme MacroLife, et PAS un agent moteur
// en C# : le moteur a DÉJÀ marché les agents (sample_foragers, déterministe) et
// nous donne, à chaque snapshot, leur position d'ancrage + l'espèce-cible. La vue
// n'invente aucune trajectoire physique : elle anime un SAUT entre les fleurs
// conspécifiques voisines de l'ancre (interpolées sur l'horloge réelle, déphasées
// par un hash). Zéro Random, zéro état persistant entre frames — comme MacroLife,
// la position se RECALCULE de l'horloge (déterministe, rotation D35 gratuite).
//
// 📖 Pédagogie — le pollen DÉPOSÉ (décision Nico 2026-06-18) : à chaque
// atterrissage d'un butineur qui PORTE du pollen, un point ambré s'ajoute sur la
// fleur, et ça s'accumule (capé) toute la saison — on VOIT les fleurs les plus
// butinées se charger. C'est un ressenti de VUE, pas la vérité moteur : le moteur
// a son `pollen_recu` exact, mais ici on compte les atterrissages (un butineur à
// vide ne dépose rien, comme la constance florale). Vidé au passage de saison.
//
// 📖 Pédagogie — les « fleurs » de saut viennent de l'index plantes-par-nom
// (WorldView) : le `target` du butineur est le NOM FR de l'espèce (Phacélie…),
// qui matche le champ `name` du bloc plants — PAS `species` (anglais, Phacelia).
// On calcule UNE fois par snapshot les K fleurs cibles les plus proches de
// l'ancre ; le sprite les visite en boucle. Si l'espèce a disparu (plante morte
// entre deux semaines), repli sur l'ancre : l'insecte hésite sur place, il ne
// disparaît pas brutalement.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class ForagerLayer : Node2D
	{
		private const float FadeInSec = 0.6f;
		private const float FadeOutSec = 0.9f;
		private const float BaseAlpha = 0.95f;
		private const float AnimHz = 24f;            // un poil + fluide que le nuage
		private const float MinZoom = 4f;            // LOD identique à MacroLife
		private const float CullMarginPx = 160f;
		// Rayon (cm monde) autour de l'ancre où chercher les fleurs cibles, et
		// nombre max de fleurs visitées en boucle. Au-delà, l'insecte resterait
		// trop loin de là où le moteur l'a posé.
		private const float HopRadiusCm = 260f;
		private const int HopMax = 4;
		// Part de la période passée POSÉE sur la fleur (le reste = vol vers la
		// suivante). Un butineur s'attarde sur la corolle plus qu'il ne vole.
		private const float DwellRatio = 0.5f;
		// Pollen déposé (décision Nico 2026-06-18) : nœud enfant PollenLot, redessiné
		// sur signal seulement (PLANTE ASSEMBLÉE ③) — cf. visuals/PollenLot.cs.

		// Par espèce de butineur : couleur, rayon px du point, période d'un saut
		// (s). Le syrphe (mouche en vol stationnaire) saute vite et court ; le
		// papillon lent et large. Le bourdon (⑤) est gros et lourd → gros point,
		// saut lent ; l'osmie (⑤) plus menue, cuivrée, vive. Le pollen porté = un
		// point ambré sur le dos (cf. _Draw).
		private static readonly Dictionary<string,
			(Color Col, float RadiusPx, float HopSec)> Guilds = new()
		{
			["abeille"]  = (new Color("e9c83c"), 2.6f, 2.2f),
			["syrphe"]   = (new Color("d98f2e"), 2.3f, 1.6f),
			["papillon"] = (new Color("dcb4d2"), 2.8f, 3.0f),
			["bourdon"]  = (new Color("d8a020"), 3.0f, 2.6f),
			["osmie"]    = (new Color("b5651d"), 2.4f, 2.0f),
		};
		private static readonly (Color, float, float) GuildeInconnue =
			(new Color("cccccc"), 2.2f, 2.2f);
		private static readonly Color PollenCol = new("fff2a8");

		private class Entry
		{
			public string Guild;
			public string Plot;           // tile|r|c : compte d'abondance (INFO-BULLE ③)
			public float Hx, Hy;          // ancre MONDE (cm) = position du snapshot
			public float Nourriture = -1f; // 8ᵉ champ (pont ≥ 0.5.47), < 0 : absent
			public bool Carrying;
			public uint Phase;
			public float BornAt;
			public float DyingAt = -1f;   // < 0 : vivant
			public Vector2[] Hops;        // fleurs cibles MONDE (cm), ≥ 1
			public int LastStep = int.MinValue;   // dernier cycle de saut comptabilisé
		}

		// Clé stable : tile|guild|rang-dans-la-guilde. Le bloc `foragers` n'expose
		// pas d'id ; l'ordre de la liste moteur est déterministe (sample_foragers
		// sur seed + champs), donc le i-ᵉ butineur d'une guilde d'une tuile est « le
		// même » d'une semaine à l'autre. Un changement d'effectif fond entrée/sortie.
		private readonly Dictionary<string, Entry> _entries = new();
		private readonly PollenLot _pollen = new() { Name = "Pollen" };
		private float _animAccum;
		private bool _lastZoomOk;
		// FLUIDITÉ PC LEVIERS ② : corps + pollen porté en UN lot (un DrawMesh),
		// grains pixel-art (LotTriangles.Grain) au lieu de DrawCircle. L'ordre
		// d'émission (corps puis pollen, insecte par insecte) = ordre de peinture.
		private readonly LotTriangles _lot = new();

		/// <summary>Nombre de butineurs affichés (overlay perfs F4).</summary>
		private bool _dessinNonVide = true;   // le dernier _Draw a-t-il pu tracer ?
		public int Count => _entries.Count;
		public int FleursPollen => _pollen.Fleurs;   // rapport de banc (FLUIDITÉ PC ①)

		/// <summary>Densité d'abeilles près d'un point MONDE (cm) : nb d'agents
		/// `abeille` VIVANTS dont l'ANCRE est dans `rayonCm`. Sert la piqûre temps
		/// réel (§J) — l'ancre (position snapshot) est stable, le vol n'en bouge pas
		/// le compte. Lecture des données en mémoire, aucune requête pipe.</summary>
		public float DensiteAbeillePres(Vector2 wMonde, float rayonCm)
		{
			float r2 = rayonCm * rayonCm, sum = 0f;
			foreach (var e in _entries.Values)
			{
				if (e.DyingAt >= 0f || e.Guild != "abeille") continue;
				float dx = e.Hx - wMonde.X, dy = e.Hy - wMonde.Y;
				if (dx * dx + dy * dy <= r2) sum += 1f;
			}
			return sum;
		}

		/// <summary>Butineur VIVANT dont l'ANCRE est la plus proche du point MONDE
		/// (cm), dans `rayonCm`, ou null (D60 ② : survol → observation ; INFO-BULLE
		/// ③ : + abondance dans le plot + nourriture). Miroir de `MacroLife.Near`
		/// pour les butineurs (rendus ici, pas dans MacroLife) : on teste l'ancre
		/// (position snapshot stable) et non la position de vol errante — le rayon
		/// couvre l'amplitude du saut. Lecture des données en mémoire, aucune
		/// requête pipe.</summary>
		public MacroPick? Near(Vector2 wMonde, float rayonCm)
		{
			float bestD = rayonCm * rayonCm;
			Entry best = null;
			foreach (var e in _entries.Values)
			{
				if (e.DyingAt >= 0f) continue;   // en train de disparaître
				float dx = e.Hx - wMonde.X, dy = e.Hy - wMonde.Y;
				float d = dx * dx + dy * dy;
				if (d < bestD) { bestD = d; best = e; }
			}
			if (best == null) return null;
			int n = 0;
			foreach (var e in _entries.Values)
				if (e.DyingAt < 0f && e.Guild == best.Guild && e.Plot == best.Plot) n++;
			return new MacroPick(best.Guild, n, best.Nourriture, null, 0f, new Vector2(best.Hx, best.Hy));
		}

		private static float NowSec() => Time.GetTicksMsec() / 1000f;

		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s) h = ((h << 5) + h) ^ ch;
			return h;
		}

		public override void _Ready() => AddChild(_pollen);

		/// <summary>Vide le pollen accumulé (appelé au passage de saison —
		/// l'accumulation est par saison, décision Nico).</summary>
		public void ClearPollen() => _pollen.Vider();

		/// <summary>Applique le bloc `foragers` (diff doux par clé stable).
		/// `plantsByName` = nom FR d'espèce → positions MONDE (cm) des plantes
		/// affichées, pour calculer les fleurs de saut. `origins` = origin_cm par
		/// tuile (même cache que les plantes).</summary>
		public void SetForagers(GDict foragers, Dictionary<string, Vector2> origins,
			Dictionary<string, List<Vector2>> plantsByName, bool fade)
		{
			float now = NowSec();
			var seen = new HashSet<string>();
			foreach (var tileKv in foragers)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o)) continue;
				var rangs = new Dictionary<string, int>();
				foreach (var av in tileKv.Value.AsGodotArray())
				{
					// [guild, r, c, x_frac, y_frac, espèce-cible(FR), charge(0/1),
					//  nourriture (≥ 0.5.47, absente d'un pont plus ancien)].
					var a = av.AsGodotArray();
					string guild = a[0].AsString();
					int r = a[1].AsInt32(), c = a[2].AsInt32();
					float xf = (float)a[3].AsDouble(), yf = (float)a[4].AsDouble();
					string target = a[5].AsString();
					bool carrying = a[6].AsInt32() != 0;
					float nour = a.Count > 7 ? (float)a[7].AsDouble() : -1f;

					int rang = rangs.TryGetValue(guild, out int n) ? n : 0;
					rangs[guild] = rang + 1;
					string key = tileId + "|" + guild + "|" + rang;
					seen.Add(key);

					float hx = o.X + (c + xf) * WorldView.PlotCm;
					float hy = o.Y + (r + yf) * WorldView.PlotCm;
					var hops = ComputeHops(target, hx, hy, plantsByName);

					if (_entries.TryGetValue(key, out var known))
					{
						known.Carrying = carrying;
						known.Nourriture = nour;
						known.Hops = hops;        // les fleurs ont pu pousser/mourir
						if (known.DyingAt >= 0f)   // revit pendant son fondu de mort
						{
							float al = Mathf.Clamp(
								1f - (now - known.DyingAt) / FadeOutSec, 0f, 1f);
							known.BornAt = now - FadeInSec * al;
							known.DyingAt = -1f;
						}
						continue;
					}
					_entries[key] = new Entry
					{
						Guild = guild, Hx = hx, Hy = hy, Carrying = carrying,
						Plot = tileId + "|" + r + "|" + c, Nourriture = nour,
						Phase = HashKey(key), BornAt = fade ? now : now - FadeInSec,
						Hops = hops,
					};
				}
			}
			foreach (var kv in _entries)
				if (kv.Value.DyingAt < 0f && !seen.Contains(kv.Key))
					kv.Value.DyingAt = now;
			_pollen.Elaguer(plantsByName);
			// Rien vu, rien à voir (hiver) : pas de redessin (FLUIDITÉ PC ①).
			if (_entries.Count > 0 || _dessinNonVide) QueueRedraw();
		}

		// Les K fleurs conspécifiques les plus proches de l'ancre (dans HopRadius),
		// triées par distance. Repli sur l'ancre seule si l'espèce a disparu.
		private static Vector2[] ComputeHops(string target, float hx, float hy,
			Dictionary<string, List<Vector2>> plantsByName)
		{
			if (plantsByName != null
				&& plantsByName.TryGetValue(target, out var pos) && pos.Count > 0)
			{
				float r2 = HopRadiusCm * HopRadiusCm;
				var near = new List<(float D2, Vector2 P)>();
				foreach (var p in pos)
				{
					float dx = p.X - hx, dy = p.Y - hy, d2 = dx * dx + dy * dy;
					if (d2 <= r2) near.Add((d2, p));
				}
				if (near.Count > 0)
				{
					near.Sort((u, v) => u.D2.CompareTo(v.D2));
					int k = Mathf.Min(HopMax, near.Count);
					var hops = new Vector2[k];
					for (int i = 0; i < k; i++) hops[i] = near[i].P;
					return hops;
				}
			}
			return new[] { new Vector2(hx, hy) };   // hésite sur place
		}

		// Banc accéléré (PLANTE ASSEMBLÉE ③) : les deux points d'entrée sont
		// chronométrés (PerfPostes), comme MacroLife.
		public override void _Process(double delta)
		{
			long t0 = PerfPostes.Debut();
			ProcessButineurs(delta);
			PerfPostes.Fin(PerfPostes.Poste.ForagerProcess, t0);
		}

		public override void _Draw()
		{
			long t0 = PerfPostes.Debut();
			DessinerButineurs();
			PerfPostes.Fin(PerfPostes.Poste.ForagerDraw, t0);
		}

		private void ProcessButineurs(double delta)
		{
			if (!Visible) return;
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk) { _lastZoomOk = zoomOk; QueueRedraw(); }
			if (_entries.Count == 0) return;
			_animAccum += (float)delta;
			if (_animAccum < 1f / AnimHz) return;
			_animAccum = 0f;
			// Les dépôts s'accumulent même DÉZOOMÉ (le LOD ne masque que le dessin) :
			// le pollen reflète l'activité réelle de butinage, pas ce qu'on regarde.
			AccumulatePollen();
			if (zoomOk) QueueRedraw();
		}

		// Détecte les atterrissages et dépose le pollen. Un cycle de saut = un entier
		// de `seg` ; quand il change, le butineur vient d'arriver sur une fleur (phase
		// de pose). S'il PORTE du pollen, +1 point sur cette fleur (capé). Un butineur
		// à vide remet son compteur (au prochain chargement, il redéposera).
		private void AccumulatePollen()
		{
			float now = NowSec();
			foreach (var e in _entries.Values)
			{
				if (e.DyingAt >= 0f) continue;
				if (!e.Carrying) { e.LastStep = int.MinValue; continue; }
				int k = e.Hops.Length;
				float hopSec = Guilds.TryGetValue(e.Guild, out var g) ? g.HopSec : 2.2f;
				float ph = (e.Phase & 0xffff) / 65536f;
				int step = (int)Mathf.Floor(now / hopSec + ph * k);
				if (step == e.LastStep) continue;
				e.LastStep = step;
				_pollen.Deposer(PollenLot.Cle(e.Hops[Mathf.PosMod(step, k)]));
			}
		}

		private void DessinerButineurs()
		{
			_dessinNonVide = false;
			_lot.Vider();
			if (WorldView.CurrentZoom < MinZoom) return;
			if (_entries.Count == 0) return;
			Rect2 vis = (GetCanvasTransform().AffineInverse()
						 * GetViewportRect()).Grow(CullMarginPx);
			float now = NowSec();
			List<string> gone = null;
			foreach (var kv in _entries)
			{
				var e = kv.Value;
				float alpha = Mathf.Clamp((now - e.BornAt) / FadeInSec, 0f, 1f);
				if (e.DyingAt >= 0f)
				{
					float fade = 1f - (now - e.DyingAt) / FadeOutSec;
					if (fade <= 0f) { (gone ??= new()).Add(kv.Key); continue; }
					alpha = Mathf.Min(alpha, fade);
				}
				var (col, radiusPx, hopSec) =
					Guilds.TryGetValue(e.Guild, out var g) ? g : GuildeInconnue;

				// Position du vol : saut bouclé entre les fleurs cibles. Déphasé par
				// le hash (chaque insecte démarre ailleurs dans son cycle).
				Vector2 scr; float lift = 0f;
				int k = e.Hops.Length;
				float ph = (e.Phase & 0xffff) / 65536f;
				if (k <= 1)
				{
					// Une seule fleur (ou repli) : léger flottement sur place.
					float w1 = (e.Phase & 0xff) * (Mathf.Tau / 256f);
					scr = WorldView.WorldToScreen(e.Hops[0].X, e.Hops[0].Y)
						+ new Vector2(2.5f * Mathf.Sin(now * 1.8f + w1),
									  2.0f * Mathf.Cos(now * 1.5f + w1));
				}
				else
				{
					float seg = now / hopSec + ph * k;
					int i = Mathf.PosMod((int)Mathf.Floor(seg), k);
					float f = seg - Mathf.Floor(seg);
					Vector2 cur = e.Hops[i];
					if (f < DwellRatio)
						scr = WorldView.WorldToScreen(cur.X, cur.Y);
					else
					{
						float t = (f - DwellRatio) / (1f - DwellRatio);
						t = t * t * (3f - 2f * t);              // smoothstep
						Vector2 nxt = e.Hops[(i + 1) % k];
						scr = WorldView.WorldToScreen(
							Mathf.Lerp(cur.X, nxt.X, t), Mathf.Lerp(cur.Y, nxt.Y, t));
						lift = -7f * Mathf.Sin(Mathf.Pi * t);   // arc de vol (px écran)
					}
				}
				scr.Y += lift;
				if (!vis.HasPoint(scr)) continue;

				col.A = BaseAlpha * alpha;
				_lot.Grain(scr, radiusPx, col);
				if (e.Carrying)
				{
					var pc = PollenCol; pc.A = alpha;
					_lot.Grain(scr + new Vector2(0f, -radiusPx), 1.2f, pc);
				}
			}
			_lot.Dessiner(this);
			if (gone != null) foreach (string k in gone) _entries.Remove(k);
			_dessinNonVide = _entries.Count > 0;
		}
	}
}
