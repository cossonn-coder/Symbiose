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

		// Fenêtre du journal récent affichée (les N dernières entrées de la trace,
		// elle-même déjà bornée à 60 côté serveur) — on n'en montre qu'une tranche
		// pour garder le panneau lisible sans scroll frénétique.
		private const int AutomateLogLignes = 18;

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

		// Met en page le bloc `automate` du snapshot (appelé depuis ApplySnapshot SI le
		// bloc est présent). PURE mise en forme : profil, objectifs + progression
		// (onglet du 1er objectif actif = son journal filtré), puis le journal récent.
		private void ApplyAutomate(GDict block)
		{
			if (_automateLabel == null || !_automateOn) return;
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

			// --- Journal récent (gestes / impasses / conséquences) ------------
			sb.Append("\n[b]Journal récent[/b]\n");
			int debut = Mathf.Max(0, trace.Count - AutomateLogLignes);
			for (int i = debut; i < trace.Count; i++)
				sb.Append(LigneTrace(trace[i].AsGodotDictionary()) + "\n");

			_automateLabel.Text = sb.ToString();
		}

		// Formate UNE entrée de trace en une ligne BBCode. Trois catégories : geste
		// (facteur→verbe→résultat), impasse (rouge, « trou de gameplay »), conséquence.
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
			// geste
			string res = e["resultat"].AsString();
			string coul = res == "echec" ? "#FFA0A0" : res == "tronque" ? "#FFE0A0" : "#C0F0C0";
			return $"[color={coul}]s{sem} {e["tile_id"].AsString()} {e["cible"].AsString()} : "
				+ $"{e["facteur_limitant"].AsString()} → {e["geste"].AsString()} ({res})[/color]";
		}
	}
}
