// SYMBIOSE — PaletteSnes.cs (sprint JARDIN VIVANT, T1)
// Branche le shader de quantification SNES (`palette_snes.gdshader`) sur le
// SubViewportContainer qui affiche le monde, et lui passe la palette maître
// (Palette16.Maitre = source UNIQUE des couleurs). Bascule debug avant/après.
//
// 📖 Pédagogie Godot/C# :
//  - Un SubViewport rend le monde dans une TEXTURE 960×540 ; le
//    SubViewportContainer (un Control) DESSINE cette texture agrandie ×2 à
//    l'écran. Lui poser un `Material` = un post-traitement plein écran gratuit :
//    une seule passe sur 960×540 pixels, quel que soit le nombre de plantes.
//  - Les uniforms tableaux (`uniform vec3 pal_srgb[48]`) se remplissent depuis
//    C# avec un `Vector3[]` via SetShaderParameter — comme écrire un bloc de
//    registres d'un coup.
//  - La conversion OKLab de la palette est faite UNE fois ici (~32 couleurs),
//    pas 518 400 fois par frame dans le shader (pas de recalcul dans un tick).
//
// Déterministe (aucun aléa), purement visuel : golden non concerné.

using Godot;

namespace Symbiose
{
	internal static class PaletteSnes
	{
		private const string ShaderPath = "res://visuals/palette_snes.gdshader";
		// Tramage « léger » (cf. shader) : seule la bande médiane entre deux
		// couleurs est tramée. Point F5 Nico : 0 = aplats, 1 = trame pleine.
		private const float Tramage = 0.5f;

		private static ShaderMaterial _mat;
		private static SubViewportContainer _cible;

		/// <summary>Actif ? (lu par le HUD/log de la bascule).</summary>
		public static bool Actif => _cible != null && _cible.Material != null;

		/// <summary>Pose le shader sur le conteneur du monde (ON par défaut).</summary>
		public static void Appliquer(SubViewportContainer cible)
		{
			_cible = cible;
			if (_mat == null)
			{
				var pal = Palette16.Maitre;
				var srgb = new Vector3[pal.Length];
				var lab = new Vector3[pal.Length];
				for (int i = 0; i < pal.Length; i++)
				{
					srgb[i] = new Vector3(pal[i].R, pal[i].G, pal[i].B);
					lab[i] = VersOklab(pal[i]);
				}
				_mat = new ShaderMaterial { Shader = GD.Load<Shader>(ShaderPath) };
				_mat.SetShaderParameter("pal_srgb", srgb);
				_mat.SetShaderParameter("pal_lab", lab);
				_mat.SetShaderParameter("pal_n", pal.Length);
				_mat.SetShaderParameter("pal_accents", pal.Length - Palette16.MaitreAccents);
				_mat.SetShaderParameter("tramage", Tramage);
			}
			_cible.Material = _mat;
		}

		/// <summary>Bascule avant/après (touche debug F11) — comparer au F5.</summary>
		public static void Basculer()
		{
			if (_cible == null) return;
			_cible.Material = _cible.Material == null ? _mat : null;
			GD.Print($"[PaletteSnes] F11 → palette SNES {(Actif ? "ON" : "OFF")}.");
		}

		// sRGB → OKLab (Ottosson 2020) — MÊMES coefficients que le shader
		// (srgb_vers_oklab) : les deux côtés doivent mesurer la même distance.
		private static Vector3 VersOklab(Color c)
		{
			Color lin = c.SrgbToLinear();
			float l = Cbrt(0.4122214708f * lin.R + 0.5363325363f * lin.G + 0.0514459929f * lin.B);
			float m = Cbrt(0.2119034982f * lin.R + 0.6806995451f * lin.G + 0.1073969566f * lin.B);
			float s = Cbrt(0.0883024619f * lin.R + 0.2817188376f * lin.G + 0.6299787005f * lin.B);
			return new Vector3(
				0.2104542553f * l + 0.7936177850f * m - 0.0040720468f * s,
				1.9779984951f * l - 2.4285922050f * m + 0.4505937099f * s,
				0.0259040371f * l + 0.7827717662f * m - 0.8086757660f * s);
		}

		private static float Cbrt(float x) => Mathf.Pow(Mathf.Max(x, 0f), 1f / 3f);
	}
}
