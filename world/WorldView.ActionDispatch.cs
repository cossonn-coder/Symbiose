// SYMBIOSE — WorldView.ActionDispatch.cs (partial de WorldView)
// Scindé de WorldView.Actions.cs (/refactor) : la RÉSOLUTION de désignation et
// le DISPATCH de l'action joueur. TryAction traduit un clic (canvas + Maj) en
// {verbe, target, params} selon le Kind du geste courant (plante / plot / tuile
// / point milieu / structure / conteneur / gestes 2 temps), puis LaunchAction
// envoie la requête au pont Python. La vue RÉSOUT et TRANSMET ; Python valide.
// L'ÉTAT (champs, table Gestes) vit dans WorldView.Actions.cs (même classe).

using Godot;
using System.Threading.Tasks;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
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
					// Récolter vise le FRUIT mûr dessiné (GESTES LISIBLES ④, WorldView.Recolte.cs).
					if (verb == "recolter")
					{
						if (!CibleRecolte(canvasPos, w, out node, out target)) return;
						break;
					}
					// Manger un CHAMPIGNON (⑧) : un carpophore tout près du clic passe
					// avant la plante (WorldView.Champignon.cs).
					if (verb == "manger" && CibleCarpophore(w, CarpoPrioriteCm, out target)) break;
					if (verb == "tailler")
						node = FindSegmentGlobal(canvasPos, out segIdx);
					if (verb == "manger") node = FindFruitPortSous(canvasPos);
					if (node == null)
						node = FindPlant(w, PickRadiusCm) ?? FindPortSous(canvasPos);
					if (node == null)
					{
						if (verb == "manger" && CibleCarpophore(w, MacroPickRadiusCm, out target)) break;
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
						string espece = _macroLife?.SpeciesNear(w, MacroPickRadiusCm, _volants);   // un volant n'est pas une cible (④)
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
					// `planter` sur un POT y sème la graine choisie (④, WorldView.DeuxTemps.cs).
					if (verb == "planter" && CiblePotPourPlanter(w, prms, out target))
					{
						verb = "planter_conteneur";
						break;
					}
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

				case 'L':   // SECTEUR de PÉRIPHÉRIE (D73 ⑦) : les gestes de paysage
					// (abattre/recéper/étêter/endiguer/dériver/entailler) portent sur
					// un BORD entier — on clique le DÉCOR, hors du jardin. Le décor
					// n'est pas un nœud pickable (ZIndex négatif) et n'a pas besoin de
					// l'être : la résolution est géométrique (FindSecteur), comme
					// FindPlot, et les deux domaines sont disjoints (dedans/dehors).
					if (!TryCibleSecteur(nom, w, out target)) return;
					break;

				case 'q':   // POSER une structure (compost ⑤) : plot {tile, r, c}.
					// Geste de PLANIFICATION dans le modèle préparation/réaction —
					// pas de garde-fou DUR ici (à confirmer au F5) : le serveur
					// applique quelle que soit la phase, on relaie son verdict.
					// `creuser` hors du jardin = une MARE de bordure (périphérie ⑤) :
					// même verbe, même coût, même fiche — seule la cible change (un
					// secteur au lieu d'un plot), et le serveur route sur la forme du
					// target. On tente donc le secteur AVANT d'exiger une tuile.
					if (verb == "creuser")
					{
						target = CibleSecteur(w);
						if (target != null) break;
					}
					if (!FindPlot(w, out string qTile, out int qr, out int qc))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict { ["tile"] = qTile, ["r"] = qr, ["c"] = qc };
					break;

				case 's':   // compost ⑤ : composter/empiler/retourner.
					// DEUX désignations selon le geste (retour F5 Nico) :
					//  · composter / empiler_bois = on clique la LITIÈRE au sol (comme
					//    tailler/cueillir) ; la vue route vers le bac/pile le plus
					//    proche de la MÊME tuile (target.structure) en joignant le plot
					//    cliqué comme SOURCE (target.r/c). Le moteur composte la litière
					//    d'un plot indépendant du plot de la structure (actions/compost).
					//  · retourner = on clique la STRUCTURE elle-même.
					// (épandre est passé en kind 'E' à 2 temps, cf. ci-dessous.)
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
					else   // retourner : clic sur la structure du plot
					{
						int sIdx = FindStructureIndex(verb, sTile, sr, sc);
						if (sIdx < 0)
						{
							_lastActionMsg = $"{nom} : aucune structure sur ce plot";
							UpdateActionHud(); FlashActionLabel();
							return;
						}
						target = new GDict { ["tile"] = sTile, ["structure"] = sIdx };
					}
					break;

				case 'E':   // ÉPANDRE à 2 temps : le tas, puis le plot (WorldView.DeuxTemps.cs).
					if (!ResoudreEpandre(w, out target)) return;
					break;

				case 'P':   // POSER un conteneur (pot/bac ⑥b) au point MONDE du clic.
					// ⚠ Repère : le serveur lit target.x_cm/y_cm comme position MONDE
					// ABSOLUE (≠ Kind 'm' qui envoie un point LOCAL tuile). On exige
					// quand même que le clic tombe sur une TUILE (pas chemin/maison) —
					// un conteneur posé hors sol n'a pas d'assise de couplage.
					if (!FindPlot(w, out _, out _, out _))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict { ["x_cm"] = w.X, ["y_cm"] = w.Y };
					prms["substrat"] = Substrats[_substratIndex];
					if (verb == "poser_pot")
						prms["volume"] = PotVolumeL;
					else   // poser_bac_culture : grille N×M + fond ouvert
					{
						prms["volume"] = BacVolumeL;
						prms["rows"] = BacRows;
						prms["cols"] = BacCols;
						prms["fond_ouvert"] = BacFondOuvert;
					}
					break;

				case 'C':   // CONTENEUR existant désigné par INDEX (déplacer/planter).
					// Déplacer = 2 temps : le pot, puis sa place (WorldView.DeuxTemps.cs).
					if (verb == "deplacer_pot")
					{
						if (!ResoudreDeplacerPot(w, out target)) return;
						break;
					}
					// planter_conteneur : 1 clic = désigner le conteneur + graine du
					// cycle S (symétrie avec `planter` sur tuile).
					if (_seeds.Count == 0)
					{
						_lastActionMsg = "planter (pot) : aucune graine en banque (récoltez en automne)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					int nearP = FindNearestContainer(w, ContainerPickRadiusCm);
					if (nearP < 0)
					{
						_lastActionMsg = "planter (pot) : aucun conteneur ici (posez-en un)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict { ["container"] = nearP };
					prms["species"] = _seeds[_seedIndex].Key;
					break;

				case 'U':   // PAILLER un plot {tile, r, c} avec la nature courante (⑧).
					// Geste sur le MILIEU au plot cliqué ; params.nature = matériau du
					// cycle N. Le serveur consomme le stock de cette nature et refuse en
					// amont s'il est vide (on relaie son message).
					if (!FindPlot(w, out string uTile, out int ur, out int uc))
					{
						_lastActionMsg = $"{nom} : aucune tuile ici (chemin/maison)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict { ["tile"] = uTile, ["r"] = ur, ["c"] = uc };
					prms["nature"] = Natures[_natureIndex];
					break;

				case 'D':   // BROYER un SQUELETTE désigné par POSITION (⑧). Comme un geste
					// plante (x_cm/y_cm), mais la cible est une plante MORTE ligneuse : le
					// serveur (_skeleton_at) ne retient que les morts porteurs de bois. On
					// désigne le nœud le plus proche (les squelettes sont dans _plantNodes).
					node = FindPlant(w, PickRadiusCm);
					if (node == null)
					{
						_lastActionMsg = $"{nom} : aucun bois à broyer ici (visez un squelette)";
						UpdateActionHud(); FlashActionLabel();
						return;
					}
					target = new GDict
					{
						["tile"] = node.GetMeta("tile"),
						["x_cm"] = node.GetMeta("lx"),
						["y_cm"] = node.GetMeta("ly"),
					};
					break;

				case 'b':   // BOUTURER à 2 temps : la mère, puis le plot (WorldView.DeuxTemps.cs).
					if (!ResoudreBouture(w, prms, out target, out node)) return;
					break;

				case 'g':   // GREFFER à 2 temps : le greffon, puis le porte-greffe (DeuxTemps).
					if (!ResoudreGreffe(w, prms, out target, out node)) return;
					break;

				// '-' : grelinette, pas de cible.
			}

			// Signal à la vie macro (PERF VUE ②) : les bêtes proches du geste sursautent.
			_macroLife?.Signal(w);
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
	}
}
