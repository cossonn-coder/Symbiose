// SYMBIOSE — CarnetPanel.cs (sprint UI voix, tronçon ③)
// Spécialisation de VoicePanel : le CARNET auto du joueur. Liste chronologique
// d'entrées, filtrable par CONCEPT. Chaque entrée est affichée VERBATIM depuis
// le pont Python (SimBridge.Carnet) — le C# ne fabrique, ne reformule, ne trie
// aucun texte de voix (INVARIANT « Godot bête », doc §1).
//
// 📖 Pédagogie Godot/C# :
//  - On hérite de VoicePanel et on surcharge Remplir() : l'ossature (fond,
//    titre, défilement, bouton Fermer) est déjà posée par la classe mère ; on
//    ne peuple que la zone `Contenu`.
//  - Le FILTRE est un OptionButton natif. Sa liste = les concepts RÉELLEMENT
//    présents dans le carnet complet (lus une fois, sans filtre), plus « (tous)
//    ». Choisir un concept re-demande le carnet filtré au pont (le pont applique
//    `filtre={"concept": …}`) — le C# ne filtre RIEN lui-même, il délègue.
//  - Deux registres visuellement distincts sans TOUCHER au texte : l'entrée
//    « interprétatif » (débloquée au palier du concept, décidé côté Python) est
//    mise en italique via BBCode ; le texte affiché reste identique au verbatim.

using Godot;

namespace Symbiose
{
	public partial class CarnetPanel : VoicePanel
	{
		// Filtres courants : null = pas de filtre. Concept ET espèce sont
		// ET-combinés côté pont (le C# ne filtre rien lui-même). L'espèce est une
		// clé catalogue, prise parmi les espèces DÉCOUVERTES (index encyclopédie).
		private string _filtreConcept;
		private string _filtreEspece;

		// Conteneurs séparés : les sélecteurs restent en tête, seule la liste des
		// entrées est reconstruite quand un filtre change.
		private OptionButton _selecteur;
		private OptionButton _selecteurEspece;
		private VBoxContainer _liste;

		protected override void Remplir()
		{
			// En-tête : libellé + sélecteur de concept. La liste des concepts
			// vient du carnet COMPLET (appel sans filtre) — source unique Python.
			var entete = new HBoxContainer();
			Contenu.AddChild(entete);
			entete.AddChild(new Label { Text = "Concept :" });

			_selecteur = new OptionButton();
			entete.AddChild(_selecteur);
			_selecteur.AddItem("(tous)");                 // index 0 → filtre null
			foreach (string concept in ConceptsPresents())
				_selecteur.AddItem(concept);
			_selecteur.ItemSelected += OnConceptChoisi;

			// Sélecteur d'ESPÈCE (retour F5) : suivre une espèce DÉCOUVERTE. La
			// liste = index encyclopédie (source Python, uniquement le découvert).
			entete.AddChild(new Label { Text = "   Espèce :" });
			_selecteurEspece = new OptionButton();
			entete.AddChild(_selecteurEspece);
			_selecteurEspece.AddItem("(toutes)");         // index 0 → filtre null
			foreach (string sp in EspecesDecouvertes())
				_selecteurEspece.AddItem(sp);
			_selecteurEspece.ItemSelected += OnEspeceChoisie;

			// La liste défilante des entrées, reconstruite à chaque filtre.
			_liste = new VBoxContainer
			{
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
			};
			Contenu.AddChild(_liste);

			ReconstruireListe();
		}

		// Concepts distincts présents dans le carnet complet, dans l'ordre de
		// première apparition (chronologique). On NE trie pas « intelligemment »
		// (invariant) : on préserve l'ordre du ledger renvoyé par le pont.
		private System.Collections.Generic.List<string> ConceptsPresents()
		{
			var vus = new System.Collections.Generic.HashSet<string>();
			var ordre = new System.Collections.Generic.List<string>();
			foreach (var ev in Bridge.Carnet())
			{
				var e = ev.AsGodotDictionary();
				string c = e["concept"].AsString();
				if (vus.Add(c)) ordre.Add(c);
			}
			return ordre;
		}

		// Espèces DÉCOUVERTES = index de l'encyclopédie (source Python : uniquement
		// ce que le joueur a observé). On préserve l'ordre du corpus (pas de tri).
		private System.Collections.Generic.List<string> EspecesDecouvertes()
		{
			var ordre = new System.Collections.Generic.List<string>();
			var enc = Bridge.Encyclopedie();          // sans espèce → l'index
			if (enc != null && enc.ContainsKey("index"))
				foreach (var sp in enc["index"].AsGodotArray())
					ordre.Add(sp.AsString());
			return ordre;
		}

		private void OnConceptChoisi(long index)
		{
			// Index 0 = « (tous) » → pas de filtre ; sinon le libellé exact.
			_filtreConcept = index == 0 ? null : _selecteur.GetItemText((int)index);
			ReconstruireListe();
		}

		private void OnEspeceChoisie(long index)
		{
			// Index 0 = « (toutes) » → pas de filtre ; sinon la clé catalogue exacte.
			_filtreEspece = index == 0 ? null : _selecteurEspece.GetItemText((int)index);
			ReconstruireListe();
		}

		// (Re)peuple _liste avec les entrées renvoyées par le pont pour le filtre
		// courant. Vide le conteneur d'abord (changement de filtre).
		private void ReconstruireListe()
		{
			foreach (Node enfant in _liste.GetChildren())
				enfant.QueueFree();

			var entrees = Bridge.Carnet(_filtreConcept, _filtreEspece);
			if (entrees.Count == 0)
			{
				_liste.AddChild(new Label { Text = "(aucune note pour ce filtre)" });
				return;
			}

			foreach (var ev in entrees)
				AjouterEntree(ev.AsGodotDictionary());
		}

		// Une entrée = deux lignes : en-tête « semaine · concept », puis le texte
		// verbatim. Registre « interprétatif » → texte en italique (BBCode), sans
		// modifier un seul caractère du verbatim.
		private void AjouterEntree(Godot.Collections.Dictionary e)
		{
			int semaine = e["semaine"].AsInt32();
			string concept = e["concept"].AsString();
			string registre = e["registre"].AsString();
			string texte = e["texte"].AsString();

			var entete = new Label { Text = $"semaine {semaine} · {concept}" };
			entete.AddThemeFontSizeOverride("font_size", 14);
			_liste.AddChild(entete);

			var corps = new RichTextLabel
			{
				BbcodeEnabled = true,
				FitContent = true,
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
			};
			// RichTextLabel interprète le BBCode : on ÉCHAPPE d'abord tout crochet
			// du verbatim (`[` → `[lb]`) pour qu'aucun caractère du texte Python ne
			// soit pris pour une balise, puis on n'ajoute QUE la balise de style.
			string sur = texte.Replace("[", "[lb]");
			corps.Text = registre == "interprétatif" ? $"[i]{sur}[/i]" : sur;
			_liste.AddChild(corps);

			_liste.AddChild(new HSeparator());
		}
	}
}
