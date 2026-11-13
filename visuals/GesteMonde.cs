// SYMBIOSE — GesteMonde.cs (GESTES LISIBLES ⑤)
// UN GESTE DE L'AUTOMATE JOUÉ DANS LE MONDE : l'outil (mêmes images que le curseur,
// `AnimationGeste.TexturesMonde`) apparaît au point que le moteur a visé, joue sa suite
// d'images (deux passages), tient la dernière un instant, puis disparaît. Rien n'est
// inventé : le verbe et le point viennent du journal de l'automate (bloc `automate` du
// snapshot) ; la conséquence au sol, elle, est la trace moteur (sol-canvas, ③).
//
// 📖 Pédagogie Godot : un Sprite2D enfant du nœud « Objects » (tri en Y) vit DANS le
// monde : la caméra le zoome comme une plante (paliers entiers → pixels nets) et le tri
// en Y le place devant ce qui est derrière lui. `Centered = false` + `Offset = −point
// chaud` : le pixel actif de l'outil tombe pile sur le point visé, comme pour le curseur
// (le point chaud ne bouge pas d'une image à l'autre, c'est le dessin qui bouge).
// Le RETARD de départ étale plusieurs gestes du même tick dans le temps.

using Godot;

namespace Symbiose
{
	public partial class GesteMonde : Sprite2D
	{
		private const int Passages = 2;          // la suite jouée deux fois : lisible au jeu
		private const double TenueSec = 0.35;    // dernière image tenue avant de disparaître

		private Texture2D[] _images;
		private double _attente;                 // secondes avant la première image
		private double _echeance;                // secondes avant l'image suivante
		private int _index = -1;

		/// <summary>Prépare le sprite : images d'exécution, point chaud (px de la
		/// texture) posé sur la position du nœud, retard de départ.</summary>
		public void Init(Texture2D[] images, Vector2 pointChaud, double retardSec)
		{
			_images = images;
			_attente = retardSec;
			Centered = false;
			Offset = -pointChaud;
			Visible = false;
		}

		public override void _Process(double delta)
		{
			if (_attente > 0) { _attente -= delta; return; }
			_echeance -= delta;
			if (_echeance > 0) return;
			_index++;
			int total = _images.Length * Passages;
			if (_index >= total) { QueueFree(); return; }
			Texture = _images[_index % _images.Length];
			Visible = true;
			_echeance = AnimationGeste.DureeImageMs / 1000.0 + (_index == total - 1 ? TenueSec : 0);
		}
	}
}
