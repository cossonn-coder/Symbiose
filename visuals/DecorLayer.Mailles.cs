// SYMBIOSE — DecorLayer.Mailles.cs (FLUIDITÉ PC LEVIERS ③ — une maille PRÊTE par palier)
// Partial de DecorLayer : le décor garde UNE maille (ArrayMesh) par palier où il est
// visible (×0,5, ×1, ×2, ×4). Changer de palier = PERMUTER la maille affichée, plus
// la reconstruire (~30-37 ms à chaque cran [VM, balayage ①]).
//
// 📖 Pédagogie (analogie embarqué) : c'est un double-buffer à 4 pages. Avant, chaque
// cran de molette recalculait toute la page (semis du kit, grilles, arbres) dans
// l'image même du cran — l'à-coup. Maintenant les pages des autres paliers sont
// calculées EN TÂCHE DE FOND, par petites tranches (budget ~8 ms par image), comme
// une DMA qui remplit un tampon pendant que le CPU affiche l'autre.
//
// 📖 Pourquoi on peut construire un palier qui n'est PAS affiché : toute la
// géométrie du décor est en px CANVAS (WorldToScreen ne dépend pas du zoom — c'est
// la Camera2D qui agrandit). Seuls le SEMIS du kit (pièces de N px internes), les
// détails fins (DetailZoom) et le calage au pixel dépendent du palier : ils lisent
// `ZoomConstr`, le palier EN CONSTRUCTION, au lieu de WorldView.CurrentZoom.
//
// Construction sur le FIL PRINCIPAL (pas de thread) : Polygone appelle
// Geometry2D.TriangulatePolygon (API Godot) et les listes de travail (_poses,
// _bouquets, _lot) sont des champs partagés — un thread imposerait de tout dupliquer
// pour un gain que le découpage en tranches donne déjà.
//
// Invalidation = mêmes signaux qu'avant : Build() (snapshot dont la ceinture change,
// rotation D35, bascule F10) jette les 4 mailles. Le palier courant est alors
// reconstruit d'un bloc au _Draw suivant (comme avant), les autres en tâche de fond.
// Une tranche = l'assise OU le motif d'UN secteur (8 tranches par palier, ordre de
// peinture conservé : 4 assises puis 4 motifs → même image au pixel).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Paliers où le décor se montre (miroir des ZoomSteps de WorldView ≤ MaxZoom).
		private static readonly float[] PaliersDecor = { 0.5f, 1f, 2f, 4f };
		private const int Tranches = 8;              // 4 assises + 4 motifs
		private const double BudgetFondMs = 8.0;     // tâche de fond, par image

		// Palier EN CONSTRUCTION : lu par le semis du kit et les détails fins.
		private static float ZoomConstr = 0.5f;

		// Une maille prête : son ArrayMesh + les points d'eau du scintillement
		// (calés au pixel interne de CE palier).
		private sealed class Maille
		{
			public ArrayMesh Mesh;
			public ArrayMesh MeshDevant;   // LEVIERS ⑤ : pièces hautes côté caméra (DecorLayer.Devant.cs)
			public int Sommets;            // total des deux mailles
			public readonly List<Vector2> Pts = new();
			public readonly List<uint> H = new();
			public void Ajouter(Vector2 p, uint h) { Pts.Add(p); H.Add(h); }
		}

		private readonly Maille[] _mailles = new Maille[4];
		private Maille _eauCible;                 // reçoit les points d'eau de DrawReflets
		private Maille _affichee;                 // dernière maille publiée au scintillement

		// Tâche de fond : un palier à la fois, tranche par tranche, dans son propre lot.
		private readonly LotTriangles _lotFond = new();
		private int _fondPalier = -1, _fondTranche;
		private Maille _fondMaille;
		private double _fondMs, _fondPireMs;

		private static int IndexPalier(float z) => System.Array.IndexOf(PaliersDecor, z);

		/// <summary>Jette les mailles (appelé par Build : profil, rotation, banc).</summary>
		private void InvaliderMailles()
		{
			System.Array.Clear(_mailles);
			_fondPalier = -1;
			_fondMaille = null;
			_affichee = null;
			PublierDevant(null);   // LEVIERS ⑤ : l'ancienne partie haute ne vaut plus
		}

		// Une tranche du palier z dans `lot` : l'assise (t < 4) ou le motif (t ≥ 4)
		// d'un secteur. On bascule _lot / ZoomConstr / _eauCible le temps de la tranche.
		// LEVIERS ⑤ : `haut` reçoit les pièces hautes des bords côté caméra (EnHaut).
		private void Tranche(LotTriangles lot, LotTriangles haut, Maille m, float z, int t)
		{
			LotTriangles lotAvant = _lot;
			float zAvant = ZoomConstr;
			_lot = lot;
			_lotHaut = haut;
			ZoomConstr = z;
			_eauCible = m;
			if (t < 4) DrawAssise(_profile.Secteurs[t]);   // DecorLayer.Patchwork.cs
			else DrawMotif(_profile.Secteurs[t - 4]);
			_lot = lotAvant;
			_lotHaut = null;
			ZoomConstr = zAvant;
			_eauCible = null;
		}

		private static void Ouvrir(LotTriangles lot)
		{
			lot.Vider();
			lot.UvUni = UvBlanc;   // aplats = texel blanc de l'atlas (DecorLayer.Kit.cs)
		}

		private static void Figer(LotTriangles lot, LotTriangles haut, Maille m)
		{
			m.Sommets = lot.Sommets + haut.Sommets;
			m.Mesh = lot.Figer(avecUv: true);
			m.MeshDevant = haut.Figer(avecUv: true);   // null si aucun bord côté caméra n'a de pièce haute
		}

		/// <summary>Maille du palier z, construite d'un bloc si absente (palier courant
		/// pas encore prêt : premier dessin, ou juste après une invalidation).</summary>
		private Maille MailleImmediate(float z, out bool construite)
		{
			int i = IndexPalier(z);
			construite = false;
			if (i >= 0 && _mailles[i] != null) return _mailles[i];
			var m = new Maille();
			Ouvrir(_lot);
			Ouvrir(_lotDevant);
			for (int t = 0; t < Tranches; t++) Tranche(_lot, _lotDevant, m, z, t);
			Figer(_lot, _lotDevant, m);
			construite = true;
			if (i < 0) return m;   // palier hors liste (capture exotique) : pas de cache
			_mailles[i] = m;
			if (_fondPalier == i) { _fondPalier = -1; _fondMaille = null; }   // rattrapé
			return m;
		}

		/// <summary>Publie les points d'eau de la maille affichée au scintillement
		/// (seulement quand la maille change : rien à faire à chaque redessin).</summary>
		private void PublierEau(Maille m)
		{
			if (_scintille == null || m == _affichee) return;
			_affichee = m;
			_scintille.Vider();
			for (int i = 0; i < m.Pts.Count; i++) _scintille.Ajouter(m.Pts[i], m.H[i]);
			_scintille.Publier();
		}

		/// <summary>Tâche de fond (_Process) : avance la construction des paliers
		/// manquants, le plus proche du palier courant d'abord, ≤ BudgetFondMs.</summary>
		private void AvancerFond()
		{
			long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
			while (true)
			{
				if (_fondPalier < 0 && !ChoisirFond()) return;
				Tranche(_lotFond, _lotFondDevant, _fondMaille, PaliersDecor[_fondPalier], _fondTranche++);
				double ms = (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0
						  / System.Diagnostics.Stopwatch.Frequency;
				if (_fondTranche == Tranches)
				{
					Figer(_lotFond, _lotFondDevant, _fondMaille);
					_mailles[_fondPalier] = _fondMaille;
					GD.Print($"[DecorLayer] maille ×{PaliersDecor[_fondPalier]} prête en tâche de fond :"
						   + $" {_fondMaille.Sommets} sommets, {_fondMs + ms:F1} ms en {Tranches} tranches"
						   + $" (pire image {Mathf.Max(_fondPireMs, ms):F1} ms)");
					_fondPalier = -1;
					_fondMaille = null;
					return;   // une maille finie par image au plus (le Figer coûte aussi)
				}
				if (ms >= BudgetFondMs)
				{
					_fondMs += ms;
					_fondPireMs = Mathf.Max(_fondPireMs, ms);
					return;
				}
			}
		}

		// Prochain palier à préparer : le manquant le plus proche du palier courant
		// (×4 d'abord quand on est au gros plan, décor éteint).
		private bool ChoisirFond()
		{
			int cour = IndexPalier(WorldView.CurrentZoom);
			if (cour < 0) cour = WorldView.CurrentZoom > MaxZoom ? PaliersDecor.Length - 1 : 0;
			for (int d = 0; d < PaliersDecor.Length; d++)
				foreach (int i in new[] { cour - d, cour + d })
				{
					if (i < 0 || i >= PaliersDecor.Length || _mailles[i] != null) continue;
					_fondPalier = i;
					_fondTranche = 0;
					_fondMaille = new Maille();
					_fondMs = _fondPireMs = 0;
					Ouvrir(_lotFond);
					Ouvrir(_lotFondDevant);
					return true;
				}
			return false;
		}
	}
}
