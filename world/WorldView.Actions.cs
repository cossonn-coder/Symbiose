// SYMBIOSE — WorldView.Actions.cs (partial de WorldView, SS⑥ refactor global)
// Les ACTIONS JOUEUR (tranche 4, volet B + taille au segment, tranche 5) :
// touches 1..8 = geste, clic gauche = exécuter. La vue RÉSOUT la désignation
// (plante par position / plot / tuile) et la TRANSMET ; Python valide,
// applique, répond ACK/NAK + snapshot. Aucune pré-validation côté C#. Inclut
// le picking (collet / branche sous la souris) et la surbrillance de taille.

using Godot;
using System.Collections.Generic;
using System.Threading.Tasks;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// --- Actions joueur (tranche 4, volet B ; +3 gestes vue·rattrapage 01) -
		// Les gestes, dans l'ORDRE de la table COUTS de sim/actions.py
		// (kickoff B·10). Kind = famille de cible : p = plante (par position),
		// q = plot (tile,r,c), t = tuile, m = point de MILIEU sur une tuile
		// (x_cm/y_cm LOCAUX — planter/arroser, protocole 0.3.3), '-' = sans cible.
		// Au-delà de 9 entrées les touches 1..9 ne couvrent plus tout : la
		// sélection cyclique Tab (cf. Controls) parcourt TOUTE la palette — c'est
		// par elle qu'on atteint les 6 gestes compost (03). Kinds compost :
		// q = poser une structure au plot (planification) ; s = agir sur la
		// structure EXISTANTE du plot cliqué (composter/empiler/retourner/épandre).
		private static readonly (string Verb, string Nom, char Kind)[] Gestes =
		{
			("recolter",             "récolter",       'p'),
			("deraciner",            "déraciner",      'p'),
			("ecraser",              "écraser",        'x'),   // plante OU nuisible
			("favoriser_auxiliaire", "favoriser aux.", 't'),
			("becher",               "ameublir",       'a'),   // bêcher / Maj grelinette
			("tailler",              "tailler",        'p'),
			("manger",               "manger",         'p'),
			("planter",              "planter",        'm'),
			("arroser",              "arroser",        'm'),
			("poser_bac",            "poser bac",      'q'),   // compost ⑤ (planification)
			("poser_pile",           "poser pile",     'q'),
			("composter",            "composter",      's'),   // litière tendre → bac
			("empiler_bois",         "empiler bois",   's'),   // bois → pile
			("retourner",            "retourner",      's'),   // accélère la maturation
			("epandre",              "épandre",        's'),   // compost mûr → sol
		};
		private int _gesteIndex = -1;              // aucun geste sélectionné
		// Graines plantables du snapshot (player.seeds, lots non vides), triées
		// par clé pour un ordre de cycle STABLE ; l'espèce courante (S cycle) sert
		// de params.species à `planter`. Le serveur reste juge (catalogue + banque).
		private readonly List<(string Key, int Count)> _seeds = new();
		private int _seedIndex;
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
		// Rayon (cm MONDE) du test « quel sprite macro sous le curseur » pour
		// l'écrasement ciblé (⑥b) : plus large que PickRadiusCm car le point
		// errant peut être à ~20 cm de son ancre (merle/hérisson).
		private const float MacroPickRadiusCm = 50f;
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

		// Sélection cyclique sur TOUTE la palette (touche Tab, cf. Controls) :
		// une seule touche atteint tous les gestes. Premier appel sans geste →
		// bord selon le sens. Modulo positif (les indices peuvent être négatifs).
		private void CyclePalette(int dir)
		{
			int n = Gestes.Length;
			int idx = _gesteIndex < 0 ? (dir > 0 ? 0 : n - 1)
									  : ((_gesteIndex + dir) % n + n) % n;
			SelectGeste(idx);
		}

		// Espèce courante pour `planter` (touche S). Cycle sur les lots non vides
		// du snapshot ; rien à faire si la banque est vide.
		private void CycleSeed()
		{
			if (_seeds.Count == 0)
			{
				GD.Print("[WorldView] aucune graine en banque (récoltez en automne).");
				return;
			}
			_seedIndex = (_seedIndex + 1) % _seeds.Count;
			GD.Print($"[WorldView] graine : {_seeds[_seedIndex].Key} (×{_seeds[_seedIndex].Count}).");
			UpdateActionHud();
		}

		// Met à jour la liste des graines plantables depuis player.seeds (appelé
		// par ApplySnapshot). Tri par clé = ordre de cycle STABLE d'un snapshot à
		// l'autre ; l'index est borné si un lot a disparu (tout planté).
		private void ApplySeeds(GDict seeds)
		{
			_seeds.Clear();
			foreach (var k in seeds.Keys)
				_seeds.Add((k.AsString(), seeds[k].AsInt32()));
			_seeds.Sort((a, b) => string.CompareOrdinal(a.Key, b.Key));
			if (_seedIndex >= _seeds.Count) _seedIndex = 0;
		}

		private void TryAction(Vector2 canvasPos, bool shift)
		{
			if (_world == null || _lastSnap == null) return;   // monde pas prêt
			if (_gesteIndex < 0)
			{
				_lastActionMsg = "aucun geste sélectionné (Tab ou 1..9)";
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
					// Manger CIBLÉ (③, protocole 0.3.4) : si la plante porte des
					// fruits, on consomme CELUI le plus proche du clic (gain ∝ sa
					// maturité, l'organe disparaît) ; sans fruit, target.fruit reste
					// absent → chemin générique (plante entière) côté serveur.
					if (verb == "manger")
					{
						int fruitIdx = node.FindFruitNear(canvasPos);
						if (fruitIdx >= 0) target["fruit"] = fruitIdx;
					}
					break;

				case 'x':   // ÉCRASER, geste unifié (retour F5 Nico) : une plante
					// si elle est sous le curseur, sinon un nuisible au plot. Le
					// serveur route DÉJÀ par la forme de la cible (x_cm ⇒ plante,
					// sinon espèce au plot) — la vue n'a qu'à choisir la
					// désignation. Le verbe reste "ecraser" dans les deux cas.
					node = FindPlant(w, PickRadiusCm);
					if (node != null)
						target = new GDict
						{
							["tile"] = node.GetMeta("tile"),
							["x_cm"] = node.GetMeta("lx"),
							["y_cm"] = node.GetMeta("ly"),
						};
					else if (FindPlot(w, out string xTile, out int xr, out int xc))
					{
						// ESPÈCE du sprite sous le curseur (protocole ⑥, target.espece) :
						// on écrase ce qu'on VOIT (puceron, limace…). Sans sprite à
						// portée → on désigne seulement le plot et le serveur applique
						// son défaut (puceron). On teste l'ancre des points MacroLife
						// dans un rayon large couvrant leur errance.
						target = new GDict { ["tile"] = xTile, ["r"] = xr, ["c"] = xc };
						string espece = _macroLife?.SpeciesNear(w, MacroPickRadiusCm);
						if (espece != null) target["espece"] = espece;
					}
					else
					{
						_lastActionMsg = $"{nom} : aucune plante ni tuile sous le clic";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					prms["urgence"] = _phase == Phase.Saison;
					break;

				case 'a':   // AMEUBLIR, geste unifié (retour F5 Nico) : clic =
					// bêcher CE plot ; Maj+clic = grelinette, qui ameublit TOUT le
					// jardin (geste global du moteur, sans cible). Le verbe envoyé
					// dépend donc du Maj — d'où la réaffectation de `verb`.
					if (shift) { verb = "grelinette"; break; }   // global, pas de cible
					if (!FindPlot(w, out string aTile, out int ar, out int ac))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					verb = "becher";
					target = new GDict { ["tile"] = aTile, ["r"] = ar, ["c"] = ac };
					break;

				case 't':   // tuile entière (favoriser auxiliaire)
					if (!FindPlot(w, out string tTile, out _, out _))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict { ["tile"] = tTile };
					break;

				case 'm':   // point de MILIEU : planter / arroser (protocole 0.3.3)
					// Le serveur attend un POINT continu {tile, x_cm, y_cm} LOCAL
					// (il le résout lui-même en plot via _plot_at) — PAS un (r,c).
					// On trouve la tuile sous le clic, puis on convertit le point
					// MONDE en coordonnées locales (point − origine de la tuile).
					if (!FindPlot(w, out string mTile, out _, out _))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					Vector2 mo = _origins[mTile];
					target = new GDict
					{
						["tile"] = mTile,
						["x_cm"] = w.X - mo.X,
						["y_cm"] = w.Y - mo.Y,
					};
					if (verb == "planter")
					{
						// Aucune graine en banque → message clair côté vue : il n'y
						// a littéralement aucune espèce à proposer (les lots vides
						// sont déjà masqués par le serveur). Récolter en automne
						// remplit player.seeds. (Le serveur reste juge du reste :
						// espèce inconnue / Vigueur → ses messages sont relayés.)
						if (_seeds.Count == 0)
						{
							_lastActionMsg = "planter : aucune graine en banque (récoltez en automne)";
							UpdateActionHud(); FlashActionLabel();
							return;
						}
						prms["species"] = _seeds[_seedIndex].Key;
					}
					if (verb == "arroser")
						prms["urgence"] = _phase == Phase.Saison;
					break;

				case 'q':   // POSER une structure (compost ⑤) : plot {tile, r, c}.
					// Geste de PLANIFICATION dans le modèle préparation/réaction —
					// pas de garde-fou DUR ici (à confirmer au F5) : le serveur
					// applique quelle que soit la phase, on relaie son verdict.
					if (!FindPlot(w, out string qTile, out int qr, out int qc))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict { ["tile"] = qTile, ["r"] = qr, ["c"] = qc };
					break;

				case 's':   // compost ⑤ : composter/empiler/retourner/épandre.
					// DEUX désignations selon le geste (retour F5 Nico) :
					//  · composter / empiler_bois = on clique la LITIÈRE au sol (comme
					//    tailler/cueillir) ; la vue route vers le bac/pile le plus
					//    proche de la MÊME tuile (target.structure) en joignant le plot
					//    cliqué comme SOURCE (target.r/c). Le moteur composte la litière
					//    d'un plot indépendant du plot de la structure (actions/compost).
					//  · retourner / épandre = on clique la STRUCTURE elle-même.
					if (!FindPlot(w, out string sTile, out int sr, out int sc))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					if (verb == "composter" || verb == "empiler_bois")
					{
						string sKind = verb == "composter" ? "bac" : "pile";
						int near = FindNearestStructure(sKind, sTile, sr, sc);
						if (near < 0)
						{
							_lastActionMsg = verb == "composter"
								? "composter : aucun bac dans cette tuile (posez-en un)"
								: "empiler : aucune pile dans cette tuile (posez-en une)";
							UpdateActionHud(); FlashActionLabel();
							return;
						}
						target = new GDict { ["tile"] = sTile, ["structure"] = near,
											 ["r"] = sr, ["c"] = sc };
					}
					else   // retourner / épandre : clic sur la structure du plot
					{
						int sIdx = FindStructureIndex(verb, sTile, sr, sc);
						if (sIdx < 0)
						{
							_lastActionMsg = $"{nom} : aucune structure sur ce plot";
							UpdateActionHud(); FlashActionLabel();
							return;
						}
						target = new GDict { ["tile"] = sTile, ["structure"] = sIdx };
						if (verb != "retourner")   // épandre cible le plot (r,c)
						{
							target["r"] = sr;
							target["c"] = sc;
						}
						// épandre : params.q omis ⇒ le serveur épand TOUT le disponible.
					}
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
				node = FindSegmentGlobal(WorldMouseCanvas(), out seg);
			if (_highlightNode != null && _highlightNode != node
				&& IsInstanceValid(_highlightNode))
				_highlightNode.HighlightSegment = -1;
			_highlightNode = node;
			if (node != null) node.HighlightSegment = seg;
		}

	}
}
