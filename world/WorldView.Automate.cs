// SYMBIOSE — WorldView.Automate.cs (partial de WorldView, sprint jardinier_auto ⑥)
// La VUE F5 du JARDINIER AUTOMATE (instrument de DÉVELOPPEMENT, du même statut que
// l'overlay debug F6 — pas une fonctionnalité de jeu). Touche A = brancher/débrancher
// l'automate déterministe côté serveur (pont 0.5.30) ; il joue alors le jardin ENTRE
// deux ticks (invariant H2, jamais dans le tick) et la vue LIT le bloc `automate` du
// snapshot pour afficher un panneau texte : profil, objectifs + progression (onglet),
// et le journal récent (gestes / impasses / conséquences). Les IMPASSES — les « trous
// de gameplay » que l'automate découvre — sautent aux yeux (rouge).
//
// « Godot bête » : aucune logique ici. On envoie l'intention (A = on/off, Maj+A =
// pousser un objectif démo) et on MET EN PAGE ce que Python a déjà écrit. Le retour
// visuel des gestes se limite v1 au journal défilant (confort de débogage) — le
// marqueur au plot viendra si Nico le demande (kickoff : « ligne de log suffit »).

using Godot;
using System.Text;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private CanvasLayer _automateLayer;   // panneau (coord écran, hors caméra)
		private RichTextLabel _automateLabel;
		private bool _automateOn;             // automate branché côté serveur ?
		private GDict _automateBlock;         // dernier bloc snapshot (re-rendu au filtrage)

		// Fenêtre du journal récent affichée (les N dernières entrées de la trace,
		// elle-même déjà bornée à 60 côté serveur) — on n'en montre qu'une tranche
		// pour garder le panneau lisible sans scroll frénétique.
		private const int AutomateLogLignes = 18;

		// Filtre de CATÉGORIES du log (D87 ⑤) : l'utilisateur « coche » les catégories à
		// voir. VUE LECTURE SEULE stricte — on masque des lignes à l'AFFICHAGE, le log
		// sous-jacent (côté Python) reste complet et déterministe (un run filtré et un
		// run brut partagent le même journal). Touche F = cycler la catégorie focus,
		// Maj+F = la (dé)cocher. Toutes cochées par défaut.
		private static readonly string[] AutomateCats = {
			"perception", "diagnostic", "plan", "geste", "geste_coupe",
			"veille", "impasse", "consequence", "resultat",
		};
		private readonly System.Collections.Generic.HashSet<string> _automateCatsOff = new();
		private int _automateCatFocus;        // index dans AutomateCats de la catégorie focus

		private void BuildAutomatePanel()
		{
			_automateLayer = new CanvasLayer { Name = "AutomateHud" };
			// Fond sombre translucide : le texte reste lisible par-dessus le jardin.
			var fond = new ColorRect
			{
				Color = new Color(0f, 0f, 0f, 0.5f),
				Position = new Vector2(1142f, 100f),
				Size = new Vector2(772f, 872f),
			};
			_automateLayer.AddChild(fond);
			_automateLabel = new RichTextLabel
			{
				Position = new Vector2(1152f, 108f),
				CustomMinimumSize = new Vector2(752f, 856f),
				Size = new Vector2(752f, 856f),
				BbcodeEnabled = true, FitContent = false, ScrollActive = true,
				AutowrapMode = TextServer.AutowrapMode.WordSmart,
			};
			_automateLabel.AddThemeFontSizeOverride("normal_font_size", 15);
			_automateLabel.AddThemeColorOverride("default_color", new Color(0.9f, 0.95f, 1f));
			_automateLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_automateLabel.AddThemeConstantOverride("outline_size", 3);
			_automateLayer.AddChild(_automateLabel);
			_automateLayer.Visible = false;   // caché tant que l'automate n'est pas branché
			AddChild(_automateLayer);
		}

		// Touche A : branche/débranche l'automate côté serveur (commande `automate`,
		// pont 0.5.30). ON → il tient le jardin (tutelle = cultivées, déclarées à
		// l'activation), OFF → il cesse de jouer (la trace reste affichée). Si le pont
		// est trop vieux (pré-0.5.30, binaire gelé), la réponse est nulle → on annule.
		private void ToggleAutomate()
		{
			if (_bridge == null) return;
			bool cible = !_automateOn;
			// Profil par défaut = LIBRE + désherbage curatif (l'automate ne paie pas
			// sa Vigueur → il joue chaque tick, retour visuel dense pour le F5).
			var profil = cible ? new GDict { ["desherbage"] = "curatif" } : null;
			var resp = _bridge.Automate(cible, profil);
			if (cible && resp == null)
			{
				GD.PrintErr("[WorldView] automate indisponible (moteur pré-0.5.30 ?).");
				return;
			}
			_automateOn = cible;
			_automateLayer.Visible = _automateOn;
			if (!_automateOn) _automateLabel.Text = "";
			int cultivees = _automateOn && resp.ContainsKey("cultivees")
				? resp["cultivees"].AsInt32() : 0;
			GD.Print($"[WorldView] A → jardinier automate {(_automateOn ? "ON" : "OFF")}"
				+ (_automateOn ? $" ({cultivees} cultivées sous tutelle)." : "."));
		}

		// Maj+A : pousse un OBJECTIF démo (récolter 5 tomates) pour valider l'onglet
		// objectifs en F5 (sans lui, aucun objectif n'existe → l'onglet reste vide).
		// Instrument debug — les vrais objectifs diégétiques = système de quêtes (D79).
		private void InjecterObjectifDemo()
		{
			if (_bridge == null || !_automateOn) return;
			_bridge.AutomateObjectif("recolter", 5, "tomate");
			GD.Print("[WorldView] Maj+A → objectif démo poussé (récolter 5 tomate).");
		}

		// Touche F (log filtrable, ⑤) : cycle la catégorie FOCUS (celle que Maj+F
		// (dé)coche). Actif seulement quand l'automate est branché. Re-rend le dernier
		// bloc pour un retour immédiat (pas d'attente du prochain snapshot).
		private void CycleAutomateCat()
		{
			if (!_automateOn) return;
			_automateCatFocus = (_automateCatFocus + 1) % AutomateCats.Length;
			if (_automateBlock != null) ApplyAutomate(_automateBlock);
		}

		// Maj+F : (dé)coche la catégorie focus — filtrage d'AFFICHAGE, jamais une
		// mutation du log (vue lecture seule stricte).
		private void ToggleAutomateCat()
		{
			if (!_automateOn) return;
			string cat = AutomateCats[_automateCatFocus];
			if (!_automateCatsOff.Remove(cat)) _automateCatsOff.Add(cat);
			if (_automateBlock != null) ApplyAutomate(_automateBlock);
		}

		// Ligne d'en-tête du filtre : [x]/[ ] par catégorie, la focus en surbrillance.
		private string EnteteFiltre()
		{
			var sb = new StringBuilder("[b]Filtre[/b] (F cycle · Maj+F coche) : ");
			for (int i = 0; i < AutomateCats.Length; i++)
			{
				string cat = AutomateCats[i];
				bool on = !_automateCatsOff.Contains(cat);
				string txt = $"{(on ? "☑" : "☐")}{cat}";
				sb.Append(i == _automateCatFocus ? $"[color=#FFE27C]▸{txt}[/color] " : $"{txt} ");
			}
			return sb.ToString();
		}

		// Met en page le bloc `automate` du snapshot (appelé depuis ApplySnapshot SI le
		// bloc est présent). PURE mise en forme : profil, objectifs + progression
		// (onglet du 1er objectif actif = son journal filtré), puis le journal récent
		// FILTRÉ par catégories cochées (⑤).
		private void ApplyAutomate(GDict block)
		{
			if (_automateLabel == null || !_automateOn) return;
			_automateBlock = block;   // mémorisé → re-rendu au (dé)cochage d'une catégorie
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
			// On garde les AutomateLogLignes dernières lignes RETENUES (filtrage
			// d'affichage) : on balaie de la fin vers le début, on empile les visibles.
			var lignes = new System.Collections.Generic.List<string>();
			for (int i = trace.Count - 1; i >= 0 && lignes.Count < AutomateLogLignes; i--)
			{
				var e = trace[i].AsGodotDictionary();
				string cat = e.ContainsKey("categorie") ? e["categorie"].AsString() : "geste";
				if (_automateCatsOff.Contains(cat)) continue;
				lignes.Add(LigneTrace(e));
			}
			lignes.Reverse();   // ré-ordonner du plus ancien au plus récent
			foreach (var l in lignes) sb.Append(l + "\n");
			if (lignes.Count == 0) sb.Append("  (aucune ligne dans les catégories cochées)\n");

			_automateLabel.Text = sb.ToString();
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
