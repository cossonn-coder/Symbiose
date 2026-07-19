// SYMBIOSE — AtelierPanel.cs (acquisition des moyens d'agir ④)
// Spécialisation de VoicePanel : l'ATELIER de la maison normande, 5ᵉ fonction du
// hub. VITRINE des OUTILS (sécateur) et MATÉRIAUX (botte de paille) à acquérir
// contre Vigueur. Deux listes dans le même panneau, chacune avec son bouton
// « Acquérir » qui va JUSQU'AU BOUT (débit de Vigueur + effet moteur : marqueur
// `posseder_secateur` pour l'outil, stock de mulch pour le matériau).
//
// Jumeau du MagazinePanel (patron kickoff §Patron) : l'offre + un bouton d'achat
// Vigueur. Différences : deux catégories (outils/matériaux) au lieu d'une, pas de
// « fiche produit » à déplier (le pont expose déjà tout le registre au clic — cf.
// cmd_atelier), possession affichée pour l'outil (masque la re-acquisition).
//
// 📖 Pédagogie Godot/C# :
//  - On surcharge Remplir() (ossature de VoicePanel déjà posée) et on n'agit que
//    sur `Contenu`. Un seul panneau, on vide/re-peuple après un achat.
//  - L'ACQUISITION est la SEULE opération qui MUTE l'état, et elle passe par le
//    pont (SimBridge.AcheterOutil/AcheterMateriau → verbes `acheter_outil`/
//    `acheter_materiau`, chemin Vigueur UNIQUE). La vue ne pré-valide RIEN : le
//    pont gate l'offre + débite la Vigueur (hors offre / fonds → `achete=false`).
//  - Le `result` renvoyé porte `vigueur`/`vigueur_max` frais + `achete` : on ne
//    les recalcule pas, on les LIT (téléonomie stricte, « Godot bête »).
//
// Les seules chaînes fabriquées ici sont des ÉTIQUETTES de mise en page (coûts,
// feedback d'achat) — jamais du texte de voix.

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class AtelierPanel : VoicePanel
	{
		// Ligne d'état Vigueur en tête (rafraîchie après un achat). Les valeurs
		// viennent du bilan du pont ; -1 = « pas encore lu » (bandeau muet).
		private double _vigueur = -1;
		private double _vigueurMax = -1;

		protected override void Remplir()
		{
			AfficherVitrine();
		}

		// ---------------------------------------------------------------------
		// VITRINE — outils puis matériaux, un bouton d'acquisition par entrée
		// ---------------------------------------------------------------------

		private void AfficherVitrine()
		{
			ViderContenu();
			AjouterBandeauVigueur();

			var resp = Bridge.Atelier();
			if (resp == null)
			{
				Contenu.AddChild(new Label
				{
					Text = "(atelier indisponible : moteur injoignable ou binaire "
						 + "trop ancien)",
					AutowrapMode = TextServer.AutowrapMode.WordSmart,
					CustomMinimumSize = new Vector2(660, 0),
				});
				return;
			}

			AfficherOutils(resp["outils"].AsGodotArray());
			AfficherMateriaux(resp["materiaux"].AsGodotArray());
		}

		// OUTILS : chacun {cle, cout_vigueur, possede}. Possédé → étiquette inerte
		// (on n'offre pas de re-acquérir) ; sinon bouton « Acquérir ».
		private void AfficherOutils(Godot.Collections.Array outils)
		{
			var titre = new Label { Text = "Outils" };
			titre.AddThemeFontSizeOverride("font_size", 22);
			Contenu.AddChild(titre);

			if (outils.Count == 0)
			{
				Contenu.AddChild(new Label { Text = "(aucun outil à l'atelier)" });
				return;
			}

			foreach (var ov in outils)
			{
				var o = ov.AsGodotDictionary();
				string cle = o["cle"].AsString();
				double cout = o["cout_vigueur"].AsDouble();
				bool possede = o["possede"].AsBool();

				if (possede)
				{
					Contenu.AddChild(new Label { Text = $"{cle} — déjà possédé" });
					continue;
				}
				var b = new Button
				{
					Text = $"{cle}  (Vigueur {cout:F0})",
					Alignment = HorizontalAlignment.Left,
				};
				b.Pressed += () => AcquerirOutil(cle);
				Contenu.AddChild(b);
			}
		}

		// MATÉRIAUX : chacun {cle, nature, dose, cout_vigueur}. Consommable → jamais
		// « possédé » (on peut en racheter). Bouton « Acquérir ».
		private void AfficherMateriaux(Godot.Collections.Array materiaux)
		{
			var titre = new Label { Text = "Matériaux" };
			titre.AddThemeFontSizeOverride("font_size", 22);
			Contenu.AddChild(titre);

			if (materiaux.Count == 0)
			{
				Contenu.AddChild(new Label { Text = "(aucun matériau à l'atelier)" });
				return;
			}

			foreach (var mv in materiaux)
			{
				var m = mv.AsGodotDictionary();
				string cle = m["cle"].AsString();
				string nature = m["nature"].AsString();
				double dose = m["dose"].AsDouble();
				double cout = m["cout_vigueur"].AsDouble();

				var b = new Button
				{
					Text = $"{cle}  ({nature} ×{dose:0.##}, Vigueur {cout:F0})",
					Alignment = HorizontalAlignment.Left,
				};
				b.Pressed += () => AcquerirMateriau(cle);
				Contenu.AddChild(b);
			}
		}

		// ---------------------------------------------------------------------
		// ACQUISITION — le SEUL geste qui mute l'état, délégué au pont
		// ---------------------------------------------------------------------

		private void AcquerirOutil(string cle)
			=> Acquerir(Bridge.AcheterOutil(cle), $"outil {cle}");

		private void AcquerirMateriau(string cle)
			=> Acquerir(Bridge.AcheterMateriau(cle), $"matériau {cle}");

		// Traite le `result` d'un `acheter_*` : lit `achete`/`message`/Vigueur (le
		// pont possède la règle), rafraîchit le bandeau Vigueur puis recharge la
		// vitrine coiffée du feedback. On ne décide RIEN — on relaie le verdict.
		private void Acquerir(GDict resp, string quoi)
		{
			var result = resp?["result"];
			string message = $"acquisition impossible ({quoi} — moteur injoignable)";
			if (result != null && result.Value.VariantType == Variant.Type.Dictionary)
			{
				var r = result.Value.AsGodotDictionary();
				message = r["message"].AsString();
				// Vigueur rafraîchie depuis le bilan (jamais recalculée en C#).
				_vigueur = r["vigueur"].AsDouble();
				_vigueurMax = r["vigueur_max"].AsDouble();
				GD.Print($"[AtelierPanel] {quoi} : achete={r["achete"].AsBool()}.");
			}
			// Recharge la vitrine (le pont a mis à jour possession/stock) + feedback.
			AfficherVitrine();
			InsererFeedback(message, position: 0);
		}

		// ---------------------------------------------------------------------
		// Utilitaires de mise en page (calqués sur MagazinePanel)
		// ---------------------------------------------------------------------

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

		// Bandeau Vigueur en tête (muet tant qu'aucun achat n'a livré de bilan —
		// l'info Vigueur primaire vit au HUD, D54). Miroir de MagazinePanel.
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
