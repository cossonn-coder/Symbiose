// SYMBIOSE — WorldView.Etalement.cs (partial de WorldView, F5 Nico 2026-10-15)
// Application ÉTALÉE d'une semaine : jamais tout le jardin dans la même frame.
//
// Mesuré (VM sans GPU, full ×32, turbo) : appliquer un snapshot d'un bloc
// gelait l'image 130-330 ms à CHAQUE semaine, dont 120-230 ms pour la seule
// boucle des plantes (~1 ms/plante) [12 semaines mesurées] → les chutes à
// 2 FPS que Nico voyait toutes les ~3 s.
//
// Règle de Nico : l'affichage se répartit en 7 FAMILLES, chacune mise à jour
// dans SA frame (tourniquet). Ordre fixe, car il y a des dépendances :
//   0 sol (relief)  → les plantes s'y recalent (ReliefRisePx) ;
//   1 plantes       → seule famille trop lourde pour une frame : découpée en
//                     tranches de BudgetPlantesUs, plantes À L'ÉCRAN d'abord ;
//   2 vie macro     → les butineurs lisent l'index des fleurs (fin de 1) ;
//   3 couches au sol · 4 structures · 5 météo/ciel · 6 ménage/HUD/saison.
//
// 📖 Pédagogie (côté embarqué) : c'est un ordonnanceur coopératif à tranches
// de temps, comme une boucle principale de microcontrôleur qui découpe une
// tâche longue en pas courts pour ne jamais rater l'échéance d'affichage.
// L'état de la tâche (où on en est) vit dans un objet `Etalement` au lieu de
// la pile : c'est ce qui permet de « reprendre » à la frame suivante.
//
// Pendant l'étalement, le jardin mélange brièvement semaine N (pas encore
// touché) et N+1 (déjà appliqué) — quelques frames, invisible à l'œil.
// Seul le step hebdomadaire est étalé. Chargement initial, rotation, saut
// debug et résultat d'une ACTION restent appliqués d'un bloc (synchrones) :
// un clic attend une réponse immédiate, et un snapshot synchrone, plus
// frais, REMPLACE un étalement en cours (il porte l'état complet).
//
// CHEVAUCHEMENT (FLUIDITÉ AN 2 ④) : avant, le step N+1 ne partait qu'une fois la
// semaine N entièrement appliquée → calcul moteur + application s'ADDITIONNAIENT
// (garde `_etale == null`, posée avec l'étalement, commit 73a3f24, pour ne jamais
// empiler deux étalements). Désormais le step N+1 part PENDANT l'application de
// N. Intention de la garde préservée autrement : au plus UNE semaine reçue en
// réserve (`_semainePrete`), démarrée à la fin de l'étalement courant — jamais
// deux étalements à la fois, jamais deux semaines en réserve (pas de step tant
// qu'une attend). Exception : en mode Saison, une semaine qui CHANGE de saison
// garde l'ancienne règle (le moteur s'arrête à la 1ʳᵉ semaine de la saison
// nouvelle, comme avant, pour le retour en planification).
// 📖 C'est un double tampon (ping-pong) : le producteur remplit le tampon B
// pendant que le consommateur vide le tampon A.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Budget d'une tranche par frame (µs), plantes ET vie macro — les deux
		// familles lourdes ; les 5 autres pèsent ≤ ~6 ms en médiane [24 semaines].
		// Budget de la tranche « plantes » par frame (µs). ~1 ms/plante mesuré
		// sur la VM → ~6 plantes/frame ; 200 plantes ≈ 35 frames ≈ 1-2 s, bien
		// sous la cadence d'une semaine. Les plantes visibles passent en tête.
		private const long BudgetPlantesUs = 6000;

		private const int NbFamilles = 7;

		/// <summary>Étalement en cours (null = aucune semaine en application).</summary>
		private Etalement _etale;

		/// <summary>Semaine reçue pendant un étalement, en réserve (au plus UNE).</summary>
		private SemaineRecue _semainePrete;

		/// <summary>Le step suivant peut-il partir côté VUE ? (le pipe libre est
		/// testé à part). Non si une semaine attend déjà, ou si la semaine en
		/// application change de saison en mode Saison (retour en planification).</summary>
		private bool VuePrete =>
			_semainePrete == null
			&& (_etale == null || _simMode != SimMode.Saison || _etale.Saison == _season);

		/// <summary>État d'une application de snapshot, reprise frame après frame.</summary>
		private sealed class Etalement
		{
			public readonly GDict Snap;
			public readonly bool Fade;
			public readonly string Saison;          // saison du snapshot (garde de bascule)
			public PlanteLue[] Lues;                // plantes déjà lues (pool), ou null
			public int Famille;                     // 0..6 : prochaine famille à traiter
			public Godot.Collections.Array Plantes; // payloads, ordonnés à la famille 1
			public List<int> Ordre;                 // indices, plantes visibles d'abord
			public int Curseur;                     // prochaine plante de Ordre
			public bool MacroCommence;              // nuage MacroLife préparé (famille 2)
			public int Born, Grown, Empty, NSegs;
			public int Attente;      // plantes connues hors marge : donnée stockée seule (T4)
			public long PlantesUs;   // temps passé dans la famille 1 (mesure du gel, T4)
			public long MacroUs;     // idem famille 2 (vie macro) — banc seulement
			public readonly HashSet<string> Seen = new();
			// Index reconstruits À CÔTÉ des index affichés, puis échangés en fin de
			// famille 1 : le clic (dossier) et les butineurs ne voient jamais un
			// index à moitié vide pendant l'étalement.
			public readonly Dictionary<string, GDict> Payloads = new();
			public readonly Dictionary<string, List<Vector2>> ByName = new();

			public Etalement(GDict snap, bool fade, PlanteLue[] lues = null)
			{
				Snap = snap; Fade = fade; Lues = lues;
				Saison = LectureSnap.S(snap, "season");
			}
		}

		/// <summary>Step hebdomadaire : appliqué en 7 familles sur plusieurs frames.
		/// Arrivé pendant un étalement → mis en réserve (remplace une réserve plus
		/// ancienne, cas qui ne se produit pas : VuePrete bloque le step).</summary>
		private void ApplySnapshotEtale(SemaineRecue s)
		{
			if (_etale != null) _semainePrete = s;
			else _etale = new Etalement(s.Snap, true, s.Plantes);
		}

		/// <summary>Appelé à chaque frame par _Process : avance d'UNE famille
		/// (ou d'une tranche de plantes). Fin de l'étalement → _etale = null. La
		/// semaine en réserve démarre à la frame SUIVANTE : la frame de fin laisse
		/// passer l'attente et le tapis (gardés par `_etale == null`).</summary>
		private void AvancerEtalement()
		{
			if (_etale == null && _semainePrete != null)
			{
				var s = _semainePrete;
				_semainePrete = null;
				_etale = new Etalement(s.Snap, true, s.Plantes);
			}
			if (_etale != null && Avancer(_etale, BudgetPlantesUs)) _etale = null;
		}

		/// <summary>Traite la famille courante de `e`. Vrai quand tout est appliqué.
		/// `budgetUs` ne borne que les plantes (les autres familles sont courtes).</summary>
		private bool Avancer(Etalement e, long budgetUs)
		{
			_survolVersion++;   // le monde affiché change → survol à recalculer (T3)
			ulong t0 = Time.GetTicksUsec();   // pire passage par famille (banc ④)
			int famille = e.Famille;
			long a0 = System.GC.GetAllocatedBytesForCurrentThread();
			bool fini = AvancerFamille(e, budgetUs);
			NoterFamille(famille, (long)(Time.GetTicksUsec() - t0),
						 System.GC.GetAllocatedBytesForCurrentThread() - a0);
			return fini;
		}

		private bool AvancerFamille(Etalement e, long budgetUs)
		{
			switch (e.Famille)
			{
				case 0: AppliquerSol(e); break;
				case 1:
					if (!AvancerPlantes(e, budgetUs)) return false;   // tranche suivante
					FinirPlantes(e);
					break;
				case 2:
					if (!AvancerVieMacro(e, budgetUs)) return false;   // tranche suivante
					if (CaptureActive) GD.Print($"[Etalement] vie macro {e.MacroUs / 1000.0:F1} ms.");
					AppliquerVieMacro(e);   // butineurs + carpophores (légers)
					break;
				case 3: AppliquerCouchesSol(e.Snap); break;
				case 4: AppliquerStructures(e.Snap); break;
				case 5: AppliquerMeteo(e.Snap); break;
				case 6: AppliquerMenage(e); break;
			}
			e.Famille++;
			return e.Famille >= NbFamilles;
		}

		// Tranche du nuage de vie macro (~10 000 bestioles, la 2ᵉ famille lourde :
		// 30-108 ms d'un bloc mesurés). Même principe que les plantes.
		private bool AvancerVieMacro(Etalement e, long budgetUs)
		{
			if (_macroLife == null || !e.Snap.ContainsKey("sprites")) return true;
			if (!e.MacroCommence)
			{
				_macroLife.BeginSprites(e.Snap["sprites"].AsGodotDictionary(), _origins, e.Fade);
				e.MacroCommence = true;
			}
			ulong t0 = Time.GetTicksUsec();
			bool fini = _macroLife.StepSprites(budgetUs);
			e.MacroUs += (long)(Time.GetTicksUsec() - t0);
			return fini;
		}

		// Tranche de plantes dans le budget. Au 1er appel : ordre « visibles
		// d'abord » (distance au centre de l'écran, ~200 plantes : négligeable).
		private bool AvancerPlantes(Etalement e, long budgetUs)
		{
			if (e.Ordre == null)
			{
				e.Plantes = e.Snap["plants"].AsGodotArray();
				// Chemin synchrone (action, saut, rotation, chargement) : rien n'a été
				// lu hors fil principal → lecture ici, d'un bloc (budget infini).
				if (e.Lues == null)
				{
					e.Lues = new PlanteLue[e.Plantes.Count];
					for (int i = 0; i < e.Plantes.Count; i++)
						using (var p = LectureSnap.Dico(e.Plantes, i)) e.Lues[i] = PlanteLue.Lire(p);
				}
				e.Ordre = new List<int>(e.Plantes.Count);
				var dist = new float[e.Plantes.Count];
				Vector2 centre = _camera != null ? _camera.Position : Vector2.Zero;
				for (int i = 0; i < e.Plantes.Count; i++)
				{
					var l = e.Lues[i];
					Vector2 o = _origins[l.Tile];
					dist[i] = WorldToScreen(o.X + l.X, o.Y + l.Y).DistanceSquaredTo(centre);
					e.Ordre.Add(i);
				}
				e.Ordre.Sort((a, b) => dist[a].CompareTo(dist[b]));
			}
			ulong t0 = Time.GetTicksUsec();
			while (e.Curseur < e.Ordre.Count)
			{
				int i = e.Ordre[e.Curseur++];
				AppliquerPlante(e, e.Plantes[i].AsGodotDictionary(), e.Lues[i]);
				if ((long)(Time.GetTicksUsec() - t0) >= budgetUs) break;
			}
			e.PlantesUs += (long)(Time.GetTicksUsec() - t0);
			return e.Curseur >= e.Ordre.Count;
		}
	}
}
