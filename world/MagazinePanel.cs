// SYMBIOSE — MagazinePanel.cs (sprint UI voix, tronçon ④)
// Spécialisation de VoicePanel : le MAGAZINE DE BOTANIQUE, 4ᵉ voix ET canal
// d'acquisition d'espèces. Deux vues dans le même panneau : la liste des OFFRES
// (sœurs des familles maîtrisées, hors banque) et la FICHE PRODUIT d'une offre,
// avec un bouton « Acheter » qui va JUSQU'AU BOUT (débit de Vigueur + graine en
// banque). Tout le texte vient VERBATIM du pont Python (SimBridge.Magazine…) ;
// le C# ne fabrique aucune phrase de voix (INVARIANT « Godot bête », doc §1).
//
// 📖 Pédagogie Godot/C# :
//  - On surcharge Remplir() (ossature déjà posée) et on n'agit que sur `Contenu`.
//    Naviguer offres ↔ fiche = vider `Contenu` puis le re-peupler ; un seul
//    panneau, pas de seconde scène (comme EncyclopediePanel).
//  - L'ACHAT est la SEULE opération qui MUTE l'état, et il passe par le pont
//    (SimBridge.AcheterMagazine → verbe `acheter_magazine`, chemin Vigueur
//    UNIQUE, Q3). La vue ne pré-valide RIEN : le pont gate l'offre et débite la
//    Vigueur (offre fermée / fonds insuffisants → `achete=false`, aucun effet).
//  - Le `bilan` renvoyé par l'achat porte `vigueur`/`vigueur_max` frais et
//    `achete` : on ne les recalcule pas, on les LIT (téléonomie stricte).
//
// Les seules chaînes fabriquées ici sont des ÉTIQUETTES de mise en page
// (« Vigueur : … », feedback d'achat) — jamais du texte de voix.

using Godot;

namespace Symbiose
{
	public partial class MagazinePanel : VoicePanel
	{
		// Ligne d'état Vigueur en tête (rafraîchie après un achat réussi). Les
		// valeurs viennent du bilan du pont ; -1 = « pas encore lu ».
		private double _vigueur = -1;
		private double _vigueurMax = -1;

		protected override void Remplir()
		{
			AfficherOffres();
		}

		// ---------------------------------------------------------------------
		// OFFRES — un bouton cliquable par sœur offerte
		// ---------------------------------------------------------------------

