// SYMBIOSE — icones/IconesCompost.cs (sprint ICÔNES & CURSEUR — données, famille « compost »)
// Grilles 16×16 des icônes de la famille COMPOST (cf. `sim/actions/familles.py`).
// Alphabet de couleurs : en-tête de `visuals/IconeGeste.cs` (K contour, C/B bois
// clair/sombre, T humus, V/G verts, '.' transparent…). Fichier de DONNÉES : aucune
// logique. Pour retoucher une icône, modifier ses lettres puis regarder la
// planche (`tools/capture_vm.sh -I`).

using System.Collections.Generic;

namespace Symbiose
{
	internal static class IconesCompost
	{
		public static readonly Dictionary<string, string[]> Grilles = new()
		{
			// Bac à compost : caisse de planches à claire-voie, humus sombre qui
			// dépasse en haut, deux brins verts fraîchement jetés dessus.
			["poser_bac"] = new[]
			{
				"................",
				"................",
				"......V..G......",
				"...KKTVTTGTKK...",
				"..KTTTTTTTTTTK..",
				".KKKKKKKKKKKKKK.",
				".KCCCKCCCCKCCCK.",
				".KCCCKCCCCKCCCK.",
				".KBBBKBBBBKBBBK.",
				".KCCCKCCCCKCCCK.",
				".KCCCKCCCCKCCCK.",
				".KBBBKBBBBKBBBK.",
				".KCCCKCCCCKCCCK.",
				".KCCCKCCCCKCCCK.",
				".KKKKKKKKKKKKKK.",
				"................",
			},
		};
	}
}
