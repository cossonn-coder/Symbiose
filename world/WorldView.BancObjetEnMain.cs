// SYMBIOSE — WorldView.BancObjetEnMain.cs (partial de WorldView, GESTES LISIBLES ④)
// BANC VM de l'objet en main et de la récolte au fruit. « Yeux » de l'agent sur la VM,
// pas un livrable joueur ; inactif sans l'argument.
//
//   tools/capture_vm.sh -b objet_en_main -w 0 -z 4 -c 1650,1650 -E bouturer@1475,1475 -s X,Y -n 80
//
// `-E VERBE@X,Y` : à 4 s le geste VERBE est armé et un 1er clic part au point MONDE X,Y
// (cm), par TryAction comme la souris du joueur (la source : la mère, le tas, le pot, le
// greffon) ; la souris revient ensuite sur `-s` → l'objet est porté là. `-E planter` seul
// arme le geste (catalogue des graines ouvert). Journal `[ObjetEnMain]`.
// `-E recolter` : sur la plante la plus proche de `-c`, clic sur un fruit MÛR, puis sur le
// collet, puis sur un fruit VERT ; une ligne de verdict par clic (message au HUD).

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly string CaptureObjet = ArgCapture("objet");
		private const float ObjetAttenteSec = 4f;

		// Appelé en fin d'AppliquerCapture.
		private void LancerBancObjetEnMain()
		{
			if (CaptureObjet == null) return;
			string[] a = CaptureObjet.Split('@');
			GetTree().CreateTimer(ObjetAttenteSec).Timeout += () =>
			{
				int g = IndexDuVerbe(a[0]);
				if (g < 0) { GD.Print($"[ObjetEnMain] verbe inconnu : {a[0]}"); return; }
				SelectGeste(g);
				if (a[0] == "recolter") { BancRecolte(); return; }
				if (a[0] == "planter") { BancCatalogue(a.Length > 1 ? a[1] : null); return; }
				if (a.Length > 1)
				{
					string[] p = a[1].Split(',');
					TryAction(WorldToScreen(ParseFloat(p[0]), ParseFloat(p[1])), false);
				}
				GD.Print($"[ObjetEnMain] {a[0]} : en main = {VerbeEnMain() ?? "rien"} · « {_lastActionMsg} »");
				if (CaptureSouris == null) return;
				string[] s = CaptureSouris.Split(',');
				Input.WarpMouse(new Vector2(ParseFloat(s[0]), ParseFloat(s[1])));
				ResemerSouris();
			};
		}

		// Catalogue des graines : ouvert à l'armement, on choisit la 3ᵉ graine comme d'un
		// clic (il doit se refermer sur elle), puis `planter` sur le point X,Y (un pot).
		private void BancCatalogue(string point)
		{
			GD.Print($"[ObjetEnMain] catalogue ouvert : {_reglagesPastilles.Count} graines · {string.Join(",", _seeds.ConvertAll(s => s.Key))}");
			GetTree().CreateTimer(2f).Timeout += () =>
			{
				if (_reglagesPastilles.Count > 2) _reglagesPastilles[2].EmitSignal(BaseButton.SignalName.Pressed);
				GD.Print($"[ObjetEnMain] choix → {_reglagesPastilles.Count} pastille(s), graine {_seeds[_seedIndex].Key}");
				if (point == null) return;
				string[] p = point.Split(',');
				TryAction(WorldToScreen(ParseFloat(p[0]), ParseFloat(p[1])), false);
				GetTree().CreateTimer(2f).Timeout += () =>
					GD.Print($"[ObjetEnMain] planter sur le pot → « {_lastActionMsg} »");
			};
		}

		// Trois clics sur la plante fruitière la plus proche du centre : fruit mûr, collet,
		// fruit vert. Un intervalle entre deux (le pont répond, le snapshot revient).
		private void BancRecolte()
		{
			PlantRenderer plante = null;
			float best = float.MaxValue;
			Vector2 centre = ScreenToWorld(_camera.Position);
			foreach (var n in _plantNodes.Values)
			{
				if (n.NombreFruits == 0) continue;
				float d = n.Position.DistanceSquaredTo(WorldToScreen(centre.X, centre.Y));
				if (d < best) { best = d; plante = n; }
			}
			if (plante == null) { GD.Print("[ObjetEnMain] recolter : aucune plante à fruits."); return; }
			int mur = -1, vert = -1;
			for (int i = 0; i < plante.NombreFruits; i++)
			{
				bool estMur = plante.DistanceFruitMur(plante.PointFruitCanvas(i)) < float.PositiveInfinity;
				if (estMur && mur < 0) mur = i;
				if (!estMur && vert < 0) vert = i;
			}
			GD.Print($"[ObjetEnMain] recolter : {plante.Espece}, {plante.NombreFruits} fruits, mûr visé {mur}, vert visé {vert}.");
			var clics = new (string, Vector2?)[]
			{
				("fruit mûr", mur >= 0 ? plante.PointFruitCanvas(mur) : null),
				("collet", plante.Position),
				("fruit vert", vert >= 0 ? plante.PointFruitCanvas(vert) : null),
			};
			for (int k = 0; k < clics.Length; k++)
			{
				var (quoi, pt) = clics[k];
				GetTree().CreateTimer(3f * k).Timeout += () =>
				{
					if (pt == null) { GD.Print($"[ObjetEnMain] clic {quoi} : pas de cible."); return; }
					_lastActionMsg = "";
					TryAction(pt.Value, false);
					GetTree().CreateTimer(2f).Timeout += () =>
						GD.Print($"[ObjetEnMain] clic {quoi} → « {_lastActionMsg} »");
				};
			}
		}
	}
}
