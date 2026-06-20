// SYMBIOSE — MacroLife.cs
// Vie macro VISIBLE (tranche 6·B — D31 côté vue). Dessine les sprites
// échantillonnés par le serveur (bloc `sprites` du snapshot, protocole 0.2.3) :
// par guilde une forme/couleur distincte mais AUCUN nom affiché — philosophie
// du naturaliste débutant : visible dès le début, non identifiable sans
// maîtrise (l'identification = tranche maîtrise future).
//
// 📖 Pédagogie — UN nœud pour des milliers de points (pas un Node2D chacun) :
// le pic mesuré est ~8600 sprites sur le monde full en automne. 8600 nœuds de
// scène = 8600 transforms, 8600 entrées de tri, des allocations à chaque
// naissance — l'arbre de scène n'est pas fait pour ça. Ici UN SEUL CanvasItem
// redessine tout dans son _Draw : les primitives partent en lot au renderer
// (batch), et la « position » de chaque point n'est qu'un Vector2 dans une
// boucle. C'est le même choix que les heatmaps à venir (volet C) et l'inverse
// des PLANTES (peu nombreuses, complexes, persistantes → un nœud chacune).
//
// 📖 Pédagogie — l'errance n'est PAS une simulation : le moteur donne un point
// d'ancrage (hash stable : un slot vit toujours au même endroit) et un scalaire
// `activite`. La vue fait osciller le point autour de l'ancre en sin/cos sur
// l'horloge réelle — déphasés par un hash de la clé pour que chaque individu
// ait « sa » trajectoire. Zéro Random, zéro état : à chaque frame la position
// se RECALCULE de l'horloge — déterministe, et la rotation D35 est gratuite
// (on re-projette par WorldToScreen à chaque dessin).
//
// 📖 Pédagogie — cadence d'animation découplée du framerate (leçon perf C2) :
// redessiner 8600 points à 60 Hz serait du gâchis pour des bestioles qui
// dérivent de quelques cm. _Process accumule et ne QueueRedraw qu'à AnimHz
// (20 Hz) — l'œil ne voit pas la différence sur une errance lente, le GPU si.

