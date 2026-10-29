// SYMBIOSE — RampesDa.cs (sprint CASSÉ À L'ÉCRAN ①, charte DA 16 bits)
// TABLE DES RAMPES : la charte chromatique du brief DA
// (docs/rendu/pixelart/etude_brief_da_16bits.md) posée en DONNÉES de vue.
//   (1) `Matieres` : une rampe de 3 à 5 tons (+ éclat isolé optionnel) par matière,
//       sombre → clair, hex TEL QUEL du brief (§ Palettes mesurées) ;
//   (2) `Deriver` : décline une teinte d'espèce existante en rampe à TEINTE QUI
//       DÉRIVE (règle 3 du brief : ombre vers le bleu-vert / le froid, éclat vers
//       le jaune) — une fonction documentée plutôt que 100 hex tapés à la main ;
//   (3) recettes PAR ESPÈCE : plantes (`PlantRenderer.TeintesEspece`), faune
//       (`MacroLife.CouleurEspece`), carpophores (`CarpophoreStyles.De`).
// Ce tronçon NE BRANCHE PAS la table au rendu (c'est ③, palette indexée + LUT par
// matière). Les rampes littérales sont relues et contrôlées par le banc
// `python3 tools/mesure_da.py --charte visuals/RampesDa.cs`.
//
// Contour sélectif (règle 7) : le trait d'un PETIT objet = le ton le plus sombre de
// SA rampe (`Contour`) — jamais #000. Les masses n'ont pas de contour.
//
// 📖 Pédagogie — pourquoi OKLab pour dériver ?
// En HSV, « assombrir de 10 % » ne donne pas le même saut visible pour un jaune et
// pour un bleu. OKLab est PERCEPTUEL : L = clarté vue, (a, b) = couleur ; en coordonnées
// polaires (L, C = chroma, h = teinte) on peut faire trois gestes indépendants :
// baisser L (plus sombre), tourner h (dériver la teinte), garder C (rester coloré).
// C'est la même idée qu'un filtre en embarqué : on change de base pour que l'opération
// voulue devienne une simple addition.
//
// Déterministe (aucun aléa), purement visuel : golden non concerné.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	/// <summary>Recette chromatique d'une espèce : une rampe (sombre → clair) par
	/// partie. Le contour d'un petit objet = `RampesDa.Contour(rampe)`.</summary>
	internal readonly record struct RecetteDa(Color[] Feuillage, Color[] Tige, Color[] Organe, Color[] Fleur);

	internal static class RampesDa
	{
		// ── (1) Matières du brief, hex tel quel (sombre → clair) ─────────────────
		// ≤ 5 tons par matière, 6 avec un éclat isolé (dernier ton). Aucun #000 ni gris
		// quasi-noir (contrôlé par le banc --charte).
		public static readonly Dictionary<string, Color[]> Matieres = new()
		{
			["canopee_jour"] = Hex("115920", "1f691e", "2f821e", "4fb023", "81d51b", "b0f800"), // éclat isolé #b0f800 (capture 3)
			["tronc"] = Hex("4f351a", "5e3e26", "745238", "a1774f"),                          // tronc et racines (capture 3)
			["buisson_vif"] = Hex("3b662b", "527e42", "5f8f41", "9fc339"),                    // capture 3
			["couvert_olive"] = Hex("302806", "454c10", "616225", "878c44", "aab164"),        // dialecte 2, bord haut le plus clair (capture 2)
			["touffe_claire"] = Hex("455314", "576824", "657731", "8ea04f"),                  // capture 2
			["gazon"] = Hex("2c3c1e", "537c44", "60804a", "568943", "7d9b4f"),                // capture 3, rangé par clarté (décor ⑥ ; le sol reste D34)
			["feuille_fleur"] = Hex("4a7237", "5c824b", "89a84d"),                            // feuilles du trio de fleurs (capture 3)
			// Fleur jaune : le brief donne corps + éclat et une « ombre orangée » NON mesurée ;
			// celle-ci = Deriver(#e5cf49) ton −1, figée ici (#caa704).
			["fleur_jaune"] = Hex("caa704", "e5cf49", "f4e559"),
			// Confettis : le brief ne mesure que la moyenne magenta #d72dcd ; ombre et
			// clair = Deriver(#d72dcd) tons −1 / +1, figés ici.
			["fleur_magenta"] = Hex("a600b1", "d72dcd", "ff4ddc"),
			["terre_cuite"] = Hex("6e4e4e", "a06a5d", "a77a51"),                              // pot fleuri (capture 3) : bacs, pots
			// Pierre : « trois tons et un éclat en haut-gauche » SANS hex mesuré → gris
			// chauds verdis (C/L ≥ 0,04 : jamais un gris neutre), dernier ton = éclat.
			["pierre"] = Hex("4a4a3c", "6e6e5a", "949480", "b4b49c"),
			// Décor crème : « deux tons (crème, gris pâle) » ; le gris pâle non mesuré =
			// Deriver(#c7c797) ton −1, figé ici.
			["creme"] = Hex("a9a374", "c7c797"),
		};

		/// <summary>Trait d'un petit objet (règle 7) : le ton le plus sombre de SA rampe.</summary>
		public static Color Contour(Color[] rampe) => rampe[0];

		// ── (2) Dérivation d'une rampe à teinte qui dérive ───────────────────────
		// 5 tons : creux (−2), ombre (−1), BASE (0, inchangée), clair (+1), éclat (+2).
		// Réglages (rationale) :
		//  - DlSombre 0,11 / DlClair 0,09 de L OKLab par cran : la canopée du brief
		//    (#115920 → #81d51b) couvre ≈ 0,40 de L sur 4 crans ; les crans sont
		//    COMPRIMÉS près des bornes (L 0,20 / 0,96) pour que 5 tons restent distincts.
		//  - PasTeinte 6° OKLab par cran : ≈ 12° HSV, soit l'ampleur du brief
		//    (110° → 133° en 2 crans d'ombre, 110° → 87° en 2 crans de clair).
		//  - TeinteChaude 105° = jaune (#f4e559) ; TeinteFroide 230° = bleu froid. On
		//    tourne par le PLUS COURT chemin : un vert s'ombre en bleu-vert, un rouge en
		//    pourpre. EXCEPTION des jaunes (à < 30° du jaune) : leur ombre vire à
		//    l'ORANGÉ (brief, épi jaune), jamais au vert.
		//  - Anti-noir : sous L 0,33 (zone quasi-noire du banc), la chroma est relevée à
		//    ≥ 0,08 × L → l'ombre la plus sombre reste colorée (#071010 vaut 0,085).
		private const float DlSombre = 0.11f, DlClair = 0.09f;
		private const float LMin = 0.20f, LMax = 0.96f;
		private const float PasTeinte = 6f;
		private const float TeinteChaude = 105f, TeinteFroide = 230f;
		private const float ZoneJaune = 30f;
		private const float ChromaNeutre = 0.02f;   // sous ce seuil la teinte n'a pas de sens
		private const float LQuasiNoir = 0.33f, ChromaAntiNoir = 0.08f;

		/// <summary>Rampe de 5 tons (sombre → clair) dérivée de `baseCol` ; le ton
		/// d'indice 2 EST `baseCol`.</summary>
		public static Color[] Deriver(Color baseCol)
		{
			var (l0, c0, h0) = VersOklch(baseCol);
			float ds = l0 > LMin ? Mathf.Min(DlSombre, (l0 - LMin) / 2f) : 0f;
			float dc = l0 < LMax ? Mathf.Min(DlClair, (LMax - l0) / 2f) : 0f;
			if (c0 < ChromaNeutre) h0 = TeinteFroide;   // gris : une ombre froide
			var r = new Color[5];
			for (int t = -2; t <= 2; t++)
			{
				if (t == 0) { r[2] = baseCol; continue; }
				float l = l0 + t * (t < 0 ? ds : dc);
				float h;
				if (t > 0) h = Tourner(h0, TeinteChaude, PasTeinte * t);
				else if (Mathf.Abs(Ecart(h0, TeinteChaude)) < ZoneJaune) h = h0 + PasTeinte * t;   // jaune → orangé
				else h = Tourner(h0, TeinteFroide, -PasTeinte * t);
				float c = l < LQuasiNoir ? Mathf.Max(c0, ChromaAntiNoir * l) : c0;
				r[t + 2] = DepuisOklch(l, c, h);
			}
			return r;
		}

		// ── (3) Recettes par espèce (mémoïsées : calculées une fois par espèce) ──
		// Arbres : tige = matière « tronc » du brief ; herbacées : tige = rampe de l'apex
		// tendre (Palette16.BoisApex), comme le bois jeune du rendu actuel.
		private static readonly HashSet<string> Arbres = new()
		{
			"AppleTree", "Fig", "CherryTree", "WalnutTree", "OakTree",
			"BeechTree", "HornbeamTree", "BirchTree", "FirTree", "Alder",
		};
		private static readonly Dictionary<string, RecetteDa> _plantes = new();
		private static readonly Dictionary<string, Color[]> _faune = new();
		private static readonly Dictionary<string, RecetteDa> _carpo = new();

		/// <summary>Plante (clé = nom de classe Python, comme `Palettes`).</summary>
		public static RecetteDa Plante(string espece)
		{
			if (_plantes.TryGetValue(espece, out var r)) return r;
			var (feuille, fleur, fruit) = PlantRenderer.TeintesEspece(espece);
			r = new RecetteDa(Deriver(feuille),
				Arbres.Contains(espece) ? Matieres["tronc"] : Deriver(Palette16.BoisApex),
				Deriver(fruit), Deriver(fleur));
			_plantes[espece] = r;
			return r;
		}

		/// <summary>Bête de la vie macro (clé = guilde du snapshot) : une rampe de corps.</summary>
		public static Color[] Faune(string guilde)
		{
			if (_faune.TryGetValue(guilde, out var r)) return r;
			r = Deriver(MacroLife.CouleurEspece(guilde));
			_faune[guilde] = r;
			return r;
		}

		/// <summary>Carpophore : Organe = chapeau, Tige = pied (Feuillage/Fleur = chapeau).</summary>
		public static RecetteDa Carpophore(string espece)
		{
			if (_carpo.TryGetValue(espece, out var r)) return r;
			var s = CarpophoreStyles.De(espece);
			var chapeau = Deriver(s.Chapeau);
			r = new RecetteDa(chapeau, Deriver(s.Pied), chapeau, chapeau);
			_carpo[espece] = r;
			return r;
		}

		// ── Conversions OKLab (Björn Ottosson, 2020) ─────────────────────────────
		private static Color[] Hex(params string[] h)
		{
			var r = new Color[h.Length];
			for (int i = 0; i < h.Length; i++) r[i] = new Color(h[i]);
			return r;
		}

		private static float Lin(float v) => v <= 0.04045f ? v / 12.92f : Mathf.Pow((v + 0.055f) / 1.055f, 2.4f);
		private static float Gam(float v) => v <= 0.0031308f ? 12.92f * v : 1.055f * Mathf.Pow(v, 1f / 2.4f) - 0.055f;

		private static (float L, float C, float H) VersOklch(Color c)
		{
			float r = Lin(c.R), g = Lin(c.G), b = Lin(c.B);
			float l = Mathf.Pow(0.4122214708f * r + 0.5363325363f * g + 0.0514459929f * b, 1f / 3f);
			float m = Mathf.Pow(0.2119034982f * r + 0.6806995451f * g + 0.1073969566f * b, 1f / 3f);
			float s = Mathf.Pow(0.0883024619f * r + 0.2817188376f * g + 0.6299787005f * b, 1f / 3f);
			float L = 0.2104542553f * l + 0.7936177850f * m - 0.0040720468f * s;
			float A = 1.9779984951f * l - 2.4285922050f * m + 0.4505937099f * s;
			float B = 0.0259040371f * l + 0.7827717662f * m - 0.8086757660f * s;
			float h = Mathf.RadToDeg(Mathf.Atan2(B, A));
			return (L, Mathf.Sqrt(A * A + B * B), h < 0f ? h + 360f : h);
		}

		// sRGB LINÉAIRE d'un point OKLab (peut sortir de [0,1] : hors gamut).
		private static (float R, float G, float B) LinDepuisOklab(float L, float a, float b)
		{
			float l = L + 0.3963377774f * a + 0.2158037573f * b;
			float m = L - 0.1055613458f * a - 0.0638541728f * b;
			float s = L - 0.0894841775f * a - 1.2914855480f * b;
			l *= l * l; m *= m * m; s *= s * s;
			return (4.0767416621f * l - 3.3077115913f * m + 0.2309699292f * s,
				-1.2684380046f * l + 2.6097574011f * m - 0.3413193965f * s,
				-0.0041960863f * l - 0.7034186147f * m + 1.7076147010f * s);
		}

		// OKLch → Color. Hors gamut : on RÉDUIT la chroma (dichotomie, 12 pas) en
		// gardant clarté et teinte — la couleur la plus vive affichable sur ce cap.
		private static Color DepuisOklch(float L, float C, float hDeg)
		{
			float ca = Mathf.Cos(Mathf.DegToRad(hDeg)), sa = Mathf.Sin(Mathf.DegToRad(hDeg));
			bool Dedans(float c)
			{
				var (r, g, b) = LinDepuisOklab(L, c * ca, c * sa);
				const float e = 1e-4f;
				return r >= -e && r <= 1f + e && g >= -e && g <= 1f + e && b >= -e && b <= 1f + e;
			}
			float cc = C;
			if (!Dedans(C))
			{
				float lo = 0f, hi = C;
				for (int i = 0; i < 12; i++) { float mid = (lo + hi) / 2f; if (Dedans(mid)) lo = mid; else hi = mid; }
				cc = lo;
			}
			var (lr, lg, lb) = LinDepuisOklab(L, cc * ca, cc * sa);
			return new Color(Gam(Mathf.Clamp(lr, 0f, 1f)), Gam(Mathf.Clamp(lg, 0f, 1f)), Gam(Mathf.Clamp(lb, 0f, 1f)));
		}

		// Écart signé de teinte (degrés, −180..180) et rotation bornée vers une cible.
		private static float Ecart(float h, float cible) => ((cible - h) % 360f + 540f) % 360f - 180f;
		private static float Tourner(float h, float cible, float deg) => h + Mathf.Clamp(Ecart(h, cible), -deg, deg);
	}
}
