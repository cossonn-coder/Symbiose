// SYMBIOSE — WorldView.BancCueillette.cs (partial de WorldView, FORMES DES PLANTES ④)
// BANC VM de la récolte au clic sur un fruit de PORT. Un tronçon qui promet « récoltable au clic »
// n'est vérifié que si le clic part vraiment : le banc arme le geste manger, clique LÀ où le
// fruit est dessiné, en passant par TryAction comme la souris du joueur, puis lit la réponse du
// moteur sur le snapshot suivant. « Yeux » de l'agent sur la VM, pas un livrable joueur.
//
//   tools/capture_vm.sh -b planche_especes -w 0 -z 4 -c <x>,<y> -C -n 200
//
// Verdict au journal, une ligne par fruit visé : `[Cueillette] Strawberry fruit 2/4 → …`.
// Le premier passage ne fait que l'aller-retour position ↔ index, sans rien toucher ; il
// couvre tous les fruits. Le clic réel en consomme ensuite un, puis un deuxième, le dernier index.

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly bool CaptureCueillette = ArgCapture("cueillette") != null;
		private const float CueilletteAttenteSec = 4f;

		// Appelé en fin d'AppliquerCapture (caméra posée sur le point visé).
		private void LancerBancCueillette()
		{
			if (!CaptureCueillette) return;
			GetTree().CreateTimer(CueilletteAttenteSec).Timeout += () =>
			{
				Vector2 centre = ScreenToWorld(_camera.Position);
				PlantRenderer plante = FindPlant(centre, 1e4f);
				if (plante == null) { GD.Print("[Cueillette] aucune plante."); GetTree().Quit(); return; }
				int n = plante.NombreFruits;
				GD.Print($"[Cueillette] {plante.Espece} : {n} fruits à ×{CurrentZoom}.");
				int bons = 0;
				for (int i = 0; i < n; i++)
				{
					Vector2 p = plante.PointFruitCanvas(i);
					if (plante.FindFruitNear(p) == i && FindFruitPortSous(p) == plante) bons++;
					else GD.Print($"[Cueillette] fruit {i} : le clic vise {plante.FindFruitNear(p)}, plante {FindFruitPortSous(p)?.Espece ?? "aucune"}.");
				}
				GD.Print($"[Cueillette] position → index : {bons}/{n}.");
				if (n == 0) { GetTree().Quit(); return; }
				_gesteIndex = System.Array.FindIndex(Gestes, g => g.Item1 == "manger");
				CliquerFruit(plante, n - 1, n, () => CliquerFruit(plante, 0, plante.NombreFruits, () => GetTree().Quit()));
			};
		}

		private void CliquerFruit(PlantRenderer plante, int i, int avant, System.Action suite)
		{
			if (avant == 0) { suite(); return; }
			TryAction(plante.PointFruitCanvas(i), false);
			GetTree().CreateTimer(CueilletteAttenteSec).Timeout += () =>
			{
				GD.Print($"[Cueillette] clic sur le fruit {i} : {avant} → {plante.NombreFruits} fruits · « {_lastActionMsg} »");
				suite();
			};
		}
	}
}
