// SYMBIOSE — WorldView.Snapshot.cs (partial de WorldView, SS⑥ refactor global)
// Appliquer un snapshot du moteur = un DIFF avec ce qui est affiché (tranche
// 3). Clé stable d'une plante = tuile + espèce + position (une plante ne bouge
// jamais ; le moteur n'expose pas d'id, la position en tient lieu) :
//  · clé connue   → SetStructure (swap sec : la plante a grandi)
//  · clé nouvelle → créer + fondu d'apparition (naissance)
//  · clé disparue → fondu de disparition puis QueueFree (mort)
// Sol et maison ne bougent pas. ~150 nœuds à 1 fois/60 s : trivial.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Saison courante du snapshot (t6·A) — lue par PlantRenderer pour la
		// COULEUR des feuilles (printemps clair, automne chaud…). Les hints
		// foliage_density/organ arrivent déjà saisonnés du serveur ; seule la
		// teinte se décide côté vue. Mise à jour dans ApplySnapshot AVANT les
		// SetStructure : les redraws qui suivent voient la bonne saison.
		public static string CurrentSeason { get; private set; } = "ete";

		// Plantes affichées, indexées par clé stable (tile|species|x|y) — base
		// du diff naissance/mort entre deux snapshots.
		private readonly Dictionary<string, PlantRenderer> _plantNodes = new();
		private int _plantSeq;                     // noms de nœuds uniques

		// Pompe de redraw du LOD plantes (sprint PERF, tronçon ①) : appelée par
		// StepZoom au franchissement d'un palier. PlantRenderer._Draw ne tourne que
		// sur QueueRedraw ; sans cette pompe, une plante ne rebasculerait pas entre
		// silhouette et segments en (dé)zoomant. Ponctuel (~500 QueueRedraw par cran).
		// Jardin vivant T2 : la pompe INVALIDE (plante « sale ») au lieu de redessiner ;
		// la BakeQueue recuit quelques plantes par frame, celles près de l'écran d'abord.
		private void RedrawAllPlants()
		{
			foreach (var node in _plantNodes.Values)
				if (IsInstanceValid(node)) node.Invalidate();   // T2 : file de cuisson, pas de pic
		}
		// Phéromone d'alarme apienne (⑦ §J, snapshot 0.4.1) : par tuile, les plots
		// en alarme → intensité. Liste CREUSE côté serveur (foyers > 0) ; ici un
		// dict par plot pour un lookup O(1) au curseur (piqûre temps réel). Vide au
		// repos. Lu par TickPiqure (WorldView.Piqure.cs).
		private readonly Dictionary<string, Dictionary<(int R, int C), float>>
			_alarme = new();
		// Horloge du dernier snapshot appliqué (pour le Label + fin de saison).
		private string _season;
		private int _year, _weekInSeason;

		private static string PlantKey(GDict p) =>
			$"{p["tile"].AsString()}|{p["species"].AsString()}"
			+ $"|{p["x_cm"].AsDouble():F1}|{p["y_cm"].AsDouble():F1}";

		// Étiquette debug « espèce · stade » (demande Nico F5 t4), toggle F3.
		// Le TEXTE est stocké en Meta "tag" sur le renderer ; le RENDU se fait
		// hors SubViewport, net, par WorldView.Etiquettes.cs (SS① : le texte dans
		// la grille pixel-art était illisible). On ne crée plus de Label enfant.
		private static string TagText(GDict p) =>
			$"{p["species"].AsString()} · {p["stage_name"].AsString()}";

		// Reconstruit l'index d'alarme par plot depuis le bloc CREUX du snapshot
		// (format `[r, c, intensité]` par tuile). Reconstruction pleine : l'alarme
		// décroît vite côté moteur, pas de diff à tenir.
		private void ApplyAlarme(GDict alarme)
		{
			_alarme.Clear();
			foreach (var tileKv in alarme)
			{
				var foyers = tileKv.Value.AsGodotArray();
				if (foyers.Count == 0) continue;
				var d = new Dictionary<(int R, int C), float>();
				foreach (var fv in foyers)
				{
					var f = fv.AsGodotArray();
					d[(f[0].AsInt32(), f[1].AsInt32())] = (float)f[2].AsDouble();
				}
				_alarme[tileKv.Key.AsString()] = d;
			}
		}

		// Range une plante VIVANTE dans l'index nom-FR → positions MONDE (cm), pour
		// les fleurs de saut des butineurs (ForagerLayer). Les morts (squelettes) ne
		// fleurissent pas → écartés. Clé = `name` (Phacélie…), pas `species` (anglais).
		// Index construit dans `byName` (celui de l'étalement en cours), échangé
		// avec _plantsByName à la fin de la famille plantes (WorldView.Etalement.cs).
		private void IndexPlantByName(GDict p, Dictionary<string, List<Vector2>> byName)
		{
			if (p.ContainsKey("dead") && p["dead"].AsBool()) return;
			Vector2 o = _origins[p["tile"].AsString()];
			var pos = new Vector2(o.X + (float)p["x_cm"].AsDouble(),
								  o.Y + (float)p["y_cm"].AsDouble());
			string name = p["name"].AsString();
			if (!byName.TryGetValue(name, out var list))
				byName[name] = list = new List<Vector2>();
			list.Add(pos);
		}

		// Application SYNCHRONE (d'un bloc) : chargement initial, rotation, saut
		// debug, résultat d'action. Mêmes 7 familles que l'étalement, budget
		// infini. Un snapshot synchrone, plus frais et complet, REMPLACE un
		// étalement en cours (WorldView.Etalement.cs).
		private void ApplySnapshot(GDict snap, bool fade = true)
		{
			_etale = null;
			var e = new Etalement(snap, fade);
			while (!Avancer(e, long.MaxValue)) { }
		}

		// Famille 0 — horloge + sol (relief) : AVANT les plantes, qui s'y recalent.
		private void AppliquerSol(Etalement e)
		{
			GDict snap = e.Snap;
			_lastSnap = snap;   // gardé pour RebuildWorld (rotation)

			// Horloge (52 sem/an, saisons de 13 — sim/engine.py saison_de).
			_year = snap["year"].AsInt32();
			int weekInYear = snap["week_in_year"].AsInt32();
			_weekInSeason = ((weekInYear - 1) % 13) + 1;
			string season = snap["season"].AsString();
			CurrentSeason = season;   // AVANT les SetStructure (couleur feuilles t6·A)

			// Épaisseur de sol (D57 ②, snapshot 0.5.16, lecture seule) : relief
			// extrudé par plot ∝ `epaisseur_sol` (le sol monte/descend). AVANT la
			// boucle des plantes : leur recalage vertical (ReliefRisePx) lit
			// l'épaisseur courante → elles restent plantées dans la terre, pas
			// suspendues. Lecture TOLÉRANTE : bloc absent (pré-0.5.16) → relief plat.
			// Altitude (micro-relief topographique FIXE, hydrologie ①, 0.5.17) :
			// socle géométrique du terrain, SOMMÉ à l'épaisseur pour le relief
			// (surface = altitude + epaisseur, comme la surface hydraulique du
			// moteur). Posé AVANT ApplyEpaisseur, qui déclenche seul UpdateRelief →
			// la remontée voit déjà l'altitude courante. Lecture TOLÉRANTE (bloc
			// absent, pré-0.5.17 → altitude nulle → terrain plat, aucun crash).
			// Ceinture périphérique (PÉRIPHÉRIE ⑦, 0.5.41, lecture seule) : les 4
			// secteurs qui entourent le jardin → `DecorLayer`, qui CESSE de générer
			// son décor et consomme la vérité moteur (fin de la couture D58·T4, D92
			// refermée par le haut). Appliquée TÔT : c'est un fond, il n'attend
			// personne. Lecture TOLÉRANTE — bloc absent (monde sans périphérie,
			// binaire pré-0.5.41) → le décor garde son profil local par seed.
			ApplyCeinture(snap.ContainsKey("ceinture")
				? snap["ceinture"].AsGodotArray() : null);

			if (snap.ContainsKey("altitude"))
				ApplyAltitude(snap["altitude"].AsGodotDictionary());
			if (snap.ContainsKey("epaisseur"))
				ApplyEpaisseur(snap["epaisseur"].AsGodotDictionary());
		}

		// Famille 1 — UNE plante (diff naissance/croissance). Appelée par tranches
		// (AvancerPlantes) ; la suppression des disparues attend FinirPlantes.
		// Semaine paresseuse (D106 T4, D2) : les INDEX (payload du dossier, fleurs
		// des butineurs, clés vues) sont toujours tenus à jour — le clic et les
		// butineurs ne voient jamais un index faux ; seule l'APPLICATION coûteuse
		// (parse des segments + setters + recuisson) d'une plante connue HORS marge
		// est différée (WorldView.Attente.cs). Les naissances, rares, restent
		// appliquées tout de suite.
		private void AppliquerPlante(Etalement e, GDict p)
		{
				int nSegs = p["segments"].AsGodotArray().Count;
				if (nSegs == 0)
				{
					e.Empty++;   // germination sans bois : rien à dessiner encore
					return;
				}
				e.NSegs += nSegs;
				string key = PlantKey(p);
				e.Seen.Add(key);
				e.Payloads[key] = p;   // dossier de plante debug (T3), lu au clic
				IndexPlantByName(p, e.ByName);   // fleurs cibles des butineurs (vivantes only)

				if (_plantNodes.TryGetValue(key, out var node))
				{
					e.Grown++;
					if (!node.Visible) { MettreEnAttente(node, p); e.Attente++; return; }
					MajPlante(node, p);   // la plante a poussé
					return;
				}
				Vector2 screenPos = PositionPlante(p, out float wx, out float wy);
				var renderer = new PlantRenderer
				{
					Position = screenPos,
					// Empilement multi-strates (luxuriance ⑥) : biais de ZIndex par
					// strate → le couvre-sol passe sous la potagère/grimpante. À strate
					// égale, le y-sort du parent "Objects" départage (intra-strate).
					ZIndex = PlantZIndex(p.ContainsKey("strate") ? p["strate"].AsString() : null),
					Name = $"{p["tile"].AsString()}_{p["species"].AsString()}_{_plantSeq++}",
				};
				// Métadonnées de picking (volet B) : position MONDE pour la
				// distance au clic/survol, et la désignation EXACTE du snapshot
				// (tile + x/y locaux) renvoyée telle quelle au serveur — la
				// position est l'identité, on n'invente pas d'id (kickoff §8).
				renderer.SetMeta("wx", wx);
				renderer.SetMeta("wy", wy);
				renderer.SetMeta("tile", p["tile"]);
				renderer.SetMeta("lx", p["x_cm"]);
				renderer.SetMeta("ly", p["y_cm"]);
				// Espèce = NOM DE CLASSE (cls.__name__ du snapshot) : envoyé au pont
				// à l'observation par survol (0.5.12). Python résout la clé catalogue.
				renderer.SetMeta("species", p["species"]);
				// Patrimoine génétique (DIVERSITÉ FONDATRICE ③) : le dict de gènes
				// exposé par le snapshot, stocké tel quel en Meta → l'affichage debug
				// de survol (WorldView.Genes.cs) le relit sans re-requêter. Tolérant à
				// un snapshot pré-③ (clé absente → dict vide → survol muet).
				if (p.ContainsKey("genes"))
					renderer.SetMeta("genes", p["genes"]);
				if (e.Fade) renderer.Modulate = new Color(1f, 1f, 1f, 0f);
				_objects.AddChild(renderer);
				MajPlante(renderer, p);   // squelette déjà mort au chargement (save) compris
				if (e.Fade)
					renderer.CreateTween()
						.TweenProperty(renderer, "modulate:a", 1f, FadeInSec);
				_plantNodes[key] = renderer;
				e.Born++;
		}

		// Position écran de la plante, RECALÉE sur le relief (D57 ②) : le collet
		// suit la surface du sol → remonté de l'épaisseur au plot. Appliquée à la
		// naissance ET à la croissance (le sol monte/descend au fil des saisons →
		// la plante suit). Sort aussi la position MONDE (cm) du collet.
		private Vector2 PositionPlante(GDict p, out float wx, out float wy)
		{
			string tile = p["tile"].AsString();
			float lx = (float)p["x_cm"].AsDouble();
			float ly = (float)p["y_cm"].AsDouble();
			Vector2 o = _origins[tile];
			wx = o.X + lx;
			wy = o.Y + ly;
			return WorldToScreen(wx, wy) - new Vector2(0f, ReliefRisePx(tile, lx, ly));
		}

		/// <summary>Applique la donnée `p` du snapshot au nœud (structure, symptômes,
		/// position…) — le coût de la famille 1. Retire la plante de l'attente.</summary>
		private void MajPlante(PlantRenderer node, GDict p)
		{
			SortirAttente(node);
			var structure = StructureLoader.FromSnapshot(p);
			Vector2 screenPos = PositionPlante(p, out float wx, out float wy);
			// Squelette (0.3.6) : `dead` → mode bois nu. Le mort GARDE sa clé
			// (même tile|species|x|y) → il n'est pas fondu sortant ; il bascule
			// squelette sur place jusqu'à ce que le moteur le retire (clé alors
			// absente → fondu). stade_mort = "seche"/"couchee".
			string stadeMort = p.ContainsKey("dead") && p["dead"].AsBool()
				? p["stade_mort"].AsString() : null;
			// Sémiologie foliaire (D33, snapshot 0.5.1) : liste de symptômes
			// {cause, intensité} déjà triée par le moteur (chlorose/sécheresse/
			// asphyxie/ravageurs/sénescence/maladie/gel/grêle). Tolérant à un
			// snapshot pré-D33 (clé absente → null → plante saine). La vue teinte
			// et texture, sans recalculer pH/pression (cf. PlantRenderer).
			var symptoms = p.ContainsKey("leaf_symptoms")
				? p["leaf_symptoms"].AsGodotArray() : null;
			// Vitalité continue (santé & résilience ④, snapshot 0.5.28) : fond
			// global d'usure ∈ [0,1] (1.0 = sain neuf), complète les symptômes
			// localisés. Tolérant à un snapshot pré-0.5.28 (clé absente → 1.0 →
			// plante rendue pleine). `etat` est aussi émis (sain/affaibli/malade/
			// mort) mais la vue consomme le CONTINU (dégradé, pas de palier).
			float vitalite = p.ContainsKey("vitalite")
				? (float)p["vitalite"].AsDouble() : 1f;
			// Accroche de grimpe (grimpantes ⑥, 0.5.18) : type d'appui accroché
			// (tuteur/mur/hote…) ou null. Tolérant à un snapshot pré-0.5.18 (clé
			// absente → plante libre → pas de vrille). Pilote la vrille (indice ⑥).
			string supportKind = p.ContainsKey("support")
				? p["support"].AsGodotDictionary()["type"].AsString() : null;
			// Luxuriance (⑥, 0.5.19) : strate du stade COURANT (ordre de dessin par
			// strate) + silhouette d'espèce (forme au LOD couronne). Tolérant à un
			// snapshot pré-0.5.19 (clés absentes → strate neutre "moyenne", silhouette
			// par défaut). La strate évolue au fil des stades (sol→basse→…) → on la
			// relit à chaque snapshot pour recaler le ZIndex, comme la position.
			string strate = p.ContainsKey("strate") ? p["strate"].AsString() : null;
			string silhouette = p.ContainsKey("silhouette")
				? p["silhouette"].AsString() : null;
			// LOD émetteurs d'ombre (D67, snapshot 0.5.21) : `emitteur` dérivé du
			// pouvoir ombrageant côté MOTEUR (miroir de fields/light.py). Tolérant à
			// un snapshot pré-0.5.21 (clé absente → true = émettrice, aucune teinte).
			// Pilote la seule teinte de l'overlay debug F9, jamais le rendu normal.
			bool emitteur = !p.ContainsKey("emitteur") || p["emitteur"].AsBool();
			// Abri local au vent (jardin vivant T3, 0.5.44) : facteur du champ
			// d'abri ; clé absente (champ pas encore calculé / pré-0.5.44) → 1.0.
			float abri = p.ContainsKey("abri") ? (float)p["abri"].AsDouble() : 1f;

			node.SetStructure(structure);   // la plante a poussé
			node.SetSkeleton(stadeMort);     // ou vient de mourir / s'est couchée
			node.SetSymptoms(symptoms);      // teinte + texture des symptômes (D33)
			node.SetVitality(vitalite);      // fond global d'usure (santé ④, 0.5.28)
			node.SetSupport(supportKind);    // vrille d'accroche (grimpantes ⑥)
			node.SetSilhouette(silhouette);  // forme au LOD couronne (luxuriance ⑥)
			node.SetEmitter(emitteur);       // teinte overlay LOD F9 (D67)
			node.SetWindAnchor(wx, wy, abri);  // onde de vent (T3)
			node.ZIndex = PlantZIndex(strate);  // empilement par strate (luxuriance ⑥)
			node.SetMeta("tag", TagText(p));   // le stade évolue (étiquette nette)
			node.Position = screenPos;         // suit le relief du sol (D57 ②)
		}

		// Fin de la famille 1 — toutes les plantes du snapshot sont passées.
		private void FinirPlantes(Etalement e)
		{
			GDict snap = e.Snap;
			// Échange des index reconstruits (dossier au clic, fleurs des butineurs).
			_plantPayloads.Clear();
			foreach (var kv in e.Payloads) _plantPayloads[kv.Key] = kv.Value;
			_plantsByName.Clear();
			foreach (var kv in e.ByName) _plantsByName[kv.Key] = kv.Value;

			// Plantes affichées absentes du snapshot = RETIRÉES par le moteur
			// (squelette à bois épuisé, ②B ; ou herbacée morte au tick) → fondu
			// sortant. La mort SEULE ne retire plus une plante (elle devient
			// squelette, traité ci-dessus) : ici c'est la fin de vie du bois.
			var dead = new List<string>();
			foreach (var kv in _plantNodes)
				if (!e.Seen.Contains(kv.Key)) dead.Add(kv.Key);
			foreach (string key in dead)
			{
				var node = _plantNodes[key];
				_plantNodes.Remove(key);   // hors index : le fondu finit seul
				SortirAttente(node);
				// Hors marge (T4) : retirée tout de suite, pas de fondu que personne ne voit.
				if (e.Fade && node.Visible)
				{
					var tw = node.CreateTween();
					tw.TweenProperty(node, "modulate:a", 0f, FadeOutSec);
					tw.TweenCallback(Callable.From(node.QueueFree));
				}
				else node.QueueFree();
			}

			_nSegments = e.NSegs;
			_nPousses = e.Empty;

			// Banc d'observation perf (sprint « run éternel » ④) : bloc `perf` du
			// snapshot (serialize.py), mesures côté MOTEUR. Lecture TOLÉRANTE : un
			// snapshot pré-perf n'a pas le bloc → l'overlay F4 garde ses tirets. La
			// vue OBSERVE, elle ne décide rien (Option B). `ms_tick` est null au
			// snapshot post-init (rien encore simulé) → on retombe sur -1.
			if (snap.ContainsKey("perf"))
			{
				var perf = snap["perf"].AsGodotDictionary();
				var mt = perf["ms_tick"];
				_srvMsTick = mt.VariantType == Variant.Type.Nil ? -1 : mt.AsDouble();
				_srvNPlants = perf["n_plants"].AsInt32();
				var rss = perf["rss_mo"];
				_srvRssMo = rss.VariantType == Variant.Type.Nil ? -1 : rss.AsDouble();
			}
			GD.Print($"[WorldView] {CurrentSeason} an {_year}, semaine {_weekInSeason}/13 : "
					 + $"{_plantNodes.Count} plantes (+{e.Born} −{dead.Count}, "
					 + $"{e.Grown} maj dont {e.Attente} en attente hors marge, {e.Empty} sans "
					 + $"segments) · famille plantes {e.PlantesUs / 1000.0:F1} ms.");
		}

		// Famille 2 — vie macro, butineurs, carpophores (index des fleurs à jour).
		private void AppliquerVieMacro(Etalement e)
		{
			GDict snap = e.Snap;
			bool fade = e.Fade;
			// Vie macro (t6·B) : même diff doux que les plantes, délégué au
			// nœud MacroLife. Lecture TOLÉRANTE : un snapshot pré-0.2.3 n'a
			// pas le bloc — la vue affiche simplement un jardin sans bestioles.
			// (Le nuage MacroLife lui-même est appliqué par tranches AVANT cette
			// fonction, cf. AvancerVieMacro dans WorldView.Etalement.cs.)

			// Butineurs (arc pollinisation, 0.3.9, lecture seule) : agents
			// fleur-en-fleur, dessinés par ForagerLayer (≠ nuage MacroLife). L'index
			// nom→positions vient d'être reconstruit ci-dessus (fleurs de saut).
			// Lecture TOLÉRANTE : un snapshot pré-0.3.9 sans le bloc → aucun butineur.
			if (snap.ContainsKey("foragers"))
				_foragerLayer?.SetForagers(snap["foragers"].AsGodotDictionary(),
										   _origins, _plantsByName, fade);

			// Carpophores (mycélium ④/⑥, 0.5.8, lecture seule) : champignons
			// échantillonnés du champ `mycelium` (perception pure). Lecture
			// TOLÉRANTE : un snapshot pré-0.5.8 sans le bloc → aucun champignon.
			if (snap.ContainsKey("carpophores"))
				_carpophoreLayer?.SetCarpophores(
					snap["carpophores"].AsGodotDictionary(), _origins, fade);
		}

		// Famille 3 — couches au sol (tapis, halos, eau, litière, mulch).
		private void AppliquerCouchesSol(GDict snap)
		{
			// Décompo·compost (③, lecture seule, protocole 0.3.7/0.3.5) : litière
			// au sol (layer batché) + structures bac/pile (nœuds YSort). Lecture
			// TOLÉRANTE : un snapshot ancien sans ces blocs → rien dessiné.
			// Tapis de couverture au sol (luxuriance ⑥, 0.5.19, lecture seule) : le
			// champ `couverture_sol` scatté par les empreintes. Lecture TOLÉRANTE : un
			// snapshot pré-0.5.19 sans le bloc → pas de tapis dessiné, jamais de crash.
			if (snap.ContainsKey("couverture"))
				ApplyCouverture(snap["couverture"].AsGodotDictionary());

			// Halo de sol pelé de l'allélopathie (⑥, 0.5.29, lecture seule) : le champ
			// `allelopathie` (allélochimiques racinaires) exposé en foyers > seuil. Lecture
			// TOLÉRANTE : un snapshot pré-0.5.29 sans le bloc → pas de halo, jamais de crash.
			if (snap.ContainsKey("allelopathie"))
				ApplyAllelopathie(snap["allelopathie"].AsGodotDictionary());

			// Eau de surface + marécage (hydrologie ⑧, 0.5.18/0.5.27, lecture seule) :
			// flaques (`eau_surface`) et voile de tourbe (`marais`) posés au sol,
			// recalés sur le relief (le PuddleLayer relit ReliefRiseAtPlot, à jour car
			// l'altitude/épaisseur ont été appliquées plus haut). Lecture TOLÉRANTE :
			// un bloc absent → liste vide, jamais de crash. Un seul appel pour les deux.
			if (_puddleLayer != null
				&& (snap.ContainsKey("eau_surface") || snap.ContainsKey("marais")))
				_puddleLayer.SetWater(
					snap.ContainsKey("eau_surface")
						? snap["eau_surface"].AsGodotDictionary() : null,
					snap.ContainsKey("marais")
						? snap["marais"].AsGodotDictionary() : null,
					_origins);

			if (snap.ContainsKey("litiere"))
				ApplyLitiere(snap["litiere"].AsGodotDictionary());
			// Tapis de mulch au sol (équilibre invasion ⑧, 0.5.20, lecture seule) : le
			// champ `paillage` posé par le geste `pailler`. Lecture TOLÉRANTE : un
			// snapshot pré-0.5.20 sans le bloc → pas de mulch dessiné, jamais de crash.
			if (snap.ContainsKey("paillage"))
				ApplyPaillage(snap["paillage"].AsGodotDictionary());
		}

		// Famille 4 — structures posées (bac/pile, supports de grimpe, conteneurs).
		private void AppliquerStructures(GDict snap)
		{
			if (snap.ContainsKey("structures"))
				ApplyStructures(snap["structures"].AsGodotDictionary());

			// Supports de grimpe posables (grimpantes ⑥, 0.5.18, lecture seule) :
			// placeholders tuteur/treillis/pergola. Lecture TOLÉRANTE : un snapshot
			// pré-0.5.18 sans le bloc → aucun support dessiné, jamais de crash.
			if (snap.ContainsKey("supports"))
				ApplySupports(snap["supports"].AsGodotDictionary());

			// Conteneurs de culture (pots/bacs ④, snapshot 0.5.7, lecture seule) :
			// placeholders ContainerStructure + plantes du mini-sol (PlantRenderer).
			// Lecture TOLÉRANTE : un snapshot pré-0.5.7 sans le bloc → aucun
			// conteneur dessiné, jamais de crash (cf. WorldView.Conteneurs.cs).
			if (snap.ContainsKey("containers"))
				ApplyContainers(snap["containers"].AsGodotArray());
		}

		// Famille 5 — alarme, météo, neige, ciel, couvertures posées.
		private void AppliquerMeteo(GDict snap)
		{
			// Alarme apienne (⑦ §J, 0.4.1, lecture seule) : foyers de phéromone par
			// plot, consommés par la piqûre temps réel. Lecture TOLÉRANTE : un
			// snapshot pré-0.4.1 n'a pas le bloc → aucun foyer, aucune piqûre.
			if (snap.ContainsKey("alarme"))
				ApplyAlarme(snap["alarme"].AsGodotDictionary());

			// Météo (⑨, snapshot 0.5.0, lecture seule) : ambiance globale (bloc
			// `weather` → ciel/précip écran) + manteau neigeux par tuile (bloc
			// `temperature.snow`). Lecture TOLÉRANTE : un snapshot pré-0.5.0 sans
			// ces blocs → jardin sans météo dessinée, aucun crash.
			if (snap.ContainsKey("weather"))
				ApplyWeather(snap["weather"].AsGodotDictionary());
			if (snap.ContainsKey("temperature"))
			{
				var temperature = snap["temperature"].AsGodotDictionary();
				ApplySnow(temperature);        // manteau neigeux par tuile (⑨)
				ApplySoilTemp(temperature);    // heatmap T sol spatialisée F7 (⑩)
			}

			// Ciel de la semaine (effondrement météo ④, snapshot 0.5.43, lecture seule) :
			// l'encart diégétique « état du ciel » (convergence du composé, signes,
			// nommage gaté maîtrise). Lecture TOLÉRANTE : un snapshot pré-0.5.43 sans
			// le bloc → encart neutre, aucun crash.
			if (snap.ContainsKey("ciel"))
				ApplyCiel(snap["ciel"].AsGodotDictionary());
			// Couvertures posées (③, snapshot 0.5.43, lecture seule) : placeholders
			// voile/cloche (couvert_pose) + ombrière (ombre_pose). Un seul appel pour
			// les deux. Lecture TOLÉRANTE : blocs absents → aucun placeholder dessiné.
			if (snap.ContainsKey("couvert_pose") || snap.ContainsKey("ombre_pose"))
				ApplyCovers(
					snap.ContainsKey("couvert_pose")
						? snap["couvert_pose"].AsGodotDictionary() : null,
					snap.ContainsKey("ombre_pose")
						? snap["ombre_pose"].AsGodotDictionary() : null);
		}

		// Famille 6 — ménage : heatmap périmée, HUD joueur, automate, fin de
		// saison, horloge, culling des plantes nées hors champ.
		private void AppliquerMenage(Etalement e)
		{
			GDict snap = e.Snap;
			string season = snap["season"].AsString();
			// Heatmap (t6·C) : la grille affichée date de la semaine d'avant →
			// périmée. Si l'overlay est ON, _Process relancera UNE requête
			// `fields` dès que le pipe sera libre ; OFF, le flag dort.
			_fieldsStale = true;

			// Bloc joueur (volet B, lecture seule) → 2e ligne du HUD.
			if (snap.ContainsKey("player"))
			{
				var pl = snap["player"].AsGodotDictionary();
				_vigueur = pl["vigueur"].AsDouble();
				_vigueurMax = pl["vigueur_max"].AsDouble();
				// Graines plantables (0.3.3) → choix d'espèce pour `planter`.
				// Lecture tolérante : un snapshot pré-0.3.3 n'a pas la clé.
				if (pl.ContainsKey("seeds"))
					ApplySeeds(pl["seeds"].AsGodotDictionary());
				// Gestes débloqués (palette ④, 0.5.23) : liste des verbes OUVERTS
				// pour l'avatar → la palette gauche n'affiche QUE ceux-là (D11).
				// Lecture TOLÉRANTE : un binaire pré-0.5.23 n'émet pas la clé →
				// ApplyGestesDebloques(null) retombe sur « tout dispo » (tous les
				// Verbs de Gestes[]). `debloques_recents` = verbes ouverts au dernier
				// tick (voie savoir) → notification diégétique, consommé à la lecture.
				ApplyGestesDebloques(
					pl.ContainsKey("gestes_debloques")
						? pl["gestes_debloques"].AsGodotArray() : null,
					pl.ContainsKey("debloques_recents")
						? pl["debloques_recents"].AsGodotArray() : null);
				// Palette persistée (macros ⑤, 0.5.26) : bloc player.palette =
				// {slots, macros}. Lecture TOLÉRANTE : un binaire pré-0.5.26 n'émet
				// pas la clé → ApplyPalette(null) vide les macros (aucun rejeu).
				ApplyPalette(pl.ContainsKey("palette")
					? pl["palette"].AsGodotDictionary() : null);
			}
			UpdateActionHud();

			// Jardinier automate (sprint jardinier_auto ⑥, snapshot 0.5.30) : bloc
			// OPT-IN, présent UNIQUEMENT quand l'automate est branché (touche A).
			// Lecture TOLÉRANTE : absent (automate off, ou binaire pré-0.5.30) →
			// le panneau garde son dernier texte, aucun crash.
			if (snap.ContainsKey("automate"))
				ApplyAutomate(snap["automate"].AsGodotDictionary());

			// Fin de saison : retour AUTOMATIQUE en planification (boucle
			// hybride) + hook auto-save. Détection = le nom de saison change.
			// En mode Continu/Turbo, on n'arrête PAS (demande Nico F5 t4) —
			// le hook auto-save reste appelé à chaque passage, lui.
			if (_season != null && season != _season)
			{
				OnSeasonEnd();
				if (_simMode == SimMode.Saison)
				{
					GD.Print($"[WorldView] passage de saison : {season}, an {_year} "
							 + "— retour en planification.");
					_phase = Phase.Planification;
				}
				else
					GD.Print($"[WorldView] passage de saison : {season}, an {_year} "
							 + $"— mode {_simMode}, on enchaîne.");
			}
			_season = season;
			UpdateClock();

			// Culling préventif (tronçon ②) : de nouvelles plantes ont pu naître
			// hors du cadre (ou d'anciennes changer de place au diff) → réévaluer
			// leur Visible d'après le viewport courant. Sans quoi une plante née
			// hors champ resterait dessinée jusqu'au prochain pan/zoom.
			CullPlants();
		}
	}
}