using Godot;
using System.Collections.Generic;
using System.Globalization;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class MacroLife : Node2D
	{
		// Mêmes durées de fondu que les plantes (t3) : un seul langage visuel
		// pour « apparaît dans l'écosystème » / « en disparaît ».
		private const float FadeInSec = 0.6f;
		private const float FadeOutSec = 0.9f;
		// Cadence de l'animation d'errance (voir pédagogie en-tête).
		private const float AnimHz = 20f;
		// Opacité de base : présents mais discrets — des bestioles, pas des UI.
		private const float BaseAlpha = 0.9f;
		// LOD (correctif t6·B2, retour F5 : « ce sont des petits animaux, ils
		// ne devraient apparaître que quand on zoome ») : invisible sous ce
		// palier. ×4 = le début de la plage pixel art officielle — à la vue
		// d'ensemble on lit le PAYSAGE, pas les pucerons. 📖 C'est aussi LE
		// correctif de perf : à ×4+ la caméra ne voit qu'une fraction du monde,
		// le culling ci-dessous ne dessine que ça (9 500 DrawCircle plein cadre
		// = FPS 3 au F5 — le dessin était le coût, pas la boucle).
		private const float MinZoom = 4f;
		// Marge du rectangle de culling, en px canvas : couvre l'amplitude
		// d'errance max (~120 cm × 0,78) pour ne pas couper un point au bord.
		private const float CullMarginPx = 160f;
		// Errance résiduelle quand la heatmap de SA guilde est affichée
		// (t6·C3, retour 4 : « des points bougent dans des cases où la carte
		// les dit absents » — c'était l'errance VISUELLE, surtout le
		// pollinisateur ±120 cm). Un instrument doit montrer la corrélation :
		// les points se rassemblent sur leur ancre (±4 cm = dans le plot),
		// l'errance libre reste le mode normal hors heatmap de guilde.
		private const float FocusAmpCm = 4f;

		/// <summary>Champ heatmap affiché (F6) — posé par WorldView. Si c'est
		/// le nom d'une espèce dessinée ici, SES points resserrent leur errance
		/// sur l'ancre ; tout autre nom (humidite…) ou null = sans effet.</summary>
		public string FocusGuild { get; set; }

		// Par ESPÈCE (catalogue enrichi ⑥b) : couleur, rayon du point en px
		// canvas (0 = tiret du ver), amplitude d'errance en cm MONDE et pulsation
		// (rad/s). Depuis la scission faune ④b-d le snapshot émet des CLÉS
		// D'ESPÈCE (puceron…cloporte), plus les 3 anciennes guildes : à chacune
		// SON placeholder procédural (forme/couleur distincte, PAS de PNG —
		// décision Nico 2026-06-18, philo du naturaliste : visible, identifiable
		// seulement à la maîtrise). Couleurs CALÉES sur FieldOverlay (heatmap par
		// espèce) — un seul langage visuel : le point sombre du carabe = le pôle
		// haut de sa heatmap. Les OISEAUX/hérisson errent plus large (amplitude
		// haute), la limace/le cloporte traînent lentement, le ver ne bouge
		// presque pas (radius 0 → tiret). Un vrai déplacement libre serait un
		// AGENT (état, trajectoire) — hors modèle : le sprite reste un quantum de
		// densité locale ancré (les butineurs sont l'exception, cf. ForagerLayer).
		private static readonly Dictionary<string, (Color Col, float RadiusPx,
			float AmpCm, float Speed)> Especes = new()
		{
			// Ravageurs (category="ravageur")
			["puceron"]    = (new Color("6f8f3a"), 2.0f, 6f, 2.0f),
			["limace"]     = (new Color("7a5a3a"), 2.4f, 4f, 0.8f),
			["doryphore"]  = (new Color("d8a83a"), 2.3f, 5f, 1.6f),
			// Auxiliaires (category="auxiliaire")
			["coccinelle"] = (new Color("c43a2e"), 2.4f, 6f, 2.6f),
			["chrysope"]   = (new Color("9fd86e"), 2.2f, 7f, 2.4f),
			["carabe"]     = (new Color("2e3a44"), 2.5f, 6f, 1.8f),
			["merle"]      = (new Color("1e1e22"), 3.2f, 20f, 1.2f),
			["herisson"]   = (new Color("8a6a4a"), 3.4f, 14f, 1.0f),
			// Détritivores (category="detritivore") — lombric = tiret du ver
			["lombric"]    = (new Color("8a4a3a"), 0f, 1.5f, 0.6f),
			["cloporte"]   = (new Color("8a8a8a"), 2.2f, 4f, 1.2f),
		};
		// Espèce inconnue d'un futur protocole : point gris, pas un crash.
		private static readonly (Color, float, float, float) EspeceInconnue =
			(new Color("999999"), 2.0f, 4f, 2.0f);

		// Espèces IGNORÉES ici (décision Nico 2026-06-18) : les pollinisateurs
		// sont des AGENTS butineurs (vol fleur-en-fleur, ForagerLayer), pas un
		// nuage de densité ancré. Le snapshot émet pourtant leur densité dans le
		// bloc `sprites` (eco.populations contient les 5) → on les SAUTE ici,
		// sinon double affichage (nuage + butineur) et points gris. Les 5 :
		// abeille/syrphe/papillon (③) + bourdon/osmie (⑤).
		private static readonly HashSet<string> NonDessine =
			new() { "abeille", "syrphe", "papillon", "bourdon", "osmie" };

		// Un sprite affiché. Position MONDE absolue en cm (origin de la tuile
		// déjà ajoutée) ; Phase = hash de la clé → déphasages d'errance propres.
		private class Entry
		{
			public string Guild;
			public float Wx, Wy, Act;
			public uint Phase;
			public float BornAt;
			public float DyingAt = -1f;   // < 0 : vivant
		}

		// Clé stable (tile|guild|r|c|x|y) → sprite. Le serveur arrondit x/y à
		// 3 décimales de façon déterministe : la clé survit aux semaines — c'est
		// le même principe que la clé de diff des plantes (tile|species|x|y).
		private readonly Dictionary<string, Entry> _entries = new();
		private float _animAccum;

		/// <summary>Nombre de sprites affichés (overlay de perfs F4).</summary>
		public int Count => _entries.Count;

		/// <summary>Espèce du sprite VIVANT dont l'ANCRE est la plus proche du
		/// point MONDE (cm), dans `rayonCm`, ou null. Sert l'écrasement ciblé
		/// (⑥b, target.espece) : on écrase ce qu'on VOIT sous le curseur. On
		/// teste l'ancre (position snapshot stable) et non la position errante —
		/// le rayon est assez large pour couvrir l'amplitude d'errance.</summary>
		public string SpeciesNear(Vector2 wMonde, float rayonCm)
		{
			float bestD = rayonCm * rayonCm;
			string best = null;
			foreach (var e in _entries.Values)
			{
				if (e.DyingAt >= 0f) continue;   // en train de disparaître
				float dx = e.Wx - wMonde.X, dy = e.Wy - wMonde.Y;
				float d = dx * dx + dy * dy;
				if (d < bestD) { bestD = d; best = e.Guild; }
			}
			return best;
		}

		private static float NowSec() => Time.GetTicksMsec() / 1000f;

		// Hash djb2-xor d'une chaîne : déterministe inter-sessions (leçon t6·A :
		// jamais GetHashCode pour du visuel stable, jamais de Random).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s)
				h = ((h << 5) + h) ^ ch;
			return h;
		}

		/// <summary>
		/// Applique le bloc `sprites` d'un snapshot (diff doux, kickoff §6) :
		/// clé connue → mise à jour de l'activité ; nouvelle → fondu d'entrée ;
		/// disparue → fondu de sortie puis oubli. `origins` = origin_cm par
		/// tuile (le même cache que les plantes).
		/// </summary>
		public void SetSprites(GDict sprites, Dictionary<string, Vector2> origins,
							   bool fade)
		{
			float now = NowSec();
			var seen = new HashSet<string>();
			foreach (var tileKv in sprites)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				foreach (var guildKv in tileKv.Value.AsGodotDictionary())
				{
					string guild = guildKv.Key.AsString();
					if (NonDessine.Contains(guild)) continue;   // butineurs → ForagerLayer
					foreach (var ev in guildKv.Value.AsGodotArray())
					{
						// Format compact 0.2.3 : [r, c, x_frac, y_frac, activite].
						var e = ev.AsGodotArray();
						int r = e[0].AsInt32(), c = e[1].AsInt32();
						double xf = e[2].AsDouble(), yf = e[3].AsDouble();
						float act = (float)e[4].AsDouble();
						string key = tileId + "|" + guild + "|" + r + "|" + c
							+ "|" + xf.ToString("F3", CultureInfo.InvariantCulture)
							+ "|" + yf.ToString("F3", CultureInfo.InvariantCulture);
						seen.Add(key);
						if (_entries.TryGetValue(key, out var known))
						{
							known.Act = act;
							// Re-franchit son seuil pendant son fondu de mort →
							// il revit : repartir du fondu d'entrée à l'alpha
							// courant (pas de pop), comme si de rien n'était.
							if (known.DyingAt >= 0f)
							{
								float alpha = Mathf.Clamp(
									1f - (now - known.DyingAt) / FadeOutSec, 0f, 1f);
								known.BornAt = now - FadeInSec * alpha;
								known.DyingAt = -1f;
							}
							continue;
						}
						// x = est (colonnes), y = sud (lignes) — la convention
						// de FindPlot/WorldToScreen, pas une 2ᵉ (leçon D2).
						_entries[key] = new Entry
						{
							Guild = guild,
							Wx = o.X + (c + (float)xf) * WorldView.PlotCm,
							Wy = o.Y + (r + (float)yf) * WorldView.PlotCm,
							Act = act,
							Phase = HashKey(key),
							BornAt = fade ? now : now - FadeInSec,
						};
					}
				}
			}
			// Slots passés sous leur seuil de densité → fondu de sortie.
			foreach (var kv in _entries)
				if (kv.Value.DyingAt < 0f && !seen.Contains(kv.Key))
					kv.Value.DyingAt = now;
			QueueRedraw();
		}

		// Le LOD vient de basculer (zoom franchit MinZoom) → UN redraw pour
		// effacer ou raviver le canvas, puis silence tant que rien ne change.
		private bool _lastZoomOk;

		public override void _Process(double delta)
		{
			if (!Visible) return;              // touche I : coût strictement nul
			bool zoomOk = WorldView.CurrentZoom >= MinZoom;
			if (zoomOk != _lastZoomOk)
			{
				_lastZoomOk = zoomOk;
				QueueRedraw();
			}
			if (!zoomOk || _entries.Count == 0) return;
			_animAccum += (float)delta;
			if (_animAccum < 1f / AnimHz) return;
			_animAccum = 0f;
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (_entries.Count == 0) return;
			if (WorldView.CurrentZoom < MinZoom) return;   // LOD : trop loin
			// Culling : seul ce que la caméra cadre se dessine. La transform
			// canvas→écran de Godot (pan + zoom), inversée, ramène le rectangle
			// du viewport en coordonnées canvas — notre espace de dessin.
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
					// La purge des morts finit AVANT le culling : un fondu
					// achevé hors champ doit s'oublier aussi.
					float fade = 1f - (now - e.DyingAt) / FadeOutSec;
					if (fade <= 0f)
					{
						(gone ??= new List<string>()).Add(kv.Key);
						continue;
					}
					alpha = Mathf.Min(alpha, fade);
				}
				if (!vis.HasPoint(WorldView.WorldToScreen(e.Wx, e.Wy)))
					continue;   // hors cadre : ni sin/cos ni dessin
				var (col, radiusPx, ampCm, speed) =
					Especes.TryGetValue(e.Guild, out var g) ? g : EspeceInconnue;

				// Errance : sin/cos déphasés par le hash, amplitude ∝ activité
				// (plancher 0.3 : même repu, un vivant n'est pas une borne).
				float ph1 = (e.Phase & 0xffff) * (Mathf.Tau / 65536f);
				float ph2 = (e.Phase >> 16) * (Mathf.Tau / 65536f);
				float amp = ampCm * (0.3f + 0.7f * e.Act);
				// Mode instrument (t6·C3) : heatmap de MA guilde à l'écran →
				// je me tiens sur mon ancre, la corrélation saute aux yeux.
				if (e.Guild == FocusGuild)
					amp = Mathf.Min(amp, FocusAmpCm);
				Vector2 scr = WorldView.WorldToScreen(
					e.Wx + amp * Mathf.Sin(now * speed + ph1),
					e.Wy + amp * Mathf.Cos(now * speed * 0.73f + ph2));

				col.A = BaseAlpha * alpha;
				if (radiusPx > 0f)
					DrawCircle(scr, radiusPx, col);
				else
				{
					// Ver de terre : petit tiret posé au sol, orienté MONDE
					// (WorldToScreenOffset → il pivote avec la vue, D35).
					Vector2 d = WorldView.WorldToScreenOffset(3.5f, 0f);
					DrawLine(scr - d, scr + d, col, 1.6f);
				}
			}
			if (gone != null)
				foreach (string k in gone)
					_entries.Remove(k);
		}
	}
}
