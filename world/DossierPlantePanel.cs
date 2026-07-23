// SYMBIOSE — DossierPlantePanel.cs (sprint retours UI/HUD, T3 — dossier de plante)
// Panneau DEBUG read-only : clic (mode inspection F2) sur une plante → son état
// physiologique COURANT, lu du DERNIER snapshot (aucun appel pont). Du même rang
// que les overlays F6/F7 (philo #5 : chiffres tolérés hors HUD de découverte).
// Ce n'est NI le carnet NI l'encyclopédie (#6) : un instrument de test distinct.
//
// Il n'existe PAS de chronologie par plante côté moteur → on n'invente pas de
// timeline : les mémoires scalaires du snapshot SONT l'histoire compressée de la
// plante (shade_memory élevé = longtemps à l'ombre). On les affiche telles quelles.
//
// 📖 Pédagogie Godot/C# :
//  - CanvasLayer : dessine en coordonnées ÉCRAN (ignore la Camera2D du monde),
//    comme le HUD — le dossier reste ancré même quand on pan/zoome le jardin.
//  - Le panneau est AGNOSTIQUE du moteur : on lui passe le dict-plante du snapshot
//    (Godot.Collections.Dictionary), il met en page. Zéro requête, zéro recalcul.
//  - Lecture TOLÉRANTE (ContainsKey) : un binaire pré-0.5.38 n'émet pas memoires/
//    expression/age → la section correspondante est simplement omise.

using Godot;
using System.Text;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class DossierPlantePanel : CanvasLayer
	{
		// = constants.PLOT_CM (source Python) : dérive le plot-foyer de la position
		// continue x_cm/y_cm. Petite duplication assumée (panneau debug, pas de
		// couplage à WorldView.Projection pour un simple floor).
		private const float PlotCm = 50f;

		// Ordre + libellés lisibles des 8 mémoires physiologiques (serialize.py,
		// clé `memoires`). L'ordre suit celui de plants/base/instance.py.
		private static readonly (string Cle, string Label)[] Memoires =
		{
			("shade_memory", "ombre"), ("drought_memory", "soif"),
			("asphyxie_memory", "asphyxie"), ("cold_memory", "froid"),
			("infection_memory", "infection"), ("wind_memory", "vent"),
			("root_herbivory_memory", "racines rongées"),
			("stress_memory", "stress"),
		};

		private RichTextLabel _texte;

		public override void _Ready()
		{
			Layer = 9;   // sous la consultation (Layer 10), au-dessus du HUD
			var panel = new Panel
			{
				Position = new Vector2(1494f, 110f),
				Size = new Vector2(410f, 660f),
			};
			AddChild(panel);
			_texte = new RichTextLabel
			{
				BbcodeEnabled = true, FitContent = true, ScrollActive = false,
				Position = new Vector2(14f, 12f),
				Size = new Vector2(382f, 636f),
			};
			_texte.AddThemeFontSizeOverride("normal_font_size", 15);
			_texte.AddThemeColorOverride("default_color", new Color(0.92f, 0.96f, 1f));
			panel.AddChild(_texte);
		}

		/// <summary>Met en page l'état physiologique COURANT de la plante (dict du
		/// dernier snapshot). Appelée à chaque clic d'inspection (rafraîchit).</summary>
		public void Afficher(GDict p)
		{
			var sb = new StringBuilder();
			string espece = p["species"].AsString();
			string nom = p.ContainsKey("name") ? p["name"].AsString() : espece;
			float x = (float)p["x_cm"].AsDouble(), y = (float)p["y_cm"].AsDouble();
			int pr = (int)(y / PlotCm), pc = (int)(x / PlotCm);
			sb.Append($"[b]{nom}[/b]  [i]{espece}[/i]\n");
			sb.Append($"tuile {p["tile"].AsString()} · plot ({pr},{pc}) · "
					  + $"x={x:F0} y={y:F0}\n");

			// Stade + âge (age_weeks/age_years = ajouts T3, tolérance ContainsKey).
			string stade = p.ContainsKey("stage_name")
				? p["stage_name"].AsString() : "?";
			sb.Append($"stade : {stade}");
			if (p.ContainsKey("age_weeks"))
				sb.Append($" · âge {p["age_weeks"].AsInt32()} sem");
			if (p.ContainsKey("age_years"))
				sb.Append($" ({p["age_years"].AsDouble():F2} an)");
			sb.Append('\n');

			// Vitalité / état (santé & résilience ④).
			if (p.ContainsKey("vitalite"))
			{
				string etat = p.ContainsKey("etat") ? p["etat"].AsString() : "?";
				sb.Append($"vitalité : {p["vitalite"].AsDouble():F2}  ({etat})\n");
			}

			AppendSymptomes(sb, p);
			AppendMemoires(sb, p);
			AppendExpression(sb, p);
			AppendGenes(sb, p);

			_texte.Text = sb.ToString();
		}

		// Symptômes ÉVÉNEMENTIELS/chroniques actifs (D33) : liste triée par le
		// moteur, `[{cause, intensity}]`. Section omise si aucune.
		private static void AppendSymptomes(StringBuilder sb, GDict p)
		{
			if (!p.ContainsKey("leaf_symptoms")) return;
			var syms = p["leaf_symptoms"].AsGodotArray();
			if (syms.Count == 0) return;
			sb.Append("\n[b]symptômes[/b]\n");
			foreach (var sv in syms)
			{
				var s = sv.AsGodotDictionary();
				sb.Append($"  · {s["cause"].AsString()} : "
						  + $"{s["intensity"].AsDouble():F2}\n");
			}
		}

		// Mémoires physiologiques (T3) : les intégrateurs lents = l'histoire
		// compressée. On n'affiche QUE les non nulles (une plante saine n'en a
		// aucune → section « aucune »). Tolérance ContainsKey (pré-0.5.38).
		private static void AppendMemoires(StringBuilder sb, GDict p)
		{
			if (!p.ContainsKey("memoires")) return;
			var mem = p["memoires"].AsGodotDictionary();
			sb.Append("\n[b]mémoires[/b]\n");
			bool aucune = true;
			foreach (var (cle, label) in Memoires)
			{
				if (!mem.ContainsKey(cle)) continue;
				double v = mem[cle].AsDouble();
				if (v <= 0.005) continue;
				sb.Append($"  · {label} : {v:F2}\n");
				aucune = false;
			}
			if (aucune) sb.Append("  (aucune)\n");
		}

		// Expression plastique (T3) : facteurs ≠ 1.0 déjà filtrés côté serveur.
		private static void AppendExpression(StringBuilder sb, GDict p)
		{
			if (!p.ContainsKey("expression")) return;
			var expr = p["expression"].AsGodotDictionary();
			if (expr.Count == 0) return;
			sb.Append("\n[b]expression[/b]\n");
			foreach (var kv in expr)
				sb.Append($"  · {kv.Key.AsString()} ×{kv.Value.AsDouble():F2}\n");
		}

		// Patrimoine génétique (diversité fondatrice ③) : dict clé→valeur.
		private static void AppendGenes(StringBuilder sb, GDict p)
		{
			if (!p.ContainsKey("genes")) return;
			var genes = p["genes"].AsGodotDictionary();
			if (genes.Count == 0) return;
			sb.Append("\n[b]gènes[/b]\n");
			foreach (var kv in genes)
				sb.Append($"  · {kv.Key.AsString()} : {kv.Value.AsDouble():F2}\n");
		}
	}
}
