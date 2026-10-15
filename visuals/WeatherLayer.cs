// SYMBIOSE — WeatherLayer.cs (tronçon ⑨, vue pure)
// L'AMBIANCE MÉTÉO GLOBALE « devant la vitre » : nébulosité (ciel qui
// s'assombrit), précipitations (pluie/neige/grêle), stries de vent (tempête) et
// flashs d'orage. Alimentée en LECTURE SEULE par le bloc `weather` du snapshot
// (protocole 0.5.0, tronçon ⑧). ZÉRO logique écologique : le moteur Python
// décide la météo (①→⑦), Godot ne fait que la PEINDRE — golden NEUTRE.
//
// 📖 Pédagogie Godot — pourquoi un CanvasLayer ?
// Un CanvasLayer se dessine en coordonnées ÉCRAN, INDÉPENDAMMENT de la Camera2D :
// zoomer/pivoter le monde ne bouge pas l'ambiance (elle reste « collée à la
// vitre »), exactement comme le HUD (lui aussi CanvasLayer). À l'opposé, la
// litière / le manteau neigeux vivent en coordonnées MONDE (Node2D, ils suivent
// la caméra). Mais un CanvasLayer n'est PAS un CanvasItem → il ne sait pas
// _Draw. On lui adjoint donc UN enfant Node2D (WeatherSky) qui, lui, dessine :
// le CanvasLayer l'isole de la caméra, le Node2D peint en pixels écran (0..1920).
//
// 📖 Pas de Random (cohérent LitterLayer/MacroLife) : positions des gouttes/
// flocons dérivées d'un HASH de leur indice → stables inter-frames et sessions ;
// l'animation vient d'un accumulateur de temps, pas d'un tirage par frame.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	// Le wrapper écran : ne porte aucun dessin, il tient juste le Node2D peintre
	// et lui relaie le bloc `weather`. Layer 1 + ajouté AVANT le HUD → l'ambiance
	// passe au-dessus du monde mais sous les labels du HUD.
	public partial class WeatherLayer : CanvasLayer
	{
		private WeatherSky _sky;

		public override void _Ready()
		{
			Layer = 1;   // au-dessus du monde (canvas 0), sous le HUD ajouté après
			_sky = new WeatherSky { Name = "Sky" };
			AddChild(_sky);
		}

		// Applique le bloc `weather` du snapshot (lecture tolérante : un snapshot
		// pré-0.5.0 sans le bloc n'appelle jamais ceci → ciel neutre, aucun crash).
		public void SetWeather(GDict w)
		{
			string kind = w.ContainsKey("kind") ? w["kind"].AsString() : "";
			float intensity = w.ContainsKey("intensity") ? (float)w["intensity"].AsDouble() : 0f;
			float nebul = w.ContainsKey("nebulosite") ? (float)w["nebulosite"].AsDouble() : 0f;
			_sky?.SetWeather(kind, intensity, nebul);
		}
	}

	// Le peintre : nébulosité + précipitations + flash d'orage, en pixels écran.
	public partial class WeatherSky : Node2D
	{
		private enum Precip { None, Rain, Snow, Hail, Storm }

		// Voile de nébulosité : on PLAFONNE l'alpha pour garder le monde lisible
		// (Pluie a nebulosite 0.90 → un voile 0.90 cacherait tout ; on lit « jour
		// gris », pas « écran éteint »).
		private const float VeilMax = 0.55f;
		private const int MaxCount = 240;

		private Precip _mode = Precip.None;
		private bool _lightning;          // Orage : flashs d'éclair
		private float _intensity;         // σ météo, ~0..3
		private int _count;               // nb de particules dessinées
		// Vent RÉEL (jardin vivant T3) : direction aval projetée À L'ÉCRAN et force
		// de la masse d'air (WindWave, bloc `weather.wind`), relues chaque frame —
		// la rotation de vue (D35) est donc suivie sans re-câblage. Ex-inclinaison
		// fixe par type de météo (_slantPx codé en dur), désormais dérivée.
		private float _slantPx;           // inclinaison des traits (px, signée)
		private float _windDxPx;          // dérive horizontale (px/s, signée)
		private Vector2 _windScreen = new(1f, 0f);   // direction aval écran (unitaire)
		private float _windForce;
		// Calibrage : px d'inclinaison / de dérive par unité de force (Orage 0,95
		// → ~15 px et ~125 px/s, proches des anciennes valeurs fixes 16 / 130).
		private const float SlantPerForce = 16f;
		private const float DriftPerForce = 130f;
		private const float StormSpeedPerForce = 900f;
		private Color _veilColor = new Color(0.42f, 0.46f, 0.52f);

		private float _nebCur, _nebTarget; // alpha voile lissé (transition douce)
		private float _t;                  // accumulateur de temps (animation)
		private float _flash;              // alpha du flash d'éclair courant
		private float _flashTimer = 2.2f;  // compte à rebours avant le prochain
		private int _flashes;              // rang de l'éclair (graine de l'intervalle)

		private static readonly Color RainColor = new Color(0.72f, 0.80f, 0.92f, 0.5f);
		private static readonly Color SnowColor = new Color(1f, 1f, 1f, 0.85f);
		private static readonly Color HailColor = new Color(0.90f, 0.95f, 1f, 0.85f);
		private static readonly Color WindColor = new Color(0.85f, 0.87f, 0.92f, 0.35f);

		public void SetWeather(string kind, float intensity, float nebul)
		{
			_intensity = Mathf.Clamp(intensity, 0f, 3f);
			_nebTarget = Mathf.Clamp(nebul, 0f, 1f);

			// kind (catalogue moteur) → type de précipitation + vent + voile.
			switch (kind)
			{
				case "Pluie prolongée":
					_mode = Precip.Rain; _lightning = false;
					_veilColor = new Color(0.42f, 0.46f, 0.52f);
					break;
				case "Orage":
					_mode = Precip.Rain; _lightning = true;
					_veilColor = new Color(0.36f, 0.39f, 0.46f);
					break;
				case "Neige":
					_mode = Precip.Snow; _lightning = false;
					_veilColor = new Color(0.72f, 0.76f, 0.82f);
					break;
				case "Grêle":
					_mode = Precip.Hail; _lightning = false;
					_veilColor = new Color(0.50f, 0.54f, 0.60f);
					break;
				case "Tempête":
					_mode = Precip.Storm; _lightning = false;
					_veilColor = new Color(0.46f, 0.49f, 0.54f);
					break;
				default:   // Canicule, Beau temps, Gelée, Redoux… : juste la nébulosité
					_mode = Precip.None; _lightning = false;
					_veilColor = new Color(0.55f, 0.55f, 0.58f);
					break;
			}

			float intNorm = _intensity / 3f;
			int baseCount = _mode switch
			{
				Precip.Rain  => 200,
				Precip.Snow  => 160,
				Precip.Hail  => 120,
				Precip.Storm => 90,
				_            => 0,
			};
			_count = Mathf.Min(MaxCount,
				Mathf.RoundToInt(baseCount * (0.35f + 0.65f * intNorm)));
			QueueRedraw();
		}

		public override void _Process(double delta)
		{
			float d = (float)delta;
			_t += d;
			_windForce = Mathf.Min(WindWave.Force, 2f);
			Vector2 down = WorldView.WorldToScreenOffset(WindWave.Downwind.X, WindWave.Downwind.Y);
			if (down.LengthSquared() > 1e-6f) _windScreen = down.Normalized();
			// La pluie s'incline et dérive selon la composante LATÉRALE du vent ;
			// la grêle, plus lourde, deux fois moins.
			float lat = _windScreen.X * _windForce;
			float heavy = _mode == Precip.Hail ? 0.5f : 1f;
			_slantPx = SlantPerForce * lat * heavy;
			_windDxPx = DriftPerForce * lat * heavy;
			// Voile : on glisse l'alpha courant vers la cible (≈1 s) → pas de saut
			// brutal au changement de semaine (même esprit que les fondus plantes).
			_nebCur = Mathf.MoveToward(_nebCur, _nebTarget, d * 1.2f);

			if (_lightning)
			{
				_flashTimer -= d;
				// T4 : un éclair = le SEUL flash autorisé, bref (~0,15 s) et à
				// intervalles irréguliers (3-9 s, hash de son rang : déterministe).
				if (_flashTimer <= 0f)
				{
					_flash = 1f;
					_flashTimer = 3f + 6f * (Hash((uint)_flashes++ + 977u) & 0xffff) / 65536f;
				}
			}
			_flash = Mathf.Max(0f, _flash - d * 7f);

			// On ne redessine que s'il y a quelque chose d'animé/visible.
			if (_mode != Precip.None || _nebCur > 0.01f || _flash > 0.01f)
				QueueRedraw();
		}

		public override void _Draw()
		{
			Vector2 sz = GetViewportRect().Size;
			float w = sz.X, h = sz.Y;
			var full = new Rect2(0f, 0f, w, h);

			if (_nebCur > 0.01f)
			{
				Color veil = _veilColor;
				veil.A = _nebCur * VeilMax;
				DrawRect(full, veil);
			}

			float intNorm = _intensity / 3f;
			switch (_mode)
			{
				case Precip.Rain:  DrawRain(w, h, intNorm); DrawSplashes(w, h); break;
				case Precip.Snow:  DrawSnow(w, h, intNorm); break;
				case Precip.Hail:  DrawHail(w, h, intNorm); break;
				case Precip.Storm: DrawStorm(w, h, intNorm); break;
			}

			if (_flash > 0.01f)
				DrawRect(full, new Color(1f, 1f, 1f, _flash * 0.5f));
		}

		// --- Précipitations : positions dérivées d'un HASH d'indice (pas de Random) ;
		//     la chute vient de l'accumulateur _t. PosMod = modulo TOUJOURS positif.

		// --- Éclaboussures au sol (T4) : par endroits, une goutte frappe (point)
		// puis rejaillit (couronne de 2 points) ; chaque site renaît ailleurs au
		// cycle suivant (hash du site × rang du cycle). Tracées en carrés de 2 px
		// alignés sur la grille du monde pixel-art (×2), couleur eau claire de la
		// palette maître (Palette16.Maitre) — ce calque écran n'est pas tramé.
		private const float SplashPeriod = 0.45f;
		private static readonly Color SplashColor = new Color("a8cfe6", 0.8f);

		private void DrawSplashes(float w, float h)
		{
			int n = _count / 3;
			var px = new Vector2(2f, 2f);
			for (int i = 0; i < n; i++)
			{
				uint hi = Hash((uint)i + 4099u);
				float cyc = _t / SplashPeriod + (hi & 0xffff) / 65536f;
				float u = cyc - Mathf.Floor(cyc);
				if (u > 0.4f) continue;   // le site est au repos le reste du cycle
				uint hp = Hash((uint)i * 7919u + (uint)Mathf.FloorToInt(cyc) * 104729u);
				var c = new Vector2(Mathf.Floor((hp & 0xffff) / 65536f * w / 2f) * 2f,
									Mathf.Floor(((hp >> 16) & 0xffff) / 65536f * h / 2f) * 2f);
				if (u < 0.15f) { DrawRect(new Rect2(c, px), SplashColor); continue; }
				DrawRect(new Rect2(c + new Vector2(-4f, -2f), px), SplashColor);
				DrawRect(new Rect2(c + new Vector2(4f, -2f), px), SplashColor);
			}
		}

		private void DrawRain(float w, float h, float intNorm)
		{
			float len = 14f + 6f * intNorm;
			float speed = 900f + 500f * intNorm;
			for (int i = 0; i < _count; i++)
			{
				uint hsh = Hash((uint)i);
				float x0 = (hsh & 0xffff) / 65536f * w;
				float ph = ((hsh >> 16) & 0xffff) / 65536f;
				float sp = speed * (0.7f + 0.6f * ph);
				float y = Mathf.PosMod(ph * h + _t * sp, h + len);
				float x = Mathf.PosMod(x0 + _windDxPx * _t, w);
				DrawLine(new Vector2(x, y),
						 new Vector2(x - _slantPx, y - len), RainColor, 1.5f);
			}
		}

		private void DrawSnow(float w, float h, float intNorm)
		{
			float speed = 70f + 40f * intNorm;
			for (int i = 0; i < _count; i++)
			{
				uint hsh = Hash((uint)i);
				float x0 = (hsh & 0xffff) / 65536f * w;
				float ph = ((hsh >> 16) & 0xffff) / 65536f;
				float sp = speed * (0.6f + 0.8f * ph);
				float y = Mathf.PosMod(ph * h + _t * sp, h + 8f);
				// Dérive sinusoïdale latérale (le flocon ne tombe pas droit) + le vent.
				float x = Mathf.PosMod(x0 + Mathf.Sin(_t * 0.6f + ph * Mathf.Tau) * 18f
									   + 0.3f * _windDxPx * _t, w);
				DrawCircle(new Vector2(x, y), 2.2f + 1.2f * ph, SnowColor);
			}
		}

		private void DrawHail(float w, float h, float intNorm)
		{
			float len = 6f;
			float speed = 1300f + 400f * intNorm;
			for (int i = 0; i < _count; i++)
			{
				uint hsh = Hash((uint)i);
				float x0 = (hsh & 0xffff) / 65536f * w;
				float ph = ((hsh >> 16) & 0xffff) / 65536f;
				float sp = speed * (0.8f + 0.4f * ph);
				float y = Mathf.PosMod(ph * h + _t * sp, h + len);
				float x = Mathf.PosMod(x0 + _windDxPx * _t, w);
				DrawLine(new Vector2(x, y),
						 new Vector2(x - _slantPx, y - len), HailColor, 2.5f);
			}
		}

		private void DrawStorm(float w, float h, float intNorm)
		{
			// Les stries FILENT dans la vraie direction du vent (écran), plus vite
			// et plus longues quand il forcit.
			float speed = 500f + StormSpeedPerForce * _windForce + 300f * intNorm;
			Vector2 v = _windScreen;
			for (int i = 0; i < _count; i++)
			{
				uint hsh = Hash((uint)i);
				float x0 = (hsh & 0xffff) / 65536f * w;
				float ph = ((hsh >> 16) & 0xffff) / 65536f;
				float len = (40f + 30f * ph) * (0.6f + 0.4f * _windForce);
				float y = Mathf.PosMod(ph * h + v.Y * _t * speed, h);
				float x = Mathf.PosMod(x0 + v.X * _t * speed, w);
				DrawLine(new Vector2(x, y), new Vector2(x, y) - v * len, WindColor, 1.5f);
			}
		}

		// Hash djb2-xor (même choix que LitterLayer : visuel stable, jamais Random).
		// T4 : finaliseur murmur3 (32 bits pleins). L'ancien hash (djb2 sur 3
		// octets) laissait les bits hauts quasi constants → toutes les gouttes
		// partageaient la même phase verticale : la pluie tombait en NAPPE (une
		// rangée horizontale de traits, constaté au banc). Corrige pluie/neige/grêle.
		private static uint Hash(uint x)
		{
			x ^= x >> 16; x *= 0x85ebca6bu; x ^= x >> 13; x *= 0xc2b2ae35u; x ^= x >> 16;
			return x;
		}
	}
}
