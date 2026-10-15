// SYMBIOSE — WindWave.cs (sprint JARDIN VIVANT T3 — vent en onde)
// L'ONDE DE VENT : un front traverse le jardin dans le sens du vent et APPUIE
// sur les plantes, qui se couchent puis se relèvent l'une après l'autre. Sans
// vent, rien ne bouge (l'animation est un SIGNAL d'état, conception §2.1).
//
// 📖 Pédagogie (analogie embarqué) : chaque plante a 8 images pré-cuites
// (PlantBaker) = 8 degrés de flexion. Animer = choisir, à chaque frame, QUEL
// index d'image afficher — une table de correspondance, pas un recalcul du
// dessin. Ce nœud calcule cet index pour les plantes visibles : quelques
// opérations flottantes + un sinus par plante, aucune allocation.
//
// Formule (doc de conception §4, kickoff T3 §3-§5) :
//   cycle  = f·(t − retard) − (position · direction_aval) / λ      [en cycles]
//   flexion = clamp(raideur × F × (fond + enveloppe(cycle) × risée)
//                   + balancement, 0, 1)        avec F = force × abri local
//   pose   = round(flexion × 7), plafonnée à la pose maximale cuite de la plante.
// Le front d'onde = enveloppe ASYMÉTRIQUE (montée rapide = la poussée, descente
// lente = la plante se relève, puis repos jusqu'au front suivant).
//
// Source des données : bloc `weather.wind` du snapshot (protocole 0.5.44, masse
// d'air PURE de sim/wind.py) + clé `abri` par plante (fields/abri.py). Zéro
// logique écologique ici — la vue peint ce que le moteur décide. Déterministe :
// le temps est l'accumulateur des delta de frame (fixes en Movie Maker).

using Godot;
using System.Diagnostics;

namespace Symbiose
{
	public partial class WindWave : Node
	{
		// --- Calibrage (à confirmer au F5 de Nico : « une main qui appuie ? ») ---
		// Sous ce seuil de force la masse d'air est CALME : 1 seule pose cuite,
		// aucune animation (images identiques frame à frame).
		public const float CalmForce = 0.05f;
		// Longueur d'onde (cm) et fréquence (Hz) des fronts à force nulle ; les
		// deux croissent avec la force (× (0,5 + force)) : une rafale de tempête
		// arrive plus vite et plus large. Force 0,7 → λ 6 m, 0,24 Hz ≈ 1,4 m/s.
		private const float LambdaCm = 500f;
		private const float FreqHz = 0.2f;
		// Enveloppe : montée sur les 12 % premiers du cycle, retour jusqu'à 65 %,
		// puis repos (la plante est revenue à son « fond » avant le front suivant).
		private const float RiseFrac = 0.12f;
		private const float DecayEnd = 0.65f;
		// Poids du front par rapport au fond.
		private const float EnvGain = 0.8f;
		// Fond ∝ force (sous vent soutenu les plantes RESTENT penchées), plafonné.
		private const float FondCoef = 0.6f;
		private const float FondCap = 1.2f;
		// Balancement propre (désynchronise sans casser le front) : amplitude en
		// unités de flexion par unité de force, pulsation de base (rad/s).
		private const float SwayAmp = 0.08f;
		private const float SwayOmega = 2.6f;
		// Re-cuisson des poses quand la direction aval dérive de plus de ce seuil.
		private const float ReBakeAngleRad = 0.26f;   // ≈ 15°

		// --- État global (dernier snapshot) ---
		public static float Force { get; private set; }
		/// <summary>Direction AVAL (vers où va le vent), vecteur unitaire monde
		/// (x_cm, y_cm) — celle de la masse d'air courante.</summary>
		public static Vector2 Downwind { get; private set; } = new(0f, 1f);
		/// <summary>Direction aval figée dans les images cuites (re-cuisson au-delà
		/// de ReBakeAngleRad). La flexion des pinceaux la lit.</summary>
		public static Vector2 BakedDir { get; private set; } = new(0f, 1f);
		public static bool Active => Force >= CalmForce;

		private static readonly float[] _gusts = { 1f, 1f, 1f, 1f };
		private static float _gustMean = 1f;
		private static double _t;   // temps animé (s), accumulateur déterministe

		// Forçage du banc de capture (--capture-vent) : NaN = inactif.
		private static float _overForce = float.NaN, _overDir = float.NaN;
		private static float _lastForce, _lastDir;

		// Mesure du coût par frame (gravée dans 00_etat.md).
		private double _msSum, _msMax, _logT;
		private int _frames, _plantsLast;
		private bool _wasActive;

