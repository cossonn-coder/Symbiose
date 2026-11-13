// SYMBIOSE — WorldView.DeuxTemps.cs (partial de WorldView, GESTES LISIBLES ④)
// LES GESTES À DEUX TEMPS, sortis de WorldView.ActionDispatch.cs (qui dépassait la
// bande de taille) : épandre (le tas, puis le plot), déplacer un pot (le pot, puis sa
// place), bouturer (la mère, puis le plot), greffer (le greffon, puis le porte-greffe).
// Le 1er clic SAISIT (la vue mémorise, rien ne part au pont, le serveur reste sans
// état) ; le 2e clic désigne la cible et consomme la saisie.
//
// Ce que ④ change (conception §6, « objet en main ») :
//  - la saisie se VOIT : WorldView.ObjetEnMain.cs lit les champs `_grabbed*` et met
//    l'objet au curseur, signale les cibles valides ;
//  - un 2e clic HORS cible ne lâche plus l'objet : on le dit, et on garde l'objet en
//    main (Échap ou clic droit le reposent) ;
//  - les phrases ne portent plus de numéro (« tas saisi », plus « tas #2 saisi ») ;
//  - le pot ne se pose que sur une tuile, comme `poser_pot` (le pont refuse déjà hors
//    du jardin, ①) ;
//  - `planter` sur un pot y sème la graine choisie (même sélection que `planter`, un
//    clic sur le pot) : le verbe envoyé devient `planter_conteneur`.
//
// Chaque résolveur rend true quand la cible est prête (2e clic valide) ; false quand
// il attend le 2e clic ou refuse (le message est déjà au HUD).

