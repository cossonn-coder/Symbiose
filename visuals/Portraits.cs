// SYMBIOSE — Portraits.cs (sprint PRÉCUISSON SPLATS ⑦)
// Les PORTRAITS d'espèce (D6) dans l'encyclopédie et le magazine. Trois portraits
// par espèce, cuits hors ligne en splats au ⑥ (`tools/splat/cuire_portraits.js`) :
// jeune · mûre en pleine saison · fin de cycle / hiver, 240×240, fond transparent.
// Le manifeste `assets/portraits/portraits.json` dit quel fichier montrer :
//   - encyclopédie : niveau de fiche 1 / 2 / 3 → jeune / mûre / fin ;
//   - magazine : le portrait mûr.
// Ce fichier ne décide d'AUCUN niveau : le niveau atteint arrive du pont (champ
// `niveau_max` de la fiche, existant) — aucune clé de pont nouvelle.
//
// 📖 Pédagogie Godot/C# :
//  - Le pont nomme une plante par sa CLÉ du catalogue Python (`tomate`,
//    `bourse_pasteur`) ; les portraits sont rangés par CLASSE (`Tomato`). Le
//    manifeste porte les deux (`cle`, écrite par l'outil depuis `plants/catalogue.py`)
//    → la correspondance vient de la vérité Python, pas d'une table recopiée ici.
//  - Chargement EXPORTABLE : `GD.Load<Texture2D>` lit la texture IMPORTÉE (comme
//    SpriteLoader : `.png.import` versionnés, compression sans perte, pas de mipmap).
//    Pas d'`Image.LoadFromFile` sur `res://` (qui ne marche pas une fois exporté).
//  - Pixel-art : affichage à échelle ENTIÈRE (×1 = 240 px, le panneau fait ~750 px)
//    et filtre Nearest posé sur le nœud (en plus du réglage projet).
//  - Le manifeste est lu UNE fois (cache statique) ; une espèce absente → aucun
//    portrait, jamais de crash.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public static class Portraits
	{
		private const string Dossier = "res://assets/portraits/";
		private const int Echelle = 1;   // entier : 240 px à l'écran

		// Clé du catalogue → entrée du manifeste ({port, jeune, mure, fin, cle}).
		private static Dictionary<string, GDict> _parCle;
		private static GDict _niveaux;   // "1" → "jeune"…
		private static string _etatMagazine = "mure";

		private static void Charger()
		{
			if (_parCle != null) return;
			_parCle = new Dictionary<string, GDict>();
			string chemin = Dossier + "portraits.json";
			if (!FileAccess.FileExists(chemin)) { GD.PushWarning($"[Portraits] manifeste absent : {chemin}"); return; }
			var m = Json.ParseString(FileAccess.GetFileAsString(chemin)).AsGodotDictionary();
			_niveaux = m["niveaux_encyclopedie"].AsGodotDictionary();
			_etatMagazine = m["magazine"].AsString();
			foreach (var (_, v) in m["especes"].AsGodotDictionary())
			{
				var e = v.AsGodotDictionary();
				if (e.TryGetValue("cle", out var cle) && cle.VariantType == Variant.Type.String)
					_parCle[cle.AsString()] = e;
			}
		}

		/// <summary>
		/// Rangée des portraits DÉVOILÉS d'une fiche d'encyclopédie : un portrait par
		/// niveau atteint (1 → jeune ; 2 → + mûre ; 3 → + fin de cycle), dans l'ordre
		/// du cycle de vie. null si l'espèce n'a pas de portrait.
		/// </summary>
		public static Control Rangee(string cle, int niveauAtteint)
		{
			Charger();
			if (!_parCle.TryGetValue(cle, out var e) || _niveaux == null) return null;
			var rangee = new HBoxContainer();
			for (int n = 1; n <= niveauAtteint; n++)
			{
				if (!_niveaux.TryGetValue(n.ToString(), out var etat)) continue;
				var vignette = Vignette(e, etat.AsString());
				if (vignette != null) rangee.AddChild(vignette);
			}
			return rangee.GetChildCount() > 0 ? rangee : null;
		}

		/// <summary>Portrait mûr d'une offre du magazine (D6). null si absent.</summary>
		public static Control Magazine(string cle)
		{
			Charger();
			return _parCle.TryGetValue(cle, out var e) ? Vignette(e, _etatMagazine) : null;
		}

		// Un portrait + son libellé (« jeune », « hiver (nu) »… — étiquette de mise en
		// page écrite au manifeste par l'outil, pas une voix).
		private static Control Vignette(GDict e, string etat)
		{
			if (!e.TryGetValue(etat, out var v)) return null;
			var d = v.AsGodotDictionary();
			var tex = GD.Load<Texture2D>(Dossier + d["fichier"].AsString());
			if (tex == null) return null;
			// ShrinkBegin : dans la colonne du panneau, la vignette garde sa largeur
			// (sinon elle s'étire et le libellé se centre loin du portrait).
			var boite = new VBoxContainer { SizeFlagsHorizontal = Control.SizeFlags.ShrinkBegin };
			boite.AddChild(new TextureRect
			{
				Texture = tex,
				TextureFilter = CanvasItem.TextureFilterEnum.Nearest,
				ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
				StretchMode = TextureRect.StretchModeEnum.Keep,
				CustomMinimumSize = tex.GetSize() * Echelle,
			});
			var libelle = new Label { Text = d["libelle"].AsString(), HorizontalAlignment = HorizontalAlignment.Center };
			libelle.AddThemeFontSizeOverride("font_size", 12);
			boite.AddChild(libelle);
			return boite;
		}
	}
}