		/// <summary>Bloc `weather.wind` du snapshot. `dirFrom` = D'OÙ vient le
		/// vent (rad, convention sim/wind.py). Lecture tolérante (gusts absent).</summary>
		public static void SetWind(float force, float dirFrom, Godot.Collections.Array gusts)
		{
			_lastForce = force;
			_lastDir = dirFrom;
			if (gusts != null && gusts.Count == _gusts.Length)
			{
				float sum = 0f;
				for (int i = 0; i < _gusts.Length; i++) sum += _gusts[i] = (float)gusts[i].AsDouble();
				_gustMean = Mathf.Max(0.1f, sum / _gusts.Length);
			}
			Apply();
		}

		/// <summary>Banc de capture : impose force (et direction si non NaN).</summary>
		public static void SetCaptureOverride(float force, float dirFrom)
		{
			_overForce = force;
			_overDir = dirFrom;
			Apply();
		}

		private static void Apply()
		{
			bool wasActive = Active;
			Force = float.IsNaN(_overForce) ? _lastForce : _overForce;
			float d = float.IsNaN(_overDir) ? _lastDir : _overDir;
			// Le vent VIENT de d → il VA vers (sin d, cos d) en (x, y) monde : même
			// convention que le sillage d'abri de fields/abri.py (gx, gy).
			Downwind = new Vector2(Mathf.Sin(d), Mathf.Cos(d));
			bool drift = Mathf.Abs(BakedDir.AngleTo(Downwind)) > ReBakeAngleRad;
			if (drift) BakedDir = Downwind;
			// Le nombre de poses cuites (1 au calme, jusqu'à 8 au vent) ou leur
			// direction change → toutes les plantes sont salies ; la FILE (T2) les
			// recuit quelques-unes par frame, l'écran d'abord.
			if (Active != wasActive || (Active && drift))
				foreach (var p in BakeQueue.All) p.Invalidate();
		}

		public override void _Process(double delta)
		{
			_t += delta;
			if (!Active)
			{
				// Retour au calme : une seule passe pour redresser tout le monde.
				if (_wasActive) foreach (var p in BakeQueue.All) p.ApplyWindPose(0);
				_wasActive = false;
				return;
			}
			_wasActive = true;
			long t0 = Stopwatch.GetTimestamp();
			int n = 0;
			foreach (var p in BakeQueue.All)
			{
				if (!p.IsVisibleInTree()) continue;   // marge du culling = « près de l'écran »
				p.UpdateWind();
				n++;
			}
			Measure(Stopwatch.GetElapsedTime(t0).TotalMilliseconds, n, delta);
		}

		/// <summary>Pose (0..maxPose) d'une plante à l'instant courant. `wx/wy` =
		/// position MONDE (cm), `abri` = facteur local, `raideur` ∈ ]0,1] (port),
		/// `lag` = retard (s) des grands ports, `swayPhase` = hash de son identité.</summary>
		public static int PoseFor(float wx, float wy, float abri, float raideur,
								  float lag, float swayPhase, int maxPose)
		{
			if (maxPose <= 0) return 0;
			float f = Force * abri;
			float scale = 0.5f + Force;
			double s = (wx * Downwind.X + wy * Downwind.Y) / (LambdaCm * scale);
			double cyc = FreqHz * scale * (_t - lag) - s;
			double n = System.Math.Floor(cyc);
			float u = (float)(cyc - n);
			float risee = _gusts[(int)(((long)n % 4 + 4) % 4)] / _gustMean;
			float fond = FondCoef * Mathf.Min(f, FondCap);
			float sway = SwayAmp * raideur * f
						 * (float)System.Math.Sin(SwayOmega * (0.8 + 0.4 * swayPhase) * _t
												  + swayPhase * Mathf.Tau);
			float flex = Mathf.Clamp(raideur * f * (fond + EnvGain * Envelope(u) * risee) + sway,
									 0f, 1f);
			return Mathf.Min(Mathf.RoundToInt(flex * 7f), maxPose);
		}

		// Front asymétrique : montée en smoothstep (la poussée), retour quadratique
		// (la plante se relève), repos ensuite.
		private static float Envelope(float u)
		{
			if (u < RiseFrac) { float x = u / RiseFrac; return x * x * (3f - 2f * x); }
			if (u < DecayEnd) { float x = (DecayEnd - u) / (DecayEnd - RiseFrac); return x * x; }
			return 0f;
		}

		// Coût CPU de la boucle d'onde, moyenné sur ~5 s de jeu (log).
		private void Measure(double ms, int n, double delta)
		{
			_msSum += ms;
			if (ms > _msMax) _msMax = ms;
			_frames++;
			_plantsLast = n;
			_logT += delta;
			if (_logT < 5.0) return;
			GD.Print($"[Vent] onde : force {Force:F2}, {_plantsLast} plantes près de l'écran, "
				+ $"{_msSum / _frames:F3} ms/frame moy. (max {_msMax:F3}) sur {_frames} frames.");
			_msSum = _msMax = _logT = 0;
			_frames = 0;
		}
	}
}
