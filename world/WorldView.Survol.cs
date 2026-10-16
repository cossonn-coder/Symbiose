// SYMBIOSE — WorldView.Survol.cs (partial de WorldView, sprint RENDU VISIBLE T3)
// Le PLANCHER FIXE de la frame : la souris est lue UNE fois par frame, et le
// survol (étiquettes, observation, losange, surbrillance de taille, gènes) n'est
// recalculé que quand quelque chose qui peut changer son résultat a bougé.
//
// 📖 Pédagogie — le constat (profil dotnet-trace, monde masqué) : _Process
// appelait WorldMouseCanvas() depuis ~8 sites par frame, chacun suivi d'un
// FindPlant / FindPlot / FindNearestContainer. Or, souris immobile et caméra
// fixe, ces recherches rendent EXACTEMENT le même résultat d'une frame à l'autre :
// c'est du travail sans information. Le remède classique est une CLÉ DE
// VALIDITÉ (comme une clé de cache auto-invalidante) : on photographie les
// entrées du calcul ; si la photo n'a pas changé, le résultat d'avant tient.
//
// Les entrées du survol sont :
//   - la souris en px fenêtre ;
//   - la caméra du SubViewport (sa transform canvas = position + zoom) ;
//   - l'orientation de la vue (la rotation reprojette le monde) ;
//   - les MODES qui choisissent ce qu'on calcule (étiquettes, gènes, geste armé) ;
//   - le MONDE affiché : il ne change qu'en appliquant un snapshot, et toute
//     application passe par WorldView.Etalement.Avancer → `_survolVersion++`
//     (un seul point de passage, donc pas d'oubli possible).
// Les animations VOULUES ne passent pas par la clé : la respiration du losange
// (geste armé) et la fin du « tap » du curseur gardent leur rythme propre.
//
// Les lectures HORS _Process (clic, zoom centré souris) gardent un appel direct
// à WorldMouseCanvas() : elles sont ponctuelles et doivent lire l'instant exact.
//
// 📖 Pourquoi la souris vient des ÉVÉNEMENTS et non de GetMousePosition() : le
// profil après la clé de survol montrait encore 75 % du temps C# de la frame
// dans CE SEUL appel. Sous Godot 4 / X11, Viewport.GetMousePosition() demande la
// position au serveur d'affichage (aller-retour X11, XQueryPointer) à CHAQUE
// appel. Or Godot nous livre déjà chaque déplacement en InputEventMouseMotion :
// on mémorise sa position dans _Input (vu AVANT l'interface, jamais consommé
// ici) et la frame lit cette mémoire — zéro aller-retour. Une seule lecture
// directe reste, au démarrage (avant tout événement) et après un WarpMouse.

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Souris de la frame courante, en canvas du SubViewport et en cm monde.
		private Vector2 _sourisCanvas, _sourisMonde;
		// Vrai quand le survol doit être recalculé cette frame (clé changée).
		private bool _survolSale = true;
		// Compteur bumpé à chaque application (partielle) d'un snapshot.
		private int _survolVersion;

		// Photo des entrées au dernier recalcul (cf. en-tête).
		private Vector2 _clePx;
		private Transform2D _cleCamera;
		private int _cleOrientation = -1, _cleVersion = -1, _cleGeste = -2;
		private LabelMode _cleLabels;
		private bool _cleGenes;

		// Dernière position souris (px fenêtre) livrée par un événement ; NaN =
		// inconnue → une lecture directe la (re)sème (démarrage, WarpMouse).
		private Vector2 _sourisPx = new(float.NaN, float.NaN);

		// Tous les événements souris (mouvement, boutons, molette) portent la
		// position : on la garde. Pas de SetInputAsHandled — on ne fait qu'écouter.
		public override void _Input(InputEvent ev)
		{
			if (ev is InputEventMouse m) _sourisPx = m.Position;
		}

		/// <summary>Oublie la position mémorisée : la prochaine frame relit le
		/// pointeur (après un Input.WarpMouse, qui ne garantit pas d'événement).</summary>
		private void ResemerSouris() => _sourisPx = new(float.NaN, float.NaN);

		/// <summary>Tête de _Process : prend la souris de la frame, la convertit, et
		/// décide si le survol est à recalculer. Coût : une comparaison de
		/// quelques champs (plus une lecture directe tant que la position est
		/// inconnue).</summary>
		private void LireSourisFrame()
		{
			if (float.IsNaN(_sourisPx.X)) _sourisPx = GetViewport().GetMousePosition();
			Vector2 px = _sourisPx;
			Transform2D cam = _worldVp.GetCanvasTransform();
			_survolSale = px != _clePx || cam != _cleCamera
				|| _orientation != _cleOrientation || _survolVersion != _cleVersion
				|| _gesteIndex != _cleGeste || _labelMode != _cleLabels
				|| _genesHoverOn != _cleGenes;
			if (!_survolSale) return;   // _sourisCanvas/_sourisMonde d'avant tiennent
			_clePx = px; _cleCamera = cam; _cleOrientation = _orientation;
			_cleVersion = _survolVersion; _cleGeste = _gesteIndex;
			_cleLabels = _labelMode; _cleGenes = _genesHoverOn;
			_sourisCanvas = SourisVersCanvas(px, cam);
			_sourisMonde = ScreenToWorld(_sourisCanvas);
		}
	}
}
