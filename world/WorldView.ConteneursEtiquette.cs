// SYMBIOSE — WorldView.ConteneursEtiquette.cs (partial de WorldView, ⑥c)
// L'ÉTIQUETTE de survol d'un CONTENEUR de culture : au survol d'un pot/bac, une
// petite étiquette NETTE (comme celles des plantes, hors SubViewport pixel-art)
// donne le SUBSTRAT, le VOLUME en mots et un état QUALITATIF du mini-sol dérivé
// d'`eco_summary` — JAMAIS de chiffre (philo #5 : indices, pas de barres ; les
// nombres bruts restent au mode debug overlay F6). L'indice suggère, il n'impose
// pas (philo #6).
//
// 📖 Pédagogie — pourquoi une étiquette SÉPARÉE des plantes : le pool de Labels
// d'Etiquettes.cs sert les plantes (index 0..N) ; on ajoute UN Label dédié au
// conteneur survolé pour ne pas se marcher dessus. Même couche (PlantLabels,
// nette hors viewport), même reprojection monde→fenêtre (WorldToWindow). Lecture
// SEULE : on mappe des scalaires moteur (humidité/N/microbiome…) sur des MOTS
// (« humide / sec », « pauvre / riche », « fond ouvert »). Aucun recalcul écolo.

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Le Label dédié au conteneur sous le curseur (créé à la demande, caché
		// quand aucun conteneur n'est survolé). Vit sur la couche nette PlantLabels.
		private Label _containerLabel;
		// Rayon de survol d'un conteneur (cm) — généreux, comme les plantes.
		private const float ContainerHoverRadiusCm = 45f;

		// Appelée chaque frame (depuis _Process, après les étiquettes de plantes).
		// Affiche/cache l'étiquette du conteneur le plus proche du curseur.
		private void UpdateContainerLabel()
		{
			if (_plantLabels == null) return;
			if (_containerLabel == null) BuildContainerLabel();
			if (!_survolSale) return;   // clé de survol inchangée (T3)

			int idx = FindNearestContainer(_sourisMonde, ContainerHoverRadiusCm);
			if (idx < 0)
			{
				_containerLabel.Visible = false;
				return;
			}
			// Retrouve l'entrée par index snapshot (Index, pas position de liste —
			// ils coïncident à l'ApplyContainers, mais on reste explicite).
			foreach (var c in _containers)
			{
				if (c.Index != idx) continue;
				_containerLabel.Text = DescribeContainer(c.Info);
				_containerLabel.Position =
					WorldToWindow(WorldToScreen(c.XCm, c.YCm)) + new Vector2(-40f, -28f);
				_containerLabel.Visible = true;
				return;
			}
			_containerLabel.Visible = false;
		}

		// Une ligne diégétique : « <substrat>, <volume> · <fond> · <humidité> ·
		// <fertilité> ». Mots seuls, pas de chiffres. Ex. « terreau, petit pot ·
		// fond fermé · sol humide · sol riche ».
		private string DescribeContainer(ContainerInfo i)
		{
			string substrat = SubstratLisible(i.Substrat);
			string taille = i.Kind == "bac"
				? "bac"
				: (i.Volume <= NainVolumeSeuilL ? "petit pot" : "grand pot");
			string fond = i.FondOuvert ? "fond ouvert" : "fond fermé";
			return $"{substrat}, {taille}\n{fond} · {Humidite(i.Humidite)} · "
				 + $"{Fertilite(i.N, i.P, i.K)}";
		}

		// Substrat → libellé naturel (clé moteur world/substrat.py → français).
		private static string SubstratLisible(string s) => s switch
		{
			"terreau" => "terreau",
			"compost" => "compost",
			"drainant_mineral" => "mélange drainant",
			"lasagnes" => "lasagnes",
			"terre_jardin" => "terre du jardin",
			"mycelium_use" => "substrat fongique",
			_ => s,
		};

		// Humidité du mini-sol → mot (seuils qualitatifs, calibrage F5).
		private static string Humidite(float h) =>
			h < 0.30f ? "sol sec" : h > 0.65f ? "sol humide" : "sol frais";

		// Fertilité globale (N/P/K, facteur limitant de Liebig = le plus bas) → mot.
		// On reflète le NUTRIMENT LIMITANT, fidèle à la loi du minimum du moteur.
		private static string Fertilite(float n, float p, float k)
		{
			float min = Mathf.Min(n, Mathf.Min(p, k));
			return min < 0.30f ? "sol pauvre" : min > 0.65f ? "sol riche"
											  : "sol moyen";
		}

		// Crée le Label dédié, stylé comme ceux des plantes (net, contour noir).
		private void BuildContainerLabel()
		{
			_containerLabel = new Label { Visible = false };
			_containerLabel.AddThemeFontSizeOverride("font_size", 14);
			_containerLabel.AddThemeColorOverride(
				"font_color", new Color(1f, 0.96f, 0.82f, 0.95f));
			_containerLabel.AddThemeColorOverride("font_outline_color", Colors.Black);
			_containerLabel.AddThemeConstantOverride("outline_size", 5);
			_plantLabels.AddChild(_containerLabel);
		}
	}
}
