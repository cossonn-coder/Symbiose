// SYMBIOSE — PlancheFaune.cs (sprint CASSÉ À L'ÉCRAN ⑤ — banc de la faune)
// BANC D'OBSERVATION « planche de la faune » : toutes les bêtes (vie macro puis
// butineurs, une RANGÉE par espèce) aux paliers ×2 · ×4 · ×8 · ×16, à la taille
// exacte du jeu, cap 0 (tête à droite), puis deux autres caps (45°, vers le haut)
// au palier ×8. Fond uni (mode planche de `tools/mesure_da.py`, `--pas 1` : ici
// 1 px interne = 1 px écran). Aucun nom affiché (les bêtes ne se nomment jamais à
// l'écran) : l'ordre des rangées est imprimé au journal. Banc VM :
// `tools/capture_vm.sh -K` (= --capture-faune=1). Pas un livrable joueur.
//
// Mêmes portraits, même lot et même shader que les couches du jeu (FauneIcones +
// palette indexée) : ce qu'on mesure ici est ce que le joueur voit, en plus grand.
// F11 coupée (`-L`) : la planche montre les rectangles / grains d'avant.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	public partial class PlancheFaune : Node2D
	{
		private static readonly float[] Paliers = { 2f, 4f, 8f, 16f };
		private const float Marge = 16f, Ecart = 14f;
		private readonly LotTriangles _lot = new();

		public override void _Ready()
		{
			if (PaletteIndexee.Active) Material = PaletteIndexee.Materiau;
			var noms = new List<string>();
			foreach (var (esp, _) in Especes()) noms.Add(esp);
			GD.Print($"[PlancheFaune] rangées (haut → bas) : {string.Join(", ", noms)} ; "
				+ "colonnes ×2 ×4 ×8 ×16 (cap 0) puis ×8 cap 1 et cap 6.");
		}

		// (espèce, longueur en px internes au palier ×1).
		private static IEnumerable<(string, float)> Especes()
		{
			foreach (string g in MacroLife.EspecesConnues)
				yield return (g, MacroLife.LongueurCm(g) * WorldView.PxPerCmX);
			foreach (string g in ForagerLayer.GuildesConnues)
				yield return (g, 2f * ForagerLayer.RayonPx(g));
		}

		public override void _Draw()
		{
			_lot.Vider();
			float y = Marge;
			foreach (var (esp, l1) in Especes())
			{
				// Hauteur de rangée : la bête la plus grande de la rangée (×16), en iso.
				float haut = Mathf.Clamp(l1 * 16f * 0.5f, 6f, 90f);
				float x = Marge, cy = y + haut * 0.5f;
				foreach (float z in Paliers)
					x = Poser(esp, l1 * z, x, cy, 0) + Ecart;
				x = Poser(esp, l1 * 8f, x + Ecart, cy, 1) + Ecart;
				Poser(esp, l1 * 8f, x, cy, 6);
				y += haut + Ecart;
			}
			if (!PaletteIndexee.Active) return;
			FauneIcones.Televerser();
			_lot.Dessiner(this, FauneIcones.Texture);
		}

		// Pose une bête de `longPx` px au bord gauche `x` ; rend le bord droit.
		private float Poser(string esp, float longPx, float x, float cy, int cap)
		{
			if (longPx < 1f) return x + 2f;   // invisible au jeu à ce palier
			float largeur = Mathf.Max(longPx, 2f);
			var c = new Vector2(x + largeur * 0.5f, cy);
			if (PaletteIndexee.Active)
				FauneIcones.Poser(_lot, esp, c, longPx, new Vector2(longPx, Mathf.Max(longPx * 0.25f, 1f)),
								  1f, (uint)cap << 16, 0.9f);
			else
				DrawRect(new Rect2(c - new Vector2(longPx, longPx * 0.25f) * 0.5f,
								   new Vector2(longPx, Mathf.Max(longPx * 0.25f, 1f))), MacroLife.CouleurEspece(esp));
			return x + largeur;
		}
	}
}
