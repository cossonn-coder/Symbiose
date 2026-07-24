// SYMBIOSE — CourrierPanel.cs (système de quêtes D79, tronçon ⑤)
// Spécialisation de VoicePanel : le COURRIER — les LETTRES du monde social qui
// posent des désirs (quêtes). Voix ÉPISTOLAIRE ANONYME (V1) : une plume signée
// d'un prénom, jamais un PNJ. Chaque lettre est affichée VERBATIM depuis le pont
// Python (SimBridge.Courrier) — le C# ne fabrique, ne reformule, ne juge aucun
// texte NI aucun avancement (INVARIANT « Godot bête », doc §1).
//
// 📖 Pédagogie Godot/C# :
//  - On hérite de VoicePanel et on surcharge Remplir() : l'ossature (fond,
//    défilement, onglet) est posée par la classe mère + le conteneur ; on ne
//    peuple que `Contenu`.
//  - LECTEUR PUR : ce panneau ne pose ni ne clôt aucune quête. L'arrivée des
//    lettres, la clôture et les récompenses vivent côté pont (driver `step_week`).
//    L'ouverture du panneau ÉVALUE juste les quêtes d'état (côté Python) ; ici on
//    ne fait qu'afficher ce que le pont renvoie.
//  - La COCHE (☑ / ✉) et la phrase d'AVANCEMENT viennent du pont : l'avancement est
//    DIÉGÉTIQUE (« ça y est presque »), JAMAIS un chiffre en primaire (#5). Le
//    chiffre exact n'existe qu'en mode debug (non demandé ici).
//  - RichTextLabel + BBCode : on ÉCHAPPE d'abord tout crochet du verbatim
//    (`[` → `[lb]`) pour qu'aucun caractère du texte Python ne soit pris pour une
//    balise — comme dans PagesPanel / CarnetPanel.

using Godot;

namespace Symbiose
{
	public partial class CourrierPanel : VoicePanel
	{
		protected override void Remplir()
		{
			// `Courrier()` = liste de {id, donneur, texte_lettre, avancement,
			// accomplie, atteignable}, déjà triée par id côté pont (on ne re-trie pas).
			var lettres = Bridge.Courrier();
			if (lettres.Count == 0)
			{
				Contenu.AddChild(new Label
				{
					Text = "(pas de courrier pour l'instant)",
				});
				return;
			}

			foreach (var lv in lettres)
				AjouterLettre(lv.AsGodotDictionary());
		}

		// Une lettre = en-tête (coche + donneur + état d'avancement diégétique) puis
		// le corps VERBATIM. Le texte n'est jamais modifié ; seul l'en-tête, fabriqué
		// à partir des DRAPEAUX du pont, situe l'état de la lettre.
		private void AjouterLettre(Godot.Collections.Dictionary l)
		{
			string donneur = l["donneur"].AsString();
			string texte = l["texte_lettre"].AsString();
			string avancement = l["avancement"].AsString();
			bool accomplie = l["accomplie"].AsBool();
			bool atteignable = l["atteignable"].AsBool();

			// Coche : ✉ (lettre en cours) → ☑ (désir comblé). L'en-tête porte le
			// prénom qui signe, l'avancement DIÉGÉTIQUE, et — si le rêve vise une
			// plante hors catalogue (kiwi, F3) — un discret signalement.
			string coche = accomplie ? "☑" : "✉";
			var entete = new Label { Text = $"{coche}  De {donneur} — {avancement}" };
			entete.AddThemeFontSizeOverride("font_size", 15);
			// Vert doux quand c'est comblé ; gris quand la plante rêvée n'existe pas
			// encore au jardin (rêve ouvert, jamais un échec, #4).
			if (accomplie)
				entete.AddThemeColorOverride("font_color", new Color(0.55f, 0.85f, 0.45f));
			else if (!atteignable)
				entete.AddThemeColorOverride("font_color", new Color(0.7f, 0.7f, 0.7f));
			Contenu.AddChild(entete);

			var corps = new RichTextLabel
			{
				BbcodeEnabled = true,
				FitContent = true,
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
				CustomMinimumSize = new Vector2(660, 0),
			};
			// Crochets du verbatim échappés → aucun caractère du corpus pris pour une
			// balise ; le corps épistolaire est en italique (registre « lettre »),
			// sans altérer un seul caractère du texte Python.
			string sur = texte.Replace("[", "[lb]");
			corps.Text = $"[i]{sur}[/i]";
			Contenu.AddChild(corps);

			Contenu.AddChild(new HSeparator());
		}
	}
}
