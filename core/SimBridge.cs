// SYMBIOSE — SimBridge.cs
// Pont vivant vers le moteur Python (sprint Intégration, tranche 1 — Option B :
// Python = moteur source de vérité, Godot = vue). Lance data/code/tools/
// sim_server.py en SOUS-PROCESS et lui parle par les pipes stdin/stdout.
//
// 📖 Pédagogie — pourquoi un sous-process et pas un portage :
// c'est un UART logiciel. L'OS fournit deux tuyaux fiables et ordonnés entre
// Godot et Python (comme une liaison série carte-mère ↔ microcontrôleur).
// Framing par délimiteur : 1 ligne = 1 message JSON complet. Maître/esclave
// strict : Godot (maître) écrit une commande, lit LA réponse, continue —
// protocole requête/réponse synchrone, comme SPI. Python ne parle jamais
// spontanément → pas de concurrence, déterminisme préservé.
//
// Choix techniques (kickoff 01_pont_minimal.md) :
//  - System.Diagnostics.Process et PAS OS.Execute : OS.Execute est BLOQUANT
//    (lance, attend la fin, rend tout stdout d'un coup) — impossible de
//    dialoguer. Process + RedirectStandardInput/Output donne les deux pipes.
//  - stderr NON redirigé : il file directement dans la console Godot → les
//    tracebacks Python s'affichent là où Nico regarde déjà. (Le rediriger sans
//    le lire risquerait en plus de bloquer Python sur un buffer plein.)
//  - API SYNCHRONE pour cette tranche (Init/StepWeek bloquent quelques ms) :
//    un thread/await viendra quand l'UI devra rester fluide pendant la saison.
//  - Json natif de Godot (Json.ParseString/Stringify), cohérent avec
//    PlantStructure.cs : Variant/Dictionary manipulés nativement, zéro stack
//    de sérialisation .NET ajoutée.
//  - Chemin (tranche 7) : DEUX modes, résolus dans Start(). Mode DISTRIBUÉ =
//    binaire gelé PyInstaller `sim_server[.exe]` posé À CÔTÉ de l'exécutable
//    Godot (il ne peut pas vivre dans le .pck : un exécutable ne se lance pas
//    depuis une archive). Mode DEV (repli) = python3 + script sous res://,
//    inchangé — F5 dans l'éditeur marche toujours sans binaire. La console
//    affiche le mode choisi (témoin).
//  - Encodage des pipes : UTF-8 SANS BOM explicite des deux côtés C#. Sous
//    Windows, .NET prendrait sinon la codepage console (cp1252…) ; et un BOM
//    en tête de flux casserait le premier json.loads côté Python. Le protocole
//    est de toute façon ASCII par construction (json.dumps ensure_ascii côté
//    serveur, verbes sans accents) — ceinture et bretelles.

