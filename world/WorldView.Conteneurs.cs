// SYMBIOSE — WorldView.Conteneurs.cs (partial de WorldView, sprint pots/bacs ⑥a)
// Le câblage VUE des CONTENEURS de culture (pots/bacs ④, snapshot 0.5.7,
// bloc `containers`) : on LIT la liste du snapshot et on DESSINE chaque conteneur
// (placeholder ContainerStructure) avec la/les plante(s) qu'il abrite. Lecture
// SEULE — la pose/le déplacement (geste joueur) arrive au ⑥b, les indices de
// couplage au ⑥c. La logique métier (effet nain, drainage, couplage) reste à
// Python : ici on ne fait que PROJETER (Godot est « bête »).
//
// 📖 Pédagogie — modèle de rendu calqué sur WorldView.Compost.cs : un conteneur
// = un nœud ContainerStructure dans la couche YSort des objets (`_objects`) pour
// s'occulter en profondeur avec plantes/maison ; reconstruction PLEINE à chaque
// snapshot (peu de conteneurs, leur forme ne change pas → pas de fondu à tenir,
// trivial comme reconstruire le sol à la rotation). La/les plante(s) du mini-sol
// se dessinent avec le PlantRenderer existant (même format `segments` que les
// plantes du monde) → l'effet nain est DÉJÀ dans `height_cm` (rien à faire ici).
//
// ⚠ REPÈRES (piège du kickoff) :
//  · le CONTENEUR a une position MONDE absolue (x_cm/y_cm) → on ne lui ajoute
//    JAMAIS l'origine d'une tuile (≠ plantes du bloc global `plants`, locales) ;
//  · les PLANTES du conteneur ont une position LOCALE au mini-sol
//    (x_cm=c·50+25, y_cm=r·50+25, cf. world/container.py::planter_dans) → on les
//    place autour du CENTRE du conteneur (offset = local − demi-grille).

