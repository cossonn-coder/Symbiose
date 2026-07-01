// SYMBIOSE — EncyclopediePanel.cs (sprint UI voix, tronçon ③)
// Spécialisation de VoicePanel : l'ENCYCLOPÉDIE naturaliste du joueur. Deux vues
// dans le même panneau : un INDEX d'espèces découvertes (cliquables) et la FICHE
// d'une espèce (niveaux N1/N2/N3 débloqués). Tout le texte vient VERBATIM du pont
// Python (SimBridge.Encyclopedie) — le C# ne fabrique aucune phrase (INVARIANT
// « Godot bête », doc §1).
//
// 📖 Pédagogie Godot/C# :
//  - On surcharge Remplir() (ossature déjà posée par VoicePanel) et on n'agit
//    que sur `Contenu`. Naviguer index ↔ fiche = vider `Contenu` puis le
//    re-peupler ; pas de seconde scène, un seul panneau.
//  - L'INDEX = un bouton par espèce (SimBridge.Encyclopedie() sans argument →
//    `index` = list d'espèces palier ≥ 1, ordre corpus). Cliquer ouvre la fiche.
//  - La FICHE (SimBridge.Encyclopedie(espece) → `fiche` = {espece, niveau_max,
//    niveaux}) affiche les niveaux 1..niveau_max. Les niveaux non débloqués ne
//    sont PAS inventés (pas de placeholder textuel — le joueur ne les a pas).
//  - JSON → clés de dict en CHAÎNE : `niveaux` arrive indexé "1"/"2"/"3".

using Godot;

namespace Symbiose
{
	public partial class EncyclopediePanel : VoicePanel
	{
		// Titres des trois niveaux (mise en page seulement — ce ne sont pas des
		// voix : ce sont des étiquettes de rubrique, comme « semaine » au carnet).
		private static readonly string[] TitresNiveau =
			{ "", "Observation", "Biologie", "Écosystème" };

		protected override void Remplir()
		{
			AfficherIndex();
		}

		// ---------------------------------------------------------------------
		// INDEX — un bouton cliquable par espèce découverte
		// ---------------------------------------------------------------------

		private void AfficherIndex()
		{
			ViderContenu();

			var resp = Bridge.Encyclopedie();
			var index = resp?["index"].AsGodotArray() ?? new Godot.Collections.Array();
			if (index.Count == 0)
			{
				Contenu.AddChild(new Label
				{
					Text = "(aucune espèce découverte pour l'instant)",
				});
				return;
			}

			foreach (var esp in index)
			{
				string espece = esp.AsString();
				var b = new Button
				{
					Text = espece,
					Alignment = HorizontalAlignment.Left,
				};
				b.Pressed += () => AfficherFiche(espece);
				Contenu.AddChild(b);
			}
		}

		// ---------------------------------------------------------------------
		// FICHE — niveaux 1..niveau_max verbatim + retour à l'index
		// ---------------------------------------------------------------------

		private void AfficherFiche(string espece)
		{
			ViderContenu();

			// Barre de retour (l'index reste à un clic).
			var retour = new Button { Text = "◀ Retour à l'index" };
			retour.Pressed += AfficherIndex;
			Contenu.AddChild(retour);

			var resp = Bridge.Encyclopedie(espece);
			// Espèce non découverte / réponse nulle → message neutre, jamais de
			// crash (le pont renvoie `fiche = null` dans ce cas).
			var fiche = resp?["fiche"];
			if (fiche == null || fiche.Value.VariantType != Variant.Type.Dictionary)
			{
				Contenu.AddChild(new Label { Text = espece });
				Contenu.AddChild(new Label { Text = "(fiche non débloquée)" });
				return;
			}

			var f = fiche.Value.AsGodotDictionary();
			int niveauMax = f["niveau_max"].AsInt32();
			var niveaux = f["niveaux"].AsGodotDictionary();

			var titre = new Label { Text = f["espece"].AsString() };
			titre.AddThemeFontSizeOverride("font_size", 22);
			Contenu.AddChild(titre);

			// Niveaux 1..niveau_max, dans l'ordre. Clés JSON en chaîne ("1"…).
			for (int n = 1; n <= niveauMax; n++)
			{
				string cle = n.ToString();
				if (!niveaux.ContainsKey(cle))
					continue;   // robustesse : niveau manquant → on saute, pas de crash

				var rubrique = new Label { Text = $"N{n} — {TitresNiveau[n]}" };
				rubrique.AddThemeFontSizeOverride("font_size", 15);
				Contenu.AddChild(rubrique);

				Contenu.AddChild(new Label
				{
					Text = niveaux[cle].AsString(),   // VERBATIM
					AutowrapMode = TextServer.AutowrapMode.WordSmart,
					CustomMinimumSize = new Vector2(660, 0),
				});
			}
		}

		private void ViderContenu()
		{
			foreach (Node enfant in Contenu.GetChildren())
				enfant.QueueFree();
		}
	}
}
