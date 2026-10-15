// SYMBIOSE — PlantRenderer.Meteo.cs (partial, sprint JARDIN VIVANT T4 — météo)
// Côté PLANTE de la météo animée : la VARIANTE de dessin que le temps qu'il
// fait impose à CETTE plante, cuite dans son image (PlantBaker, × ses poses de
// flexion T3) — jamais une déformation recalculée chaque frame.
//
//  · CANICULE : seule une plante qui porte DÉJÀ le symptôme moteur `secheresse`
//    (intensité i, sim/semiologie.py) répond — ses feuilles pendent davantage et
//    se referment (limbe rétréci) ∝ i. Sa voisine abritée/arrosée, sans le
//    symptôme, reste intacte : c'est l'hétérogénéité D104 (philo #7), lue dans
//    le snapshot, jamais inventée par la vue.
//  · PLUIE / ORAGE : feuillage alourdi (les extrémités retombent, ∝ hauteur dans
//    la plante et ∝ souplesse du port : l'herbacée ploie, l'arbre à peine) +
//    reflets humides (1-2 px clairs de la palette) ; puis se ressuie en quelques
//    secondes de jeu après l'épisode (MeteoPlantes, niveaux quantifiés).
//
// 📖 Pédagogie : la variante est un petit ÉTAT par plante (_heat, _wet). Il ne
// change qu'à un changement de météo ou de symptôme → la plante devient « sale »
// (Invalidate) et la FILE à budget (BakeQueue) la recuit — le début d'une averse
// salit tout le jardin, la file l'étale sur quelques frames, l'écran d'abord.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		// Canicule : affaissement SUPPLÉMENTAIRE (cm, à i = 1) par-dessus celui,
		// permanent, de la sécheresse (DroughtDroopCm) et fermeture du limbe
		// (largeur × (1 − HeatFoldMax·i)) : la feuille se roule, se tasse.
		private const float HeatDroopCm = 6f;
		private const float HeatFoldMax = 0.55f;
		// Pluie : retombée des extrémités (cm à l'apex, port souple, feuillage
		// trempé) ; part des feuilles qui portent un reflet (au hash, stable).
		private const float WetDroopCm = 4f;
		private const float GlintShare = 0.45f;
		private static readonly Color GlintColor = Palette16.MaitreBlanc;

		// Variante courante (copiée dans le pinceau, cf. CopyDrawStateTo).
		private float _heat;   // fermeture caniculaire ∈ [0,1] (= `secheresse` si canicule)
		private float _wet;    // humidité du feuillage ∈ [0,1] (niveau quantifié)

		/// <summary>Recalcule la variante météo de la plante (météo globale ×
		/// SES symptômes) ; la salit seulement si elle a changé.</summary>
		internal void RefreshMeteo()
		{
			bool vivante = string.IsNullOrEmpty(_deadStade) && _structure != null;
			float heat = vivante && MeteoPlantes.Canicule ? _drought : 0f;
			// Pas de feuilles (caduc en hiver) → rien à mouiller, rien à recuire.
			float wet = vivante && _structure.FoliageDensity > 0f ? MeteoPlantes.Wet : 0f;
			bool cold = RefreshCold(vivante);   // neige + givre (T5, PlantRenderer.Froid.cs)
			if (heat == _heat && wet == _wet && !cold) return;
			_heat = heat;
			_wet = wet;
			Invalidate();
		}

		/// <summary>Abaissement (cm) d'une feuille à la hauteur `z` : sécheresse
		/// (permanente) + canicule + poids de l'eau (croît vers l'apex).</summary>
		private float LeafDropCm(float z)
		{
			float drop = _drought * DroughtDroopCm + _heat * HeatDroopCm;
			if (_wet > 0f)
				drop += _wet * WetDroopCm * _raideur * Mathf.Clamp(z / _heightCm, 0f, 1f);
			return drop;
		}

		/// <summary>Ouverture du limbe (facteur de largeur) : 1 = étalé.</summary>
		private float LeafOpen => 1f - HeatFoldMax * _heat;

		/// <summary>Reflet humide : 1-2 pixels clairs côté lumière (sud écran)
		/// sur une part des feuilles, choisie au hash (les mêmes à chaque cuisson).</summary>
		private void DrawWetGlint(Vector2 c, float r, int i, int j)
		{
			if (_wet <= 0f || Hash01(41, i, j) >= _wet * GlintShare) return;
			// Taille en PIXELS pixel-art (grille interne = canvas × zoom) : 1 px aux
			// petits paliers, ~2-4 px aux grands — un reflet, pas une tache.
			float z = WorldView.CurrentZoom;
			float s = Mathf.Max(1f, Mathf.Round(r * 0.1f * z)) / z;
			Vector2 at = ((c + SouthDir() * (r * 0.35f) - new Vector2(0f, r * 0.2f)) * z).Floor() / z;
			DrawRect(new Rect2(at, new Vector2(s, s)), GlintColor);
			// Deuxième pixel en goutte qui perle, sur une feuille sur deux.
			if (Hash01(43, i, j) < 0.5f)
				DrawRect(new Rect2(at + new Vector2(s, s), new Vector2(s, s)), GlintColor);
		}
	}
}
