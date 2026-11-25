// SYMBIOSE — WorldView.BancPortraits.cs (partial de WorldView, PRÉCUISSON SPLATS ⑦)
// BANC VM : ouvre la consultation sur une fiche d'ENCYCLOPÉDIE ou du MAGAZINE pour
// voir les portraits d'espèce (D6) avant le F5. « Yeux » de l'agent sur la VM sans
// écran — pas un livrable joueur. Inactif sans l'argument.
//
// Arguments (après `--`) :
//   --capture-portraits=encyclo:<clé>    fiche d'encyclopédie (ex. encyclo:tomate) ;
//                                        le niveau vient du pont → combiner avec
//                                        --capture-palier3=1 (niveau 3) ou rien de plus
//                                        (espèce non vue → pas de fiche, pas de portrait)
//   --capture-portraits=magazine:<clé>   fiche produit du magazine (portrait mûr)
//
// 📖 Pédagogie : la consultation construit ses onglets elle-même ; on retrouve le
// contenu voulu en parcourant l'arbre de nœuds (`is EncyclopediePanel`), puis on
// lui demande d'ouvrir la fiche — le même chemin qu'un clic dans l'index.

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly string CapturePortraits = ArgCapture("portraits");

		// Appelé en fin d'AppliquerCapture (debug palier3 éventuel déjà envoyé).
		private void LancerBancPortraits()
		{
			string[] a = CapturePortraits?.Split(':');
			if (a == null || a.Length != 2) return;
			GetTree().CreateTimer(2.0).Timeout += () =>
			{
				bool magazine = a[0] == "magazine";
				OuvrirConsultation(magazine ? "Magazine" : "Encyclopédie");
				foreach (Node n in _consultation.FindChildren("*", "", true, false))
				{
					if (!magazine && n is EncyclopediePanel enc) enc.OuvrirFiche(a[1]);
					if (magazine && n is MagazinePanel mag) mag.OuvrirFiche(a[1]);
				}
				GD.Print($"[Capture] portraits : fiche {CapturePortraits} ouverte.");
			};
		}
	}
}
