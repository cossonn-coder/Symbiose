// SYMBIOSE — MacroLife.cs
// Vie macro VISIBLE (tranche 6·B — D31 côté vue ; peintre refait au sprint PERF
// VUE ②). Dessine les bêtes du bloc `sprites` du snapshot : par espèce une
// couleur et une TAILLE RÉELLE, mais AUCUN nom affiché — philosophie du
// naturaliste débutant : visible dès le début, identifiable à la maîtrise.
//
// 📖 Pédagogie — ce que le serveur envoie a changé (protocole 0.5.45) : plus un
// point par quantum de densité (3 848 bêtes au banc ①, ~60 k primitives), mais
// « présence + points chauds » (data/code/fields/population/perception.py :
// peindre_presence) : 1 individu par espèce présente et par tuile, quelques-uns
// de plus là où ça pullule, en grappe pour les coloniales. Quelques dizaines à
// quelques centaines de bêtes. Le CHAMP de densité, côté moteur, est intact.
//
// 📖 Pédagogie — taille réelle, en pixels internes : 1 cm monde = PxPerCmX
// (0,39) px canvas, et la caméra multiplie par le zoom. Un puceron de 2 mm fait
// 0,08 px à ×1 → il n'existe pas à l'écran ; à ×16 il fait 1,2 px → il apparaît,
// en UN pixel (jamais un disque). Chaque espèce a donc son palier d'apparition
// naturel, sans table de LOD : c'est la géométrie qui décide.
//
// 📖 Pédagogie — UN lot, redessiné rarement. Godot GARDE les commandes de dessin
// d'un CanvasItem tant qu'on ne rappelle pas QueueRedraw : la carte graphique
// rejoue la liste (quelques centaines de rectangles, regroupés en très peu de
// draw calls) sans que _Draw ne repasse. On ne redessine donc qu'au snapshot, au
// changement de palier, au ré-ancrage de la marge (pan/zoom, MargeVue), à la
// rotation, et pendant une animation de SIGNAL — brève, puis la bête se fige.
// Au repos, elle mange : c'est la DA « l'animation est un signal ».
//
// 📖 Pédagogie — signaux animés : (1) apparition / disparition = fondus (le même
// langage que les plantes) ; (2) un GESTE du joueur près d'elle (Signal) = un
// bref sursaut qui s'amortit. Pas d'errance continue, pas de Random.

