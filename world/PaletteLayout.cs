// SYMBIOSE — PaletteLayout.cs (persistance du layout de la palette, T1)
// Le layout des SLOTS de la palette de gestes, persisté GLOBALEMENT dans
// `user://palette.json` (survit au retour à l'écran d'accueil, D2). On sérialise
// PAR VERBE et non par index de Gestes[] : robuste à tout réordonnancement futur
// de la table des gestes (un index déplacé n'invaliderait pas le fichier).
//
// 📖 Pédagogie Godot/C# :
//  - `user://` = dossier de données utilisateur (persistant, hors du .pck du jeu).
//  - FileAccess.Open renvoie null en cas d'échec (pas d'exception) : on teste.
//  - `using var f` ferme/flush le fichier à la sortie du bloc (RAII C#).
//  - Format : { "slots": ["arroser", "", "planter", …] } — 10 entrées, la chaîne
//    vide marquant un slot vide. Un seul fichier, une seule responsabilité (I/O).

using Godot;

namespace Symbiose
{
	internal static class PaletteLayout
	{
		private const string Chemin = "user://palette.json";

		// Écrit les verbes par slot (chaîne vide = slot vide). Silencieux si le
		// disque refuse (le layout reste correct en mémoire pour la session).
		public static void Sauver(string[] verbs)
		{
			var arr = new Godot.Collections.Array();
			foreach (var v in verbs) arr.Add(v ?? "");
			using var f = FileAccess.Open(Chemin, FileAccess.ModeFlags.Write);
			if (f == null)
			{
				GD.PrintErr($"[PaletteLayout] écriture impossible : {Chemin}");
				return;
			}
			f.StoreString(Json.Stringify(
				new Godot.Collections.Dictionary { ["slots"] = arr }));
		}

		// Relit les verbes par slot, ou null si aucun fichier (première partie) ou
		// contenu illisible → l'appelant retombe sur l'auto-remplissage seul.
		public static string[] Charger()
		{
			if (!FileAccess.FileExists(Chemin)) return null;
			using var f = FileAccess.Open(Chemin, FileAccess.ModeFlags.Read);
			if (f == null) return null;
			var parsed = Json.ParseString(f.GetAsText());
			if (parsed.VariantType != Variant.Type.Dictionary) return null;
			var dict = parsed.AsGodotDictionary();
			if (!dict.ContainsKey("slots")) return null;
			var arr = dict["slots"].AsGodotArray();
			var verbs = new string[arr.Count];
			for (int i = 0; i < arr.Count; i++) verbs[i] = arr[i].AsString();
			return verbs;
		}
	}
}
