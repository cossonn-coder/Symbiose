// SYMBIOSE — WorldView.Etiquettes.cs (partial de WorldView, SS① pixel-art)
// Les ÉTIQUETTES « espèce · stade » sous les plantes, rendues HORS du SubViewport
// pixel-art → toujours NETTES (décision Nico, 1er F5 SS① : le texte dans la grille
// basse-réso était illisible). Le principe : le texte vit dans un CanvasLayer plein
// écran (viewport principal 1920×1080), et on REPROJETTE chaque frame la position
// monde de chaque plante vers les pixels ÉCRAN. C'est l'exact symétrique du picking
// (WorldMouseCanvas) : là on faisait écran → monde, ici monde → écran.
//
// 📖 Pédagogie — pourquoi un POOL de Labels : créer/détruire 170 Labels chaque
// frame jetterait du GC à la poubelle. On garde une LISTE réutilisée : on (re)place
// les N premiers sur les plantes à étiqueter, on cache le reste. Le pool ne grandit
// que jusqu'au pic (mode « Toutes » ≈ 170). Coût : ~170 reprojections/frame, trivial.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// CanvasLayer plein écran (viewport principal) + pool de Labels réutilisés.
		private CanvasLayer _plantLabels;
		private readonly List<Label> _labelPool = new();

		// Créé au démarrage (StartSimulation) : couche nette au-dessus du monde.
		private void BuildPlantLabels()
		{
			_plantLabels = new CanvasLayer { Name = "PlantLabels" };
			AddChild(_plantLabels);
			BuildInfoBulle();   // info-bulle à deux niveaux (PLANTE ASSEMBLÉE ⑦)
		}

		// Appelée chaque frame (_Process) : selon le mode (Aucune / Survol / Toutes),
		// place les étiquettes nettes sur les plantes concernées.
		private void UpdatePlantLabels()
		{
			// Clé de survol inchangée (T3) : les Labels posés tiennent tels quels.
			if (_plantLabels == null || !_survolSale) return;
			int n = 0;
			if (_labelMode != LabelMode.Aucune && _plantNodes.Count > 0)
			{
				if (_labelMode == LabelMode.Survol)
				{
					// Seule la plante la plus proche du curseur (défaut, demande Nico).
					var best = FindPlant(_sourisMonde, HoverRadiusCm);
					if (best != null) n = PlaceLabel(n, best);
				}
				else   // Toutes
				{
					foreach (var node in _plantNodes.Values)
						n = PlaceLabel(n, node);
				}
			}
			// Cacher les Labels du pool non utilisés ce frame.
			for (int i = n; i < _labelPool.Count; i++)
				_labelPool[i].Visible = false;
		}

		// Place le i-ème Label du pool sous la plante `node` (texte + position écran),
		// renvoie l'index suivant. Le texte « espèce · stade » est stocké en Meta
		// "tag" sur le renderer (posé/maj à l'ApplySnapshot).
		private int PlaceLabel(int i, PlantRenderer node)
		{
			if (!IsInstanceValid(node)) return i;
			var lbl = LabelFromPool(i);
			lbl.Text = node.GetMeta(LectureSnap.Meta("tag"), "").AsString();
			// node.Position = WorldToScreen(collet) en canvas SubViewport → écran.
			// Offset ÉCRAN constant (px fenêtre) : sous le collet, centré à la louche.
			lbl.Position = WorldToWindow(node.Position) + new Vector2(-24f, 8f);
			lbl.Visible = true;
			return i + 1;
		}

		// Récupère (ou crée à la demande) le i-ème Label du pool, stylé une fois.
		private Label LabelFromPool(int i)
		{
			while (_labelPool.Count <= i)
			{
				var l = new Label();
				l.AddThemeFontSizeOverride("font_size", 14);
				l.AddThemeColorOverride("font_color", new Color(1f, 1f, 1f, 0.9f));
				l.AddThemeColorOverride("font_outline_color", Colors.Black);
				l.AddThemeConstantOverride("outline_size", 5);
				_plantLabels.AddChild(l);
				_labelPool.Add(l);
			}
			return _labelPool[i];
		}

		// Monde (canvas SubViewport) → pixels ÉCRAN fenêtre. Symétrique de
		// WorldMouseCanvas : on applique la transform de la caméra du SubViewport
		// (zoom + pan) puis l'upscale du conteneur (= stretch_shrink). Container à
		// l'origine, échelle uniforme → multiplication scalaire.
		private Vector2 WorldToWindow(Vector2 canvasPoint)
		{
			var container = _worldVp.GetParent<SubViewportContainer>();
			float up = container.Size.X / _worldVp.Size.X;   // = stretch_shrink
			return container.GlobalPosition
				+ (_worldVp.GetCanvasTransform() * canvasPoint) * up;
		}
	}
}
