// SYMBIOSE — PlantStructure.cs
// Miroir C# de la structure de croissance procédurale (tronçon 4 du sprint
// Croissance). C# est ici un CONSOMMATEUR PASSIF : zéro logique écologique,
// zéro RNG. Le moteur de croissance vit UNIQUEMENT en Python (source de vérité,
// data/code/sim/growth.py). Python EXPORTE la structure déjà calculée en JSON
// (tools/export_structure.py) ; ce fichier la LIT et la rend disponible au
// renderer (visuals/PlantRenderer.cs).
//
// Ne PAS confondre avec core/PlantData.cs : celui-là modélise la plante à
// l'ANCIEN modèle (offsets de plots, hérité d'avant la croissance procédurale)
// et survit pour le reste du code C# (non porté). Ici on n'ajoute QUE ce dont le
// rendu de structure a besoin : les segments de bois.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	// ---------------------------------------------------------------------------
	// SEGMENT — miroir minimal du Segment Python (plants/base.py)
	// ---------------------------------------------------------------------------
	// Pédagogie C# : un `record struct` est un type VALEUR (copié, pas référencé,
	// comme un struct C) doté de l'égalité par valeur et d'une syntaxe concise.
	// Idéal pour un petit agrégat de données immuables sans identité propre.
	// On ne mirrore QUE les champs utiles au rendu : base, dir, length, thickness,
	// is_apex. Les champs purement dynamiques du Python (age_weeks, auxin, has_bud,
	// parent, organs) ne servent pas au dessin → on ne les transporte pas.
	public readonly record struct Segment(
		Vector3 Base,        // origine du segment (cm, espace sol 3D)
		Vector3 Dir,         // vecteur directeur unitaire 3D
		float LengthCm,      // longueur → extrémité = Base + Dir * LengthCm
		float ThicknessCm,   // épaisseur (vieux bois = épais) → largeur de trait
		bool IsApex);        // extrémité de croissance active (dessinée en vert)

	// ---------------------------------------------------------------------------
	// FRUIT — miroir d'un fruit tracé du moteur (plant.fruits, décompo·compost ③)
	// ---------------------------------------------------------------------------
	// VRAI état moteur (≠ proxy saisonnier `Organ`) : un fruit NOUE vert, MÛRIT
	// chaque semaine (maturité 0→1), sur-mûrit (>1.3 = MATURITE_CHUTE), tombe ou se
	// mange. `SegmentId` = index du segment porteur à la nouaison (repère VUE
	// best-effort, les indices glissent avec la croissance) → la vue ancre le
	// sprite au bout de ce segment. L'index DANS la liste = clé du `manger` ciblé.
	public readonly record struct FruitData(
		int SegmentId,       // segment porteur (index dans Segments, best-effort)
		float Maturite,      // 0→1 (mûr), >1.3 = sur-mûr/fermenté → teinte brune
		float Masse);        // masse → taille du sprite

	// ---------------------------------------------------------------------------
	// PLANT STRUCTURE — un spécimen exporté (DTO)
	// ---------------------------------------------------------------------------
	// DTO = Data Transfer Object : sac de données issu du JSON, sans comportement.
	// HeightCm / CanopyRadiusCm = empreinte dérivée (§G) — sert à dessiner la
	// silhouette de couronne au LOD faible (zoom ×4), quand on ne rastérise pas
	// chaque brindille.
	public sealed class PlantStructure
	{
		public string Title = "";
		public string SpeciesName = "";
		public float HeightCm;
		public float CanopyRadiusCm;
		public Vector3 ColletCm;             // point sol du collet (origine projection)
		public List<Segment> Segments = new();

		// --- Hints d'organes (sprint Intégration t6·A, protocole 0.2.2) ---
		// PUR rendu, calculés côté Python (proxy saisonnier du prototype SVG,
		// cf. tools/render_structure.py) : la vue dessine, ne décide rien.
		public float FoliageDensity = 1f;    // 0..1, déjà saisonnier (caduc hiver = 0)
		public string Organ = "";            // ""|"flower"|"fruit_unripe"|"fruit_ripe"
		public string OrganSite = "terminal"; // "terminal"|"lateral" — où naissent fleurs/fruits

		// --- Fruits tracés (③, protocole 0.3.4) : VRAI état moteur ---
		// Les FLEURS restent sur le proxy `Organ` (pas d'état moteur de fleur) ;
		// les FRUITS basculent ici (maturité visible, déplétion par `manger`).
		// Ordre = ordre du snapshot = index moteur (clé du geste `manger` ciblé).
		public List<FruitData> Fruits = new();
	}

	// ---------------------------------------------------------------------------
	// CHARGEUR JSON
	// ---------------------------------------------------------------------------
	// Choix : `Json` natif de Godot (Json.ParseString) plutôt que System.Text.Json.
	// Pourquoi ? C'est l'API idiomatique du moteur, zéro dépendance .NET ajoutée,
	// et elle retourne des Variant/Dictionary/Array que Godot manipule nativement.
	// Compromis : peu typée (tout est Variant → on caste à la main, double pour les
	// nombres). Pour un DTO aussi simple, le coût de typage manuel est négligeable
	// et l'on évite d'introduire une stack de sérialisation .NET dans un projet où
	// Nico débute le frontend.
	public static class StructureLoader
	{
		// Chemin du JSON exporté par Python. On le lit DIRECTEMENT là où Python
		// l'écrit (data/code/tools/), sous res:// (= racine du projet Godot). Pas de
		// copie/duplication : source unique. NB : pour un export PCK packagé il
		// faudrait l'ajouter aux filtres d'export ; en éditeur/dev, FileAccess lit
		// le fichier projet sans souci.
		public const string DefaultPath = "res://data/code/tools/structure.json";

		public static List<PlantStructure> Load(string path = DefaultPath)
		{
			var result = new List<PlantStructure>();

			if (!FileAccess.FileExists(path))
			{
				GD.PrintErr($"[StructureLoader] Fichier introuvable : {path} "
							+ "(as-tu lancé `python3 -m tools.export_structure` ?)");
				return result;
			}

			using var file = FileAccess.Open(path, FileAccess.ModeFlags.Read);
			string text = file.GetAsText();

			// ParseString retourne un Variant ; il vaut `null` si le JSON est invalide.
			Variant parsed = Json.ParseString(text);
			if (parsed.VariantType != Variant.Type.Dictionary)
			{
				GD.PrintErr($"[StructureLoader] JSON racine invalide dans {path}");
				return result;
			}

			var root = parsed.AsGodotDictionary();
			if (!root.ContainsKey("specimens"))
			{
				GD.PrintErr("[StructureLoader] Clé 'specimens' absente.");
				return result;
			}

			var specimens = root["specimens"].AsGodotArray();
			foreach (var specVar in specimens)
				result.Add(ParseSpecimen(specVar.AsGodotDictionary()));

			GD.Print($"[StructureLoader] {result.Count} spécimens chargés depuis {path}.");
			return result;
		}

		private static PlantStructure ParseSpecimen(Godot.Collections.Dictionary spec)
		{
			var plant = new PlantStructure
			{
				Title = spec["title"].AsString(),
				SpeciesName = spec["species"].AsString(),
				ColletCm = ParseVec3(spec["collet_cm"].AsGodotArray()),
			};

			var fp = spec["footprint"].AsGodotDictionary();
			plant.HeightCm = (float)fp["height_cm"].AsDouble();
			plant.CanopyRadiusCm = (float)fp["canopy_radius_cm"].AsDouble();

			foreach (var segVar in spec["segments"].AsGodotArray())
				plant.Segments.Add(ParseSegment(segVar.AsGodotDictionary()));

			return plant;
		}

		// -------------------------------------------------------------------
		// POINT D'ENTRÉE SNAPSHOT (sprint Intégration, tranche 2)
		// Même schéma de segments que structure.json (format Croissance·6) mais
		// reçu par le PONT (SimBridge) au lieu d'un fichier, et par PLANTE du
		// snapshot au lieu d'un specimen complet : pas de collet_cm/footprint
		// dédiés. Le collet = base du PREMIER segment (exactement ce que fait
		// tools/export_structure.py côté Python). Le rayon de couronne n'est pas
		// exposé par le snapshot v0 → 0 (le LOD silhouette n'est pas utilisé en
		// tranche 2 ; si besoin un jour : l'exposer en LECTURE dans le snapshot
		// Python, jamais le recalculer ici).
		// -------------------------------------------------------------------

		public static PlantStructure FromSnapshot(Godot.Collections.Dictionary plant)
		{
			var ps = new PlantStructure
			{
				Title = plant["name"].AsString(),
				SpeciesName = plant["species"].AsString(),
				HeightCm = (float)plant["height_cm"].AsDouble(),
				CanopyRadiusCm = 0f,
			};
			// Hints d'organes (t6·A). Lecture TOLÉRANTE (ContainsKey + défauts) :
			// un snapshot pré-0.2.2 reste lisible. `organ` JSON null → Variant
			// Nil → AsString() rend "" = « pas d'organe », exactement le défaut.
			if (plant.ContainsKey("foliage_density"))
				ps.FoliageDensity = (float)plant["foliage_density"].AsDouble();
			if (plant.ContainsKey("organ"))
				ps.Organ = plant["organ"].AsString();
			if (plant.ContainsKey("organ_site"))
				ps.OrganSite = plant["organ_site"].AsString();
			// Fruits tracés (③, 0.3.4) : lecture tolérante (un snapshot pré-0.3.4
			// ou une plante morte n'a pas la clé → liste vide, rien à dessiner).
			if (plant.ContainsKey("fruits"))
				foreach (var fv in plant["fruits"].AsGodotArray())
				{
					var f = fv.AsGodotDictionary();
					ps.Fruits.Add(new FruitData(
						f["segment"].AsInt32(),
						(float)f["maturite"].AsDouble(),
						(float)f["masse"].AsDouble()));
				}
			foreach (var segVar in plant["segments"].AsGodotArray())
				ps.Segments.Add(ParseSegment(segVar.AsGodotDictionary()));
			if (ps.Segments.Count > 0)
				ps.ColletCm = ps.Segments[0].Base;
			return ps;
		}

		// Un segment JSON → Segment C# (champs communs structure.json/snapshot ;
		// les champs dynamiques du moteur — auxin, age_weeks… — sont ignorés).
		private static Segment ParseSegment(Godot.Collections.Dictionary seg) =>
			new Segment(
				Base: ParseVec3(seg["base"].AsGodotArray()),
				Dir: ParseVec3(seg["dir"].AsGodotArray()),
				LengthCm: (float)seg["length_cm"].AsDouble(),
				ThicknessCm: (float)seg["thickness_cm"].AsDouble(),
				IsApex: seg["is_apex"].AsBool());

		private static Vector3 ParseVec3(Godot.Collections.Array a) =>
			new Vector3((float)a[0].AsDouble(), (float)a[1].AsDouble(), (float)a[2].AsDouble());
	}
}
