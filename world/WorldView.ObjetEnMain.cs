// SYMBIOSE — WorldView.ObjetEnMain.cs (partial de WorldView, GESTES LISIBLES ④)
// L'OBJET EN MAIN (conception §6, D136 d) : entre les deux clics d'un geste à deux
// temps, on VOIT ce qu'on tient et où on peut le poser.
//  - bouture (`bouturer`), greffon (`greffer`), pelletée de compost (`epandre`) : une
//    petite image portée à côté du curseur (grilles `visuals/icones/ObjetsEnMain.cs`) ;
//  - le POT (`deplacer_pot`) : c'est le pot lui-même, avec sa terre et ses plantes, qui
//    suit la souris au sol ;
//  - les cibles valides : pour les gestes « même tuile », les plots de la tuile source
//    s'éclairent (ZoneCible) ; hors cible, l'objet se GRISE (silhouette d'une teinte,
//    pot à demi transparent) ;
//  - Échap ou clic droit reposent l'objet (WorldView.Controls.cs).
//
// UNE SEULE SOURCE D'ÉTAT : les champs `_grabbed*` de WorldView.Actions.cs, écrits par
// WorldView.DeuxTemps.cs. Ce fichier ne fait que les LIRE à chaque image et montrer.
//
// 📖 Pédagogie Godot : l'objet porté est un Sprite2D dans un calque d'interface
// (CanvasLayer), placé à la position souris. Contrairement au curseur de l'OS, un dessin
// du jeu suit la souris avec une image de retard — invisible pour un objet tenu à côté
// de la pointe, et ça évite de recomposer l'image du curseur à chaque animation.
// Note `composter` : un seul clic (la litière cliquée part au bac de la tuile),
// pas de temps où l'on « tient » la brassée → pas d'objet en main (écart au kickoff).

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private const int ObjetEchelle = 2;                          // comme le curseur
		private static readonly Vector2 ObjetDecalage = new(12f, 14f);   // en bas à droite de la pointe
		private const float PotHorsCibleAlpha = 0.45f;

		private Sprite2D _objetSprite;
		private ZoneCible _zoneCible;
		private string _zoneTuile;
		private readonly Dictionary<(string, bool), ImageTexture> _objetTextures = new();
		// Pot porté : son nœud et le décalage écran déjà appliqué (à défaire au lâcher).
		private ContainerStructure _potPorte;
		private List<PlantRenderer> _potPortePlantes;
		private Vector2 _potDecalage;

		// Le geste dont un objet est en main, ou null.
		private string VerbeEnMain() =>
			_grabbedBac >= 0 ? "epandre"
			: _grabbedContainer >= 0 ? "deplacer_pot"
			: _grabbedMother != null && IsInstanceValid(_grabbedMother) ? "bouturer"
			: _grabbedScion != null && IsInstanceValid(_grabbedScion) ? "greffer"
			: null;

		// Tuile imposée à la cible (gestes « même tuile »), ou null (le pot va partout).
		private string TuileEnMain(string verbe) => verbe switch
		{
			"epandre" => _grabbedBacTile,
			"bouturer" => _grabbedMother.GetMeta("tile").AsString(),
			"greffer" => _grabbedScionTile,
			_ => null,
		};

		/// <summary>Le point visé est-il une cible valide pour l'objet en main ?</summary>
		private bool CibleValideEnMain(string verbe)
		{
			if (!FindPlot(_sourisMonde, out string tuile, out _, out _)) return false;
			return verbe switch
			{
				"deplacer_pot" => true,
				"greffer" => FindPlant(_sourisMonde, PickRadiusCm) is { } p
							 && p.GetMeta("tile").AsString() == _grabbedScionTile,
				_ => tuile == TuileEnMain(verbe),
			};
		}

		/// <summary>Chaque image (UpdateCurseur) : objet porté, zone des cibles, pot qui suit.</summary>
		private void SuivreObjetEnMain()
		{
			string verbe = VerbeEnMain();
			if (verbe == null && _objetSprite == null) return;   // rien en main, rien monté
			bool valide = verbe != null && CibleValideEnMain(verbe);
			MontrerZoneCible(verbe != null ? TuileEnMain(verbe) : null);
			SuivrePotPorte(verbe == "deplacer_pot", valide);
			if (_objetSprite == null)
			{
				var calque = new CanvasLayer { Layer = 110, Name = "ObjetEnMain" };
				AddChild(calque);
				_objetSprite = new Sprite2D { Centered = false };
				calque.AddChild(_objetSprite);
			}
			bool surInterface = GetViewport().GuiGetHoveredControl() != null;
			Texture2D tex = verbe != null && !surInterface ? TextureObjet(verbe, !valide) : null;
			_objetSprite.Visible = tex != null;
			if (tex == null) return;
			if (_objetSprite.Texture != tex) _objetSprite.Texture = tex;
			Vector2 souris = float.IsNaN(_sourisPx.X) ? GetViewport().GetMousePosition() : _sourisPx;
			_objetSprite.Position = souris + ObjetDecalage;
		}

		// Texture de l'objet (en cache) ; `grise` = silhouette d'une teinte (hors cible).
		private ImageTexture TextureObjet(string verbe, bool grise)
		{
			if (!ObjetsEnMain.Grilles.TryGetValue(verbe, out string[] grille)) return null;
			if (_objetTextures.TryGetValue((verbe, grise), out ImageTexture tex)) return tex;
			tex = grise ? IconeGeste.CuireSilhouette(grille, ObjetEchelle) : IconeGeste.Cuire(grille, ObjetEchelle);
			_objetTextures[(verbe, grise)] = tex;
			return tex;
		}

		// Éclaire les plots de `tuile` (null = éteint). Ne refait le dessin qu'au changement.
		private void MontrerZoneCible(string tuile)
		{
			if (tuile == _zoneTuile) return;
			_zoneTuile = tuile;
			if (_zoneCible == null)
			{
				// Enfant direct du SubViewport (comme PlotHover) : survit à RebuildWorld.
				_zoneCible = new ZoneCible { Name = "ZoneCible", ZIndex = 2 };
				AddWorld(_zoneCible);
			}
			if (tuile == null || !GeometrieTuile(tuile, out Vector2 o, out int rows, out int cols))
			{
				_zoneCible.Cacher();
				return;
			}
			_zoneCible.Montrer(tuile, o, rows, cols, ReliefRiseAtPlot);
		}

		private bool GeometrieTuile(string id, out Vector2 origine, out int rows, out int cols)
		{
			foreach (var tv in _world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				if (t["id"].AsString() != id) continue;
				origine = new Vector2((float)t["origin_x_cm"].AsDouble(), (float)t["origin_y_cm"].AsDouble());
				rows = t["rows"].AsInt32();
				cols = t["cols"].AsInt32();
				return true;
			}
			origine = Vector2.Zero; rows = cols = 0;
			return false;
		}

		// Le pot saisi suit la souris au sol (et ses plantes avec lui) ; à demi transparent
		// hors tuile. Lâché ou posé : il revient à sa place, le snapshot suivant le redessine
		// là où le moteur l'a mis.
		private void SuivrePotPorte(bool porte, bool valide)
		{
			ContainerStructure node = null;
			List<PlantRenderer> plantes = null;
			Vector2 ici = Vector2.Zero;
			if (porte)
				foreach (var c in _containers)
					if (c.Index == _grabbedContainer && IsInstanceValid(c.Node))
					{ node = c.Node; plantes = c.Plants; ici = WorldToScreen(c.XCm, c.YCm); }
			if (node != _potPorte)
			{
				DeplacerPot(-_potDecalage, 1f);   // l'ancien revient à sa place, opaque
				_potPorte = node;
				_potPortePlantes = plantes;
				_potDecalage = Vector2.Zero;
			}
			if (node == null) return;
			Vector2 voulu = WorldToScreen(_sourisMonde.X, _sourisMonde.Y) - ici;
			DeplacerPot(voulu - _potDecalage, valide ? 1f : PotHorsCibleAlpha);
			_potDecalage = voulu;
		}

		private void DeplacerPot(Vector2 delta, float alpha)
		{
			if (_potPorte == null || !IsInstanceValid(_potPorte)) return;
			_potPorte.Position += delta;
			_potPorte.Modulate = new Color(1f, 1f, 1f, alpha);
			foreach (var p in _potPortePlantes)
				if (IsInstanceValid(p)) { p.Position += delta; p.Modulate = new Color(1f, 1f, 1f, alpha); }
		}

		/// <summary>Échap / clic droit : repose l'objet en main. False s'il n'y en avait pas
		/// (l'appelant passe alors la touche à la suite de sa chaîne).</summary>
		private bool LacherObjetEnMain()
		{
			if (VerbeEnMain() == null) return false;
			_grabbedBac = -1;
			_grabbedContainer = -1;
			_grabbedMother = null;
			_grabbedScion = null;
			_lastActionMsg = "objet reposé";
			UpdateActionHud();
			SuivreObjetEnMain();   // le pot revient, la zone s'éteint tout de suite
			return true;
		}

		/// <summary>_ExitTree (via LibererCurseur) : textures hors cache d'IconeGeste.</summary>
		private void LibererObjetEnMain()
		{
			foreach (var t in _objetTextures.Values) t.Dispose();
			_objetTextures.Clear();
		}
	}
}