using Godot;
using System.Collections.Generic;
using GArray = Godot.Collections.Array;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Conteneurs affichés. On garde l'INDEX dans la liste du snapshot (=
		// `target.container` attendu par le serveur pour la désignation des gestes
		// ⑥b) + la position MONDE (pour le picking ⑥b/⑥c) + les nœuds (conteneur et
		// ses plantes) pour les libérer à la reconstruction. ⑥c ajoute l'identité
		// affichable (substrat/volume/kind/fondOuvert) et l'`eco_summary` du
		// mini-sol pour l'étiquette QUALITATIVE au survol (mots, pas chiffres).
		private readonly List<(int Index, string Id, float XCm, float YCm,
							   ContainerStructure Node, List<PlantRenderer> Plants,
							   ContainerInfo Info)>
			_containers = new();

		// Identité + état lisible d'un conteneur, figés à l'ApplyContainers et
		// relus par l'étiquette de survol (⑥c.C). Pure lecture du snapshot.
		private readonly struct ContainerInfo
		{
			public readonly string Kind, Substrat;
			public readonly float Volume;
			public readonly bool FondOuvert;
			public readonly float Humidite, N, P, K, Ph, Microbiome;
			public ContainerInfo(string kind, string substrat, float volume,
								 bool fondOuvert, float humidite, float n, float p,
								 float k, float ph, float microbiome)
			{
				Kind = kind; Substrat = substrat; Volume = volume;
				FondOuvert = fondOuvert; Humidite = humidite;
				N = n; P = p; K = k; Ph = ph; Microbiome = microbiome;
			}
		}

		// Seuil de volume (litres) en deçà duquel un conteneur fond fermé est
		// considéré confiné pour l'INDICE de nain (⑥c.B). Aligné qualitativement
		// sur le moteur (world/container.py VOLUME_REF=75 : la plante d'un pot
		// nettement sous la pleine terre est rapetissée). Const = calibrage F5.
		private const float NainVolumeSeuilL = 60f;

		// Lit `eco_summary` (scalaires plot 0,0 du mini-sol) en ContainerInfo pour
		// l'étiquette de survol. Tolérant : valeurs neutres si le bloc manque.
		private ContainerInfo ReadInfo(GDict ct, string kind, string substrat,
									   float volume, bool fondOuvert)
		{
			float h = 0.5f, n = 0.5f, p = 0.5f, k = 0.5f, ph = 7f, mic = 0.5f;
			if (ct.ContainsKey("eco_summary"))
			{
				var e = ct["eco_summary"].AsGodotDictionary();
				h = (float)e["humidite"].AsDouble();
				n = (float)e["n"].AsDouble();
				p = (float)e["p"].AsDouble();
				k = (float)e["k"].AsDouble();
				ph = (float)e["ph"].AsDouble();
				mic = (float)e["microbiome"].AsDouble();
			}
			return new ContainerInfo(kind, substrat, volume, fondOuvert,
									 h, n, p, k, ph, mic);
		}

		// Vrai si le conteneur abrite au moins une plante VIVANTE (sert l'indice de
		// nain ⑥c.B : sans plante à confiner, pas de racines tassées à montrer).
		private static bool HasLivingPlant(GDict ct)
		{
			if (!ct.ContainsKey("plants")) return false;
			foreach (var pv in ct["plants"].AsGodotArray())
			{
				var p = pv.AsGodotDictionary();
				if (!(p.ContainsKey("dead") && p["dead"].AsBool())) return true;
			}
			return false;
		}

		// Applique le bloc `containers` (lecture tolérante : un snapshot pré-0.5.7
		// n'a pas la clé → aucun conteneur dessiné, jamais de crash, comme
		// ApplyStructures pré-0.3.5). Reconstruction pleine : on libère les anciens
		// nœuds (conteneur + plantes) puis on recrée tout depuis la liste.
		private void ApplyContainers(GArray containers)
		{
			foreach (var c in _containers)
			{
				if (IsInstanceValid(c.Node)) c.Node.QueueFree();
				foreach (var pr in c.Plants)
					if (IsInstanceValid(pr)) pr.QueueFree();
			}
			_containers.Clear();

			int idx = 0;
			foreach (var cv in containers)
			{
				var ct = cv.AsGodotDictionary();
				string kind = ct["kind"].AsString();
				string substrat = ct["substrat"].AsString();
				float volume = (float)ct["volume"].AsDouble();
				int rows = ct["rows"].AsInt32(), cols = ct["cols"].AsInt32();
				float cx = (float)ct["x_cm"].AsDouble();   // position MONDE absolue
				float cy = (float)ct["y_cm"].AsDouble();
				string id = ct["id"].AsString();
				bool fondOuvert = ct.ContainsKey("fond_ouvert")
					&& ct["fond_ouvert"].AsBool();

				// ⑥c.B — root-bound (effet nain NON levé) : VUE PURE, on ne recalcule
				// pas l'effet (height_cm vient du moteur), on DÉDUIT seulement quand
				// dessiner l'indice de cause. Conditions = petit volume confiné, fond
				// FERMÉ (un bac couplé lève le nain, ⑤) ET au moins une plante vivante
				// (sinon rien à confiner). Seuil aligné sur le moteur (VOLUME_REF=75).
				bool rootBound = !fondOuvert
					&& volume <= NainVolumeSeuilL
					&& HasLivingPlant(ct);

				var node = new ContainerStructure(kind, substrat, volume, rows, cols,
												  fondOuvert, rootBound)
				{
					Position = WorldToScreen(cx, cy),
					Name = $"container_{id}",
				};
				_objects.AddChild(node);

				// Plante(s) du mini-sol → PlantRenderer ancré autour du centre du
				// conteneur (offset local − demi-grille, projeté en OFFSET → tourne
				// avec la vue). On réutilise le diff/rendu PlantRenderer standard.
				var plantNodes = BuildContainerPlants(ct, cx, cy, rows, cols);
				_containers.Add((idx, id, cx, cy, node, plantNodes,
								 ReadInfo(ct, kind, substrat, volume, fondOuvert)));
				idx++;
			}
		}

		// Instancie un PlantRenderer par plante VIVANTE/morte du conteneur (même
		// chemin que les plantes du monde, cf. WorldView.Snapshot.cs), positionné à
		// la position MONDE de la plante = centre du conteneur + offset de cellule.
		// Pas de fondu (reconstruction pleine) ; pas de diff par clé (les conteneurs
		// sont peu nombreux → on recrée). Tolérant à un conteneur sans plante.
		private List<PlantRenderer> BuildContainerPlants(GDict ct, float cx, float cy,
														 int rows, int cols)
		{
			var nodes = new List<PlantRenderer>();
			if (!ct.ContainsKey("plants")) return nodes;
			foreach (var pv in ct["plants"].AsGodotArray())
			{
				var p = pv.AsGodotDictionary();
				var structure = StructureLoader.FromSnapshot(p);
				if (structure.Segments.Count == 0)
					continue;   // germination sans bois : rien à dessiner encore

				// Position MONDE de la plante : centre du conteneur + (local du
				// mini-sol − centre de la grille). Local : x=c·50+25, y=r·50+25.
				float lx = (float)p["x_cm"].AsDouble() - cols * PlotCm / 2f;
				float ly = (float)p["y_cm"].AsDouble() - rows * PlotCm / 2f;
				Vector2 worldPos = WorldToScreen(cx, cy)
					+ WorldToScreenOffset(lx, ly);

				var renderer = new PlantRenderer
				{
					Position = worldPos,
					Name = $"potplant_{_plantSeq++}",
				};
				_objects.AddChild(renderer);
				renderer.SetStructure(structure);
				// Squelette si morte (le snapshot conteneur n'expose pas `stade_mort`
				// → mode bois nu par défaut "seche"). Symptômes foliaires si présents.
				string stadeMort = p.ContainsKey("dead") && p["dead"].AsBool()
					? "seche" : null;
				renderer.SetSkeleton(stadeMort);
				if (p.ContainsKey("leaf_symptoms"))
					renderer.SetSymptoms(p["leaf_symptoms"].AsGodotArray());
				// Vitalité continue (santé ④, 0.5.28) : même fond d'usure que le
				// vivant en pleine terre. Tolérant à un snapshot pré-0.5.28 (→ 1.0).
				if (p.ContainsKey("vitalite"))
					renderer.SetVitality((float)p["vitalite"].AsDouble());
				nodes.Add(renderer);
			}
			return nodes;
		}

		/// <summary>
		/// INDEX snapshot (= `target.container`) du conteneur dont le CENTRE MONDE
		/// est le plus proche du point `w` (cm) sous `radiusCm`, ou -1. Calqué sur
		/// FindPlant/FindNearestStructure : recherche linéaire (une poignée de
		/// conteneurs → pas de quadtree à inventer). Premier index gagne à égalité
		/// (déterministe). Sert la désignation des gestes ⑥b (déplacer / planter
		/// dans un conteneur) : la vue DÉSIGNE par index, le serveur juge.
		/// </summary>
		private int FindNearestContainer(Vector2 w, float radiusCm)
		{
			int best = -1;
			float bestD = radiusCm * radiusCm;
			foreach (var c in _containers)
			{
				float dx = c.XCm - w.X, dy = c.YCm - w.Y;
				float d = dx * dx + dy * dy;
				if (d < bestD) { bestD = d; best = c.Index; }
			}
			return best;
		}
	}
}
