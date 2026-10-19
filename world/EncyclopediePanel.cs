// SYMBIOSE — EncyclopediePanel.cs (sprint Voix narratives ③ ; multi-règnes D60 ⑥)
// Spécialisation de VoicePanel : l'ENCYCLOPÉDIE naturaliste du joueur, désormais
// MULTI-RÈGNES (D60). Le même panneau porte trois vues : une BARRE DE 7 ONGLETS
// (plante · animal · champignon · concept · technique · outil · geste) qui filtre
// l'index par règne, un INDEX des entrées découvertes du règne courant
// (cliquables), et la FICHE d'une entrée. Tout le texte vient VERBATIM du pont
// Python (SimBridge.Encyclopedie) — le C# ne fabrique aucune phrase (INVARIANT
// « Godot bête », doc §1) : il met en page (onglets, sections, graphe).
//
// 📖 Pédagogie Godot/C# :
//  - On surcharge Remplir() (ossature déjà posée par VoicePanel) et on n'agit
//    que sur `Contenu`. Naviguer onglet ↔ index ↔ fiche = vider `Contenu` puis le
//    re-peupler ; pas de seconde scène, un seul panneau.
//  - L'INDEX est TAGUÉ (① a changé sa forme : liste de dicts {cle, type, titre},
//    plus de strings). On demande au pont l'index déjà FILTRÉ par type
//    (Bridge.Encyclopedie(type: …)) — « Godot bête » : le tri/filtre vit en
//    Python, la vue affiche. Le libellé d'un bouton = le champ `titre`.
//  - La FICHE (Bridge.Encyclopedie(cle) → {cle, type, niveau_max, niveaux,
//    interconnexions?}) se rend selon le type :
//      · plante/concept/technique/outil/geste → niveaux 1..niveau_max verbatim ;
//      · animal/champignon → MONO-niveau : blurb (N1) + section « Interconnexions »
//        (le graphe `interconnexions`). Pas de N2/N3 (cap palier 1).
//  - JSON → clés de dict en CHAÎNE : `niveaux` arrive indexé "1"/"2"/"3".

using Godot;

namespace Symbiose
{
	public partial class EncyclopediePanel : VoicePanel
	{
		// Les 8 onglets (règnes + signes, ⑦), dans l'ordre figé (taxonomie QA, kickoff ⑥). Une
		// paire {clé de type protocole, libellé d'onglet affiché}. La clé de type
		// est celle que le pont attend (`msg.type`) et que porte chaque entrée.
		private static readonly (string Type, string Libelle)[] Onglets =
		{
			("plante",     "Plantes"),
			("animal",     "Animaux"),
			("champignon", "Champignons"),
			("concept",    "Concepts"),
			("technique",  "Techniques"),
			("outil",      "Outils"),
			("geste",      "Gestes"),
			("signe",      "Signes"),   // fiche ouverte quand le signe est APPRIS (⑥/⑦)
		};

		// Titres des trois niveaux des fiches 3-niveaux (mise en page seulement — ce
		// ne sont pas des voix : ce sont des étiquettes de rubrique). Les fiches
		// mono (animal/champignon) n'utilisent PAS cette table (cf. AfficherFiche).
		private static readonly string[] TitresNiveau =
			{ "", "Observation", "Biologie", "Écosystème" };

		// Onglet courant : index dans `Onglets`. Défaut = plante (kickoff §À faire).
		private int _ongletActif = 0;

		protected override void Remplir()
		{
			AfficherIndex();
		}

		// ---------------------------------------------------------------------
		// BARRE D'ONGLETS — un bouton de filtre par règne, onglet actif surligné
		// ---------------------------------------------------------------------

		private void AjouterBarreOnglets()
		{
			var barre = new HBoxContainer();
			for (int i = 0; i < Onglets.Length; i++)
			{
				int idx = i;                          // capture par valeur (closure)
				var b = new Button
				{
					Text = Onglets[i].Libelle,
					// L'onglet actif reste cliquable mais désactivé (surbrillance
					// standard Godot du bouton disabled = repère visuel « ici »).
					Disabled = (i == _ongletActif),
				};
				b.Pressed += () => { _ongletActif = idx; AfficherIndex(); };
				barre.AddChild(b);
			}
			Contenu.AddChild(barre);
		}

		// ---------------------------------------------------------------------
		// INDEX — entrées découvertes du règne courant (boutons cliquables)
		// ---------------------------------------------------------------------

