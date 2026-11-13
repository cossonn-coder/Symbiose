// SYMBIOSE — WorldView.CurseurTemoin.cs (partial de WorldView, ICÔNES & CURSEUR ③)
// Le TÉMOIN DE CURSEUR, actif EN CAPTURE SEULEMENT (option `-s X,Y` du banc,
// `--capture-souris`). Le curseur système est dessiné par l'OS, hors de l'image
// rendue par Godot : le Movie Maker du banc VM ne le voit pas. Pour vérifier le
// curseur sans F5, ce témoin peint la MÊME texture à la position de la souris,
// point chaud compris, dans un calque au-dessus de tout.
//
// Il imite la règle du vrai curseur : sur un Control qui capte la souris
// (panneau, barre, tiroir) → la main ; ailleurs → l'icône du geste armé, ou la
// main s'il n'y en a pas.
//
// 📖 Pédagogie Godot : en jeu normal on n'utilise JAMAIS ce sprite — un curseur
// dessiné par le jeu suit la souris avec une image de retard ; celui de l'OS non.

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private Sprite2D _curseurTemoin;   // null hors capture

		/// <summary>Crée le témoin (appelé par la mise en place de la capture).</summary>
		private void PoserTemoinCurseur()
		{
			var calque = new CanvasLayer { Layer = 120 };
			AddChild(calque);
			// Centered = false : le coin haut-gauche de la texture est à la position,
			// comme le curseur de l'OS ; on retranche le point chaud.
			_curseurTemoin = new Sprite2D { Centered = false, Name = "CurseurTemoin" };
			calque.AddChild(_curseurTemoin);
		}

		/// <summary>Chaque frame en capture : texture et position du témoin.</summary>
		private void SuivreTemoinCurseur()
		{
			if (_curseurTemoin == null) return;
			bool surInterface = GetViewport().GuiGetHoveredControl() != null;
			bool icone = _curseurIcone && !surInterface;
			Texture2D tex = icone ? IconeGeste.Texture(_curseurVerbe, CurseurEchelle) : _curseurRepos;
			Vector2 hotspot = icone ? _curseurIconeHotspot : CurseurHotspot;
			if (_curseurTemoin.Texture != tex) _curseurTemoin.Texture = tex;
			_curseurTemoin.Position = GetViewport().GetMousePosition() - hotspot;
		}
	}
}
