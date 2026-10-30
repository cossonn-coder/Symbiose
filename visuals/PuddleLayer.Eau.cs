// SYMBIOSE — PuddleLayer.Eau.cs (sprint MARE VIVANTE ②)
// Le BRANCHEMENT du shader de l'eau (`visuals/eau_mare.gdshader`) sur la couche :
// matériau partagé, rampes de couleurs posées en uniforms depuis RampesDa (une seule
// source chromatique), palier de zoom tenu à jour, texture blanche 1×1.
//
// 📖 Pédagogie — pourquoi une texture blanche ? LotTriangles n'envoie les UV au GPU
// que si on lui donne une texture. Or nos triangles CODÉS de la mare se signalent au
// shader par leur UV (x ≥ 1). Une texture blanche 1×1 ne change pas la couleur des
// triangles littéraux (couleur × blanc = couleur) et fait partir les UV : on garde
// UN SEUL envoi pour flaques, tourbe, berge ET mare (aucun draw call en plus).

using Godot;

namespace Symbiose
{
	public partial class PuddleLayer
	{
		private const string ShaderEau = "res://visuals/eau_mare.gdshader";
		private static ShaderMaterial _matEau;
		private static ImageTexture _texBlanche;
		private float _uZoom = -1f;

		private static ShaderMaterial MateriauEau
		{
			get
			{
				if (_matEau != null) return _matEau;
				_matEau = new ShaderMaterial { Shader = GD.Load<Shader>(ShaderEau) };
				_matEau.SetShaderParameter("eau", Rampe("eau_mare"));
				_matEau.SetShaderParameter("vase", Rampe("vase"));
				_matEau.SetShaderParameter("glace", Rampe("glace"));
				return _matEau;
			}
		}

		private static Texture2D TexBlanche
		{
			get
			{
				if (_texBlanche != null) return _texBlanche;
				var img = Image.CreateEmpty(1, 1, false, Image.Format.Rgba8);
				img.Fill(Colors.White);
				_texBlanche = ImageTexture.CreateFromImage(img);
				return _texBlanche;
			}
		}

		// Rampe RampesDa → tableau vec3 (uniform `vec3 x[n]` du shader).
		private static Vector3[] Rampe(string nom)
		{
			Color[] r = RampesDa.Matieres[nom];
			var v = new Vector3[r.Length];
			for (int i = 0; i < r.Length; i++) v[i] = new Vector3(r[i].R, r[i].G, r[i].B);
			return v;
		}

		// Chaque image : n'écrit l'uniform qu'au changement de palier.
		private void MajZoomEau()
		{
			float z = WorldView.CurrentZoom;
			if (z == _uZoom) return;
			_uZoom = z;
			MateriauEau.SetShaderParameter("zoom", z);
		}
	}
}