		private void AfficherIndex()
		{
			ViderContenu();
			AjouterBarreOnglets();

			string type = Onglets[_ongletActif].Type;
			// Index déjà FILTRÉ par le pont (« Godot bête » : pas de filtre local).
			var resp = Bridge.Encyclopedie(type: type);
			var index = resp?["index"].AsGodotArray() ?? new Godot.Collections.Array();
			if (index.Count == 0)
			{
				Contenu.AddChild(new Label
				{
					Text = "(rien de découvert dans cette catégorie)",
				});
				return;
			}

			foreach (var e in index)
			{
				var entree = e.AsGodotDictionary();
				string cle = entree["cle"].AsString();
				string titre = entree["titre"].AsString();
				var b = new Button
				{
					Text = titre,
					Alignment = HorizontalAlignment.Left,
				};
				b.Pressed += () => AfficherFiche(cle);
				Contenu.AddChild(b);
			}
		}

		// ---------------------------------------------------------------------
		// FICHE — dispatchée par type : 3-niveaux OU mono-niveau + graphe
		// ---------------------------------------------------------------------

		private void AfficherFiche(string cle)
		{
			ViderContenu();

			// Barre de retour (l'index du règne courant reste à un clic).
			var retour = new Button { Text = "◀ Retour à l'index" };
			retour.Pressed += AfficherIndex;
			Contenu.AddChild(retour);

			var resp = Bridge.Encyclopedie(cle);
			// Clé non découverte / réponse nulle → message neutre, jamais de crash
			// (le pont renvoie `fiche = null` dans ce cas).
			var fiche = resp?["fiche"];
			if (fiche == null || fiche.Value.VariantType != Variant.Type.Dictionary)
			{
				Contenu.AddChild(new Label { Text = cle });
				Contenu.AddChild(new Label { Text = "(fiche non débloquée)" });
				return;
			}

			var f = fiche.Value.AsGodotDictionary();

			var titre = new Label { Text = f["cle"].AsString() };
			titre.AddThemeFontSizeOverride("font_size", 22);
			Contenu.AddChild(titre);

			// Animal / champignon = fiche MONO-niveau à graphe (champ
			// `interconnexions`). Les autres = fiche 3-niveaux classique.
			if (f.ContainsKey("interconnexions"))
				AfficherFicheMono(f);
			else
				AfficherFicheNiveaux(f);
		}

		// Fiche 3-niveaux (plante · concept · technique · outil · geste) : niveaux
		// 1..niveau_max, dans l'ordre. Clés JSON en chaîne ("1"…).
		private void AfficherFicheNiveaux(Godot.Collections.Dictionary f)
		{
			int niveauMax = f["niveau_max"].AsInt32();
			var niveaux = f["niveaux"].AsGodotDictionary();

			for (int n = 1; n <= niveauMax; n++)
			{
				string cle = n.ToString();
				if (!niveaux.ContainsKey(cle))
					continue;   // robustesse : niveau manquant → on saute, pas de crash

				var rubrique = new Label { Text = $"N{n} — {TitresNiveau[n]}" };
				rubrique.AddThemeFontSizeOverride("font_size", 15);
				Contenu.AddChild(rubrique);

				AjouterTexte(niveaux[cle].AsString());
			}
		}

		// Fiche MONO-niveau (animal · champignon, cap palier 1) : le blurb (niveau 1)
		// puis une section « Interconnexions » listant le graphe `interconnexions`
		// (verbatim du pont — `faune_encyclo` / `champignon_encyclo`).
		private void AfficherFicheMono(Godot.Collections.Dictionary f)
		{
			var niveaux = f["niveaux"].AsGodotDictionary();
			if (niveaux.ContainsKey("1"))
				AjouterTexte(niveaux["1"].AsString());

			var liens = f["interconnexions"].AsGodotArray();
			if (liens.Count == 0)
				return;

			var rubrique = new Label { Text = "Interconnexions" };
			rubrique.AddThemeFontSizeOverride("font_size", 15);
			Contenu.AddChild(rubrique);

			foreach (var lien in liens)
				AjouterTexte($"• {lien.AsString()}");
		}

		// Un paragraphe de texte VERBATIM, mis en page (retour à la ligne souple,
		// largeur bornée). Factorise les trois rendus (niveaux, blurb, liens).
		private void AjouterTexte(string texte)
		{
			Contenu.AddChild(new Label
			{
				Text = texte,   // VERBATIM — aucune phrase fabriquée ici
				AutowrapMode = TextServer.AutowrapMode.WordSmart,
				CustomMinimumSize = new Vector2(660, 0),
			});
		}

		private void ViderContenu()
		{
			foreach (Node enfant in Contenu.GetChildren())
				enfant.QueueFree();
		}
	}
}
