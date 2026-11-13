// SYMBIOSE — WorldView.CurseurAnim.cs (partial de WorldView, ICÔNES & CURSEUR ④)
// L'ANIMATION DU CURSEUR-GESTE : le curseur qui porte l'icône du geste armé
// (forme `FormeGeste`, posée par WorldView.Curseur.cs) joue une courte suite
// d'images, UNE fois, puis redevient immobile :
//   - au CLIC : une image « tap » (l'outil appuie d'un pixel vers sa cible) —
//     réponse immédiate, même quand l'action attend le pont, et seul signe du
//     premier clic d'un geste à deux temps (épandre, déplacer un pot, bouturer,
//     greffer), qui n'envoie rien ;
//   - à la RÉPONSE du pont : le mouvement du geste s'il est appliqué (verser,
//     couper, frapper…), la secousse du « non » s'il est refusé.
// Une nouvelle animation interrompt la précédente et repart du début.
//
// 📖 Pédagogie Godot/C# : pas de `_Process` ni de Timer en plus. On garde une
// ÉCHÉANCE en millisecondes (`Time.GetTicksMsec`, horloge du moteur) et
// `UpdateCurseur`, déjà appelé à chaque image, regarde si elle est passée —
// le même mécanisme que la fin du « tap » de la main (`_tapFinMs`).
// Chaque changement d'image re-pose une image sur la forme système : l'OS en
// refait son curseur (32×32 px, quelques microsecondes), 2 à 5 fois par action,
// jamais au repos.

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private AnimationGeste.ImageCurseur[] _animImages;   // null = curseur immobile
		private int _animIndex;
		private ulong _animEcheanceMs;
		private Texture2D _curseurAnimTex;   // image montrée pendant l'animation (témoin de capture)

		/// <summary>Lance une animation du curseur-geste (sans effet si aucune icône
		/// de geste n'est en main : la main gantée garde son propre tap).</summary>
		private void JouerAnimationCurseur(AnimationGeste.Sorte sorte)
		{
			if (!_curseurIcone) return;
			var images = AnimationGeste.Images(_curseurVerbe, sorte, CurseurEchelle);
			if (images == null) return;
			_animImages = images;
			_animIndex = 0;
			PoserImageCurseur(images[0]);
		}

		/// <summary>Chaque frame (UpdateCurseur) : image suivante à l'échéance ; après
		/// la dernière, l'icône immobile revient.</summary>
		private void AvancerAnimationCurseur()
		{
			if (_animImages == null || Time.GetTicksMsec() < _animEcheanceMs) return;
			if (++_animIndex < _animImages.Length)
			{
				PoserImageCurseur(_animImages[_animIndex]);
				return;
			}
			ArreterAnimationCurseur();
			var repos = AnimationGeste.Images(_curseurVerbe, AnimationGeste.Sorte.Repos, CurseurEchelle);
			if (repos != null) Input.SetCustomMouseCursor(repos[0].Img, FormeGeste, _curseurIconeHotspot);
		}

		/// <summary>Oublie l'animation en cours, sans toucher au curseur (le geste a
		/// changé : SuivreGesteCurseur pose déjà la nouvelle icône).</summary>
		private void ArreterAnimationCurseur()
		{
			_animImages = null;
			_curseurAnimTex = null;
		}

		// Même point chaud pour toutes les images : c'est le dessin qui bouge.
		private void PoserImageCurseur(AnimationGeste.ImageCurseur image)
		{
			Input.SetCustomMouseCursor(image.Img, FormeGeste, _curseurIconeHotspot);
			_curseurAnimTex = image.Tex;
			_animEcheanceMs = Time.GetTicksMsec() + AnimationGeste.DureeImageMs;
		}
	}
}
