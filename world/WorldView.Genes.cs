// SYMBIOSE — WorldView.Genes.cs (partial de WorldView, sprint DIVERSITÉ FONDATRICE ③,
// refondu au sprint GÉNÉTIQUE INFINITÉSIMALE ④, D139)
// Le SURVOL GÈNES (debug). Pointer une plante affiche sa LIGNÉE (fixée / en voie de
// fixation / mélangée, d'après sa consanguinité F) puis CHAQUE caractère dans son
// unité : « optimum de levée −2,1 °C », « avance de floraison +1,0 sem. »,
// « autofécondation 93 % », « vigueur ×1,04 ». Niche thermique ⑤ : la PLAGE VIVABLE
// en °C (gèle, froid, chaud, brûle) et la nuit / la feuille de la semaine, lues dans
// `PlantRenderer.PlageThermique` (pont 0.6.19). Instrument d'observation, étiqueté
// debug (philo #5 : chiffres tolérés hors HUD final), toggle G, caché par défaut.
//
// 📖 Pédagogie — on RÉUTILISE le picking de survol des étiquettes/observation
// (FindPlant sur la souris, WorldView.Actions.cs) : là on AFFICHE le nom, ici on
// LIT les Meta "genes" et "F" posées à l'ApplySnapshot (WorldView.Snapshot.cs) et on
// les met en texte. Zéro requête pont. La vue NE CONNAÎT PAS les unités : le snapshot
// porte une table `caracteres` (pont 0.6.17, `genes_pont.py`) qui dit, pour chaque
// gène, son unité, son libellé et son sens d'affichage, plus les deux seuils de F.
// Le moteur Python reste la seule source de vérité ; la vue ne fait que formater.

