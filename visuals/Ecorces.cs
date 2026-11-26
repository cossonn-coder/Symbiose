// SYMBIOSE — Ecorces.cs (sprint BOIS & ARBRES ② — écorces cuites)
// Le CHARGEUR des bandes d'écorce cuites par tools/splat/cuire_ecorces.js : 13 essences (les 12
// arbres + « Generique ») × 3 âges (rameau, branche, tronc) × 4 paliers (×4 → ×32), rangées
// dans une planche par palier (`assets/splats/ecorces_x<z>.png`) + `ecorces.json`.
//
// Une bande = un cylindre sculpté photographié de face, PÉRIODIQUE en hauteur (la période en
// cm est dans le manifeste). Elle ne porte que des TONS (crevasses, plaques, lenticelles), en
// orientation « plate » : le modelé du flanc (côté soleil) reste celui de la géométrie du tube
// (décision C3, maquette du ②, cf. 00_etat). Le ton de base (2) est rendu TRANSPARENT : la
// bande se pose PAR-DESSUS l'âme et les flancs orientés du tube, seules ses marques se voient.
//
// Chargement, texture (blanc + codes + littéral) : BandesCuites.cs (extrait au ③, partagé avec
// les limbes des graminées).
//
// 📖 Pédagogie (embarqué) : c'est un masque de sérigraphie posé sur une pièce déjà peinte —
// le masque ne dit QUE où mettre l'encre sombre ; la couleur de la pièce et son éclairage
// restent ceux d'en dessous.
//
// Déterministe (fichiers versionnés), purement visuel : golden non concerné.

namespace Symbiose
{
	internal static class Ecorces
	{
		public const int Rameau = 0, Branche = 1, Tronc = 2;
		public const string Generique = "Generique";

		private static readonly BandesCuites _jeu = new("ecorces.json", "rameau", "branche", "tronc");

		/// <summary>La bande `essence` × `age` au palier servi pour `zoom` (cf. BandesCuites).</summary>
		public static bool Trouver(string essence, int age, float zoom, out BandesCuites.Bande b) =>
			_jeu.Trouver(essence, age, zoom, out b);
	}
}
