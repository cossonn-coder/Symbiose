// SYMBIOSE — world/UiScroll.cs
// Patron réutilisable « conteneur défilable si débordement » (sprint fenêtrage
// UI, T1). Règle transversale du sprint : toute fenêtre qui déborde DÉFILE au
// lieu de pousser ses voisins hors écran. On l'isole ici pour le réemployer
// tel quel au launcher (T1), au panneau Paramètres (T2) et au conteneur à
// onglets (T3) — une seule responsabilité, testable d'un regard.
//
// 📖 Pédagogie Godot/C# :
//  - ScrollContainer : un cadre à taille BORNÉE qui laisse défiler son unique
//    enfant quand celui-ci est plus grand que le cadre. La barre n'apparaît QUE
//    si ça déborde (exactement « défile si débordement »).
//  - CustomMinimumSize fixe la hauteur du cadre ; sans SizeFlags Expand vertical,
//    le cadre s'en tient à cette hauteur dans un VBox → la fenêtre reste bornée.
//  - On coupe le défilement HORIZONTAL : nos listes débordent en hauteur, jamais
//    en largeur — un scroll horizontal parasite gênerait la lecture.

using Godot;

namespace Symbiose
{
	public static class UiScroll
	{
		/// <summary>
		/// Enveloppe <paramref name="contenu"/> dans un ScrollContainer de hauteur
		/// bornée à <paramref name="hauteurMax"/> px : au-delà, le contenu défile
		/// verticalement (barre auto), en deçà rien ne change. Le contenu épouse la
		/// largeur du cadre. Renvoie le ScrollContainer à ajouter à l'arbre.
		/// </summary>
		public static ScrollContainer Envelopper(Control contenu, float hauteurMax)
		{
			var scroll = new ScrollContainer
			{
				CustomMinimumSize = new Vector2(0, hauteurMax),
				HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled,
			};
			contenu.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
			scroll.AddChild(contenu);
			return scroll;
		}
	}
}
