// SYMBIOSE — WorldView.Soleil.cs (partial de WorldView, SS⑥ refactor global)
// L'ombre solaire ANIMÉE (volet C) : portage de fields/light.py:solar_slice,
// balayé continûment sur la semaine vécue. Statiques LUES par PlantRenderer
// (capsules d'ombre des plantes) ; ici on calcule la direction/longueur de
// l'ombre et on re-projette celle de la maison. Aucune règle écologique : un
// éclairage de vue fidèle au modèle, jamais une contrainte sur le moteur.

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// --- Soleil de la vue (volet C) --------------------------------------
		// 📖 Pédagogie — la MÊME formule que le moteur, pas une invention :
		// fields/light.py:solar_slice (astronomie : latitude 49°N, déclinaison
		// saisonnière ±23,4°, angle horaire → azimut + élévation → direction et
		// longueur d'ombre). Le moteur n'échantillonne que 3 tranches horaires
		// pour l'INTÉGRALE écologique hebdo ; la vue, elle, balaye l'angle
		// horaire CONTINÛMENT pendant la semaine vécue : 1 semaine (60 s) ≈ 1
		// journée visuelle, du lever au coucher (le moteur n'a pas de notion de
		// jour — c'est un éclairage de vue, fidèle au modèle, jamais une règle).
		// Ces statiques sont LUES par PlantRenderer (capsules d'ombre).
		public static Vector2 SunShadowDir { get; private set; } = new Vector2(0f, -1f);
		public static float SunInvTan { get; private set; } = 1.0f;   // longueur = h × invTan
		public static float SunStrength { get; private set; } = 1.0f; // sin(élévation)
		// Touche O (volet C2, retour perf Nico) : coupe TOUTES les ombres
		// (plantes + maison) — le lot PlantShadow se vide, UpdateSun
		// s'endort. Lu par PlantShadow.
		public static bool ShadowsOn { get; private set; } = true;
		private const float LatitudeDeg = 49.0f;    // = fields/light.py LATITUDE_DEG
		// Ombre bornée à 3,5× la hauteur : au ras de l'horizon 1/tan(élév) → ∞,
		// l'écran n'a pas besoin d'ombres kilométriques pour dire « soir ».
		private const float MaxInvTan = 3.5f;
		// Marge au lever/coucher (°) : on ne balaye pas jusqu'à l'horizon exact.
		private const float SunriseMarginDeg = 8f;
		private float _lastSunH = float.NaN;        // dernier angle horaire appliqué
		private string _lastSunSeason;

		// = SOLAR_DECLINATION de fields/light.py (clés sans accent du moteur).
		private static float DeclinationOf(string season) => season switch
		{
			"ete"   => 23.4f,
			"hiver" => -23.4f,
			_       => 0.0f,    // printemps / automne : équinoxes
		};

		// -------------------------------------------------------------------
		// SOLEIL (volet C) — portage de fields/light.py:solar_slice, balayé
		// continûment sur la semaine vécue. Appelé chaque frame, mais ne
		// REDESSINE que si l'angle horaire a bougé de ≥ 2° (à 60 s/semaine
		// c'est ~1 redraw/s ; à 3 s debug, ~15/s — toujours trivial).
		// -------------------------------------------------------------------

		private void UpdateSun()
		{
			if (!ShadowsOn) return;        // ombres coupées (O) : zéro travail
			if (_season == null) return;   // pas encore de snapshot
			float spw = DebugSecondsPerWeek > 0f ? DebugSecondsPerWeek : SecondsPerWeek;

			// Lever/coucher astronomiques : cos H_set = −tan φ · tan δ. C'est
			// LUI qui fait les jours longs d'été (±120° à 49°N) et courts
			// d'hiver (±60°) — aucune table à écrire, la formule décide.
			float phi = Mathf.DegToRad(LatitudeDeg);
			float dec = Mathf.DegToRad(DeclinationOf(_season));
			float hSet = Mathf.RadToDeg(Mathf.Acos(
				Mathf.Clamp(-Mathf.Tan(phi) * Mathf.Tan(dec), -1f, 1f)));

			// Angle horaire courant : la jauge intra-semaine devient l'heure du
			// jour. Temps figé (Planification), plein régime (Turbo) → midi.
			float h;
			if (_phase == Phase.Planification || _simMode == SimMode.Turbo || spw <= 0f)
				h = 0f;
			else
				h = Mathf.Lerp(-hSet + SunriseMarginDeg, hSet - SunriseMarginDeg,
							   Mathf.Clamp(_timeAccum / spw, 0f, 1f));
			// En Pause, _timeAccum est figé → h ne bouge plus : l'ombre attend.

			if (_season == _lastSunSeason && !float.IsNaN(_lastSunH)
				&& Mathf.Abs(h - _lastSunH) < 2f)
				return;   // soleil quasi immobile : rien à redessiner
			_lastSunH = h;
			_lastSunSeason = _season;

			// --- solar_slice (fields/light.py), au degré près -----------------
			float H = Mathf.DegToRad(h);
			float sinElev = Mathf.Sin(phi) * Mathf.Sin(dec)
				+ Mathf.Cos(phi) * Mathf.Cos(dec) * Mathf.Cos(H);
			if (sinElev <= 1e-3f) return;   // sous l'horizon (marge le rend rare)
			float elev = Mathf.Asin(Mathf.Clamp(sinElev, -1f, 1f));
			float cosElev = Mathf.Cos(elev);
			float cosAz = (Mathf.Sin(dec) - sinElev * Mathf.Sin(phi))
				/ (cosElev * Mathf.Cos(phi));
			float az = Mathf.Acos(Mathf.Clamp(cosAz, -1f, 1f));
			if (h > 0f) az = Mathf.Tau - az;   // après-midi → soleil à l'Ouest

			// L'ombre pointe à l'OPPOSÉ du soleil. Monde : x = Est, y = Sud →
			// midi (az = 180°) donne (0, −1) = plein Nord, comme le moteur.
			SunShadowDir = new Vector2(-Mathf.Sin(az), Mathf.Cos(az));
			SunInvTan = Mathf.Min(cosElev / sinElev, MaxInvTan);
			SunStrength = sinElev;

			// Re-projeter les ombres : maison (polygone) + lot des ombres de
			// plantes (PERF VUE ③ : une commande, jamais les segments des plantes).
			UpdateHouseShadow();
			PlantShadow.MarquerSale();
		}

		// Ombre de la maison = enveloppe convexe, EN COORDONNÉES MONDE, de
		// l'empreinte au sol + des coins hauts-de-mur projetés au sol le long
		// de la direction d'ombre + du faîte projeté — puis projection écran
		// point à point (une enveloppe convexe reste convexe par application
		// affine : l'ordre des sommets survit à la projection ET à la rotation).
		private void UpdateHouseShadow()
		{
			if (_houseShadow == null) return;
			Vector2 d = SunShadowDir;
			float lWall = _hWallCm * SunInvTan;
			float lApex = _hHeightCm * SunInvTan;
			var w = new Vector2[]
			{
				new(_hx0, _hy0), new(_hx1, _hy0), new(_hx1, _hy1), new(_hx0, _hy1),
				new Vector2(_hx0, _hy0) + d * lWall, new Vector2(_hx1, _hy0) + d * lWall,
				new Vector2(_hx1, _hy1) + d * lWall, new Vector2(_hx0, _hy1) + d * lWall,
				new Vector2((_hx0 + _hx1) / 2f, (_hy0 + _hy1) / 2f) + d * lApex,
			};
			var hull = Geometry2D.ConvexHull(w);
			var scr = new Vector2[hull.Length];
			for (int i = 0; i < hull.Length; i++)
				scr[i] = WorldToScreen(hull[i].X, hull[i].Y);
			_houseShadow.Polygon = scr;
			// Soleil bas = lumière faible = ombre plus pâle (et plus longue).
			var col = OmbreColor;
			col.A = OmbreColor.A * Mathf.Clamp(SunStrength * 1.4f, 0.3f, 1f);
			_houseShadow.Color = col;
		}
	}
}
