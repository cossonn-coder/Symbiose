// SYMBIOSE — WorldView.Couches.cs (partial de WorldView, sprint RENDU VISIBLE T1)
// BASCULE DE COUCHES debug (Shift+F4) : masque une famille de couches pour
// mesurer ce qu'elle coûte (lecture F4 : FPS + draw calls). Même mécanique
// pour le banc VM : `--capture-cacher=Nom1,Nom2` (WorldView.Capture.cs).
// Outil de MESURE, pas un réglage joueur : n'optimise rien.
//
// 📖 Pédagogie Godot/C# :
//  - Masquer = `Visible = false` sur le nœud racine d'une couche : Godot ne
//    dessine plus ce nœud NI ses enfants (le sous-arbre entier sort du rendu).
//    `CanvasItem` (Node2D, Control) et `CanvasLayer` ont chacun leur propre
//    propriété `Visible` — d'où le petit aiguillage par type plus bas.
//  - On retrouve les couches PAR NOM (`FindChild`, recherche récursive) : le
//    même nom sert à la touche et à l'argument du banc, et les nœuds RECRÉÉS
//    (Ground/Objects à chaque rotation, RebuildWorld) sont retrouvés sans
//    garder de référence périmée → on ré-applique après reconstruction.
//  - Retour au cas « tout » = état initial EXACT : on mémorise la visibilité
//    d'avant masquage (une couche déjà cachée, ex. vie macro par I, le reste).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView
	{
		// Noms vérifiés au `grep 'Name = "'` (2026-10-16). Sky est un enfant de
		// Weather ; Vignette = le dessin de l'encart ciel (SkyPanel).
		private static readonly string[] CouchesMacro = { "MacroLife", "ForagerLayer", "Carpophores" };
		private static readonly string[] CouchesSol =
			{ "Couverture", "Allelopathie", "Mulch", "Puddle", "Litter", "LeafLitter", "Snow", "Covers" };
		private static readonly string[] CouchesCiel = { "Weather", "Sky", "Vignette" };

		private static readonly (string Nom, string[] Couches)[] CasCouches =
		{
			("tout", new string[0]),
			("sans Sol", new[] { "Ground" }),
			("sans Décor", new[] { "Decor" }),
			("sans Objets (plantes+maison)", new[] { "Objects" }),
			("sans vie macro", CouchesMacro),
			("sans couches au sol", CouchesSol),
			("sans ciel/météo/vignette", CouchesCiel),
			("rien du monde", Union("Ground", "Decor", "Objects")),
		};

		private int _casCouches;
		// Visibilité d'AVANT masquage, par nœud masqué (restaurée au démasquage).
		private readonly Dictionary<Node, bool> _visAvantMasque = new();

		private static string[] Union(params string[] base_)
		{
			var l = new List<string>(base_);
			l.AddRange(CouchesMacro); l.AddRange(CouchesSol); l.AddRange(CouchesCiel);
			return l.ToArray();
		}

		private string NomCasCouches() =>
			CaptureCacher == null ? CasCouches[_casCouches].Nom
				: $"{CasCouches[_casCouches].Nom} + banc[{CaptureCacher}]";

		// Shift+F4 : cas suivant (boucle).
		private void CycleCouches()
		{
			_casCouches = (_casCouches + 1) % CasCouches.Length;
			AppliquerMasqueCouches();
			GD.Print($"[WorldView] Shift+F4 → couches : {NomCasCouches()}.");
		}

		// Noms à masquer = cas courant ∪ liste du banc (--capture-cacher).
		private HashSet<string> NomsMasques()
		{
			var s = new HashSet<string>(CasCouches[_casCouches].Couches);
			if (CaptureCacher != null)
				foreach (string n in CaptureCacher.Split(','))
					if (n.Length > 0) s.Add(n.Trim());
			return s;
		}

		// (Ré)applique le masque. Appelé au changement de cas, après la
		// construction du monde (AppliquerCapture) et après RebuildWorld.
		private void AppliquerMasqueCouches()
		{
			// 1) Démasquer ce qui ne doit plus l'être (et oublier les nœuds libérés).
			var masques = NomsMasques();
			foreach (var kv in new List<KeyValuePair<Node, bool>>(_visAvantMasque))
			{
				bool valide = GodotObject.IsInstanceValid(kv.Key);
				if (valide && masques.Contains(kv.Key.Name)) continue;
				if (valide) PoserVisible(kv.Key, kv.Value);
				_visAvantMasque.Remove(kv.Key);
			}
			// 2) Masquer chaque nom demandé (nœud actuel, éventuellement recréé).
			foreach (string nom in masques)
			{
				Node n = FindChild(nom, true, false);
				if (n == null) { GD.PushWarning($"[Couches] nœud « {nom} » introuvable."); continue; }
				if (_visAvantMasque.ContainsKey(n)) continue;
				_visAvantMasque[n] = LireVisible(n);
				PoserVisible(n, false);
			}
		}

		private static bool LireVisible(Node n) =>
			n is CanvasItem ci ? ci.Visible : n is CanvasLayer cl && cl.Visible;

		private static void PoserVisible(Node n, bool v)
		{
			if (n is CanvasItem ci) ci.Visible = v;
			else if (n is CanvasLayer cl) cl.Visible = v;
		}
	}
}
