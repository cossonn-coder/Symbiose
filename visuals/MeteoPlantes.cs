// SYMBIOSE — MeteoPlantes.cs (sprint JARDIN VIVANT T4-T5 — météo sur les plantes)
// L'ÉTAT MÉTÉO GLOBAL que les plantes lisent pour choisir leur variante de
// dessin (PlantRenderer.Meteo.cs, PlantRenderer.Froid.cs). Lu dans le bloc
// `weather` du snapshot (kind, intensity) — aucune météo inventée par la vue.
//
// Trois temps (doc de conception §5) : AVANT = préavis déjà existant (encart
// ciel, sim/ciel.py) ; PENDANT = canicule (feuilles qui pendent, plantes en
// `secheresse` seulement), pluie/orage (feuillage trempé), neige (charge
// blanche), gelée tardive (givre) ; APRÈS = le feuillage se ressuie, la neige
// fond, le givre se dissipe en quelques secondes de jeu, par NIVEAUX discrets.
// Les DÉGÂTS (gel, grêle) ne sont PAS ici : ce sont des symptômes du snapshot
// (`leaf_symptoms`), qui restent dessinés tant que le moteur les porte.
//
// 📖 Pédagogie (analogie embarqué) : chaque grandeur est un compteur qui décroît
// en temps réel, mais on ne la PUBLIE qu'en paliers (quantification, comme un
// CAN à 2 bits) : chaque palier = une vague de re-cuisson étalée par la file à
// budget (BakeQueue), au lieu d'une re-cuisson à chaque frame. La neige va plus
// loin : chaque plante quantifie SA charge avec un décalage propre (hash) → elle
// tombe plante par plante, jamais tout le jardin à la même frame.
// Animation = SIGNAL : sans épisode ni reste à résorber, _Process sort tout de
// suite — aucune animation ne tourne.

using Godot;

namespace Symbiose
{
	public partial class MeteoPlantes : Node
	{
		// Le feuillage se ressuie en ~8 s de jeu après la fin de la pluie, en
		// 3 paliers (1 → 2/3 → 1/3 → sec). Calibrage F5 (« on sent la pluie ? »).
		private const float DryingSec = 8f;
		private const int Levels = 3;
		// Neige : fond en MeltSec après l'épisode ; sous un vent ≥ ShedForce elle
		// tombe des branches en ShedSec (pendant la chute, jusqu'à ShedFloor de la
		// charge : il continue de neiger). Givre : se dissipe en ThawSec.
		private const float MeltSec = 6f;
		private const float ShedForce = 0.5f;
		private const float ShedSec = 5f;
		private const float ShedFloor = 0.3f;
		private const float ThawSec = 5f;
		// Re-examen des plantes pendant la fonte/chute (s) : borne le coût de la
		// boucle (chaque plante ne se salit qu'à SON changement de palier).
		private const float SnowScanSec = 0.2f;

		/// <summary>Canicule en cours (`weather.kind == "Canicule"`).</summary>
		public static bool Canicule { get; private set; }
		/// <summary>Humidité du feuillage publiée ∈ {0, 1/3, 2/3, 1}.</summary>
		public static float Wet { get; private set; }
		/// <summary>Givre publié ∈ {0, 1/3, 2/3, 1} (« Gelée tardive »).</summary>
		public static float Frost { get; private set; }
		/// <summary>Charge de neige CONTINUE ∈ [0,1] : chaque plante la quantifie
		/// elle-même avec son décalage (PlantRenderer.Froid.cs).</summary>
		public static float SnowRaw { get; private set; }

		/// <summary>Averse en cours (Pluie prolongée / Orage) : sa charge ∈ [0,25 ; 1],
		/// 0 sinon. Lue par les ronds de pluie de la mare (MARE VIVANTE ③).</summary>
		public static float Pluie { get; private set; }

		private static bool _raining, _snowing, _freezing;
		private static float _wetRaw, _frostRaw, _snowLoad, _scan;
		private static int _waves;      // vagues de re-cuisson (mesure, log)

