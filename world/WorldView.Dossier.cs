// SYMBIOSE — WorldView.Dossier.cs (partial de WorldView, sprint retours UI/HUD T3)
// Le MODE INSPECTION (outil de test) : une touche debug (F2, registre F6/F7)
// transforme le clic gauche en « inspecter » — clic sur une plante → dossier de
// son état physiologique courant (DossierPlantePanel), lu du DERNIER snapshot.
// Aucun appel pont : on relit le dict-plante déjà reçu (comme le survol gènes G).
//
// 📖 Pédagogie — on RÉUTILISE le picking FindPlant (WorldView.Actions.cs, employé
// par étiquettes/gènes/actions). La plante pointée est un PlantRenderer ; on
// reconstitue sa clé de snapshot (tile|species|x|y, == PlantKey) depuis ses Metas
// pour retrouver son payload dans le cache `_plantPayloads` rempli à l'ApplySnapshot.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Cache clé(tile|species|x|y) → dict-plante du DERNIER snapshot. Rempli à
		// chaque ApplySnapshot (WorldView.Snapshot.cs, dans la boucle des plantes) ;
		// lu ici au clic d'inspection. Clé IDENTIQUE à PlantKey → lookup direct.
		private readonly Dictionary<string, GDict> _plantPayloads = new();

		// Mode inspection (touche debug F2). Tant qu'il est ON, le clic gauche ouvre
		// le dossier de la plante pointée AU LIEU d'exécuter le geste courant.
		private bool _inspectMode;
		private DossierPlantePanel _dossier;

		// Toggle F2 : (dé)active le mode inspection. Le couper ferme le dossier.
		private void ToggleInspectMode()
		{
			_inspectMode = !_inspectMode;
			if (!_inspectMode) FermerDossier();
			GD.Print($"[WorldView] F2 → mode inspection {(_inspectMode ? "ON" : "OFF")}"
					 + " (clic = inspecter une plante).");
		}

		// Clé de dossier d'un renderer, RECONSTRUITE de ses Metas — même format que
		// PlantKey (tile|species|x_cm:F1|y_cm:F1), posées à la création du nœud.
		private static string DossierKey(PlantRenderer node) =>
			$"{node.GetMeta("tile").AsString()}|{node.GetMeta("species").AsString()}"
			+ $"|{node.GetMeta("lx").AsDouble():F1}|{node.GetMeta("ly").AsDouble():F1}";

		/// <summary>Clic en mode inspection : plante pointée → ouvre/rafraîchit son
		/// dossier ; clic dans le vide → ferme. Retourne true si le clic a été
		/// CONSOMMÉ (mode ON) — l'appelant ne joue alors aucun geste.</summary>
		private bool InspecterAuClic(Vector2 canvasMouse)
		{
			if (!_inspectMode) return false;
			var node = FindPlant(ScreenToWorld(canvasMouse), PickRadiusCm);
			AppliquerSiEnAttente(node);   // consultation : plante à jour d'abord (T4)
			if (node == null || !IsInstanceValid(node)
				|| !_plantPayloads.TryGetValue(DossierKey(node), out var payload))
			{
				FermerDossier();   // clic ailleurs = referme
				return true;
			}
			if (_dossier == null || !IsInstanceValid(_dossier))
			{
				_dossier = new DossierPlantePanel();
				AddChild(_dossier);
			}
			_dossier.Afficher(payload);
			return true;
		}

		// Ferme le dossier s'il est ouvert (clic ailleurs, Échap, F2 off). Intégrée
		// à la PRÉCÉDENCE Échap (WorldView.Controls.cs) : le dossier se ferme AVANT
		// le panneau de consultation, lui-même AVANT le retour à l'accueil.
		private void FermerDossier()
		{
			if (_dossier != null && IsInstanceValid(_dossier)) _dossier.QueueFree();
			_dossier = null;
		}
	}
}