		private void AfficherOffres()
		{
			ViderContenu();
			AjouterBandeauVigueur();

			var offres = Bridge.MagazineOffres();
			if (offres.Count == 0)
			{
				Contenu.AddChild(new Label
				{
					Text = "(aucune offre : maîtrisez une famille pour "
						 + "que ses sœurs s'offrent)",
					AutowrapMode = TextServer.AutowrapMode.WordSmart,
					CustomMinimumSize = new Vector2(660, 0),
				});
				return;
			}

			foreach (var esp in offres)
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
		// FICHE PRODUIT — argument de vente verbatim + bouton Acheter
		// ---------------------------------------------------------------------

		private void AfficherFiche(string espece)
		{
			ViderContenu();

			var retour = new Button { Text = "◀ Retour aux offres" };
			retour.Pressed += AfficherOffres;
			Contenu.AddChild(retour);

			var resp = Bridge.MagazineFiche(espece);
			var fiche = resp?["fiche"];
			if (fiche == null || fiche.Value.VariantType != Variant.Type.Dictionary)
			{
				Contenu.AddChild(new Label { Text = espece });
				Contenu.AddChild(new Label { Text = "(fiche produit indisponible)" });
				return;
			}

			var f = fiche.Value.AsGodotDictionary();
			int niveauMax = f["niveau_max"].AsInt32();
			var niveaux = f["niveaux"].AsGodotDictionary();

			var titre = new Label { Text = f["espece"].AsString() };
			titre.AddThemeFontSizeOverride("font_size", 22);
			Contenu.AddChild(titre);

			// Niveaux 1..niveau_max, dans l'ordre. Clés JSON en chaîne ("1"…) —
			// VERBATIM, aucune synthèse (comme EncyclopediePanel).
			for (int n = 1; n <= niveauMax; n++)
			{
				string cle = n.ToString();
				if (!niveaux.ContainsKey(cle))
					continue;
				Contenu.AddChild(new Label
				{
					Text = niveaux[cle].AsString(),
					AutowrapMode = TextServer.AutowrapMode.WordSmart,
					CustomMinimumSize = new Vector2(660, 0),
				});
			}

			// Le geste d'achat : un seul bouton, tout le reste est au pont.
			var acheter = new Button { Text = "Acheter cette graine" };
			acheter.Pressed += () => Acheter(espece);
			Contenu.AddChild(acheter);
		}

		// ---------------------------------------------------------------------
		// ACHAT — le SEUL geste qui mute l'état, entièrement délégué au pont
		// ---------------------------------------------------------------------

		private void Acheter(string espece)
		{
			var resp = Bridge.AcheterMagazine(espece);
			// `result` = bilan {achete, vigueur, vigueur_max, message} ; le pont
			// possède la règle (gate offre + fonds). On LIT, on ne décide pas.
			var result = resp?["result"];
			bool achete = false;
			string message = "achat impossible (moteur injoignable)";
			if (result != null && result.Value.VariantType == Variant.Type.Dictionary)
			{
				var r = result.Value.AsGodotDictionary();
				achete = r["achete"].AsBool();
				message = r["message"].AsString();
				// Vigueur rafraîchie depuis le bilan (jamais recalculée en C#).
				_vigueur = r["vigueur"].AsDouble();
				_vigueurMax = r["vigueur_max"].AsDouble();
			}

			if (achete)
			{
				// Succès → l'offre disparaît (le pont l'a retirée : elle est
				// désormais en banque). On revient à la liste, forcément à jour.
				GD.Print($"[MagazinePanel] achat réussi : {espece}.");
				AfficherOffresAvecFeedback(message);
			}
			else
			{
				// Refus sobre : aucune mutation, on reste sur la fiche avec le
				// message du pont (offre fermée / Vigueur insuffisante).
				GD.Print($"[MagazinePanel] achat refusé : {espece}.");
				AfficherFicheAvecFeedback(espece, message);
			}
		}

		// Recharge les offres (le pont a retiré la sœur achetée) et coiffe la vue
		// d'un feedback d'achat, placé en tête. Le feedback est une étiquette de
		// mise en page — pas une voix.
		private void AfficherOffresAvecFeedback(string message)
		{
			AfficherOffres();
			InsererFeedback(message, position: 0);
		}

		// Re-affiche la fiche courante avec un message de refus juste sous le
		// bouton « Retour ».
		private void AfficherFicheAvecFeedback(string espece, string message)
		{
			AfficherFiche(espece);
			InsererFeedback(message, position: 1);
		}

		// Ajoute une étiquette de feedback puis la déplace à la `position` voulue
		// dans `Contenu` (MoveChild n'agit qu'après AddChild — l'ordre importe).
		private void InsererFeedback(string message, int position)
		{
			var fb = new Label
			{
				Text = message,
				AutowrapMode = TextServer.AutowrapMode.WordSmart,
				CustomMinimumSize = new Vector2(660, 0),
			};
			Contenu.AddChild(fb);
			Contenu.MoveChild(fb, position);
		}

		// ---------------------------------------------------------------------
		// Utilitaires de mise en page
		// ---------------------------------------------------------------------

		// Bandeau Vigueur en tête des offres. Tant qu'aucun achat n'a été tenté,
		// on n'a pas de bilan → on interroge le pont via une offre neutre serait
		// coûteux ; on affiche donc le bandeau seulement quand on connaît la
		// valeur (après un achat). Avant, le bandeau est muet (l'info Vigueur
		// primaire vit au HUD, D54).
		private void AjouterBandeauVigueur()
		{
			if (_vigueur < 0)
				return;
			var bandeau = new Label
			{
				Text = $"Vigueur : {_vigueur:F0} / {_vigueurMax:F0}",
			};
			bandeau.AddThemeFontSizeOverride("font_size", 15);
			Contenu.AddChild(bandeau);
		}

		private void ViderContenu()
		{
			foreach (Node enfant in Contenu.GetChildren())
				enfant.QueueFree();
		}
	}
}
