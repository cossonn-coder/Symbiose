// SYMBIOSE — WorldView.Actions.cs (partial de WorldView, SS⑥ refactor global)
// Les ACTIONS JOUEUR (tranche 4, volet B + taille au segment, tranche 5) :
// touches 1..8 = geste, clic gauche = exécuter. La vue RÉSOUT la désignation
// (plante par position / plot / tuile) et la TRANSMET ; Python valide,
// applique, répond ACK/NAK + snapshot. Aucune pré-validation côté C#. Inclut
// le picking (collet / branche sous la souris) et la surbrillance de taille.

using Godot;
using System.Threading.Tasks;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// --- Actions joueur (tranche 4, volet B) ----------------------------
		// Les 8 gestes, dans l'ORDRE de la table COUTS de sim/actions.py
		// (kickoff B·10). Kind = famille de cible : p = plante (par position),
		// q = plot (tile,r,c), t = tuile, '-' = sans cible.
		private static readonly (string Verb, string Nom, char Kind)[] Gestes =
		{
			("recolter",             "récolter",       'p'),
			("deraciner",            "déraciner",      'p'),
			("ecraser",              "écraser",        'q'),
			("favoriser_auxiliaire", "favoriser aux.", 't'),
			("becher",               "bêcher",         'q'),
			("grelinette",           "grelinette",     '-'),
			("tailler",              "tailler",        'p'),
			("manger",               "manger",         'p'),
		};
		private int _gesteIndex = -1;              // aucun geste sélectionné
		private Task<GDict> _pendingAction;        // action en vol (ou null)
		// File d'UNE intention (retour F5 Nico : en Turbo le pipe ne désemplit
		// jamais → tout clic était ignoré). Si une requête est en vol, le clic
		// est MÉMORISÉ (un seul) et part en PRIORITÉ dès que le pipe se libère
		// — avant la semaine suivante. Un 2e clic pendant l'attente l'écrase.
		private (string Verb, GDict Target, GDict Prms, PlantRenderer Node)? _queuedIntent;
		// Plante visée par l'action en vol → flash de feedback si appliquée
		// (retour F5 Nico : « tailler ne montre rien » — la coupe de quelques
		// cm sur un jeune sujet est invisible sans surlignage).
		private PlantRenderer _actionTargetNode;
		// Rayon de tolérance du clic sur une plante, en cm MONDE (kickoff B·11).
		private const float PickRadiusCm = 30f;
		// Rayon du survol (étiquette) : un peu plus généreux que le clic.
		private const float HoverRadiusCm = 40f;
		// Tolérance du hit-test de segment (tranche 5), en px ÉCRAN — divisée
		// par le zoom pour travailler en canvas : le ressenti au pixel près est
		// le même à tous les paliers (comme PanSpeedPx).
		private const float SegmentPickPx = 8f;
		// Plante dont un segment est surligné (mode tailler) — pour éteindre
		// l'ancienne quand la souris change de plante.
		private PlantRenderer _highlightNode;
		private double _vigueur = -1.0, _vigueurMax;   // bloc player du snapshot
		private string _lastActionMsg = "";

		// -------------------------------------------------------------------
		// ACTIONS JOUEUR (tranche 4, volet B) — touches 1..8 = geste, clic
		// gauche = exécuter. La vue RÉSOUT la désignation (plante/plot/tuile)
		// et TRANSMET ; Python valide, applique, répond ACK/NAK + snapshot.
		// -------------------------------------------------------------------

		private void SelectGeste(int idx)
		{
			_gesteIndex = idx;
			_lastActionMsg = "";
			GD.Print($"[WorldView] geste : {Gestes[idx].Nom} [{idx + 1}].");
			UpdateActionHud();
		}

		private void TryAction(Vector2 canvasPos, bool shift)
		{
			if (_world == null || _lastSnap == null) return;   // monde pas prêt
			if (_gesteIndex < 0)
			{
				_lastActionMsg = "aucun geste sélectionné (touches 1..8)";
				UpdateActionHud();
				FlashActionLabel();
				return;
			}

			var (verb, nom, kind) = Gestes[_gesteIndex];
			Vector2 w = ScreenToWorld(canvasPos);
			GDict target = null;
			var prms = new GDict();
			PlantRenderer node = null;

			switch (kind)
			{
				case 'p':   // plante la plus proche dans le rayon de tolérance
					// Taille (tranche 5, correctif t5·B) : la plante se résout
					// par LA BRANCHE sous la souris (toutes plantes, couronnes
					// débordantes comprises) ; sans branche sous le curseur,
					// repli sur le collet à 30 cm = comportement t4 inchangé.
					int segIdx = -1;
					if (verb == "tailler")
						node = FindSegmentGlobal(canvasPos, out segIdx);
					if (node == null)
						node = FindPlant(w, PickRadiusCm);
					if (node == null)
					{
						_lastActionMsg = $"{nom} : aucune plante à portée du clic";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict
					{
						["tile"] = node.GetMeta("tile"),
						["x_cm"] = node.GetMeta("lx"),
						["y_cm"] = node.GetMeta("ly"),
					};
					// params.cible reste TOUJOURS envoyé : repli serveur si
					// target.segment est absent (clic au pied).
					if (verb == "tailler")
					{
						prms["cible"] = shift ? "branche" : "apex";
						if (segIdx >= 0) target["segment"] = segIdx;
					}
					break;

				case 'q':   // plot (tile, r, c) sous le clic
				case 't':   // tuile sous le clic
					if (!FindPlot(w, out string tileId, out int r, out int c))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict { ["tile"] = tileId };
					if (kind == 'q') { target["r"] = r; target["c"] = c; }
					// La couture préparation/réaction (§3.1, déjà codée moteur) :
					// en phase Saison le geste est une RÉACTION → urgence (×1.5).
					// En Pause on réfléchit : temps figé = tarif planification.
					if (verb == "ecraser")
						prms["urgence"] = _phase == Phase.Saison;
					break;

				// '-' : grelinette, pas de cible.
			}

			// Pipe occupé (step, action ou fields en vol) → l'intention est
			// MÉMORISÉE (une seule, la dernière gagne) et partira dès que le
			// tube se libère — indispensable en Turbo où le pipe ne dort jamais.
			if (!PipeFree)
			{
				_queuedIntent = (verb, target, prms, node);
				GD.Print($"[WorldView] pipe occupé — intention {verb} mémorisée.");
				return;
			}
			LaunchAction(verb, target, prms, node);
		}

		private void LaunchAction(string verb, GDict target, GDict prms, PlantRenderer node)
		{
			GD.Print($"[WorldView] → action {verb} "
					 + (target != null ? Json.Stringify(target) : "(sans cible)")
					 + (prms != null && prms.Count > 0 ? $" params {Json.Stringify(prms)}" : "") + ".");
			_actionTargetNode = node;
			var prmsArg = prms != null && prms.Count > 0 ? prms : null;
			_pendingAction = Task.Run(() => _bridge.Action(verb, target, prmsArg));
		}

		/// <summary>Plante affichée la plus proche du point MONDE (cm), dans
		/// `radiusCm`, ou null. ~170 nœuds : recherche linéaire, pas de quadtree
		/// à inventer (leçon perf : mesurer avant d'optimiser).</summary>
		private PlantRenderer FindPlant(Vector2 w, float radiusCm)
		{
			PlantRenderer best = null;
			float bestD = radiusCm * radiusCm;
			foreach (var node in _plantNodes.Values)
			{
				float dx = (float)node.GetMeta("wx").AsDouble() - w.X;
				float dy = (float)node.GetMeta("wy").AsDouble() - w.Y;
				float d = dx * dx + dy * dy;
				if (d < bestD) { bestD = d; best = node; }
			}
			return best;
		}

		/// <summary>Tuile + plot contenant le point MONDE (cm). False si le
		/// point tombe entre les tuiles (chemins) ou sur la maison.</summary>
		private bool FindPlot(Vector2 w, out string tileId, out int r, out int c)
		{
			foreach (var tv in _world["tiles"].AsGodotArray())
			{
				var t = tv.AsGodotDictionary();
				float ox = (float)t["origin_x_cm"].AsDouble();
				float oy = (float)t["origin_y_cm"].AsDouble();
				int rows = t["rows"].AsInt32(), cols = t["cols"].AsInt32();
				if (w.X >= ox && w.X < ox + cols * PlotCm
					&& w.Y >= oy && w.Y < oy + rows * PlotCm)
				{
					tileId = t["id"].AsString();
					c = (int)((w.X - ox) / PlotCm);
					r = (int)((w.Y - oy) / PlotCm);
					return true;
				}
			}
			tileId = null; r = c = 0;
			return false;
		}

		// Tolérance du hit-test de segment en px CANVAS : 8 px ÉCRAN quel que
		// soit le palier de zoom (le canvas est multiplié par Zoom à l'écran).
		private float SegmentPickTolPx() =>
			SegmentPickPx / (_camera != null ? _camera.Zoom.X : 1f);

		/// <summary>
		/// LA branche sous la souris, toutes plantes confondues (correctif
		/// t5·B) : le segment le plus proche du curseur sous la tolérance,
		/// cherché chez TOUTES les plantes dont la portée (PickExtentCm,
		/// étalement + hauteur) atteint le point souris — plus de filtre par
		/// collet à 30 cm, qui excluait la couronne des arbres. Préfiltre
		/// monde au carré (pas de racine), puis hit-test exact par segment ;
		/// ~170 plantes dont une poignée passent le préfiltre : trivial.
		/// Survol ET clic passent ici : ce qui est surligné = ce qui part.
		/// </summary>
		private PlantRenderer FindSegmentGlobal(Vector2 canvasMouse, out int segIndex)
		{
			segIndex = -1;
			PlantRenderer best = null;
			float bestD = SegmentPickTolPx();
			Vector2 w = ScreenToWorld(canvasMouse);
			foreach (var node in _plantNodes.Values)
			{
				float dx = (float)node.GetMeta("wx").AsDouble() - w.X;
				float dy = (float)node.GetMeta("wy").AsDouble() - w.Y;
				float ext = node.PickExtentCm;
				if (dx * dx + dy * dy > ext * ext) continue;
				int seg = node.FindSegmentNear(canvasMouse, bestD, out float d);
				if (seg >= 0 && d < bestD) { bestD = d; best = node; segIndex = seg; }
			}
			return best;
		}

		// Surbrillance de la branche sous la souris en mode tailler (tranche
		// 5) : MÊME résolution que le clic (FindSegmentGlobal) — ce qui est
		// surligné est EXACTEMENT ce qui partira en target.segment. Appelée
		// chaque frame ; les setters HighlightSegment font early-out, le
		// redraw ne part qu'au changement.
		private void UpdateTailleHighlight()
		{
			PlantRenderer node = null;
			int seg = -1;
			if (_gesteIndex >= 0 && Gestes[_gesteIndex].Verb == "tailler"
				&& _plantNodes.Count > 0)
				node = FindSegmentGlobal(GetGlobalMousePosition(), out seg);
			if (_highlightNode != null && _highlightNode != node
				&& IsInstanceValid(_highlightNode))
				_highlightNode.HighlightSegment = -1;
			_highlightNode = node;
			if (node != null) node.HighlightSegment = seg;
		}

		// Étiquette au survol (demande Nico 2e F5 t4) : seule la plante la plus
		// proche de la souris montre la sienne. Premier consommateur du picking
		// ScreenToWorld — le clic réutilise exactement la même résolution.
		private void UpdateHoverTag()
		{
			if (_labelMode != LabelMode.Survol || _plantNodes.Count == 0) return;
			var best = FindPlant(ScreenToWorld(GetGlobalMousePosition()), HoverRadiusCm);
			foreach (var node in _plantNodes.Values)
			{
				var tag = node.GetNodeOrNull<Label>("Tag");
				if (tag != null) tag.Visible = node == best;
			}
		}
	}
}
