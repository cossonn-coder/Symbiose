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
		private float _slantPx;           // inclinaison des traits (vent)
		private float _windDxPx;          // dérive horizontale (px/s)
		private Color _veilColor = new Color(0.42f, 0.46f, 0.52f);

		private float _nebCur, _nebTarget; // alpha voile lissé (transition douce)
		private float _t;                  // accumulateur de temps (animation)
		private float _flash;              // alpha du flash d'éclair courant
		private float _flashTimer = 2.2f;  // compte à rebours avant le prochain

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
					_slantPx = 4f; _windDxPx = 30f;
					_veilColor = new Color(0.42f, 0.46f, 0.52f);
					break;
				case "Orage":
					_mode = Precip.Rain; _lightning = true;
					_slantPx = 16f; _windDxPx = 130f;
					_veilColor = new Color(0.36f, 0.39f, 0.46f);
					break;
				case "Neige":
					_mode = Precip.Snow; _lightning = false;
					_slantPx = 0f; _windDxPx = 0f;
					_veilColor = new Color(0.72f, 0.76f, 0.82f);
					break;
				case "Grêle":
					_mode = Precip.Hail; _lightning = false;
					_slantPx = 6f; _windDxPx = 40f;
					_veilColor = new Color(0.50f, 0.54f, 0.60f);
					break;
				case "Tempête":
					_mode = Precip.Storm; _lightning = false;
					_slantPx = 0f; _windDxPx = 0f;
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
			// Voile : on glisse l'alpha courant vers la cible (≈1 s) → pas de saut
			// brutal au changement de semaine (même esprit que les fondus plantes).
			_nebCur = Mathf.MoveToward(_nebCur, _nebTarget, d * 1.2f);

			if (_lightning)
			{
				_flashTimer -= d;
				if (_flashTimer <= 0f) { _flash = 1f; _flashTimer = 2.4f; }
			}
			_flash = Mathf.Max(0f, _flash - d * 4f);

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
				case Precip.Rain:  DrawRain(w, h, intNorm); break;
				case Precip.Snow:  DrawSnow(w, h, intNorm); break;
				case Precip.Hail:  DrawHail(w, h, intNorm); break;
				case Precip.Storm: DrawStorm(w, h, intNorm); break;
			}

			if (_flash > 0.01f)
				DrawRect(full, new Color(1f, 1f, 1f, _flash * 0.5f));
		}

		// --- Précipitations : positions dérivées d'un HASH d'indice (pas de Random) ;
		//     la chute vient de l'accumulateur _t. PosMod = modulo TOUJOURS positif.

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
				// Dérive sinusoïdale latérale : le flocon ne tombe pas droit.
				float x = Mathf.PosMod(x0 + Mathf.Sin(_t * 0.6f + ph * Mathf.Tau) * 18f, w);
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
			float speed = 1400f + 300f * intNorm;
			for (int i = 0; i < _count; i++)
			{
				uint hsh = Hash((uint)i);
				float x0 = (hsh & 0xffff) / 65536f * w;
				float ph = ((hsh >> 16) & 0xffff) / 65536f;
				float len = 40f + 30f * ph;
				float y = Mathf.PosMod(ph * h, h);            // rangées fixes
				float x = Mathf.PosMod(x0 - _t * speed, w);   // file vers la gauche
				DrawLine(new Vector2(x, y),
						 new Vector2(x + len, y), WindColor, 1.5f);
			}
		}

		// Hash djb2-xor (même choix que LitterLayer : visuel stable, jamais Random).
		private static uint Hash(uint i)
		{
			uint h = 5381u;
			h = ((h << 5) + h) ^ (i & 0xff);
			h = ((h << 5) + h) ^ ((i >> 8) & 0xff);
			h = ((h << 5) + h) ^ ((i >> 16) & 0xff);
			return h;
		}
	}
}
