// SYMBIOSE — DecorLayer.Devant.cs (FLUIDITÉ PC LEVIERS ⑤ — la lisière CÔTÉ CAMÉRA devant le jardin)
// Partial de DecorLayer : les pièces HAUTES (arbres et sous-bois, face de falaise,
// berges à roseaux) des deux bords tournés vers la caméra passent dans une couche
// AU-DESSUS du jardin. Le reste du décor (assise, tapis, lit de rivière, bords du
// fond) reste derrière le sol, en ZIndex −5 comme avant.
//
// 📖 Pédagogie — POURQUOI deux couches et pas une : en iso, ce qui est plus BAS à
// l'écran est plus PRÈS de l'œil. Un arbre planté au-delà du bord sud-est est donc
// DEVANT le jardin : son houppier, qui monte à l'écran, doit recouvrir les tuiles
// et les plantes qu'il cache. Avec tout le décor en ZIndex −5, le sol (0) et les
// plantes (Objects 10 + strate) passaient par-dessus → les tuiles « coupaient » les
// arbres (bug F5 Nico 2026-10-26). Les bords du fond, eux, sont derrière : leurs
// arbres montent VERS le haut de l'écran, loin du jardin, ils restent dessous.
//
// 📖 Pourquoi un z FIXE au-dessus de toutes les plantes suffit : les arbres de
// lisière sont posés au-delà de la frontière (profondeur > AmplitudeCm, cf.
// DrawForet). Tout point du jardin qui partage une colonne d'écran avec un arbre
// d'un bord côté caméra est plus loin de l'œil que lui (il est vers l'intérieur) :
// l'arbre le masque toujours. Pas besoin de trier arbre par arbre avec les plantes.
//
// « Côté caméra » dépend de la rotation D35 : le test projette la NORMALE sortante
// du bord (WorldToScreenOffset, la même projection). Une rotation appelle Build(),
// qui jette les mailles → la répartition devant/derrière est refaite au palier
// suivant, sans état à tenir ici. Coût : UN DrawMesh de plus (une maille « devant »
// figée par palier, construite avec la maille de fond, mêmes tranches).

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Au-dessus des plantes (Objects 10 + strate 10..14 = 20..24 en relatif),
		// des bâches (12) et des butineurs (11). Absolu : ne dépend pas du −5 parent.
		private const int ZDevant = 30;

		private Node2D _devant;          // la couche « devant » (enfant, dessinée via son signal Draw)
		private Maille _devantMaille;    // maille dont la partie haute est affichée (null = rien)

		// Lot où partent les pièces hautes d'un bord côté caméra pendant une tranche.
		// null (ancien redessin DessinerToutLot) = tout reste dans _lot, comme avant.
		private LotTriangles _lotHaut;
		private readonly LotTriangles _lotDevant = new();       // construction immédiate
		private readonly LotTriangles _lotFondDevant = new();   // tâche de fond

		/// <summary>Crée la couche « devant » (appelé depuis _Ready).</summary>
		private void CreerDevant()
		{
			_devant = new Node2D { Name = "DecorDevant", ZIndex = ZDevant, ZAsRelative = false };
			// Un simple Node2D : il peint dans le signal Draw (pas de classe dédiée).
			_devant.Draw += () =>
			{
				if (_devantMaille?.MeshDevant != null) _devant.DrawMesh(_devantMaille.MeshDevant, KitTexture);
			};
			AddChild(_devant);
		}

		/// <summary>Affiche la partie haute de `m` (null = décor éteint au gros plan).
		/// Ne redessine la couche que si la maille change.</summary>
		private void PublierDevant(Maille m)
		{
			if (_devant == null || m == _devantMaille) return;
			_devantMaille = m;
			_devant.QueueRedraw();
		}

		// Un bord est côté caméra si sa normale sortante descend à l'écran.
		private static bool CoteCamera(int cote)
		{
			(float dx, float dy) = cote switch
			{
				0 => (0f, -1f),   // nord
				1 => (1f, 0f),    // est
				2 => (0f, 1f),    // sud
				_ => (-1f, 0f),   // ouest
			};
			return WorldView.WorldToScreenOffset(dx, dy).Y > 0f;
		}

		/// <summary>Peint `peindre` (pièces hautes du secteur) dans le lot « devant »
		/// si le bord est côté caméra, sinon dans le lot courant. L'ordre de peinture
		/// à l'intérieur de chaque lot est inchangé.</summary>
		private void EnHaut(Secteur s, System.Action peindre)
		{
			if (_lotHaut == null || !CoteCamera(s.Cote)) { peindre(); return; }
			LotTriangles avant = _lot;
			_lot = _lotHaut;
			peindre();
			_lot = avant;
		}
	}
}
