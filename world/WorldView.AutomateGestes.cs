// SYMBIOSE — WorldView.AutomateGestes.cs (partial de WorldView, GESTES LISIBLES ⑤)
// ON VOIT CE QUE FAIT L'AUTOMATE, même onglet fermé :
//  - ses GESTES du dernier tick sont joués dans le monde, au point visé, avec les images
//    de l'outil (GesteMonde) — étalés dans le temps, nombre borné ;
//  - un TÉMOIN discret (l'icône de son dernier geste, coin haut-droit, aucun chiffre)
//    dit qu'il est branché.
//
// Source unique : le bloc `automate` du snapshot (pont 0.6.16) — chaque ligne `geste`
// porte `tile_id`, `geste` (verbe), `resultat`, `semaine` et `point` (cm tuile-local,
// null pour un geste sans lieu). La vue ne rejoue QUE ce qui a porté (résultat ≠ échec)
// et ne place rien que le moteur n'ait situé. Les traces au sol arrivent par
// `traces_sol` (le moteur les écrit pour l'automate comme pour le joueur).

using System.Collections.Generic;
using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		private const int GestesAutomateMax = 6;        // sprites vivants au plus (et par tick)
		private const double GestesAutomateEcartSec = 0.45;   // étalement entre deux départs
		private const int TemoinAutomateEchelle = 2;     // comme le curseur

		private int _automateSemaineVue = -1;            // dernier tick déjà joué à l'écran
		private readonly List<GesteMonde> _gestesAutomate = new();
		private TextureRect _temoinAutomate;
		private string _temoinVerbe;

		/// <summary>Appelé avec chaque bloc `automate` : joue les gestes du DERNIER tick
		/// (une seule fois), puis met le témoin à l'icône du dernier geste.</summary>
		private void JouerGestesAutomate(GDict block)
		{
			var trace = block["trace"].AsGodotArray();
			int derniere = -1;
			foreach (var v in trace)
			{
				var e = v.AsGodotDictionary();
				if (EstGesteJoue(e)) derniere = Mathf.Max(derniere, e["semaine"].AsInt32());
			}
			if (derniere <= _automateSemaineVue) return;
			_automateSemaineVue = derniere;
			_gestesAutomate.RemoveAll(g => !IsInstanceValid(g));
			int lances = 0;
			foreach (var v in trace)
			{
				var e = v.AsGodotDictionary();
				if (!EstGesteJoue(e) || e["semaine"].AsInt32() != derniere) continue;
				_temoinVerbe = e["geste"].AsString();
				if (_gestesAutomate.Count >= GestesAutomateMax) continue;
				if (PoserGesteMonde(e, lances * GestesAutomateEcartSec)) lances++;
			}
			MajTemoinAutomate();
			GD.Print($"[Automate] semaine {derniere} : {lances} geste(s) joué(s) au monde (image {Engine.GetFramesDrawn()}).");
		}

		// Un geste qui a porté (pas un échec), situé par le moteur (`point` non nul).
		private static bool EstGesteJoue(GDict e) =>
			e.ContainsKey("categorie") && e["categorie"].AsString() == "geste"
			&& e["resultat"].AsString() != "echec"
			&& e.ContainsKey("point") && e["point"].VariantType == Variant.Type.Array;

		// Le sprite de l'outil au point visé (cm tuile-local → monde → écran, relief compris).
		private bool PoserGesteMonde(GDict e, double retardSec)
		{
			string verbe = e["geste"].AsString();
			string tuile = e["tile_id"].AsString();
			if (_objects == null || _origins == null || !_origins.TryGetValue(tuile, out Vector2 o)) return false;
			Texture2D[] images = AnimationGeste.TexturesMonde(verbe, 1);
			if (images == null || !IconesPointsChauds.PointsChauds.TryGetValue(verbe, out var chaud)) return false;
			var p = e["point"].AsGodotArray();
			float lx = (float)p[0].AsDouble(), ly = (float)p[1].AsDouble();
			float rise = ReliefRiseAtPlot(tuile, (int)(ly / PlotCm), (int)(lx / PlotCm));
			var g = new GesteMonde
			{
				Name = $"geste_auto_{verbe}",
				// +1 px en Y : devant la plante visée (même pied) dans le tri en Y.
				Position = WorldToScreen(o.X + lx, o.Y + ly) + new Vector2(0f, 1f - rise),
				ZIndex = ZObjet(o.X + lx, o.Y + ly),
			};
			g.Init(images, new Vector2(chaud.X + 0.5f, chaud.Y + 0.5f), retardSec);
			_objects.AddChild(g);
			_gestesAutomate.Add(g);
			return true;
		}

		// Témoin « l'automate tourne » : l'icône de son dernier geste, discrète, en haut à
		// droite sous le témoin de build ; visible tant qu'il est branché, onglet fermé ou non.
		private void MajTemoinAutomate()
		{
			if (_temoinAutomate == null)
			{
				var calque = new CanvasLayer { Layer = 9, Name = "TemoinAutomate" };
				AddChild(calque);
				_temoinAutomate = new TextureRect
				{
					Position = new Vector2(1920f - 16f - 16f * TemoinAutomateEchelle, 34f),
					MouseFilter = Control.MouseFilterEnum.Ignore,
					TooltipText = "jardinier automate branché (A pour le débrancher)",
				};
				calque.AddChild(_temoinAutomate);
			}
			_temoinAutomate.Texture = IconeGeste.Texture(_temoinVerbe ?? "arroser", TemoinAutomateEchelle);
			_temoinAutomate.Visible = _automateOn;
		}
	}
}