using Godot;
using System.Collections.Generic;
using System.Globalization;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class MacroLife : Node2D
	{
		// Mêmes durées de fondu que les plantes (t3).
		private const float FadeInSec = 0.6f;
		private const float FadeOutSec = 0.9f;
		// Cadence de redessin PENDANT une animation de signal (sinon : aucune).
		private const float AnimHz = 20f;
		// Opacité de base : présents mais discrets — des bestioles, pas des UI.
		private const float BaseAlpha = 0.9f;
		// Sursaut sur geste : rayon d'effet, durée, amplitude (cm monde), pulsation.
		private const float SignalRayonCm = 100f;
		private const float SignalSec = 1.2f;
		private const float SignalAmpCm = 3f;
		private const float SignalSpeed = 18f;
		// Marge d'objet du culling (px canvas) : la plus grande bête + son sursaut.
		private const float CullMarginPx = 24f;

		/// <summary>Champ heatmap affiché (F6), posé par WorldView. Depuis PERF VUE
		/// ② les bêtes sont FIXES sur leur ancre : la corrélation avec la heatmap
		/// est déjà exacte, la propriété ne change plus rien (gardée pour l'API).</summary>
		public string FocusGuild { get; set; }

		// Par ESPÈCE : couleur (calée sur FieldOverlay — un seul langage visuel) et
		// TAILLE RÉELLE vue de dessus, en cm : longueur × largeur (ordre de grandeur
		// adulte). Le palier où la longueur atteint 1 px interne est indiqué en
		// commentaire (conception PERF VUE §3).
		private static readonly Dictionary<string, (Color Col, float LongCm, float LargCm)>
			Especes = new()
		{
			// Ravageurs
			["puceron"]    = (new Color("6f8f3a"), 0.2f, 0.1f),    // ×16
			["limace"]     = (new Color("7a5a3a"), 6f, 1f),        // ×0,5
			["doryphore"]  = (new Color("d8a83a"), 1f, 0.7f),      // ×4
			// Auxiliaires
			["coccinelle"] = (new Color("c43a2e"), 0.7f, 0.5f),    // ×4
			["chrysope"]   = (new Color("9fd86e"), 1.5f, 0.8f),    // ×2
			["carabe"]     = (new Color("2e3a44"), 2.5f, 1f),      // ×2
			["merle"]      = (new Color("1e1e22"), 25f, 8f),       // ×0,5
			["herisson"]   = (new Color("8a6a4a"), 25f, 15f),      // ×0,5
			// Détritivores (le lombric, souterrain, n'est jamais envoyé)
			["cloporte"]   = (new Color("8a8a8a"), 1.5f, 0.7f),    // ×2
			// Herbivore vertébré
			["campagnol"]  = (new Color("9a6a3a"), 10f, 4f),       // ×0,5
			// Super-prédateurs (le rapace : ailes déployées au-dessus du jardin)
			["rapace"]     = (new Color("b58a4a"), 30f, 12f),      // ×0,5
			["couleuvre"]  = (new Color("5a7a3a"), 60f, 2f),       // ×0,5
			// Faune de mare
			["moustique"]  = (new Color("6a5f57"), 0.6f, 0.3f),    // ×8
			["libellule"]  = (new Color("2f9f8f"), 7f, 1f),        // ×0,5
		};
		// Espèce inconnue d'un futur protocole : un pixel gris, pas un crash.
		private static readonly (Color, float, float) EspeceInconnue =
			(new Color("999999"), 1f, 1f);

		// Espèces IGNORÉES ici : les pollinisateurs sont des AGENTS butineurs
		// (ForagerLayer) ; le lombric vit sous terre. Le serveur 0.5.45 leur envoie
		// des listes vides — le filtre reste pour un serveur plus ancien.
		private static readonly HashSet<string> NonDessine =
			new() { "abeille", "syrphe", "papillon", "bourdon", "osmie", "lombric" };

		// Une bête affichée. Position MONDE absolue en cm (origine de tuile ajoutée).
		private class Entry
		{
			public string Guild;
			public float Wx, Wy;
			public uint Phase;            // hash de la clé : déphasage du sursaut
			public float BornAt;
			public float DyingAt = -1f;   // < 0 : vivante
			public float SignalAt = -1f;  // < 0 : au repos
		}

		// Clé stable (tile|guild|r|c|x|y) → bête : le serveur arrondit x/y à 3
		// décimales, la clé survit aux semaines (cf. clé de diff des plantes).
		private readonly Dictionary<string, Entry> _entries = new();

		// État du lot : redessin demandé, fin de la dernière animation en cours,
		// échéance de la prochaine purge des mourantes (< 0 : aucune).
		private bool _dirty;
		private float _animUntil = -1f, _purgeAt = -1f, _animAccum;
		private float _lastZoom = -1f;
		private int _margeVersion = -1;
		private Vector2 _lastOrient = new(float.NaN, float.NaN);

		/// <summary>Nombre de bêtes connues (overlay de perfs F4).</summary>
		public int Count => _entries.Count;

		/// <summary>Bêtes en fondu de sortie (banc PERF VUE : témoin de la fuite).</summary>
		public int CountMourantes
		{
			get
			{
				int n = 0;
				foreach (var e in _entries.Values) if (e.DyingAt >= 0f) n++;
				return n;
			}
		}

		/// <summary>Espèce de la bête VIVANTE la plus proche du point MONDE (cm),
		/// dans `rayonCm`, ou null. Sert l'écrasement ciblé (target.espece) et
		/// l'observation au survol : on désigne ce qu'on VOIT sous le curseur.</summary>
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

		/// <summary>Un geste du joueur au point MONDE `wMonde` : les bêtes proches
		/// sursautent brièvement (signal), puis se figent.</summary>
		public void Signal(Vector2 wMonde)
		{
			float now = NowSec(), r2 = SignalRayonCm * SignalRayonCm;
			bool any = false;
			foreach (var e in _entries.Values)
			{
				float dx = e.Wx - wMonde.X, dy = e.Wy - wMonde.Y;
				if (e.DyingAt >= 0f || dx * dx + dy * dy > r2) continue;
				e.SignalAt = now;
				any = true;
			}
			if (any) Animer(now + SignalSec);
		}

		private static float NowSec() => Time.GetTicksMsec() / 1000f;

		// Hash djb2-xor d'une chaîne : déterministe inter-sessions (jamais
		// GetHashCode pour du visuel stable, jamais de Random).
		private static uint HashKey(string s)
		{
			uint h = 5381;
			foreach (char ch in s)
				h = ((h << 5) + h) ^ ch;
			return h;
		}

		private void Animer(float jusqua)
		{
			_animUntil = Mathf.Max(_animUntil, jusqua);
			_dirty = true;
		}

		// Application REPRENABLE (F5 Nico 2026-10-15) : le diff se découpe en
		// tranches de temps (WorldView.Etalement.cs). BeginSprites prépare la liste
		// des groupes (tuile × espèce), StepSprites en traite jusqu'à épuisement du
		// budget et reprend à la frame suivante.
		private struct Groupe { public string Tile, Guild; public Vector2 O; public Godot.Collections.Array Ev; }
		private List<Groupe> _groupes;
		private int _gi, _ei;             // groupe courant, événement courant
		private HashSet<string> _seen;
		private bool _fade;

		public void SetSprites(GDict sprites, Dictionary<string, Vector2> origins,
							   bool fade)
		{
			BeginSprites(sprites, origins, fade);
			StepSprites(long.MaxValue);
		}

		public void BeginSprites(GDict sprites, Dictionary<string, Vector2> origins,
								 bool fade)
		{
			_groupes = new List<Groupe>();
			_gi = _ei = 0;
			_seen = new HashSet<string>();
			_fade = fade;
			foreach (var tileKv in sprites)
			{
				string tileId = tileKv.Key.AsString();
				if (!origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init : on n'invente rien
				foreach (var guildKv in tileKv.Value.AsGodotDictionary())
				{
					string guild = guildKv.Key.AsString();
					if (NonDessine.Contains(guild)) continue;
					_groupes.Add(new Groupe { Tile = tileId, Guild = guild, O = o,
											  Ev = guildKv.Value.AsGodotArray() });
				}
			}
		}

		/// <summary>Traite des bêtes jusqu'à `budgetUs` µs. Vrai = diff terminé.</summary>
		public bool StepSprites(long budgetUs)
		{
			if (_groupes == null) return true;
			ulong t0 = Time.GetTicksUsec();
			float now = NowSec();
			for (; _gi < _groupes.Count; _gi++, _ei = 0)
			{
				var g = _groupes[_gi];
				for (; _ei < g.Ev.Count; _ei++)
				{
					if ((long)(Time.GetTicksUsec() - t0) >= budgetUs) return false;
					// Format compact : [r, c, x_frac, y_frac, activite] (activite
					// n'est plus lue : les bêtes sont fixes au repos).
					var e = g.Ev[_ei].AsGodotArray();
					int r = e[0].AsInt32(), c = e[1].AsInt32();
					double xf = e[2].AsDouble(), yf = e[3].AsDouble();
					string key = g.Tile + "|" + g.Guild + "|" + r + "|" + c
						+ "|" + xf.ToString("F3", CultureInfo.InvariantCulture)
						+ "|" + yf.ToString("F3", CultureInfo.InvariantCulture);
					_seen.Add(key);
					if (_entries.TryGetValue(key, out var known))
					{
						// Revenue pendant son fondu de mort → elle revit depuis
						// l'alpha courant (pas de pop).
						if (known.DyingAt >= 0f)
						{
							float alpha = Mathf.Clamp(
								1f - (now - known.DyingAt) / FadeOutSec, 0f, 1f);
							known.BornAt = now - FadeInSec * alpha;
							known.DyingAt = -1f;
							Animer(now + FadeInSec);
						}
						continue;
					}
					// x = est (colonnes), y = sud (lignes) — convention FindPlot.
					_entries[key] = new Entry
					{
						Guild = g.Guild,
						Wx = g.O.X + (c + (float)xf) * WorldView.PlotCm,
						Wy = g.O.Y + (r + (float)yf) * WorldView.PlotCm,
						Phase = HashKey(key),
						BornAt = _fade ? now : now - FadeInSec,
					};
					if (_fade) Animer(now + FadeInSec);
				}
			}
			// Bêtes absentes du snapshot → fondu de sortie, puis purge (au _Process).
			foreach (var kv in _entries)
				if (kv.Value.DyingAt < 0f && !_seen.Contains(kv.Key))
				{
					kv.Value.DyingAt = now;
					if (_purgeAt < 0f) _purgeAt = now + FadeOutSec;
					Animer(now + FadeOutSec);
				}
			_groupes = null;
			_seen = null;
			_dirty = true;
			return true;
		}

		// Banc PERF VUE ① : les deux points d'entrée sont chronométrés (PerfPostes).
		public override void _Process(double delta)
		{
			long t0 = PerfPostes.Debut();
			ProcessMacro(delta);
			PerfPostes.Fin(PerfPostes.Poste.MacroProcess, t0);
		}

		public override void _Draw()
		{
			long t0 = PerfPostes.Debut();
			DessinerMacro();
			PerfPostes.Fin(PerfPostes.Poste.MacroDraw, t0);
		}

		private void ProcessMacro(double delta)
		{
			float now = NowSec();
			// Purge des mourantes AVANT tout test de visibilité (correctif de la
			// fuite PERF VUE ①) : masquée ou dézoomée, la couche oublie quand même
			// ses morts. La prochaine échéance = la plus proche fin de fondu restante.
			if (_purgeAt >= 0f && now >= _purgeAt) Purger(now);
			if (!Visible) return;              // touche I : aucun dessin
			Vector2 orient = WorldView.WorldToScreen(0f, 0f);   // signature de rotation
			if (WorldView.CurrentZoom != _lastZoom || _margeVersion != MargeVue.Version
				|| orient != _lastOrient)
			{
				_lastZoom = WorldView.CurrentZoom;
				_margeVersion = MargeVue.Version;
				_lastOrient = orient;
				_dirty = true;
			}
			if (now < _animUntil)
			{
				// Animation de signal en cours : redessin cadencé à AnimHz.
				_animAccum += (float)delta;
				if (_animAccum >= 1f / AnimHz) { _animAccum = 0f; _dirty = true; }
			}
			else if (_animUntil >= 0f)
			{
				_animUntil = -1f;               // fin d'animation : une image pour figer
				_dirty = true;
			}
			if (_dirty) { _dirty = false; QueueRedraw(); }
		}

		private void Purger(float now)
		{
			_purgeAt = -1f;
			List<string> gone = null;
			foreach (var kv in _entries)
			{
				float d = kv.Value.DyingAt;
				if (d < 0f) continue;
				if (now - d >= FadeOutSec) (gone ??= new List<string>()).Add(kv.Key);
				else if (_purgeAt < 0f || d + FadeOutSec < _purgeAt) _purgeAt = d + FadeOutSec;
			}
			if (gone == null) return;
			foreach (string k in gone) _entries.Remove(k);
			_dirty = true;
		}

		private void DessinerMacro()
		{
			if (_entries.Count == 0) return;
			float zoom = Mathf.Max(WorldView.CurrentZoom, 0.01f);
			float px1 = 1f / zoom;   // 1 pixel interne, en px canvas
			// Culling : cadre de marge COMMUN et stable (world/MargeVue.cs).
			Rect2 vis = MargeVue.CadreCouche(CullMarginPx);
			float now = NowSec();
			foreach (var e in _entries.Values)
			{
				var (col, longCm, largCm) =
					Especes.TryGetValue(e.Guild, out var g) ? g : EspeceInconnue;
				// Taille réelle : invisible tant qu'elle fait moins d'1 px interne.
				float w = longCm * WorldView.PxPerCmX;
				if (w < px1) continue;
				float h = Mathf.Max(largCm * WorldView.PxPerCmY, px1);
				float alpha = Mathf.Clamp((now - e.BornAt) / FadeInSec, 0f, 1f);
				if (e.DyingAt >= 0f)
					alpha = Mathf.Min(alpha, 1f - (now - e.DyingAt) / FadeOutSec);
				if (alpha <= 0f) continue;
				float wx = e.Wx, wy = e.Wy;
				float ts = now - e.SignalAt;
				if (e.SignalAt >= 0f && ts < SignalSec)
				{
					// Sursaut amorti, déphasé par le hash de la clé.
					float amp = SignalAmpCm * (1f - ts / SignalSec);
					float ph = (e.Phase & 0xffff) * (Mathf.Tau / 65536f);
					wx += amp * Mathf.Sin(ts * SignalSpeed + ph);
					wy += amp * Mathf.Cos(ts * SignalSpeed * 0.73f + ph);
				}
				Vector2 scr = WorldView.WorldToScreen(wx, wy);
				if (!vis.HasPoint(scr)) continue;
				col.A = BaseAlpha * alpha;
				DrawRect(new Rect2(scr.X - w * 0.5f, scr.Y - h * 0.5f, w, h), col);
			}
		}
	}
}
