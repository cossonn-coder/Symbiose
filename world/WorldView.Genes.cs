// SYMBIOSE — WorldView.Genes.cs (partial de WorldView, sprint DIVERSITÉ FONDATRICE ③)
// Le SURVOL GÈNES (debug). Pointer une plante affiche son vecteur de gènes de
// RYTHME (`vigueur`, `germination_thermique`, `phenologie_florale`) — l'outil qui
// laisse Nico corréler au F5 « ce tournesol-ci est en avance » ↔ « ses gènes de
// rythme ». Instrument d'observation, étiqueté debug (philo #5 : chiffres tolérés
// hors HUD final), toggle G, caché par défaut.
//
// 📖 Pédagogie — on RÉUTILISE le picking de survol des étiquettes/observation
// (FindPlant sur la souris, WorldView.Actions.cs) : là on AFFICHE le nom, ici on
// LIT la Meta "genes" posée à l'ApplySnapshot (WorldView.Snapshot.cs) et on la met
// en texte. Zéro requête pont : le snapshot porte déjà les gènes (serialize.py ③).
// Les gènes sont un DÉRIVÉ de l'état moteur (patrimoine de l'instance), la vue ne
// les recalcule pas — elle les relit, comme le nom ou les symptômes.

using Godot;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Label du survol gènes (créé dans BuildHud, dans le CanvasLayer "Hud").
		private Label _genesLabel;
		private bool _genesHoverOn;

		// Gènes de RYTHME mis en avant (les autres restent lisibles au besoin, mais
		// ce sont ces trois-là que le sprint donne à VOIR — cf. kickoff ③).
		private static readonly string[] GenesRythme =
			{ "vigueur", "germination_thermique", "phenologie_florale" };

		// Toggle G : affiche/masque le survol gènes (instrument debug).
		private void ToggleGenesHover()
		{
			_genesHoverOn = !_genesHoverOn;
			if (_genesLabel != null)
			{
				_genesLabel.Visible = _genesHoverOn;
				if (!_genesHoverOn) _genesLabel.Text = "";
			}
			GD.Print($"[WorldView] survol gènes (debug) : {(_genesHoverOn ? "ON" : "OFF")}.");
		}

		// Appelée chaque frame (_Process) quand le survol gènes est actif : lit la
		// plante sous le curseur et affiche ses gènes de rythme. Aucune plante sous
		// la souris (ou sans gènes, snapshot pré-③) → ligne d'invite discrète.
		private void UpdateGenesHover()
		{
			if (!_genesHoverOn || _genesLabel == null) return;
			var node = FindPlant(ScreenToWorld(WorldMouseCanvas()), HoverRadiusCm);
			if (node == null || !IsInstanceValid(node) || !node.HasMeta("genes"))
			{
				_genesLabel.Text = "[gènes] survole une plante";
				return;
			}
			var genes = node.GetMeta("genes").AsGodotDictionary();
			string species = node.GetMeta("species", "?").AsString();
			var sb = new System.Text.StringBuilder();
			sb.Append($"[gènes] {species}");
			// Gènes de rythme d'abord (l'objet du sprint), formatés à 2 déc.
			foreach (var g in GenesRythme)
				if (genes.ContainsKey(g))
					sb.Append($"\n  {g} : {genes[g].AsDouble():F2}");
			_genesLabel.Text = sb.ToString();
		}
	}
}