		/// <summary>Charge d'un épisode ∈ [0,25 ; 1] tirée de son intensité (σ) :
		/// même bornage [0,5 ; 2] que l'effet moteur (sim/weather.py).</summary>
		private static float Load(float intensity) => Mathf.Clamp(intensity, 0.5f, 2f) / 2f;

		/// <summary>Bloc `weather` du snapshot (kind, intensity déjà lus par WorldView).</summary>
		public static void SetWeather(string kind, float intensity)
		{
			bool canicule = kind == "Canicule";
			_raining = kind == "Pluie prolongée" || kind == "Orage";
			_snowing = kind == "Neige";
			_freezing = kind == "Gelée tardive";
			if (_raining) _wetRaw = 1f;
			Pluie = _raining ? Load(intensity) : 0f;
			if (_freezing) _frostRaw = Load(intensity);
			if (_snowing) SnowRaw = _snowLoad = Load(intensity);
			bool changed = canicule != Canicule;
			Canicule = canicule;
			bool wet = Publish(_wetRaw, Wet, out float w); Wet = w;
			bool frost = Publish(_frostRaw, Frost, out float f); Frost = f;
			if (wet || frost || changed || _snowing) RefreshAll();
		}

		public override void _Process(double delta)
		{
			float d = (float)delta;
			bool refresh = false;
			if (!_raining && _wetRaw > 0f)
			{
				_wetRaw = Mathf.Max(0f, _wetRaw - d / DryingSec);
				refresh |= Publish(_wetRaw, Wet, out float w); Wet = w;
			}
			if (!_freezing && _frostRaw > 0f)
			{
				_frostRaw = Mathf.Max(0f, _frostRaw - d / ThawSec);
				refresh |= Publish(_frostRaw, Frost, out float f); Frost = f;
			}
			if (refresh) RefreshAll();
			if (SnowRaw > 0f) SnowStep(d);
		}

		// Fonte (après l'épisode) et chute sous le vent (pendant) : la charge
		// continue décroît ; les plantes sont ré-examinées toutes les SnowScanSec.
		private static void SnowStep(float d)
		{
			bool shed = WindWave.Force >= ShedForce;
			float floor = _snowing ? (shed ? _snowLoad * ShedFloor : _snowLoad) : 0f;
			float rate = (_snowing ? 0f : 1f / MeltSec) + (shed ? 1f / ShedSec : 0f);
			if (SnowRaw <= floor || rate <= 0f) return;   // charge stable : rien à faire
			SnowRaw = Mathf.Max(floor, SnowRaw - d * rate);
			_scan += d;
			if (_scan < SnowScanSec && SnowRaw > 0f) return;
			_scan = 0f;
			foreach (var p in BakeQueue.All) p.RefreshMeteo();
		}

		// Quantifie une grandeur en paliers ; vrai si le palier publié a changé.
		private static bool Publish(float raw, float current, out float level)
		{
			level = Mathf.Ceil(raw * Levels) / Levels;
			return level != current;
		}

		/// <summary>Palier de neige d'UNE plante : décalage propre ∈ [−0,15 ; 0,15]
		/// (phase de hash) → les plantes changent de palier à des instants différents.</summary>
		public static float SnowLevelFor(float phase)
		{
			if (SnowRaw <= 0f) return 0f;
			float raw = Mathf.Clamp(SnowRaw + (phase - 0.5f) * 0.3f, 0f, 1f);
			return Mathf.Ceil(raw * Levels) / Levels;
		}

		// Chaque plante recalcule SA variante ; seules celles qui changent sont
		// salies (une plante sans `secheresse` ne recuit pas à la canicule).
		private static void RefreshAll()
		{
			_waves++;
			GD.Print($"[Météo] variante plantes : canicule {Canicule}, humidité {Wet:F2}, "
				+ $"givre {Frost:F2}, neige {SnowRaw:F2} (vague {_waves}, "
				+ $"{BakeQueue.All.Count} plantes examinées).");
			foreach (var p in BakeQueue.All) p.RefreshMeteo();
		}
	}
}
