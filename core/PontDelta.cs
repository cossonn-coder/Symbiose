// SYMBIOSE — PontDelta.cs (sprint FLUIDITÉ PC LEVIERS ④ — pont en delta, protocole 0.6.0)
// Côté vue du pont EN DELTA : garde, par plante (`pid`), les segments reçus la fois
// précédente et applique les opérations `segd` du serveur pour retrouver la liste
// COMPLÈTE (miroir exact de data/code/tools/simserver/pont_delta.py, vérifié par
// tests/simserver/delta.py).
//
// Où ça tourne : dans SimBridge.Request, juste après le parse JSON, sur le fil qui a
// fait la requête (pool pour un step / une action, principal pour un snapshot). Le
// résultat est ÉCRIT DANS LE SNAPSHOT lui-même, par plante :
//  · `segs_lus` = PackedFloat32Array, 10 flottants par segment
//    [bx, by, bz, dx, dy, dz, longueur, épaisseur, apex 0/1, âge en semaines] —
//    lu par PlantStructure.FromSnapshot / PlanteLue à la place de `segments` ;
//  · `genes` = remis depuis le cache (le serveur ne l'envoie qu'au 1er envoi).
// Le snapshot se suffit donc à lui-même : la rotation qui ré-applique `_lastSnap`,
// le dossier de plante (payload gardé) et l'étalement le relisent sans état caché.
//
// Ordre : un delta n'a de sens qu'appliqué dans l'ordre d'ENVOI. Le pont est appelé
// depuis deux fils et le parse se fait hors verrou d'I/O → chaque réponse porteuse
// de snapshot reçoit un TICKET sous ce verrou, et `Appliquer` attend son tour.
//
// 📖 Pédagogie (vue de l'embarqué) : c'est le récepteur d'une liaison « image clé +
// différences » (comme une trame de télémesure compressée). Le récepteur garde sa
// copie de l'image ; s'il perd le fil (recopie hors bornes = trame incohérente), il
// lève un drapeau et la requête suivante redemande une image complète (`complet`).
// Zéro logique écologique ici : on recopie et on soustrait des semaines, c'est tout.

