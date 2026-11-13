// SYMBIOSE — icones/AnimsStructures.cs (sprint GESTES LISIBLES ② — données, famille « structures »)
// LES SUITES D'IMAGES des gestes de la famille STRUCTURES (format : en-tête de
// `AnimsEau.cs` et de `visuals/EtapeGeste.cs`). Fichier de DONNÉES : aucune
// logique. Planche de contrôle : `tools/capture_vm.sh -W`.
// La plupart des structures se POSENT (patron `Poser` : chute, contact,
// poussière) ; chacune y ajoute, quand il y a lieu, son propre détail.

using System.Collections.Generic;
using static Symbiose.EtapeGeste;

namespace Symbiose
{
	internal static class AnimsStructures
	{
		public static readonly Dictionary<string, Etape[]> Suites = new()
		{
			["poser_pot"] = Poser(13),
			["poser_bac_culture"] = Poser(14),
			["poser_treillis"] = Poser(15),
			["poser_pergola"] = Poser(14),
			["poser_ombriere"] = Poser(15),
			// Le perchoir se plante ; l'oiseau chante (deux notes jaunes).
			["poser_perchoir"] = Puis(Poser(15), T(0, 0, (12, 1, 'Y'), (14, 0, 'Y'))),
			// La cloche se pose ; un reflet glisse sur le verre.
			["poser_cloche"] = Puis(Poser(15), T(0, 0, (5, 4, 'W'), (6, 3, 'W')).Dessus()),
			// La ruche se pose ; deux abeilles sortent.
			["poser_ruche"] = Puis(Poser(14), T(0, 0, (1, 2, 'Y'), (2, 2, 'K'), (13, 1, 'Y'), (14, 1, 'K'))),
			// Le tuteur est ENFONCÉ en deux coups : il descend, remonte, descend encore.
			["poser_tuteur"] = new[]
			{
				T(0, -5),
				T(0, 0, (5, 15, 'C'), (9, 15, 'C')),
				T(0, -2),
				T(0, 1, (4, 15, 'T'), (10, 15, 'T'), (5, 14, 'C'), (9, 14, 'C')),
				T(0, 1, (3, 14, 'C'), (11, 14, 'C')),
			},
			// Le voile descend en flottant (il dérive de gauche à droite), sans bruit.
			["poser_voile"] = new[]
			{
				T(0, -6),
				T(1, -4),
				T(-1, -2),
				T(0, -1),
				T(0, 0, (1, 14, 'W'), (14, 14, 'W')),
			},
			// La pelote TOURNE sur elle-même (elle se dévide), le brin s'allonge.
			["palisser"] = new[]
			{
				R(45, 7, 7, 0, 0),
				R(90, 7, 7, 0, 0),
				R(135, 7, 7, 0, 0),
				R(180, 7, 7, 0, 0, (12, 15, 'L'), (13, 15, 'L')),
				T(0, 0, (13, 15, 'L'), (14, 15, 'L'), (15, 14, 'L')),
			},
			// On soulève le pot, on le porte de côté, on le repose.
			["deplacer_pot"] = new[]
			{
				T(0, -2),
				T(0, -3),
				T(2, -3),
				T(3, -1),
				T(3, 0, (3, 14, 'C'), (14, 14, 'C')),
			},
			// Le pot se lève, se repose, un reflet court sur le miel, deux éclats :
			// c'est récolté.
			["recolter_miel"] = new[]
			{
				T(0, -2),
				T(0, 0, (4, 8, 'W')).Dessus(),
				T(0, 0, (6, 10, 'W')).Dessus(),
				T(0, 0, (9, 11, 'W')).Dessus(),
				T(0, 0, (1, 3, 'Y'), (14, 3, 'Y'), (2, 1, 'W'), (13, 1, 'W')),
			},
		};
	}
}
