// SYMBIOSE — FauneSilhouettes.cs (sprint CASSÉ À L'ÉCRAN ⑤ — faune en icônes)
// Le PORTRAIT de chaque bête visible (vie macro `MacroLife` + butineurs
// `ForagerLayer`) : une silhouette caractéristique vue de DESSUS, décrite en
// DONNÉES — une liste d'ellipses peintes dans l'ordre (la dernière couvre), comme
// CarpophoreStyles pour les champignons. Le rasteriseur (`FauneIcones`) les cuit
// en pixels indexés (encodage ③) à la taille exacte du palier.
//
// 📖 Pédagogie — le repère du CORPS : u = axe de la bête (tête en u = +1, queue en
// u = −1), v = travers ; unité = la DEMI-longueur. Une coccinelle de 0,7 × 0,5 cm a
// donc un corps de demi-largeur ≈ 0,7 (0,5 / 0,7). On décrit la bête une fois dans
// ce repère ; tourner, rapetisser, écraser en iso, c'est le rasteriseur qui le fait
// (comme une police vectorielle qu'on rend à toutes les tailles).
//
// Lecture d'une partie : centre (U, V), rayons (Ru, Rv), couleur = indice dans
// `Couleurs` (une RAMPE dérivée par couleur, RampesDa.Deriver), Ton :
//   −1 = DÔME (ton de base + orientation de face : le soleil modèle le volume),
//   0..4 = ton fixe à plat (0 = le plus sombre de la rampe : yeux, taches, bandes).
// Fin = détail qui n'apparaît qu'à partir de quelques px (palier fin = plus de
// détails, jamais un autre dessin). Miroir = aussi en −V (paires : ailes, taches).
//
// Couleurs : la 1ʳᵉ est celle du corps = la couleur d'espèce de MacroLife /
// ForagerLayer (un seul langage visuel avec la heatmap F6). Jamais de noir : les
// « noirs » (merle, taches de coccinelle) sont le ton 0 d'une rampe COLORÉE.
// Données pures, déterministes : golden non concerné. Aucun nom affiché à l'écran
// (philo du naturaliste débutant) — les clés ne servent qu'à la table.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	/// <summary>Motif posé sur une partie (texture de la bête, en tons de SA rampe).</summary>
	internal enum MotifFaune { Aucun, Bandes, Segments, Piquants, Ecailles }

	internal readonly record struct PartieFaune(
		float U, float V, float Ru, float Rv, int Couleur = 0, int Ton = -1,
		bool Fin = false, bool Miroir = false, MotifFaune Motif = MotifFaune.Aucun);

	/// <summary>Une bête : couleurs (rampes) + parties ; `Serpent` = l'axe ondule.</summary>
	internal sealed record SilhouetteFaune(Color[] Couleurs, PartieFaune[] Parties, bool Serpent = false);

	internal static class FauneSilhouettes
	{
		private static Color[] C(params string[] hex)
		{
			var r = new Color[hex.Length];
			for (int i = 0; i < hex.Length; i++) r[i] = new Color(hex[i]);
			return r;
		}

		private static PartieFaune P(float u, float v, float ru, float rv, int coul = 0, int ton = -1,
									 bool fin = false, bool miroir = false, MotifFaune motif = MotifFaune.Aucun)
			=> new(u, v, ru, rv, coul, ton, fin, miroir, motif);

		// Ordre = ordre de peinture (ailes sous le corps, taches sur le dôme…).
		private static readonly Dictionary<string, SilhouetteFaune> Table = new()
		{
			// ── Ravageurs ──
			["puceron"] = new(C("6f8f3a"), new[]
			{
				P(-0.1f, 0f, 0.85f, 0.5f),                                   // abdomen en poire
				P(0.7f, 0f, 0.3f, 0.3f),                                     // tête
				P(-0.6f, 0.25f, 0.2f, 0.06f, 0, 1, fin: true, miroir: true), // cornicules
			}),
			["limace"] = new(C("7a5a3a", "8c6c48"), new[]
			{
				P(0f, 0f, 1f, 0.17f, motif: MotifFaune.Segments),           // pied allongé, rides
				P(0.35f, 0f, 0.32f, 0.18f, 1),                               // manteau (bouclier)
				P(1.02f, 0.07f, 0.1f, 0.025f, 0, 0, fin: true, miroir: true), // cornes
			}),
			["doryphore"] = new(C("d8a83a", "c8782a"), new[]
			{
				P(-0.08f, 0f, 0.88f, 0.66f),                                 // élytres en dôme
				P(-0.1f, 0.18f, 0.65f, 0.05f, 0, 0, fin: true, miroir: true), // rayures
				P(-0.1f, 0.42f, 0.55f, 0.05f, 0, 0, fin: true, miroir: true),
				P(0.82f, 0f, 0.2f, 0.32f, 1),                                // pronotum orangé
			}),
			// ── Auxiliaires ──
			["coccinelle"] = new(C("c43a2e"), new[]
			{
				P(-0.05f, 0f, 0.88f, 0.7f),                                  // dôme rouge
				P(0.15f, 0.36f, 0.14f, 0.14f, 0, 0, fin: true, miroir: true), // points
				P(-0.4f, 0.3f, 0.14f, 0.14f, 0, 0, fin: true, miroir: true),
				P(-0.1f, 0f, 0.12f, 0.12f, 0, 0, fin: true),
				P(0.85f, 0f, 0.2f, 0.42f, 0, 0),                             // tête sombre
			}),
			["chrysope"] = new(C("9fd86e", "dcf0cc", "d8b030"), new[]
			{
				P(-0.15f, 0.3f, 0.62f, 0.26f, 1, 3, miroir: true),           // ailes de dentelle
				P(0f, 0f, 0.85f, 0.12f),                                     // corps fin
				P(0.88f, 0.09f, 0.08f, 0.08f, 2, 3, fin: true, miroir: true), // yeux d'or
			}),
			["carabe"] = new(C("2a3a52"), new[]
			{
				P(-0.25f, 0f, 0.7f, 0.4f),                                   // élytres irisés
				P(-0.25f, 0f, 0.66f, 0.02f, 0, 0, fin: true),                // suture
				P(0.45f, 0f, 0.2f, 0.3f),                                    // pronotum
				P(0.75f, 0f, 0.15f, 0.17f),                                  // tête
				P(1.0f, 0.15f, 0.2f, 0.03f, 0, 0, fin: true, miroir: true),  // antennes
			}),
			["merle"] = new(C("2b2a3a", "e8a020", "3a3850"), new[]
			{
				P(-0.72f, 0f, 0.32f, 0.13f),                                 // queue
				P(-0.05f, 0f, 0.58f, 0.32f),                                 // corps noir bleuté
				P(-0.15f, 0.2f, 0.42f, 0.12f, 2, miroir: true),              // ailes repliées
				P(0.58f, 0f, 0.22f, 0.21f),                                  // tête
				P(0.84f, 0f, 0.13f, 0.05f, 1, 2),                            // bec orange
				P(0.62f, 0.12f, 0.035f, 0.035f, 1, 3, fin: true, miroir: true), // cercle de l'œil
			}),
			["herisson"] = new(C("8a6a4a", "c8a87a"), new[]
			{
				P(-0.12f, 0f, 0.82f, 0.6f, motif: MotifFaune.Piquants),     // dôme de piquants
				P(0.72f, 0f, 0.24f, 0.24f, 1),                               // museau clair
				P(0.95f, 0f, 0.07f, 0.07f, 1, 0, fin: true),                 // truffe
				P(0.72f, 0.12f, 0.05f, 0.05f, 1, 0, fin: true, miroir: true), // yeux
			}),
			// ── Disperseurs de graines (zoochorie ⑧, D42) ──
			// Geai : beige-rosé, la BANDE BLEUE barrée à l'aile (le signe du geai),
			// queue et moustache sombres, croupion blanc vu de dessus.
			["geai"] = new(C("c09a88", "3a78c8", "3a3040", "f0ece4"), new[]
			{
				P(-0.74f, 0f, 0.3f, 0.12f, 2),                               // queue sombre
				P(-0.05f, 0f, 0.56f, 0.3f),                                  // corps beige-rosé
				P(-0.2f, 0.2f, 0.42f, 0.12f, 2, miroir: true),               // ailes sombres
				P(0.05f, 0.24f, 0.11f, 0.07f, 1, 2, miroir: true),           // bande bleue
				P(-0.48f, 0f, 0.1f, 0.1f, 3, 3, fin: true),                  // croupion blanc
				P(0.56f, 0f, 0.21f, 0.19f),                                  // tête
				P(0.66f, 0.1f, 0.07f, 0.03f, 2, 0, fin: true, miroir: true), // moustache noire
				P(0.83f, 0f, 0.1f, 0.05f, 2, 1),                             // bec
			}),
			// Écureuil : roux, la QUEUE en panache aussi large que le corps (sa
			// silhouette de dessus), oreilles à pinceaux.
			["ecureuil"] = new(C("b8582a", "e8d8c0"), new[]
			{
				P(-0.58f, 0f, 0.42f, 0.24f, motif: MotifFaune.Piquants),    // panache de la queue
				P(0.08f, 0f, 0.4f, 0.2f),                                    // corps roux
				P(0.52f, 0f, 0.17f, 0.15f),                                  // tête
				P(0.5f, 0.11f, 0.05f, 0.04f, 0, 1, miroir: true),            // pinceaux des oreilles
				P(0.62f, 0.08f, 0.03f, 0.03f, 1, 3, fin: true, miroir: true), // cercle clair de l'œil
			}),
			// Mulot : brun-fauve, ventre clair qui déborde du flanc, GRANDES oreilles et
			// gros yeux (≠ campagnol trapu à oreilles cachées), queue aussi longue que lui.
			["mulot"] = new(C("a87a48", "e8dcc0"), new[]
			{
				P(-0.55f, 0f, 0.45f, 0.03f, 0, 2, fin: true),                // longue queue
				P(0.02f, 0f, 0.42f, 0.24f, 1, 3),                            // ventre clair (flancs)
				P(0.02f, 0f, 0.4f, 0.19f),                                   // dos fauve
				P(0.42f, 0f, 0.15f, 0.13f),                                  // tête
				P(0.36f, 0.13f, 0.09f, 0.08f, 0, 2, miroir: true),           // grandes oreilles
				P(0.5f, 0.07f, 0.035f, 0.035f, 0, 0, fin: true, miroir: true), // gros yeux
			}),
			// ── Détritivore ──
			["cloporte"] = new(C("8a8a8a"), new[]
			{
				P(0f, 0f, 0.9f, 0.46f, motif: MotifFaune.Segments),         // carapace segmentée
				P(1.0f, 0.18f, 0.18f, 0.03f, 0, 0, fin: true, miroir: true), // antennes
			}),
			// ── Herbivore vertébré ──
			["campagnol"] = new(C("9a6a3a", "b89068"), new[]
			{
				P(-0.95f, 0f, 0.25f, 0.035f, 1, fin: true),                  // queue courte
				P(-0.12f, 0f, 0.66f, 0.4f),                                  // corps
				P(0.58f, 0f, 0.3f, 0.27f),                                   // tête
				P(0.5f, 0.22f, 0.09f, 0.09f, 0, 1, fin: true, miroir: true), // oreilles
				P(0.74f, 0.12f, 0.04f, 0.04f, 0, 0, fin: true, miroir: true), // yeux
			}),
			// ── Super-prédateurs ──
			["rapace"] = new(C("b58a4a", "e0c890"), new[]
			{
				P(-0.05f, 0.42f, 0.24f, 0.4f, miroir: true),                // ailes déployées
				P(-0.12f, 0.72f, 0.14f, 0.12f, 0, 0, fin: true, miroir: true), // rémiges
				P(-0.7f, 0f, 0.22f, 0.16f),                                  // queue en éventail
				P(0f, 0f, 0.5f, 0.15f, 1),                                   // corps clair
				P(0.55f, 0f, 0.15f, 0.13f),                                  // tête
			}),
			["couleuvre"] = new(C("5a7a3a", "c8c070"), new[]
			{
				P(0f, 0f, 1f, 0.04f, motif: MotifFaune.Ecailles),           // corps ondulant
				P(0.93f, 0f, 0.08f, 0.055f),                                 // tête
				P(0.84f, 0.035f, 0.05f, 0.02f, 1, 3, fin: true, miroir: true), // collier clair
			}, Serpent: true),
			// ── Faune de mare ──
			["moustique"] = new(C("6a5f57", "c8c4c0"), new[]
			{
				P(-0.1f, 0.22f, 0.5f, 0.16f, 1, 3, miroir: true),            // ailes
				P(0f, 0f, 0.75f, 0.13f),                                     // corps
			}),
			["libellule"] = new(C("2f9f8f", "d8eef0"), new[]
			{
				P(0.32f, 0.55f, 0.13f, 0.5f, 1, 3, miroir: true),            // ailes antérieures
				P(0.08f, 0.55f, 0.13f, 0.5f, 1, 3, miroir: true),            // ailes postérieures
				// Abdomen ÉPAISSI (0,07 → 0,11, MARE VIVANTE ③) : à 1 px il se noyait
				// dans l'eau sombre et la libellule se lisait « bâtonnet gris » d'ailes.
				P(-0.15f, 0f, 0.85f, 0.11f, motif: MotifFaune.Segments),    // abdomen
				P(0.82f, 0f, 0.12f, 0.18f),                                  // tête, gros yeux
			}),
			// ── Butineurs (ForagerLayer) ──
			["abeille"] = new(C("e9c83c", "f0f0e8"), new[]
			{
				P(0.05f, 0.42f, 0.32f, 0.26f, 1, 3, miroir: true),           // ailes claires
				P(-0.2f, 0f, 0.7f, 0.42f, motif: MotifFaune.Bandes),        // abdomen rayé
				P(0.55f, 0f, 0.25f, 0.3f),                                   // thorax
				P(0.85f, 0f, 0.15f, 0.25f, 0, 0),                            // tête
			}),
			["syrphe"] = new(C("d98f2e", "f0f0e8"), new[]
			{
				P(0.15f, 0.45f, 0.4f, 0.22f, 1, 3, miroir: true),            // ailes
				P(-0.25f, 0f, 0.65f, 0.36f, motif: MotifFaune.Bandes),      // abdomen plat rayé
				P(0.5f, 0f, 0.25f, 0.3f, 0, 0),                              // thorax sombre
				P(0.82f, 0f, 0.15f, 0.3f, 0, 1),                             // gros yeux
			}),
			["papillon"] = new(C("dcb4d2", "3a3048", "f0e070"), new[]
			{
				P(0.3f, 0.5f, 0.3f, 0.48f, miroir: true),                    // ailes antérieures
				P(-0.25f, 0.4f, 0.28f, 0.36f, miroir: true),                 // ailes postérieures
				P(0.35f, 0.62f, 0.09f, 0.09f, 2, 3, fin: true, miroir: true), // ocelles
				P(0f, 0f, 0.7f, 0.08f, 1),                                   // corps sombre
			}),
			["bourdon"] = new(C("d8a020", "f0f0e8", "3a3050"), new[]
			{
				P(0.15f, 0.48f, 0.3f, 0.22f, 1, 3, miroir: true),            // ailes
				P(-0.1f, 0f, 0.82f, 0.6f, motif: MotifFaune.Bandes),        // gros corps velu
				P(-0.8f, 0f, 0.16f, 0.32f, 1, 3),                            // queue blanche
				P(0.8f, 0f, 0.16f, 0.3f, 2, 1),                              // tête
			}),
			["osmie"] = new(C("b5651d", "f0f0e8", "3a3a58"), new[]
			{
				P(0.1f, 0.42f, 0.3f, 0.24f, 1, 3, miroir: true),             // ailes
				P(-0.2f, 0f, 0.7f, 0.42f, motif: MotifFaune.Piquants),      // abdomen roux velu
				P(0.6f, 0f, 0.3f, 0.36f, 2),                                 // thorax bleu-noir
			}),
			// Pollen porté par un butineur : un grain en dôme.
			["pollen"] = new(C("fff2a8"), new[] { P(0f, 0f, 1f, 1f) }),
		};

		// Espèce inconnue d'un futur protocole : un petit dôme gris, pas un crash.
		private static readonly SilhouetteFaune Inconnue = new(C("999999"), new[] { P(0f, 0f, 1f, 1f) });

		/// <summary>Silhouette de l'espèce (repli : dôme gris).</summary>
		public static SilhouetteFaune De(string espece)
			=> espece != null && Table.TryGetValue(espece, out var s) ? s : Inconnue;
	}
}
