// SYMBIOSE — PagesPanel.cs (sprint UI voix, tronçon ④)
// Spécialisation de VoicePanel : les PAGES SECRÈTES du coffret au grenier. Voix
// MULTIPLES (poème, savoir paysan, herbier, citation…), lore pur, registre
// téléologique ASSUMÉ. Chaque page trouvée est affichée VERBATIM depuis le pont
// Python (SimBridge.Pages) — le C# ne fabrique, ne corrige, ne reformule aucun
// texte (INVARIANT « Godot bête », doc §1).
//
// 📖 Pédagogie Godot/C# :
//  - On hérite de VoicePanel et on surcharge Remplir() : l'ossature (fond, titre,
//    défilement, bouton Fermer) est déjà posée ; on ne peuple que `Contenu`.
//  - Ce panneau est un LECTEUR PUR : il ne révèle AUCUNE page. Les pages
//    arrivent par le robinet « récompense » au palier (câblé côté pont, ①). Rien
//    à muter ici.
//  - Le champ `voix` (registre éditorial de la page) STYLE l'en-tête sans
//    toucher au texte du corps : le lecteur voit d'où parle la page, mais le
//    texte reste identique au verbatim Python.
//  - RichTextLabel + BBCode : on ÉCHAPPE d'abord tout crochet du verbatim
//    (`[` → `[lb]`) pour qu'aucun caractère du texte Python ne soit pris pour une
//    balise — comme dans CarnetPanel.

using Godot;

namespace Symbiose
{
	public partial class PagesPanel : VoicePanel
	{
		protected override void Remplir()
		{
			var resp = Bridge.Pages();
			// `pages` = list de {id, voix, concept, texte} déjà dans l'ORDRE
			// éditorial du corpus (le pont ne trie pas « intelligemment »).
			var pages = resp?["pages"].AsGodotArray() ?? new Godot.Collections.Array();
			if (pages.Count == 0)
			{
				Contenu.AddChild(new Label
				{
					Text = "(le coffret du grenier est encore vide)",
				});
				return;
			}

			foreach (var pv in pages)
				AjouterPage(pv.AsGodotDictionary());
		}

		// Une page = en-tête « voix · concept » (le registre éditorial) puis le
		// texte verbatim. Le texte n'est jamais modifié — seul l'en-tête situe la
		// voix qui parle.
		private void AjouterPage(Godot.Collections.Dictionary p)
		{
			string voix = p["voix"].AsString();
			string concept = p["concept"].AsString();
			string texte = p["texte"].AsString();

			var entete = new Label { Text = $"— {voix} · {concept} —" };
			entete.AddThemeFontSizeOverride("font_size", 15);
			Contenu.AddChild(entete);

			var corps = new RichTextLabel
			{
				BbcodeEnabled = true,
				FitContent = true,
				SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
				CustomMinimumSize = new Vector2(660, 0),
			};
			// Crochets du verbatim échappés → aucun caractère du corpus pris pour
			// une balise ; le corps des pages est en italique (registre poétique/
			// ésotérique assumé), sans altérer un seul caractère du texte.
			string sur = texte.Replace("[", "[lb]");
			corps.Text = $"[i]{sur}[/i]";
			Contenu.AddChild(corps);

			Contenu.AddChild(new HSeparator());
		}
	}
}