using Godot;
using System.Diagnostics;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public sealed class SimBridge : System.IDisposable
	{
		// Le serveur s'importe depuis data/code/ (imports absolus du moteur) →
		// on lance python3 AVEC ce répertoire courant.
		public const string ServerScript = "res://data/code/tools/sim_server.py";
		public const string CodeDir = "res://data/code";

		private Process _proc;

		// Verrou d'I/O du pipe : le pont est appelé depuis DEUX mondes — le thread
		// principal (voix/init/skip, appels SYNCHRONES) et les threads du pool
		// (Task.Run step/action/fields). Le garde `PipeFree` côté WorldView ne
		// coordonne que les lancements async ENTRE EUX ; il n'empêche pas un appel
		// synchrone du thread principal de chevaucher une Task déjà en vol. Sans
		// verrou, deux threads font WriteLine+ReadLine en même temps → les lignes
		// JSON s'entrelacent → « Réponse non-JSON » puis désync permanente du tube.
		// Ce lock rend chaque échange write→read ATOMIQUE : c'est le « maître/esclave
		// strict » que l'en-tête promet, enfin garanti quel que soit l'appelant.
		private readonly object _ioLock = new object();

		public bool IsAlive => _proc != null && !_proc.HasExited;

		// Pont EN DELTA (FLUIDITÉ PC LEVIERS ④, protocole 0.6.0) : les requêtes qui
		// rapportent un snapshot (step_week / snapshot / action) demandent les segments
		// en delta ; `PontDelta` les remet au format complet DANS le snapshot (clé
		// `segs_lus`). Désactivable (smoke test console, qui lit `segments`). Un moteur
		// < 0.6.0 ignore la demande et répond complet : rien à faire, c'est toléré.
		public bool ModeDelta { get; set; } = true;
		private readonly PontDelta _delta = new();

		// Identité du moteur lancé (FLUIDITÉ PC ①) : exécutable passé à l'OS (binaire
		// gelé, `python3` ou `python`), puis — à l'init, pont ≥ 0.5.58 — la version du
		// protocole et l'interpréteur Python effectif. Lus par le HUD et le rapport perf.
		public string Lanceur { get; private set; } = "?";
		public string EngineVersion { get; private set; } = "?";
		public string Interpreteur { get; private set; } = "? (pont < 0.5.58)";

		// -------------------------------------------------------------------
		// CYCLE DE VIE DU SOUS-PROCESS
		// -------------------------------------------------------------------

		public bool Start()
		{
			// MODE DISTRIBUÉ (tranche 7) : binaire gelé à côté de l'exécutable
			// Godot. En éditeur, GetExecutablePath() pointe l'éditeur lui-même
			// → pas de binaire à côté → on tombe naturellement sur le repli dev.
			string exeDir = System.IO.Path.GetDirectoryName(OS.GetExecutablePath());
			string binName = OS.GetName() == "Windows" ? "sim_server.exe" : "sim_server";
			string binPath = System.IO.Path.Combine(exeDir, binName);
			if (System.IO.File.Exists(binPath) && TryLaunch(binPath, "", exeDir))
			{
				GD.Print($"[SimBridge] Mode BINAIRE — moteur gelé {binPath} (pid {_proc.Id}).");
				return true;
			}

			// MODE DEV (repli, inchangé) : python3 + script sous res://.
			// GlobalizePath : res://… → chemin absolu disque (l'OS ne connaît
			// pas res://). Ne marche qu'en éditeur/dev. Sous Windows dev,
			// l'interpréteur s'appelle souvent "python" — on tente les deux.
			string script = ProjectSettings.GlobalizePath(ServerScript);
			string cwd = ProjectSettings.GlobalizePath(CodeDir);
			foreach (string python in new[] { "python3", "python" })
			{
				if (TryLaunch(python, $"\"{script}\"", cwd))
				{
					GD.Print($"[SimBridge] Mode DEV — {python} + sim_server.py (pid {_proc.Id}).");
					return true;
				}
			}

			GD.PrintErr("[SimBridge] Aucun moteur lançable : ni binaire gelé "
				+ $"({binPath}), ni python3/python + script.");
			return false;
		}

		private bool TryLaunch(string fileName, string arguments, string cwd)
		{
			var psi = new ProcessStartInfo
			{
				FileName = fileName,
				Arguments = arguments,
				WorkingDirectory = cwd,
				UseShellExecute = false,         // requis pour rediriger les pipes
				RedirectStandardInput = true,    // Godot → Python
				RedirectStandardOutput = true,   // Python → Godot
				// stderr volontairement NON redirigé (cf. en-tête).
				// Sous Windows, une app GUI qui lance une app console ouvre
				// sinon une fenêtre cmd noire à côté du jeu (console parasite).
				// Le serveur reste une app console (il lui faut ses stdio) —
				// c'est au PARENT de ne pas lui créer de fenêtre.
				CreateNoWindow = true,
				// UTF-8 sans BOM (cf. en-tête — codepage Windows, BOM fatal).
				StandardInputEncoding = new System.Text.UTF8Encoding(false),
				StandardOutputEncoding = new System.Text.UTF8Encoding(false),
			};

			try
			{
				_proc = Process.Start(psi);
				Lanceur = fileName;
				BaisserPriorite();
				return true;
			}
			catch (System.Exception e)
			{
				GD.Print($"[SimBridge] {fileName} : lancement impossible ({e.Message}).");
				_proc = null;
				return false;
			}
		}

		// PERF VUE ④ — le moteur passe APRÈS l'affichage. Sur le PC de Nico (2 cœurs),
		// un tick Python (0,8-2,3 s) en mode accéléré volait un cœur au fil principal
		// de Godot. Priorité « sous la normale » : l'OS donne la main à l'affichage
		// d'abord, le moteur prend le temps CPU restant — le tick dure parfois un peu
		// plus, l'image ne saute plus. Baisser sa propre priorité ne demande aucun
		// droit (Windows : BELOW_NORMAL_PRIORITY_CLASS ; Linux/macOS : nice +10,
		// posé avant que Python ne crée ses threads, qui en héritent). Échec = sans
		// gravité : le jeu tourne comme avant, on le dit en console.
		// 📖 Pédagogie (embarqué) : c'est la priorité de tâche d'un RTOS — la tâche
		// d'affichage (échéance à 16 ms) passe devant la tâche de calcul (échéance
		// d'une semaine de jeu), qui tourne dans les creux.
		private void BaisserPriorite()
		{
			try
			{
				_proc.PriorityClass = ProcessPriorityClass.BelowNormal;
				GD.Print($"[SimBridge] moteur en priorité réduite ({_proc.PriorityClass}).");
			}
			catch (System.Exception e)
			{
				GD.Print($"[SimBridge] priorité du moteur inchangée ({e.Message}).");
			}
		}

		public void Quit()
		{
			if (!IsAlive) return;
			Request(new GDict { ["cmd"] = "quit" });
			_proc.WaitForExit(2000);             // EOF/quit → le serveur sort seul
			Dispose();
		}

		public void Dispose()
		{
			if (_proc == null) return;
			if (!_proc.HasExited) _proc.Kill();  // ceinture : jamais de Python zombie
			_proc.Dispose();
			_proc = null;
		}

		// -------------------------------------------------------------------
		// PROTOCOLE v0 — une commande = une réponse (cf. sim_server.py)
		// -------------------------------------------------------------------

		/// <summary>init(seed) → partie STATIQUE du monde (tuiles, maison), ou null.
		/// Options d'INIT du panneau Paramètres (fenêtrage UI T2), toutes deux
		/// OPTIONNELLES : <paramref name="encycloDemarrage"/> ∈ {vierge, amorcee,
		/// fournie} amorce l'encyclopédie de départ ; <paramref name="carnetAnticipe"/>
		/// bascule le carnet interprétatif dès le palier 1. Non renseignées (null),
		/// elles ne sont pas transmises → moteur inchangé (binaire pré-0.5.37 les
		/// ignore de toute façon). <paramref name="vigueurInfinie"/> (réglage de TEST,
		/// pont 0.5.49) : les gestes ne débitent plus la Vigueur.</summary>
		public GDict Init(int seed, string config = "smoke",
						  string encycloDemarrage = null, bool? carnetAnticipe = null,
						  bool? vigueurInfinie = null)
		{
			var msg = new GDict { ["cmd"] = "init", ["seed"] = seed, ["config"] = config };
			if (encycloDemarrage != null) msg["encyclo_demarrage"] = encycloDemarrage;
			if (carnetAnticipe.HasValue) msg["carnet_anticipe"] = carnetAnticipe.Value;
			if (vigueurInfinie.HasValue) msg["vigueur_infinie"] = vigueurInfinie.Value;
			_delta.Oublier();   // nouveau monde : le 1er snapshot delta sera complet
			var resp = Request(msg);
			if (resp == null) return null;
			if (resp.ContainsKey("engine_version")) EngineVersion = resp["engine_version"].AsString();
			if (resp.ContainsKey("python"))
			{
				var py = resp["python"].AsGodotDictionary();
				Interpreteur = $"{py["implementation"].AsString()} {py["version"].AsString()} ({py["executable"].AsString()})";
			}
			return resp["world"].AsGodotDictionary();
		}

		/// <summary>Avance la simulation d'une semaine → snapshot, ou null.</summary>
		public GDict StepWeek()
		{
			var resp = Request(new GDict { ["cmd"] = "step_week" },
				out double pipe, out double parse, out int octets);
			StepPipeMs = pipe; StepParseMs = parse; StepOctets = octets;
			return resp?["snapshot"].AsGodotDictionary();
		}

		// Chronos du DERNIER step (banc accéléré, PLANTE ASSEMBLÉE ③) : écrits par le
		// thread du pool qui fait le step, lus par le fil principal APRÈS que la Task
		// est terminée (IsCompleted = barrière mémoire, pas de verrou nécessaire).
		//  - pipe  = écriture → réponse lue (calcul Python + sérialisation + transport,
		//            attente du verrou comprise) ;
		//  - parse = Json.ParseString de la réponse (thread du pool, PAS le fil
		//            principal — mais sur 2 cœurs il lui dispute quand même le CPU).
		public double StepPipeMs { get; private set; }
		public double StepParseMs { get; private set; }
		public int StepOctets { get; private set; }

		/// <summary>Priorité du moteur LUE APRÈS COUP par l'OS (banc accéléré) : dit si
		/// `BaisserPriorite` tient vraiment (Windows : BelowNormal ; Linux : nice).</summary>
		public string PrioriteEffective()
		{
			if (!IsAlive) return "moteur absent";
			try
			{
				_proc.Refresh();
				return $"{_proc.PriorityClass} (base {_proc.BasePriority})";
			}
			catch (System.Exception e) { return $"illisible ({e.Message})"; }
		}

		/// <summary>Relit l'état courant sans avancer → snapshot, ou null.</summary>
		public GDict GetSnapshot()
		{
			var resp = Request(new GDict { ["cmd"] = "snapshot" });
			return resp?["snapshot"].AsGodotDictionary();
		}

		/// <summary>
		/// Rapport perf enrichi (demande Nico) : `worst` = liste des K pires ticks
		/// (dump par tuile/espèce/segments) + `current` = état courant. Read-only,
		/// lu par le presse-papier (touche C). Synchrone — le verrou d'I/O rend
		/// l'appel sûr même si une Task step/fields est en vol. Null si pas de moteur.
		/// </summary>
		public GDict PerfReport() => Request(new GDict { ["cmd"] = "perf_report" });

		/// <summary>
		/// Geste joueur (protocole v1, tranche 4) : verbe + cible + params.
		/// Renvoie la réponse COMPLÈTE (`result` = ACK/NAK métier + Vigueur,
		/// `snapshot` = état frais joint) — c'est le seul appel où l'appelant a
		/// besoin des deux. Un refus métier (Vigueur insuffisante, cible
		/// introuvable) arrive en `ok:true` + `result.applied=false` : Python
		/// possède les RÈGLES, la vue ne pré-valide rien.
		/// </summary>
		public GDict Action(string verb, GDict target = null, GDict prms = null)
		{
			var msg = new GDict { ["cmd"] = "action", ["verb"] = verb };
			if (target != null) msg["target"] = target;
			if (prms != null) msg["params"] = prms;
			return Request(msg);
		}

		/// <summary>
		/// Mode debug champs écologiques (t6·C) : sans argument → le REGISTRE
		/// (`fields` = liste de noms) ; avec un nom → les grilles par tuile
		/// (`tiles` = {id: {rows, cols, values row-major}}). L'appelant
		/// distingue les deux par la clé présente. Champ inconnu → null
		/// (erreur loggée par Request, le serveur survit).
		/// </summary>
		public GDict Fields(string field = null)
		{
			var msg = new GDict { ["cmd"] = "fields" };
			if (field != null) msg["field"] = field;
			return Request(msg);
		}

		// -------------------------------------------------------------------
		// VOIX NARRATIVES (sprint UI voix, tronçon ②) — commandes READ-ONLY du
		// pont (0.5.11). INVARIANT « Godot bête » : chaque méthode envoie la
		// requête et renvoie la réponse désérialisée TELLE QUELLE. Aucun tri,
		// aucune concaténation, aucun texte fabriqué ici — le corpus verbatim
		// vit en Python (cf. tools/simserver/voix.py). L'appelant (les panneaux
		// ③④) lit les clés du dict renvoyé et se contente de METTRE EN PAGE.
		// -------------------------------------------------------------------

		/// <summary>
		/// Carnet auto du joueur courant. `filtreConcept` non-null → filtre
		/// `{concept}` transmis tel quel. Renvoie la liste d'entrées
		/// (`entrees` = list de {semaine, zone, concept, registre, texte}), ou []
		/// si le pont ne répond pas.
		/// </summary>
		public Godot.Collections.Array Carnet(string concept = null, string espece = null)
		{
			var msg = new GDict { ["cmd"] = "carnet" };
			if (concept != null || espece != null)
			{
				var f = new GDict();
				if (concept != null) f["concept"] = concept;   // filtre ET-combiné
				if (espece != null) f["espece"] = espece;       // clé catalogue (F5)
				msg["filtre"] = f;
			}
			var resp = Request(msg);
			return resp?["entrees"].AsGodotArray() ?? new Godot.Collections.Array();
		}

		/// <summary>
		/// Aide au jardinier (0.5.13, retour F5 « debug d'abord ») : pour une
		/// espèce, les remèdes de ses problèmes récents — `aide` = liste de
		/// {concept, remede, debloque}. Le texte du remède vient de Python
		/// (corpus, « Godot bête ») ; `debloque` = concept maîtrisé (gating futur).
		/// Renvoie [] si le pont ne répond pas.
		/// </summary>
		public Godot.Collections.Array Aide(string espece)
		{
			var resp = Request(new GDict { ["cmd"] = "aide", ["espece"] = espece });
			return resp?["aide"].AsGodotArray() ?? new Godot.Collections.Array();
		}

		/// <summary>
		/// Encyclopédie multi-règnes du joueur courant (D60). Sans `cle` → l'INDEX
		/// des entrées découvertes, TAGUÉES par type (`index` = liste de
		/// {cle, type, titre}), éventuellement restreint à un `type` (un des 7
		/// onglets : plante · animal · champignon · concept · technique · outil ·
		/// geste). Avec `cle` → la fiche DISPATCHÉE par type (`fiche` = {cle, type,
		/// niveau_max, niveaux, interconnexions?}) ou `null`. L'appelant distingue
		/// par la clé présente. Renvoie la réponse COMPLÈTE, ou null.
		///
		/// `cle` part sous l'ancien nom de champ protocole `espece` (alias hérité
		/// accepté par `cmd_encyclopedie`) — compat pont, la vue raisonne en « clé ».
		/// </summary>
		public GDict Encyclopedie(string cle = null, string type = null)
		{
			var msg = new GDict { ["cmd"] = "encyclopedie" };
			if (cle != null) msg["espece"] = cle;   // alias hérité côté pont
			if (type != null) msg["type"] = type;   // filtre d'onglet (index)
			return Request(msg);
		}

		/// <summary>
		/// Pages secrètes TROUVÉES (coffret grenier). Renvoie la réponse complète
		/// (`ids` = liste ordonnée, `pages` = list de {id, voix, concept, texte}),
		/// ou null. Read-only pur.
		/// </summary>
		public GDict Pages() => Request(new GDict { ["cmd"] = "pages" });

		/// <summary>
		/// Offres du magazine (sœurs des familles maîtrisées, hors banque) :
		/// `offres` = liste d'espèces. Renvoie [] si le pont ne répond pas.
		/// </summary>
		public Godot.Collections.Array MagazineOffres()
		{
			var resp = Request(new GDict { ["cmd"] = "magazine" });
			return resp?["offres"].AsGodotArray() ?? new Godot.Collections.Array();
		}

		/// <summary>
		/// Fiche PRODUIT d'une espèce du magazine (argument de vente, indépendant
		/// du palier joueur) : `fiche` = {espece, niveau_max, niveaux} ou `null`.
		/// Renvoie la réponse complète, ou null.
		/// </summary>
		public GDict MagazineFiche(string espece)
			=> Request(new GDict { ["cmd"] = "magazine", ["espece"] = espece });

		/// <summary>
		/// Achat au magazine (Q3) : passe par le verbe `cmd_action`
		/// `acheter_magazine` (chemin Vigueur UNIQUE, cohérent avec tous les
		/// gestes joueur). Renvoie la réponse complète (`result.achete` =
		/// succès/échec métier, `snapshot` = bilan Vigueur rafraîchi), ou null.
		/// La vue ne pré-valide RIEN : Python possède la règle d'achat.
		/// </summary>
		public GDict AcheterMagazine(string espece)
			=> Action("acheter_magazine", prms: new GDict { ["espece"] = espece });

		/// <summary>
		/// Vitrine READ-ONLY de l'ATELIER (acquisition des moyens d'agir ④, pont
		/// 0.5.34) : `outils` = liste de {cle, cout_vigueur, possede}, `materiaux` =
		/// liste de {cle, nature, dose, cout_vigueur}. Le pont possède l'offre + le
		/// coût + la possession (dérivée) — la vue LIT et met en page (« Godot bête »).
		/// Renvoie la réponse complète, ou null (binaire pré-0.5.34 → « commande
		/// inconnue » → l'Atelier s'affiche vide, inoffensif).
		/// </summary>
		public GDict Atelier() => Request(new GDict { ["cmd"] = "atelier" });

		/// <summary>
		/// COURRIER des quêtes (D79 ⑤, pont 0.5.40) : les lettres du joueur, actives
		/// ET accomplies — `lettres` = liste (triée par id) de {id, donneur,
		/// texte_lettre, avancement (phrase DIÉGÉTIQUE, jamais un chiffre), accomplie
		/// (→ coche), atteignable (→ rêve hors catalogue, le kiwi)}. Avec `debug`, chaque
		/// lettre gagne aussi `progression`/`condition` (chiffre exact, mode debug #5).
		/// Le pont calcule tout (avancement, coche, atteignabilité) — la vue LIT et met
		/// en page (« Godot bête »). Renvoie [] si le pont ne répond pas (binaire
		/// pré-0.5.40 → « commande inconnue » → l'onglet Courrier s'affiche vide).
		/// </summary>
		public Godot.Collections.Array Courrier(bool debug = false)
		{
			var msg = new GDict { ["cmd"] = "courrier" };
			if (debug) msg["debug"] = true;
			var resp = Request(msg);
			return resp?["lettres"].AsGodotArray() ?? new Godot.Collections.Array();
		}

		/// <summary>
		/// Acquisition d'un OUTIL à l'Atelier (D82, tronçon ②) : passe par le verbe
		/// `cmd_action` `acheter_outil` (chemin Vigueur UNIQUE, jumeau
		/// d'`AcheterMagazine`). `params.outil` = clé du registre `OUTILS`
		/// (`secateur`). Renvoie la réponse complète (`result.achete` = succès/échec
		/// métier + Vigueur rafraîchie, `snapshot` frais où `gestes_debloques` gagne
		/// `couper` si l'outil est neuf), ou null. La vue ne pré-valide RIEN.
		/// </summary>
		public GDict AcheterOutil(string outil)
			=> Action("acheter_outil", prms: new GDict { ["outil"] = outil });

		/// <summary>
		/// Acquisition d'un MATÉRIAU (mulch) à l'Atelier (canal 3, tronçon ③) : verbe
		/// `cmd_action` `acheter_materiau` (chemin Vigueur UNIQUE). `params.materiau`
		/// = clé du registre `MATERIAUX` (`botte_paille`) → crédite le STOCK de mulch
		/// de sa nature (consommable, PAS idempotent). Renvoie la réponse complète
		/// (`result.achete` + Vigueur, `snapshot`), ou null.
		/// </summary>
		public GDict AcheterMateriau(string materiau)
			=> Action("acheter_materiau", prms: new GDict { ["materiau"] = materiau });

		/// <summary>
		/// Observation par SURVOL (0.5.12, retour F5) : une plante n'est apprise
		/// que si le joueur passe la souris dessus. On envoie le NOM DE CLASSE de
		/// la plante (Meta "species" du renderer, = `cls.__name__` du snapshot) ;
		/// Python résout la clé catalogue et découvre. Idempotent — appelable en
		/// continu (l'appelant déduplique déjà par espèce pour ne pas spammer).
		/// </summary>
		public GDict Observer(string species)
			=> Request(new GDict { ["cmd"] = "observer", ["species"] = species });

		/// <summary>Observation d'un SIGNE visible sur la plante survolée (⑥/⑦) :
		/// `observer` + `signe` + lieu (tuile, cm locaux) → note au carnet, dédupliquée
		/// côté Python par (espèce, signe, saison).</summary>
		public void ObserverSigne(string species, string signe, Variant tile, Variant xCm, Variant yCm)
			=> Request(new GDict { ["cmd"] = "observer", ["species"] = species, ["signe"] = signe,
								   ["tile"] = tile, ["x_cm"] = xCm, ["y_cm"] = yCm });

		/// <summary>VISION (sol qui respire ⑧, pont ≥ 0.5.54) : `parler` à l'ENTRÉE du
		/// survol d'un être → `{vision, phrases}`. `cible` = plante `{tile, x_cm, y_cm}`
		/// ou bête/champignon `{espece, tile, r, c}`. Le pont COMPTE ce survol (ce qui
		/// reste après la vision) : un appel par entrée, jamais par frame.</summary>
		public GDict Parler(GDict cible)
		{
			var msg = cible.Duplicate();
			msg["cmd"] = "parler";
			return Request(msg);
		}

		/// <summary>Légende STATIQUE des signes et des bêtes (⑥/⑦) : `vu` (et `cause`
		/// des signes) — demandée une fois, l'info-bulle gate par `player.appris`.</summary>
		public GDict Legende() => Request(new GDict { ["cmd"] = "legende" });

		/// <summary>
		/// Raccourci DEBUG (0.5.12, retour F5) : `op` ∈ {"palier3", "observer_tout",
		/// "reset"}. Force la maîtrise pour tester magazine/pages/carnet sans jouer
		/// jusqu'au palier 3. Hors golden (pont opt-in). Étiqueté debug côté vue.
		/// </summary>
		public void Debug(string op)
			=> Request(new GDict { ["cmd"] = "debug", ["op"] = op });

		/// <summary>
		/// Persiste le LAYOUT de palette du joueur (palette de gestes ⑤, 0.5.26) :
		/// `slots` = verbes curés (colonne ④), `macros` = liste de {nom, sequence}
		/// (D1/D5). Chaque argument non-null REMPLACE la clé (curation complète — la
		/// vue possède le layout et le renvoie entier). Python VALIDE la cohérence de
		/// cible des macros AVANT d'écrire (refus en bloc, transaction) : une macro
		/// mixte revient `ok:false` et RIEN n'est modifié. « Godot bête » : on envoie
		/// ce que le joueur a curé, la règle vit en Python. Renvoie la réponse complète
		/// (`palette` = layout écrit en miroir), ou null (refus/erreur, loggé par Request).
		/// </summary>
		public GDict Palette(Godot.Collections.Array slots = null,
							  Godot.Collections.Array macros = null)
		{
			var msg = new GDict { ["cmd"] = "palette" };
			if (slots != null) msg["slots"] = slots;
			if (macros != null) msg["macros"] = macros;
			return Request(msg);
		}

		/// <summary>
		/// Liste des bancs d'essai montables (`init config="<nom>"`), DEMANDÉE au
		/// serveur (commande `list_bancs`) : la source reste le registre Python
		/// `BANCS` — le C# ne duplique pas les noms (un menu périmé = le piège D47).
		/// Appelable après Start() SANS Init (lecture du registre, pas du moteur).
		/// Chaque entrée porte sa CATÉGORIE (module thématique, pont 0.5.36) → le
		/// sélecteur filtre par thème. Renvoie [] si le serveur ne répond pas (vieux
		/// binaire gelé pré-0.5.4) → le sélecteur retombe sur full/smoke.
		/// COMPAT : un binaire 0.5.4→0.5.35 renvoie des noms NUS (chaînes) → mappés
		/// en catégorie "divers".
		/// </summary>
		public (string Nom, string Categorie)[] ListBancs()
		{
			var resp = Request(new GDict { ["cmd"] = "list_bancs" });
			if (resp == null) return System.Array.Empty<(string, string)>();
			var arr = resp["bancs"].AsGodotArray();
			var bancs = new (string Nom, string Categorie)[arr.Count];
			for (int i = 0; i < arr.Count; i++)
			{
				if (arr[i].VariantType == Variant.Type.Dictionary)
				{
					var d = arr[i].AsGodotDictionary();
					string cat = d.ContainsKey("categorie")
						? d["categorie"].AsString() : "divers";
					bancs[i] = (d["nom"].AsString(), cat);
				}
				else  // binaire pré-0.5.36 : nom nu → catégorie de repli
					bancs[i] = (arr[i].AsString(), "divers");
			}
			return bancs;
		}

		// -------------------------------------------------------------------
		// JARDINIER AUTOMATE (sprint jardinier_auto ⑥, pont 0.5.30) — commandes
		// de CONTRÔLE de l'automate déterministe branché en OPTION F5. « Godot
		// bête » : la vue envoie l'intention (activer/régler/pousser un objectif),
		// toute la logique (tutelle, table facteur→geste, comptabilité) vit en
		// Python. L'automate joue ENTRE deux ticks côté serveur (invariant H2) ;
		// la vue LIT ensuite le bloc `automate` du snapshot (trace + objectifs).
		// -------------------------------------------------------------------

		/// <summary>
		/// Active/désactive l'automate. `on=true` le monte avec `profil` (dict, défaut
		/// preset LIBRE côté Python) et DÉCLARE le jardin courant cultivé (tutelle) ;
		/// `on=false` le démonte (la trace reste lisible côté vue). Renvoie la réponse
		/// (`actif`, `profil`, `cultivees`), ou null. Un binaire pré-0.5.30 renvoie
		/// null (commande inconnue) → l'appelant garde son état « pas d'automate ».
		/// </summary>
		public GDict Automate(bool on, GDict profil = null)
		{
			var msg = new GDict { ["cmd"] = "automate", ["op"] = on ? "on" : "off" };
			if (on && profil != null) msg["profil"] = profil;
			return Request(msg);
		}

		/// <summary>
		/// Pousse un OBJECTIF (geste+quantité+cible) à l'automate en planification
		/// (injectable à tout moment). `cible` = clé d'espèce du catalogue ; `id` =
		/// identifiant stable (défaut = cible côté Python). Renvoie la réponse
		/// (`id`), ou null. Le suivi de progression apparaît au bloc `automate` du
		/// snapshot suivant (onglet objectifs).
		/// </summary>
		public GDict AutomateObjectif(string geste, int quantite, string cible, string id = null)
		{
			var msg = new GDict
			{
				["cmd"] = "automate", ["op"] = "objectif",
				["geste"] = geste, ["quantite"] = quantite, ["cible"] = cible,
			};
			if (id != null) msg["id"] = id;
			return Request(msg);
		}

		/// <summary>
		/// Cœur du pont : écrit 1 ligne JSON, lit 1 ligne JSON (bloquant).
		/// Retourne le message si ok:true, sinon null (+ erreur en console).
		/// </summary>
		private GDict Request(GDict msg) => Request(msg, out _, out _, out _);

		private GDict Request(GDict msg, out double pipeMs, out double parseMs, out int octets)
		{
			pipeMs = parseMs = 0; octets = 0;
			if (!IsAlive)
			{
				GD.PrintErr("[SimBridge] Requête sur un moteur non démarré/mort.");
				return null;
			}
			// Write→read SOUS VERROU (cf. _ioLock) : l'échange doit être atomique
			// pour que deux threads ne s'entrelacent jamais sur le pipe. Le parse
			// (coûteux, mais local) se fait APRÈS, hors verrou — inutile de le
			// sérialiser, seul l'accès au tube l'exige.
			string line;
			long t0 = Stopwatch.GetTimestamp();
			// Delta (0.6.0) : demande posée et rang pris SOUS le verrou → l'ordre des
			// tickets est l'ordre du tube, quel que soit le fil qui parse ensuite.
			string cmd = msg["cmd"].AsString();
			bool delta = ModeDelta && (cmd == "step_week" || cmd == "snapshot" || cmd == "action");
			long ticket = -1;
			lock (_ioLock)
			{
				if (delta) _delta.Marquer(msg);
				_proc.StandardInput.WriteLine(Json.Stringify(msg));
				_proc.StandardInput.Flush();     // symétrique du flush=True Python
				line = _proc.StandardOutput.ReadLine();
				if (delta && line != null) ticket = _delta.Ticket();
			}
			if (line == null)                    // EOF = le serveur est mort
			{
				GD.PrintErr("[SimBridge] Le moteur Python s'est arrêté (EOF).");
				return null;
			}

			long t1 = Stopwatch.GetTimestamp();
			Variant parsed = Json.ParseString(line);
			pipeMs = (t1 - t0) * 1000.0 / Stopwatch.Frequency;
			octets = line.Length;
			GDict resp = null;
			if (parsed.VariantType != Variant.Type.Dictionary)
				GD.PrintErr($"[SimBridge] Réponse non-JSON : {line}");
			else
			{
				resp = parsed.AsGodotDictionary();
				if (!resp["ok"].AsBool())
				{
					GD.PrintErr($"[SimBridge] Erreur moteur : {resp["error"].AsString()}");
					resp = null;
				}
			}
			// TOUTE réponse à ticket passe par Appliquer (null compris → resynchro),
			// sinon les suivantes attendraient leur tour pour toujours. Le temps de
			// reconstitution des segments est compté dans `parse` (coût de la réponse).
			if (ticket >= 0) _delta.Appliquer(ticket, resp);
			parseMs = (Stopwatch.GetTimestamp() - t1) * 1000.0 / Stopwatch.Frequency;
			return resp;
		}

		// -------------------------------------------------------------------
		// SMOKE TEST (preuve visible de la tranche 1 — appelé depuis TileGrid)
		// Init → StepWeek ×4 → GetSnapshot, résumé en console. Pas de rendu :
		// le tube d'abord (le monde dessiné = tranche 2).
		// -------------------------------------------------------------------

		public static void SmokeTest()
		{
			GD.Print("[SimBridge] — smoke test du pont Python —");
			using var bridge = new SimBridge { ModeDelta = false };   // lit `segments`
			if (!bridge.Start()) return;

			var world = bridge.Init(seed: 42);
			if (world == null) { bridge.Quit(); return; }
			GD.Print($"[SimBridge] init ok : {world["tiles"].AsGodotArray().Count} tuiles + maison.");

			GDict snap = null;
			for (int i = 0; i < 4; i++)
				snap = bridge.StepWeek();
			if (snap == null) { bridge.Quit(); return; }

			var plants = snap["plants"].AsGodotArray();
			GD.Print($"[SimBridge] semaine {snap["week"].AsInt32()} "
					 + $"(an {snap["year"].AsInt32()}, {snap["season"].AsString()}) : "
					 + $"{plants.Count} plantes vivantes.");
			foreach (var pv in plants)
			{
				var p = pv.AsGodotDictionary();
				GD.Print($"    {p["tile"].AsString()} {p["name"].AsString(),-12} "
						 + $"stade={p["stage_name"].AsString()} "
						 + $"h={p["height_cm"].AsDouble():F1}cm "
						 + $"segments={p["segments"].AsGodotArray().Count}");
			}
			bridge.Quit();
			GD.Print("[SimBridge] — smoke test terminé, moteur arrêté proprement —");
		}
	}
}
