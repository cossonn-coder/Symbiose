// SYMBIOSE — SolMateriau.cs (sprint RENDU VISIBLE D106, tronçon T2 « sol en un lot »)
// Le MATÉRIAU partagé par les maillages
// de tuile (SolMaillage), qui les rend IDENTIQUES AU PIXEL aux anciens nœuds
// (Sprite2D pour les dessus, Polygon2D pour les flancs).
//
// 📖 POURQUOI UN SHADER (fragment seul, 2 lignes). Un maillage n'a qu'une
// texture et qu'une couleur par sommet ; il faut pourtant y peindre deux
// choses différentes, dans l'ordre entrelacé d'avant :
//   · le FLANC du relief = couleur unie (pas de texture) → repéré par un UV
//     hors texture (SolMaillage.UvFlanc), il prend sa couleur de sommet seule ;
//   · le DESSUS = texture × damier. Le damier passe en DRAPEAU (blanc/noir)
//     et la teinte 0,95 est une constante du shader, parce qu'une couleur de
//     sommet est stockée sur 8 bits (0,95 → 242/255) alors que le Modulate du
//     Sprite2D était un flottant : ±1 niveau sur ~80 000 pixels sinon (mesuré).
// L'arrondi au pixel des positions, lui, est rejoué côté CPU (SolMaillage).

using Godot;

namespace Symbiose
{
	internal static class SolMateriau
	{
		// Un seul matériau pour toutes les tuiles (la texture du sol est portée
		// par chaque MeshInstance2D, pas par le matériau). La couleur de sommet
		// est recopiée en varying : en fragment, COLOR arrive déjà multiplié par
		// la texture, ce qui effacerait le flanc (UV hors texture = transparent).
		public static readonly ShaderMaterial Materiau = new() { Shader = new Shader { Code = Code() } };

		// Teinte des plots « sombres » du damier (ex-Modulate du Sprite2D).
		public const float DamierSombre = 0.95f;

		/// <summary>Couleur de sommet d'un dessus : drapeau damier lu par le shader.</summary>
		public static Color DrapeauDamier(bool sombre) => sombre ? Colors.Black : Colors.White;

		private static string Code()
		{
			// Calculé ICI (pas en champ statique) : l'ordre d'initialisation des
			// statiques suivrait celui du fichier, Materiau passerait avant.
			string damier = DamierSombre.ToString("R", System.Globalization.CultureInfo.InvariantCulture);
			return "shader_type canvas_item;\n"
				+ "varying vec4 couleur;\n"
				+ "void vertex() {\n"
				+ "	couleur = COLOR;\n"
				+ "}\n"
				+ "void fragment() {\n"
				// Flanc : couleur de sommet seule ; dessus : texture × damier
				// (drapeau = canal rouge du sommet, cf. en-tête).
				+ "	if (UV.x < 0.0) COLOR = couleur;\n"
				+ "	else COLOR = texture(TEXTURE, UV) * (couleur.r > 0.5 ? vec4(1.0)\n"
				+ $"		: vec4({damier}, {damier}, {damier}, 1.0));\n"
				+ "}\n";
		}
	}
}
