// SYMBIOSE — MeteoPlantes.cs (sprint JARDIN VIVANT T4 — canicule, pluie/orage)
// L'ÉTAT MÉTÉO GLOBAL que les plantes lisent pour choisir leur variante de
// dessin (PlantRenderer.Meteo.cs). Lu dans le bloc `weather` du snapshot
// (kind) — aucune météo inventée par la vue.
//
// Trois temps (doc de conception §5) : AVANT = préavis déjà existant (encart
// ciel, sim/ciel.py) ; PENDANT = canicule (feuilles qui pendent, plantes en
// `secheresse` seulement) ou pluie/orage (feuillage trempé) ; APRÈS = le
// feuillage se ressuie en DryingSec secondes de jeu, par NIVEAUX discrets.
//
// 📖 Pédagogie (analogie embarqué) : l'humidité est un compteur qui décroît en
// temps réel, mais on ne la PUBLIE qu'en WetLevels paliers (quantification,
// comme un CAN à 2 bits) : chaque palier = une vague de re-cuisson étalée par
// la file à budget (BakeQueue), au lieu d'une re-cuisson à chaque frame.
// Animation = SIGNAL : sans épisode (ni canicule, ni pluie, sol sec), _Process
// sort tout de suite — aucune animation ne tourne.

using Godot;

namespace Symbiose
{
	public partial class MeteoPlantes : Node
	{
		// Le feuillage se ressuie en ~8 s de jeu après la fin de la pluie, en
		// 3 paliers (1 → 2/3 → 1/3 → sec). Calibrage F5 (« on sent la pluie ? »).
		private const float DryingSec = 8f;
		private const int WetLevels = 3;

		/// <summary>Canicule en cours (`weather.kind == "Canicule"`).</summary>
		public static bool Canicule { get; private set; }
		/// <summary>Humidité du feuillage publiée ∈ {0, 1/3, 2/3, 1}.</summary>
		public static float Wet { get; private set; }

		private static bool _raining;
		private static float _wetRaw;   // humidité continue (décroît après la pluie)
		private static int _waves;      // vagues de re-cuisson (mesure, log)

		/// <summary>Bloc `weather` du snapshot (kind déjà lu par WorldView).</summary>
		public static void SetWeather(string kind)
		{
			bool canicule = kind == "Canicule";
			_raining = kind == "Pluie prolongée" || kind == "Orage";
			if (_raining) _wetRaw = 1f;
			bool changed = canicule != Canicule;
			Canicule = canicule;
			if (Publish() || changed) RefreshAll();
		}

		public override void _Process(double delta)
		{
			if (_raining || _wetRaw <= 0f) return;   // rien à sécher : aucun travail
			_wetRaw = Mathf.Max(0f, _wetRaw - (float)delta / DryingSec);
			if (Publish()) RefreshAll();
		}

		// Quantifie l'humidité en paliers ; vrai si le palier publié a changé.
		private static bool Publish()
		{
			float level = Mathf.Ceil(_wetRaw * WetLevels) / WetLevels;
			if (level == Wet) return false;
			Wet = level;
			return true;
		}

		// Chaque plante recalcule SA variante ; seules celles qui changent sont
		// salies (une plante sans `secheresse` ne recuit pas à la canicule).
		private static void RefreshAll()
		{
			_waves++;
			GD.Print($"[Météo] variante plantes : canicule {Canicule}, humidité {Wet:F2} "
				+ $"(vague {_waves}, {BakeQueue.All.Count} plantes examinées).");
			foreach (var p in BakeQueue.All) p.RefreshMeteo();
		}
	}
}
