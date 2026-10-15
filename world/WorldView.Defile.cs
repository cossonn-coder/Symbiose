// SYMBIOSE — WorldView.Defile.cs (partial de WorldView, sprint JARDIN VIVANT T5)
// BANC F5 « jardin vivant » : touche F12 = DÉFILÉ des situations du sprint sur le
// jardin courant — calme → vent → canicule → pluie → neige (puis le vent forcit :
// la neige tombe par plaques) → grêle → gelée — StepSec secondes de jeu chacune,
// en boucle. Re-F12 = arrêt, retour à la météo et au ciel du snapshot.
//
// C'est un OUTIL D'OBSERVATION (comme le banc décor F10) : il IMPOSE seulement le
// bloc `weather` reçu par la vue (même chemin que le banc de capture T4) et le
// vent de l'onde (T3) ; le moteur Python n'est pas touché. Les TRACES (grêle, gel)
// restent celles du snapshot : pour les voir, monter un monde où le moteur les a
// produites (banc `effondrement` : grêle réelle + moitié sous voile).
// L'encart ciel affiche la situation (ligne nommée) le temps du défilé.
//
// 📖 Pédagogie Godot/C# : GetTree().CreateTimer(s) rend un SceneTreeTimer à usage
// unique (comme un one-shot matériel) ; on en chaîne un par étape. Le compteur
// _defileGen « périme » les minuteries d'un défilé arrêté (sinon un Timeout en
// vol relancerait une étape après l'arrêt).

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView
	{
		private const float DefileStepSec = 10f;

		// (libellé, kind moteur, intensité σ, vent, vent en 2e moitié, nébulosité)
		private static readonly (string Nom, string Kind, float Int, float Vent, float Vent2, float Neb)[] Defile =
		{
			("Calme",    "Beau temps",      0f,   0f,   0f,   0.10f),
			("Vent",     "Beau temps",      0f,   0.9f, 0.9f, 0.30f),
			("Canicule", "Canicule",        1.5f, 0.1f, 0.1f, 0.05f),
			("Pluie",    "Pluie prolongée", 1.5f, 0.3f, 0.3f, 0.90f),
			("Neige",    "Neige",           1.5f, 0.1f, 0.9f, 0.80f),
			("Grêle",    "Grêle",           1.9f, 0.5f, 0.5f, 0.70f),
			("Gelée",    "Gelée tardive",   1.5f, 0f,   0f,   0.20f),
		};

		private int _defileStep = -1;   // -1 = défilé arrêté
		private int _defileGen;

		private bool DefileActif => _defileStep >= 0;

		// Touche F12 : lance / arrête le défilé.
		private void ToggleDefile()
		{
			_defileGen++;
			if (DefileActif)
			{
				_defileStep = -1;
				WindWave.SetCaptureOverride(float.NaN, float.NaN);
				if (_lastWeather != null) ApplyWeather(_lastWeather);
				if (_lastCiel != null) _skyPanel?.SetSky(_lastCiel);
				GD.Print("[Défilé] F12 → arrêt, météo du snapshot.");
				return;
			}
			DefileEtape(0, _defileGen);
		}

		private void DefileEtape(int step, int gen)
		{
			if (gen != _defileGen) return;   // défilé arrêté entre-temps
			_defileStep = step % Defile.Length;
			var e = Defile[_defileStep];
			WindWave.SetCaptureOverride(e.Vent, float.NaN);
			if (_lastWeather != null) ApplyWeather(_lastWeather);
			_skyPanel?.SetSky(new GDict
			{
				["nebulosite"] = e.Neb,
				["evenement_courant"] = e.Kind,
				["nom_compose"] = $"jardin vivant · {e.Nom} ({_defileStep + 1}/{Defile.Length})",
			});
			GD.Print($"[Défilé] {_defileStep + 1}/{Defile.Length} : {e.Nom} ({e.Kind}, σ {e.Int}, vent {e.Vent}).");
			if (e.Vent2 != e.Vent)
				GetTree().CreateTimer(DefileStepSec / 2f).Timeout += () =>
				{
					if (gen != _defileGen || _defileStep != step % Defile.Length) return;
					WindWave.SetCaptureOverride(e.Vent2, float.NaN);
					GD.Print($"[Défilé] le vent forcit ({e.Vent2}).");
				};
			GetTree().CreateTimer(DefileStepSec).Timeout += () => DefileEtape(step + 1, gen);
		}

		// Bloc `weather` remplacé par la situation du défilé (sinon inchangé).
		private GDict DefileOverride(GDict weather)
		{
			if (!DefileActif) return weather;
			var e = Defile[_defileStep];
			var w = weather.Duplicate();
			w["kind"] = e.Kind;
			w["intensity"] = e.Int;
			w["nebulosite"] = e.Neb;
			return w;
		}
	}
}
