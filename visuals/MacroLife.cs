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

		// Par guilde : couleur, rayon du point en px canvas (0 = tiret du ver),
		// amplitude d'errance en cm MONDE et pulsation (rad/s). Le pollinisateur
		// erre plus large (kickoff §5), le ver bouge à peine et lentement.
		private static readonly Dictionary<string, (Color Col, float RadiusPx,
			float AmpCm, float Speed)> Guilds = new()
		{
			["ravageur"]      = (new Color("3a2c1e"), 2.2f, 6f, 2.0f),
			["auxiliaire"]    = (new Color("ece6d2"), 2.2f, 6f, 2.6f),
			["pollinisateur"] = (new Color("e9c83c"), 2.6f, 18f, 3.2f),
			["vers_de_terre"] = (new Color("6b4a32"), 0f, 1.5f, 0.6f),
		};
		// Guilde inconnue d'un futur protocole : point gris, pas un crash.
		private static readonly (Color, float, float, float) GuildeInconnue =
			(new Color("999999"), 2.0f, 4f, 2.0f);

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

		public override void _Process(double delta)
		{
			if (_entries.Count == 0) return;   // jardin d'hiver : coût nul
			_animAccum += (float)delta;
			if (_animAccum < 1f / AnimHz) return;
			_animAccum = 0f;
			QueueRedraw();
		}

		public override void _Draw()
		{
			if (_entries.Count == 0) return;
			float now = NowSec();
			List<string> gone = null;
			foreach (var kv in _entries)
			{
				var e = kv.Value;
				float alpha = Mathf.Clamp((now - e.BornAt) / FadeInSec, 0f, 1f);
				if (e.DyingAt >= 0f)
				{
					float fade = 1f - (now - e.DyingAt) / FadeOutSec;
					if (fade <= 0f)
					{
						(gone ??= new List<string>()).Add(kv.Key);
						continue;
					}
					alpha = Mathf.Min(alpha, fade);
				}
				var (col, radiusPx, ampCm, speed) =
					Guilds.TryGetValue(e.Guild, out var g) ? g : GuildeInconnue;

				// Errance : sin/cos déphasés par le hash, amplitude ∝ activité
				// (plancher 0.3 : même repu, un vivant n'est pas une borne).
				float ph1 = (e.Phase & 0xffff) * (Mathf.Tau / 65536f);
				float ph2 = (e.Phase >> 16) * (Mathf.Tau / 65536f);
				float amp = ampCm * (0.3f + 0.7f * e.Act);
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