using Godot;
using System.Collections.Generic;
using System.Threading;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public sealed class PontDelta
	{
		/// <summary>Flottants par segment dans `segs_lus` (et dans le cache).</summary>
		public const int Pas = 10;

		// Cache par plante : segments au format `segs_lus` mais avec la SEMAINE DE
		// NAISSANCE en dernière colonne (elle ne bouge pas ; l'âge, si).
		private sealed class Entree
		{
			public float[] Segs = System.Array.Empty<float>();
			public Variant Genes;     // dict de gènes reçu au 1er envoi (gardé tel quel)
			public bool AGenes;
		}

		private readonly Dictionary<int, Entree> _plantes = new();
		private readonly object _verrou = new();
		private long _ticketEmis, _ticketApplique;
		private volatile bool _resync = true;   // la prochaine requête demande un complet

		/// <summary>Sous le verrou d'I/O du pont, AVANT l'écriture : demande le delta
		/// (ou une resynchro complète si le cache a été perdu / est incohérent).</summary>
		public void Marquer(GDict msg)
		{
			msg["delta"] = _resync ? "complet" : (Variant)true;
			_resync = false;
		}

		/// <summary>Sous le verrou d'I/O, APRÈS la lecture de la réponse : son rang.</summary>
		public long Ticket() => _ticketEmis++;

		/// <summary>Nouveau monde (init) : tout oublier, redemander un complet.</summary>
		public void Oublier()
		{
			lock (_verrou) _plantes.Clear();
			_resync = true;
		}

		/// <summary>Applique la réponse `resp` (null = réponse perdue) À SON TOUR.
		/// Toute réponse ayant reçu un ticket DOIT passer ici, sinon les suivantes
		/// attendraient pour toujours.</summary>
		public void Appliquer(long ticket, GDict resp)
		{
			lock (_verrou)
			{
				while (_ticketApplique != ticket) Monitor.Wait(_verrou);
				try
				{
					if (resp == null) _resync = true;   // trou dans la suite des deltas
					else if (LectureSnap.A(resp, "snapshot"))
						using (var snap = LectureSnap.Dico(resp, "snapshot")) Materialiser(snap);
				}
				catch (System.Exception e)
				{
					GD.PrintErr($"[PontDelta] delta illisible ({e.Message}) → resynchro.");
					_resync = true;
				}
				finally
				{
					_ticketApplique++;
					Monitor.PulseAll(_verrou);
				}
			}
		}

		private void Materialiser(GDict snap)
		{
			if (!LectureSnap.A(snap, "delta")) return;   // serveur < 0.6.0 : format complet
			using (var bloc = LectureSnap.Dico(snap, "delta"))
			{
				if (LectureSnap.B(bloc, "complet")) _plantes.Clear();
				int semaine = LectureSnap.I(snap, "week");
				using (var plantes = LectureSnap.Tab(snap, "plants"))
					for (int i = 0; i < plantes.Count; i++)
						using (var p = LectureSnap.Dico(plantes, i)) Plante(p, semaine);
				using var disparues = LectureSnap.Tab(bloc, "disparues");
				for (int i = 0; i < disparues.Count; i++)
				{
					using Variant v = disparues[i];
					_plantes.Remove((int)v.AsDouble());
				}
			}
		}

		private void Plante(GDict p, int semaine)
		{
			if (!LectureSnap.A(p, "pid")) return;
			int pid = LectureSnap.I(p, "pid");
			if (!_plantes.TryGetValue(pid, out var e)) _plantes[pid] = e = new Entree();
			// Gènes : reçus au 1er envoi seulement ; remis pour le survol / le dossier.
			// Une plante morte n'en porte pas (même règle que le format complet).
			if (LectureSnap.A(p, "genes")) { e.Genes = p[LectureSnap.Cle("genes")]; e.AGenes = true; }
			else if (e.AGenes && !(LectureSnap.A(p, "dead") && LectureSnap.B(p, "dead")))
				p[LectureSnap.Cle("genes")] = e.Genes;

			float[] anc = e.Segs;
			using var ops = LectureSnap.Tab(p, "segd");
			// 1re passe : taille de la nouvelle liste (recopies + littéraux).
			int n = 0;
			for (int i = 0; i < ops.Count; i++)
			{
				using Variant op = ops[i];
				if (op.VariantType == Variant.Type.Array) n++;
				else { int k = (int)op.AsDouble(); if (k > 0) n += k; }
			}
			var neuf = new float[n * Pas];
			int j = 0, w = 0;   // curseur dans l'ancienne liste, écriture dans la neuve
			for (int i = 0; i < ops.Count; i++)
			{
				using Variant op = ops[i];
				if (op.VariantType == Variant.Type.Array)
				{
					// [parent, bx, by, bz, dx, dy, dz, long, ép, apex, naissance] → parent ignoré
					using var lit = op.AsGodotArray();
					for (int c = 0; c < Pas; c++) neuf[w * Pas + c] = (float)LectureSnap.D(lit, c + 1);
					w++;
					continue;
				}
				int k = (int)op.AsDouble();
				if (k < 0) { j -= k; continue; }
				if ((j + k) * Pas > anc.Length)
				{
					GD.PrintErr($"[PontDelta] plante {pid} : recopie hors bornes → resynchro.");
					_resync = true;
					e.Segs = System.Array.Empty<float>();
					p[LectureSnap.Cle("segs_lus")] = System.Array.Empty<float>();
					return;
				}
				System.Array.Copy(anc, j * Pas, neuf, w * Pas, k * Pas);
				j += k;
				w += k;
			}
			e.Segs = neuf;
			// Sortie : même tableau, dernière colonne = âge (semaine − naissance).
			var sortie = (float[])neuf.Clone();
			for (int s = Pas - 1; s < sortie.Length; s += Pas) sortie[s] = semaine - sortie[s];
			p[LectureSnap.Cle("segs_lus")] = sortie;
		}
	}
}
