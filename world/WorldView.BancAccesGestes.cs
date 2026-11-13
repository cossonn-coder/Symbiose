// SYMBIOSE — WorldView.BancAccesGestes.cs (partial de WorldView, ACCÈS AUX GESTES ④)
// BANC VM de l'ouverture d'un geste. Le tronçon promet « on achète un outil, ses gestes
// deviennent jouables » : ce n'est vérifié que si l'achat part VRAIMENT par le pont et
// que la palette réagit. Le banc relève la palette, achète un outil à l'Atelier (même
// action `acheter_outil` que le panneau), puis la relève à nouveau. « Yeux » de l'agent
// sur la VM, pas un livrable joueur ; inactif sans l'argument.
//
//   tools/capture_vm.sh -b acces_gestes -w 0 -A tuteurs,voile -n 240
//
// Journal : `[AccesGestes] avant : …` puis `[AccesGestes] après : …` (gestes ouverts,
// gestes en case, gestes ouverts HORS case). À chaque relevé le menu du clic droit de
// la première case est ouvert : c'est lui qui liste les gestes ouverts hors case, donc
// lui qui change à l'image (les dix cases sont déjà pleines des gestes de base). Une
// dernière image range les gestes hors case dans les cases, pour voir leurs pictogrammes.
//
//   tools/capture_vm.sh -b acces_gestes -w 0 -Q 1 -n 20           (tiroir ouvert)
//   tools/capture_vm.sh -b acces_gestes -w 0 -Q glaner -n 60      (puis geste choisi)
//
// PALETTE & TIROIR ① : `-Q` ouvre le tiroir au montage ; avec un VERBE, ce geste est
// ensuite choisi comme par un clic dans le tiroir (qui se ferme : le bouton du bas de
// barre doit alors porter son pictogramme s'il n'a pas de case). Journal `[Tiroir]`.
//
//   tools/capture_vm.sh -b acces_gestes -w 0 -A tuteurs -Q 1 -s 240,418 -n 118   (③)
//
// Avec `-A` : à 10 s (l'achat est passé, le menu du relevé est fermé) le journal liste
// les gestes PRESSENTIS et leur phrase, et la souris est ramenée sur `-s` pour faire
// lever l'info-bulle de la silhouette. Images utiles : 100 à 117.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly string CaptureAcces = ArgCapture("acces");
		private const float AccesAttenteSec = 4f;
		private static readonly string CaptureTiroir = ArgCapture("tiroir");

		// Appelé en fin d'AppliquerCapture.
		private void LancerBancAccesGestes()
		{
			if (CaptureTiroir != null)
			{
				OuvrirTiroir();
				GD.Print($"[Tiroir] ouvert · familles : {(_famillesOrdre == null ? "(aucune reçue)" : string.Join(",", _famillesOrdre))}");
				if (CaptureAcces != null)
					GetTree().CreateTimer(10f).Timeout += () =>
					{
						var lus = new List<string>();
						foreach (var (v, phrase) in _pressentis) lus.Add($"{v} → « {phrase} »");
						GD.Print($"[Tiroir] pressentis : {(lus.Count == 0 ? "(aucun)" : string.Join(" · ", lus))}");
						if (CaptureSouris == null) return;
						string[] s = CaptureSouris.Split(',');
						if (s.Length == 2)   // +1 px : un vrai déplacement, donc un survol relu
							Input.WarpMouse(new Vector2(ParseFloat(s[0]) + 1f, ParseFloat(s[1])));
					};
				int g = IndexDuVerbe(CaptureTiroir);
				if (g >= 0)
					Apres(() =>
					{
						_tiroirPanel.OnChoisi(g);
						GD.Print($"[Tiroir] choisi : {Gestes[g].Verb} · en case : {DansUnSlot(g)} · tiroir ouvert : {TiroirOuvert}");
					});
			}
			if (CaptureAcces == null) return;
			Apres(() =>
			{
				ReleverPalette("avant");
				Apres(() => { _editMenu?.Hide(); AcheterSuivant(CaptureAcces.Split(','), 0); });
			});
		}

		private void Apres(System.Action suite)
			=> GetTree().CreateTimer(AccesAttenteSec).Timeout += suite;

		// Un achat à la fois (le pipe est 1↔1), puis le relevé « après ».
		private void AcheterSuivant(string[] outils, int i)
		{
			if (i > 0) GD.Print($"[AccesGestes] achat de {outils[i - 1]} → « {_lastActionMsg} »");
			if (i == outils.Length)
			{
				ReleverPalette("après");
				Apres(MontrerHorsCase);
				return;
			}
			var prms = new GDict { ["outil"] = outils[i] };
			// Même règle que TryAction : un pipe occupé → intention mémorisée.
			if (PipeFree) LaunchAction("acheter_outil", null, prms, null);
			else _queuedIntent = ("acheter_outil", null, prms, null);
			Apres(() => AcheterSuivant(outils, i + 1));
		}

		// Dernière image : les gestes ouverts hors case prennent les cases, pour VOIR
		// leurs pictogrammes. Rien n'est sauvegardé (pas de SauverSlots) : banc seul.
		private void MontrerHorsCase()
		{
			_editMenu?.Hide();
			int s = 0;
			for (int g = Gestes.Length - 1; g >= 0 && s < SlotCount; g--)
				if (EstDebloque(g) && !DansUnSlot(g)) _slots[s++] = g;
			RebuildPaletteIcons();
			GD.Print("[AccesGestes] cases : "
					 + string.Join(",", System.Array.ConvertAll(_slots, g => g < 0 ? "-" : Gestes[g].Verb)));
		}

		// Trois listes au journal, puis le menu du clic droit ouvert pour l'image.
		private void ReleverPalette(string quand)
		{
			var enCase = new List<string>();
			var horsCase = new List<string>();
			int ouverts = 0;
			for (int g = 0; g < Gestes.Length; g++)
			{
				if (!EstDebloque(g)) continue;
				ouverts++;
				(DansUnSlot(g) ? enCase : horsCase).Add(Gestes[g].Verb);
			}
			GD.Print($"[AccesGestes] {quand} : {ouverts} gestes ouverts sur {Gestes.Length} · "
					 + $"en case : {string.Join(",", enCase)} · hors case : {string.Join(",", horsCase)}");
			if (_slotIcons[0] != null) OuvrirEditSlot(0, _slotIcons[0]);
		}
	}
}