using Godot;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Refus de désignation : dit au HUD, avec le flash (l'objet reste en main).
		private void RefusDeuxTemps(string msg)
		{
			_lastActionMsg = msg;
			UpdateActionHud(); FlashActionLabel();
		}

		// Saisie réussie (1er clic) : dit au HUD, sans flash (ce n'est pas un refus).
		private void SaisieDeuxTemps(string msg)
		{
			_lastActionMsg = msg;
			UpdateActionHud();
		}

		/// <summary>ÉPANDRE (mycélium ⑥, §3.2) : 1er clic = le bac/pile source, 2e clic =
		/// le plot à amender, sur la tuile du tas (le moteur écrit le sol de CETTE tuile).
		/// params.q omis ⇒ tout le mûr.</summary>
		private bool ResoudreEpandre(Vector2 w, out GDict target)
		{
			target = null;
			if (_grabbedBac < 0)
			{
				int near = FindNearestStructureWorld(w, ContainerPickRadiusCm,
					out string bTile, out _, out _);
				if (near < 0) { RefusDeuxTemps("épandre : aucun tas ici (cliquez un bac ou une pile)"); return false; }
				_grabbedBac = near;
				_grabbedBacTile = bTile;
				SaisieDeuxTemps("pelletée prise — cliquez le plot à amender");
				return false;
			}
			if (!FindPlot(w, out string eTile, out int er, out int ec))
			{ RefusDeuxTemps("épandre : aucune tuile ici (chemin/maison)"); return false; }
			if (eTile != _grabbedBacTile)
			{ RefusDeuxTemps("épandre : la cible doit être sur la tuile du tas"); return false; }
			target = new GDict { ["tile"] = eTile, ["structure"] = _grabbedBac, ["r"] = er, ["c"] = ec };
			_grabbedBac = -1;   // saisie consommée
			return true;
		}

		/// <summary>DÉPLACER UN POT (décision Nico : outil + clic, pas de drag) : 1er clic =
		/// le pot le plus proche, 2e clic = sa nouvelle place, point MONDE sur une tuile.
		/// Le refus « immobile » (bac) reste rendu par le serveur.</summary>
		private bool ResoudreDeplacerPot(Vector2 w, out GDict target)
		{
			target = null;
			if (_grabbedContainer < 0)
			{
				int near = FindNearestContainer(w, ContainerPickRadiusCm);
				if (near < 0) { RefusDeuxTemps("déplacer : aucun conteneur ici (cliquez un pot)"); return false; }
				_grabbedContainer = near;
				SaisieDeuxTemps("pot soulevé — cliquez où le poser");
				return false;
			}
			if (!FindPlot(w, out _, out _, out _))
			{ RefusDeuxTemps("déplacer : posez le pot sur une tuile, pas sur le chemin"); return false; }
			target = new GDict { ["container"] = _grabbedContainer, ["x_cm"] = w.X, ["y_cm"] = w.Y };
			_grabbedContainer = -1;   // saisie consommée
			return true;
		}

		/// <summary>BOUTURER (②) : 1er clic = la plante-mère, 2e clic = le PLOT cible de la
		/// MÊME tuile (le moteur enracine le clone dans l'eco de la mère). Le serveur route
		/// la mère par target.x_cm/y_cm et la cible par params.r/c.</summary>
		private bool ResoudreBouture(Vector2 w, GDict prms, out GDict target, out PlantRenderer node)
		{
			target = null;
			node = null;
			if (_grabbedMother == null)
			{
				PlantRenderer mere = FindPlant(w, PickRadiusCm);
				if (mere == null) { RefusDeuxTemps("bouturer : aucune plante-mère à portée du clic"); return false; }
				_grabbedMother = mere;
				SaisieDeuxTemps("bouture prélevée — cliquez le plot où l'enraciner");
				return false;
			}
			if (!FindPlot(w, out string cutTile, out int cutR, out int cutC))
			{ RefusDeuxTemps("bouturer : aucune tuile ici (chemin/maison)"); return false; }
			if (cutTile != _grabbedMother.GetMeta("tile").AsString())
			{ RefusDeuxTemps("bouturer : le plot doit être sur la tuile de la mère"); return false; }
			target = new GDict
			{
				["tile"] = _grabbedMother.GetMeta("tile"),
				["x_cm"] = _grabbedMother.GetMeta("lx"),
				["y_cm"] = _grabbedMother.GetMeta("ly"),
			};
			prms["r"] = cutR;
			prms["c"] = cutC;
			node = _grabbedMother;
			_grabbedMother = null;   // saisie consommée
			return true;
		}

		/// <summary>GREFFER (③) : 1er clic = le GREFFON (mémorisé en params.scion_x_cm/y_cm),
		/// 2e clic = le PORTE-GREFFE (cible primaire), MÊME tuile (le serveur résout un seul
		/// `eco`). La façade Python fait foi (compatibilité, gates).</summary>
		private bool ResoudreGreffe(Vector2 w, GDict prms, out GDict target, out PlantRenderer node)
		{
			target = null;
			node = FindPlant(w, PickRadiusCm);
			if (_grabbedScion == null)
			{
				if (node == null) { RefusDeuxTemps("greffer : aucun greffon à portée du clic"); return false; }
				_grabbedScion = node;
				_grabbedScionTile = node.GetMeta("tile").AsString();
				SaisieDeuxTemps("greffon prélevé — cliquez le porte-greffe (même tuile)");
				node = null;
				return false;
			}
			if (node == null) { RefusDeuxTemps("greffer : aucun porte-greffe à portée du clic"); return false; }
			if (node.GetMeta("tile").AsString() != _grabbedScionTile)
			{
				RefusDeuxTemps("greffer : porte-greffe et greffon doivent être sur la même tuile");
				node = null;
				return false;
			}
			target = new GDict
			{
				["tile"] = node.GetMeta("tile"),
				["x_cm"] = node.GetMeta("lx"),
				["y_cm"] = node.GetMeta("ly"),
			};
			prms["scion_x_cm"] = _grabbedScion.GetMeta("lx");
			prms["scion_y_cm"] = _grabbedScion.GetMeta("ly");
			_grabbedScion = null;   // saisie consommée
			return true;
		}

		/// <summary>`planter` armé et clic SUR un pot : la graine choisie va dans le pot
		/// (verbe `planter_conteneur`, désigné par index). False = pas de pot sous le clic
		/// (ou banque vide) → le chemin `planter` ordinaire continue.</summary>
		private bool CiblePotPourPlanter(Vector2 w, GDict prms, out GDict target)
		{
			target = null;
			if (_seeds.Count == 0) return false;
			int pot = FindNearestContainer(w, PickRadiusCm);
			if (pot < 0) return false;
			target = new GDict { ["container"] = pot };
			prms["species"] = _seeds[_seedIndex].Key;
			return true;
		}
	}
}
