// SYMBIOSE — PlantRenderer.Limbes.cs (partial, sprint BOIS & ARBRES ③ — rubans des graminées)
// Le LIMBE CUIT des graminées, plaqué sur chaque brin que pose PoserBrin (dactyle, fétuque, rubans
// du chaume, rosettes à ruban) : nervures parallèles en ombre, cœur clair, bords soulignés
// (tools/splat/recettes/limbe_graminee.js, bandes chargées par BandesCuites). Même primitive que
// l'écorce du bois (RubanTexture.PoserBandePeriodique), même règle (décision C3 du ②) : la bande
// ne porte que des TONS plats, le ton de base est transparent → le brin garde sa teinte (espèce,
// saison, santé, givre), son ton et sa face orientée ; seules les marques s'y posent.
//
// La GÉOMÉTRIE reste celle de la vue : PoserBrin remplit les points, demi-largeurs et normales de
// son arc (projeté point par point par Iso, qui plie le brin au vent) et la bande les épouse. Une
// pièce fixe ne ploierait plus (constat du (a) ④bis). u en travers sur toute la largeur → les
// nervures convergent vers la pointe, comme sur une vraie feuille.
//
// Les marques sont VERSÉES dans le lot de la plante (_lotPrairie), juste après le brin : l'ordre de
// peinture est gardé (un brin devant recouvre les nervures du brin derrière), toujours UN envoi.
// Sous `LimbeMinPx` de large au pied (px internes) le brin reste uni, comme avant : à ×8 le dactyle
// (≈ 5 px) montrait des nervures d'un pixel en POINTILLÉ le long du brin oblique — du bruit, pas une
// feuille (capture VM du ③). D'où : dactyle, blé dès ×16 ; seigle, pâturin (≤ 1 cm) à ×32.
// Interrupteur Maj+F11 (TubeActif) : brin uni partout (dessin d'avant).
//
// Déterministe (pas d'aléa), purement visuel : golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private const float LimbeLargeMinCm = 1f;   // ≥ : bande « large » (1,5 cm), sinon « etroit » (0,6 cm)
		private const float LimbeMinPx = 7f;        // largeur au pied (px internes) dès laquelle le limbe se plaque [choix]

		private static readonly BandesCuites _limbes = new("limbes.json", "limbe");
		private static readonly System.Func<int, bool> TousLesQuads = _ => true;

		// L'arc du brin en cours, rempli par PoserBrin (réutilisé : la vue dessine un brin à la fois).
		private readonly Vector2[] _brinPts = new Vector2[SegmentsBrin + 1];
		private readonly Vector2[] _brinNrm = new Vector2[SegmentsBrin + 1];
		private readonly float[] _brinDemi = new float[SegmentsBrin + 1];
		private readonly float[] _brinV = new float[SegmentsBrin + 1];   // longueur d'arc, cm

		/// <summary>Plaque le limbe cuit sur l'arc du brin (`_brin*`) dans la palette de `teinte` ;
		/// `wi` = largeur du brin au pied en px internes.</summary>
		private void PlaquerLimbe(float largeurCm, float wi, Color teinte)
		{
			if (!TubeActif || wi < LimbeMinPx) return;
			string nom = largeurCm >= LimbeLargeMinCm ? "large" : "etroit";
			if (!_limbes.Trouver(nom, 0, WorldView.CurrentZoom, out var b)) return;
			bool idx = Indexe;
			Color mod = idx ? PaletteIndexee.ModulatePiece(PaletteIndexee.Palette(teinte)) : TeinteLitterale(teinte);
			RubanTexture.PoserBandePeriodique(_brinPts, _brinDemi, _brinNrm, _brinV, -1f, 1f, b.Tex,
				idx ? b.Codes : b.Litteral, b.PeriodeCm, 0f, mod, TousLesQuads);
			RubanTexture.Verser(_lotPrairie, b.Tex);
		}
	}
}
