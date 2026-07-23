// SYMBIOSE — AutomateContent.cs (sprint fenêtrage UI, T3 ; ex-WorldView.Automate.cs)
// Le CONTENU de l'onglet « Automate » du conteneur de consultation. C'est la VUE
// F5 du JARDINIER AUTOMATE (instrument de DÉVELOPPEMENT, même rang que l'overlay
// debug F6 — pas une fonctionnalité de jeu), migrée depuis son ancien CanvasLayer
// autonome vers un onglet (T3, décision A6 dev-gated). Il reste un HUD LIVE : tant
// qu'il est l'onglet VISIBLE, WorldView lui pousse le bloc `automate` du snapshot ;
// sinon on n'assemble RIEN (perf). L'automate joue le jardin ENTRE deux ticks
// (invariant H2), la vue ne fait que METTRE EN PAGE ce que Python a écrit.
//
// « Godot bête » : aucune logique de jeu ici. On met en page profil, objectifs +
// progression, et le journal récent filtrable (les IMPASSES — trous de gameplay —
// sautent aux yeux en rouge). Le filtre de catégories est un masque d'AFFICHAGE
// pur : le log Python reste complet et déterministe (un run filtré et un run brut
// partagent le même journal).

using Godot;
using System.Text;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class AutomateContent : Control
	{
		private RichTextLabel _label;

		// Fenêtre du journal récent affichée (les N dernières entrées RETENUES de la
		// trace, elle-même bornée à 60 côté serveur) — tranche lisible sans scroll frénétique.
		private const int LogLignes = 18;

		// Filtre de CATÉGORIES du log (D87 ⑤) : l'utilisateur « coche » les catégories
		// à voir. Touche F = cycler la catégorie focus, Maj+F = la (dé)cocher.
		// Toutes cochées par défaut. VUE LECTURE SEULE stricte (masque d'affichage).
		private static readonly string[] Cats = {
			"perception", "diagnostic", "plan", "geste", "geste_coupe",
			"veille", "impasse", "consequence", "resultat",
		};
		private readonly System.Collections.Generic.HashSet<string> _catsOff = new();
		private int _catFocus;                 // index dans Cats de la catégorie focus
		private GDict _dernierBloc;            // dernier bloc snapshot (re-rendu au filtrage)

		/// <summary>Construit la surface (RichTextLabel défilant plein onglet).</summary>
		public void Construire()
		{
			SizeFlagsHorizontal = SizeFlags.ExpandFill;
			SizeFlagsVertical = SizeFlags.ExpandFill;
			CustomMinimumSize = new Vector2(752f, 800f);
			_label = new RichTextLabel
			{
				BbcodeEnabled = true, FitContent = false, ScrollActive = true,
				AutowrapMode = TextServer.AutowrapMode.WordSmart,
			};
			_label.SetAnchorsPreset(LayoutPreset.FullRect);
			_label.AddThemeFontSizeOverride("normal_font_size", 15);
			AddChild(_label);
		}

		// Touche F : cycle la catégorie FOCUS (celle que Maj+F (dé)coche). Re-rend le
		// dernier bloc pour un retour immédiat (pas d'attente du prochain snapshot).
		public void CyclerCategorie()
		{
			_catFocus = (_catFocus + 1) % Cats.Length;
			if (_dernierBloc != null) Rendre(_dernierBloc);
		}

		// Maj+F : (dé)coche la catégorie focus — filtrage d'AFFICHAGE, jamais une
		// mutation du log (vue lecture seule stricte).
		public void BasculerCategorie()
		{
			string cat = Cats[_catFocus];
			if (!_catsOff.Remove(cat)) _catsOff.Add(cat);
			if (_dernierBloc != null) Rendre(_dernierBloc);
		}

		// Met en page le bloc `automate` du snapshot. PURE mise en forme : profil,
		// objectifs + progression (onglet du 1er objectif actif = son journal filtré),
		// puis le journal récent FILTRÉ par catégories cochées (⑤).
		public void Rendre(GDict block)
		{
			if (_label == null) return;
			_dernierBloc = block;   // mémorisé → re-rendu au (dé)cochage d'une catégorie
			var sb = new StringBuilder();
			var profil = block["profil"].AsGodotDictionary();
			sb.Append("[b]Jardinier automate[/b] — désherbage ");
			sb.Append(profil["desherbage"].AsString());
			sb.Append(" · récolte ×");
			sb.Append(profil["part_recoltee"].AsDouble().ToString("0.0"));
			sb.Append(profil["paie_vigueur"].AsBool() ? " · paie Vigueur" : " · Vigueur libre");
			sb.Append("\n\n");

			// --- Objectifs + onglet du 1er actif ------------------------------
			var objectifs = block["objectifs"].AsGodotArray();
			sb.Append("[b]Objectifs[/b]\n");
			if (objectifs.Count == 0)
				sb.Append("  (aucun — Maj+A pour un objectif démo)\n");
			string ongletId = null;
			foreach (var ov in objectifs)
			{
				var o = ov.AsGodotDictionary();
				bool accompli = o["accompli"].AsBool();
				string marque = accompli ? "[color=#7CFC7C]✓[/color]" : "•";
				sb.Append($"  {marque} {o["geste"].AsString()} {o["cible"].AsString()} : "
					+ $"{o["progression"].AsInt32()}/{o["quantite"].AsInt32()}\n");
				if (!accompli && ongletId == null) ongletId = o["id"].AsString();
			}

			var trace = block["trace"].AsGodotArray();
			if (ongletId != null)
			{
				sb.Append($"\n[b]Onglet[/b] ({ongletId}) — gestes servant l'objectif :\n");
				int n = 0;
				foreach (var ev in trace)
				{
					var e = ev.AsGodotDictionary();
					string oid = e.ContainsKey("objectif_id") ? e["objectif_id"].AsString() : null;
					if (oid != ongletId) continue;
					sb.Append("  " + LigneTrace(e) + "\n");
					n++;
				}
				if (n == 0) sb.Append("  (pas encore de geste)\n");
			}

			// --- Journal récent, FILTRÉ par catégories cochées (⑤) ------------
			sb.Append("\n").Append(EnteteFiltre()).Append("\n[b]Journal récent[/b]\n");
			// On garde les LogLignes dernières lignes RETENUES (filtrage d'affichage) :
			// on balaie de la fin vers le début, on empile les visibles.
			var lignes = new System.Collections.Generic.List<string>();
			for (int i = trace.Count - 1; i >= 0 && lignes.Count < LogLignes; i--)
			{
				var e = trace[i].AsGodotDictionary();
				string cat = e.ContainsKey("categorie") ? e["categorie"].AsString() : "geste";
				if (_catsOff.Contains(cat)) continue;
				lignes.Add(LigneTrace(e));
			}
			lignes.Reverse();   // ré-ordonner du plus ancien au plus récent
			foreach (var l in lignes) sb.Append(l + "\n");
			if (lignes.Count == 0) sb.Append("  (aucune ligne dans les catégories cochées)\n");

			_label.Text = sb.ToString();
		}

		// Ligne d'en-tête du filtre : [x]/[ ] par catégorie, la focus en surbrillance.
		private string EnteteFiltre()
		{
			var sb = new StringBuilder("[b]Filtre[/b] (F cycle · Maj+F coche) : ");
			for (int i = 0; i < Cats.Length; i++)
			{
				string cat = Cats[i];
				bool on = !_catsOff.Contains(cat);
				string txt = $"{(on ? "☑" : "☐")}{cat}";
				sb.Append(i == _catFocus ? $"[color=#FFE27C]▸{txt}[/color] " : $"{txt} ");
			}
			return sb.ToString();
		}

		// Formate UNE entrée de trace en une ligne BBCode. Catégories LEGACY (clés à
		// plat) : geste (facteur→verbe→résultat), impasse (rouge), conséquence. Catégories
		// NEUVES (D87, charge dans `detail` dict) : plan/diagnostic/perception/geste_coupe/
		// veille/resultat — rendu DÉRIVÉ des champs (jamais du texte libre côté Python).
		private static string LigneTrace(GDict e)
		{
			string cat = e.ContainsKey("categorie") ? e["categorie"].AsString() : "geste";
			int sem = e.ContainsKey("semaine") ? e["semaine"].AsInt32() : 0;
			if (cat == "impasse")
				return $"[color=#FF7070]s{sem} ⊘ {e["cible"].AsString()} : "
					+ $"{e["facteur_limitant"].AsString()} → {e["cause"].AsString()}[/color]";
			if (cat == "consequence")
				return $"[color=#FFD27C]s{sem} ⚑ {e["type"].AsString()} : "
					+ $"{e["detail"].AsString()}[/color]";
			if (cat == "geste")
			{
				string res = e["resultat"].AsString();
				string c = res == "echec" ? "#FFA0A0" : res == "tronque" ? "#FFE0A0" : "#C0F0C0";
				return $"[color={c}]s{sem} {e["tile_id"].AsString()} {e["cible"].AsString()} : "
					+ $"{e["facteur_limitant"].AsString()} → {e["geste"].AsString()} ({res})[/color]";
			}
			// Catégories neuves (schéma commun) : localisation + detail aplati (clés triées).
			string coul = cat == "plan" ? "#9FE0FF" : cat == "veille" ? "#FFC98A"
				: cat == "resultat" ? "#B0F0B0" : cat == "geste_coupe" ? "#D0B0B0" : "#B8C4CC";
			return $"[color={coul}]s{sem} [{cat}] {LocEtDetail(e)}[/color]";
		}

		// Localisation (espèce, zone, #objectif) + `detail` dict aplati (clés triées →
		// stable), pour les catégories neuves. Défensif : champs/clés absents ignorés.
		private static string LocEtDetail(GDict e)
		{
			var parts = new System.Collections.Generic.List<string>();
			if (e.ContainsKey("espece") && e["espece"].VariantType == Variant.Type.String)
				parts.Add(e["espece"].AsString());
			if (e.ContainsKey("zone") && e["zone"].VariantType == Variant.Type.Array)
			{
				var z = e["zone"].AsGodotArray();
				if (z.Count >= 1) parts.Add(z.Count >= 3 && z[1].VariantType != Variant.Type.Nil
					? $"{z[0].AsString()}({z[1].AsInt32()},{z[2].AsInt32()})" : z[0].AsString());
			}
			if (e.ContainsKey("objectif_id") && e["objectif_id"].VariantType == Variant.Type.String)
				parts.Add($"#{e["objectif_id"].AsString()}");
			if (e.ContainsKey("detail") && e["detail"].VariantType == Variant.Type.Dictionary)
			{
				var d = e["detail"].AsGodotDictionary();
				var cles = new System.Collections.Generic.List<string>();
				foreach (var k in d.Keys) cles.Add(k.AsString());
				cles.Sort();
				foreach (var k in cles) parts.Add($"{k}={d[k]}");
			}
			return string.Join(" ", parts);
		}
	}
}