using System.Globalization;
using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Banc F5 des lignées (registre Python `bancs/lignees.py`) : monté, il ouvre le
		// survol G d'emblée (StartSimulation) — c'est l'instrument qu'il sert.
		private const string BancLignees = "lignees";
		private const string BancNicheThermique = "niche_thermique";

		// Label du survol gènes (créé dans BuildHud, dans le CanvasLayer "Hud").
		private Label _genesLabel;
		private bool _genesHoverOn;

		// Table `caracteres.unites` du snapshot (null = serveur pré-0.6.17 → valeurs
		// brutes) et seuils de lecture de F. Les seuils par défaut sont un REPLI pour un
		// ancien serveur ; la valeur qui compte vient du pont (`sim/lignee.py`).
		private GDict _unitesGenes;
		private Godot.Collections.Array _ordreGenes;   // ordre du registre (JSON trié côté pont)
		private double _seuilFixee = 0.75, _seuilMelangee = 0.25;

		// Lit la table des caractères (constante : une lecture suffit). Tolérant à
		// l'absence de la clé (ancien serveur) : le survol retombe sur les valeurs brutes.
		private void LireCaracteres(GDict snap)
		{
			if (_unitesGenes != null || !snap.ContainsKey("caracteres")) return;
			var c = snap["caracteres"].AsGodotDictionary();
			_unitesGenes = c["unites"].AsGodotDictionary();
			if (c.ContainsKey("ordre")) _ordreGenes = c["ordre"].AsGodotArray();
			var l = c["lignee"].AsGodotDictionary();
			_seuilFixee = l["fixee"].AsDouble();
			_seuilMelangee = l["melangee"].AsDouble();
		}

		// Toggle G : affiche/masque le survol gènes (instrument debug).
		private void ToggleGenesHover()
		{
			_genesHoverOn = !_genesHoverOn;
			if (_genesLabel != null)
			{
				_genesLabel.Visible = _genesHoverOn;
				if (!_genesHoverOn) _genesLabel.Text = "";
			}
			GD.Print($"[WorldView] survol gènes (debug) : {(_genesHoverOn ? "ON" : "OFF")}.");
		}

		// Appelée chaque frame (_Process) quand le survol gènes est actif : lit la
		// plante sous le curseur et affiche lignée + gènes. Aucune plante sous la
		// souris (ou sans gènes) → ligne d'invite discrète.
		private void UpdateGenesHover()
		{
			if (!_genesHoverOn || _genesLabel == null || !_survolSale) return;
			var node = FindPlant(_sourisMonde, HoverRadiusCm);
			if (node == null || !IsInstanceValid(node) || !node.HasMeta(LectureSnap.Meta("genes")))
			{
				_genesLabel.Text = "[gènes] survole une plante";
				return;
			}
			var genes = node.GetMeta(LectureSnap.Meta("genes")).AsGodotDictionary();
			string species = node.GetMeta(LectureSnap.Meta("species"), "?").AsString();
			var sb = new System.Text.StringBuilder();
			sb.Append($"[gènes] {species}");
			if (node.HasMeta(LectureSnap.Meta("F")))
				sb.Append($"\n  {Lignee(node.GetMeta(LectureSnap.Meta("F")).AsDouble())}");
			if (node is PlantRenderer pr && pr.PlageThermique is { } plage)
				sb.Append(PlageVivable(plage));
			// Ordre du registre moteur quand la table le donne (le pont sérialise ses
			// dicts clés triées : seule la liste `ordre` garde l'ordre du registre).
			System.Collections.Generic.IEnumerable<Variant> ordre =
				_ordreGenes != null ? _ordreGenes : genes.Keys;
			foreach (var g in ordre)
				if (genes.ContainsKey(g))
					sb.Append($"\n  {FormatGene(g.AsString(), genes[g].AsDouble())}");
			_genesLabel.Text = sb.ToString();
		}

		// Plage vivable (niche thermique ⑤, pont 0.6.19) : « gèle < −1,0 °C · froid
		// < 10,0 °C · chaud > 35,0 °C · brûle > 45,0 °C », puis la nuit la plus froide
		// et la feuille au jour le plus chaud vécues cette semaine. Valeur absente
		// (espèce que le froid sans gel ne lèse pas, plante pas encore tiquée) → omise.
		private static string PlageVivable(float[] p)
		{
			var sb = new System.Text.StringBuilder("\n  plage :");
			Borne(sb, " gèle <", p[0]);
			Borne(sb, " · froid <", p[1]);
			Borne(sb, " · chaud >", p[2]);
			Borne(sb, " · brûle >", p[3]);
			sb.Append("\n  vécu :");
			Borne(sb, " nuit", p[4]);
			Borne(sb, " · feuille", p[5]);
			return sb.ToString();
		}

		private static void Borne(System.Text.StringBuilder sb, string lib, float v)
		{
			if (!float.IsNaN(v)) sb.Append($"{lib} {Nombre(v, "F1")} °C");
		}

		// « lignée fixée (F 0,94) » — trois mots, seuils du pont.
		private string Lignee(double f)
		{
			string mot = f >= _seuilFixee ? "lignée fixée"
				: f <= _seuilMelangee ? "lignée mélangée" : "lignée en voie de fixation";
			return $"{mot} (F {Nombre(f, "F2")})";
		}

		// Un caractère dans son unité. Sans table (ancien serveur) → nom et valeur brute.
		private string FormatGene(string nom, double v)
		{
			if (_unitesGenes == null || !_unitesGenes.ContainsKey(nom))
				return $"{nom} : {Nombre(v, "F2")}";
			var d = _unitesGenes[nom].AsGodotDictionary();
			string lib = d["libelle"].AsString();
			double x = v * d["sens"].AsDouble();
			return d["unite"].AsString() switch
			{
				"°C" => $"{lib} {Signe(x, "F1")} °C",
				"semaines" => $"{lib} {Signe(x, "F1")} sem.",
				"probabilité" => $"{lib} {Nombre(x * 100.0, "F0")} %",
				_ => $"{lib} ×{Nombre(x, "F2")}",   // facteur (multiplicateur sans dimension)
			};
		}

		// Nombre à la française (virgule) ; Signe ajoute « + » ou le vrai moins « − ».
		private static string Nombre(double v, string fmt) =>
			v.ToString(fmt, CultureInfo.InvariantCulture).Replace('.', ',').Replace('-', '−');

		private static string Signe(double v, string fmt) =>
			(v >= 0 ? "+" : "") + Nombre(v, fmt);
	}
}
