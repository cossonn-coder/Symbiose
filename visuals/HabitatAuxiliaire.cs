// SYMBIOSE — HabitatAuxiliaire.cs (sprint GESTES LISIBLES ④, conception §6)
// L'HABITAT D'AUXILIAIRES posé par `favoriser_auxiliaire` (ou par une pile de bois) :
// une tige plantée au sol qui porte 1 à 3 RONDELLES `auxiliaire` — un petit hôtel à
// insectes, rouge pointé de noir comme une coccinelle. Le nombre de rondelles vient du
// moteur (bloc `habitats_auxiliaires`, pont 0.6.15) : la vue n'en invente aucune.
//
// Dessin en pixels pleins, couleurs de la palette maître, origine du nœud = pied de la
// tige (posé au sol par WorldView.Habitats.cs, trié en profondeur avec les objets).

using Godot;

namespace Symbiose
{
	public partial class HabitatAuxiliaire : Node2D
	{
		private static readonly Color Bois = Palette16.BoisMur;
		private static readonly Color Contour = Palette16.MaitreSombre;
		private static readonly Color Rondelle = Palette16.Maitre[30];   // rouge accent
		private static readonly Color Ombre = Palette16.Ombre;

		private const float TigeHautPx = 18f;        // hauteur de la tige (px internes ×1)
		private const float RondelleLargePx = 7f;
		private const float RondelleHautPx = 3f;
		private const float PasRondellePx = 4f;      // écart vertical entre deux rondelles

		private int _rondelles;

		/// <summary>Nombre de rondelles portées (1..3, borné : une tige n'en porte pas plus).</summary>
		public void Init(int rondelles) => _rondelles = Mathf.Clamp(rondelles, 1, 3);

		public override void _Draw()
		{
			// Ombre au pied, puis la tige (1 px de bois cerné de contour).
			DrawRect(new Rect2(-3f, -1f, 6f, 2f), Ombre);
			DrawRect(new Rect2(-1.5f, -TigeHautPx, 3f, TigeHautPx), Contour);
			DrawRect(new Rect2(-0.5f, -TigeHautPx + 1f, 1f, TigeHautPx - 1f), Bois);
			// Les rondelles du haut vers le bas : disque rouge cerné, deux points noirs.
			for (int i = 0; i < _rondelles; i++)
			{
				float y = -TigeHautPx + 2f + i * PasRondellePx;
				float x = -RondelleLargePx / 2f;
				DrawRect(new Rect2(x - 1f, y - 1f, RondelleLargePx + 2f, RondelleHautPx + 2f), Contour);
				DrawRect(new Rect2(x, y, RondelleLargePx, RondelleHautPx), Rondelle);
				DrawRect(new Rect2(x + 1f, y + 1f, 1f, 1f), Contour);
				DrawRect(new Rect2(x + RondelleLargePx - 2f, y + 1f, 1f, 1f), Contour);
			}
		}
	}
}
