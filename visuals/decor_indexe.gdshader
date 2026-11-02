// SYMBIOSE — decor_indexe.gdshader (sprint CASSÉ À L'ÉCRAN ⑥ — lisière : dialecte 2, soleil, vent)
// Shader UNIQUE du décor de lisière (DecorLayer + sa couche « devant »). Trois rôles :
//  1. LECTURE de la palette indexée (même encodage que palette_indexee.gdshader, cf.
//     visuals/PaletteIndexee.cs) : le texel porte n° de palette + ton + orientation de
//     face, le soleil réel monte/descend le ton → l'éclat suit le soleil, 0 recuisson.
//  2. GRAINS procéduraux du DIALECTE 2 (Chrono Trigger forêt) sur les aplats, calés au
//     PIXEL INTERNE du palier (« même recette, plus de motifs en zoomant ») :
//       orientation 9  = TISSAGE en chevrons 2×3 px (sol, couvert, plateau) ;
//       orientation 10 = ROCHE en blocs 8×4 px à joints (face de falaise) — la face
//                        réelle vient de la couleur de sommet (canal B), donc s'éclaire
//                        au soleil comme une pièce ;
//       orientation 11 / 12 = ÉCORCE, flanc gauche / droit d'un tronc : stries
//                        verticales au hash, puis éclairée comme une face 4 / 0.
//  3. VENT : déformation des sommets (aucun redessin CPU), même onde que les plantes
//     (visuals/WindWave.cs PoseFor) : front qui avance dans le sens du vent, risées,
//     balancement propre ; amplitude par sommet (canal G, px canvas) posée à la
//     construction (houppiers > sous-bois > roseaux ; roche = 0), phase au hash (B).
//
// COULEUR DE SOMMET (posée par DecorLayer.Indexe.cs) — ce n'est plus une couleur :
//   R = valeur (plan du rideau, 1 devant → plus sombre au fond)   G = amplitude du vent
//   B = phase au hash (ou orientation de la face pour la roche)  A = alpha (touche H)
//
// TEXEL de l'atlas (AUTOMNE VISIBLE ⑥) : les 2 bits hauts de G, libres (n° de palette
// ≤ 63 en octet haut), portent la CLASSE de la matière, posée à la construction :
//   0 = inerte (eau, galets, écorce) · 1 = feuillu · 2 = prairie, sous-bois, roseaux
//   3 = sapin et roche (pas de saison, mais la neige et le givre s'y posent)
// Orientation 13 = FLEUR de prairie (éclairée à plat).
//
// 4. SAISON ET MÉTÉO DE LA LISIÈRE (⑥) : couleurs choisies par pied, sans reconstruire
//    la maille (uniforms de DecorLayer.Saison.cs). La phase B sert de hash du pied : il
//    décale sa semaine et son roux, d'où une saison qui gagne le bois pied par pied.
//    La rampe d'arrivée est lue à la VALEUR du texel d'origine : une hêtraie sombre
//    reste plus sombre qu'un bouleau, et tout reste dans la LUT (palette 16 bits).
//    Semaines (wiy 1 = équinoxe de printemps) à calibrer ici : conception §3.5.
//
// 📖 Pédagogie : c'est la même astuce qu'un registre de configuration multiplexé en
// embarqué — 4 octets par sommet, dont le SENS est fixé par un contrat (en-tête), pas
// par leur nom (« color »). Le GPU s'en moque : ce sont 4 nombres interpolés.

shader_type canvas_item;

uniform sampler2D lut : filter_nearest;
uniform vec2 soleil = vec2(0.0, -1.0);   // direction ÉCRAN vers le soleil (normalisée)
uniform float zoom = 1.0;                // palier affiché : 1 px interne = 1/zoom px canvas
// --- vent (posés chaque image par DecorLayer.Vent.cs ; force 0 = immobile) ---
uniform float vent_force = 0.0;
uniform vec2 vent_dir = vec2(1.0, 0.0);  // direction ÉCRAN aval (normalisée)
uniform vec2 onde_k = vec2(0.0);         // cycles par px canvas (projection inverse incluse)
uniform float onde_c = 0.0;              // terme constant (origine du monde)
uniform float onde_f = 0.2;              // fréquence × échelle de force (Hz)
uniform float temps = 0.0;               // WindWave.Temps (s)
uniform vec4 risees = vec4(1.0);         // risées normées (cycle n → risees[n mod 4])

// --- saison et météo (posés par DecorLayer.Saison.cs ; défaut = été, temps calme) ---
uniform float semaine = 20.0;            // week_in_year lissée
uniform float m_seche = 0.0;             // prairie grillée
uniform float m_humide = 0.0;            // prairie sombre
uniform float m_givre = 0.0;
uniform float m_neige = 0.0;
uniform float m_brume_chaude = 0.0;      // voile + tremblement de chaleur
uniform float m_brume_froide = 0.0;      // brume rasante
uniform int r_tendre = 0;
uniform int r_jaune = 0;
uniform int r_orange = 0;
uniform int r_roux = 0;
uniform int r_terne = 0;
uniform int r_regain = 0;
uniform int r_paille = 0;
uniform int r_grille = 0;
uniform int r_sombre = 0;
uniform int r_givre = 0;
uniform int r_neige = 0;
uniform int r_brume_chaude = 0;
uniform int r_brume_froide = 0;
uniform int r_fleur_b = 0;
uniform int r_fleur_j = 0;
// --- floraison des colonies (LISIÈRE NUE ②, pont `floraison`, DecorLayer.Colonies.cs) ---
uniform float f_blanc = 0.0;
uniform float f_jaune = 0.0;
uniform int i_fleur_jaune = -1;          // n° de palette de la teinte « fleur jaune »
// --- couronne d'hiver (LISIÈRE NUE ③) ---
uniform int i_bouleau = -1;              // n° de palette du bouleau, seul feuillu tout nu

const float AMP_MAX = 32.0;              // px canvas pour G = 1
const float SEUIL = 0.3;
const float SEUIL_ECLAT = 0.8;
const int PALETTES_PAR_LIGNE = 64;
const int TEXELS_PAR_PALETTE = 8;
const int CLASSE_FEUILLU = 1;
const int CLASSE_PRAIRIE = 2;
const int CLASSE_SANS_SAISON = 3;
const int ORIENT_FLEUR = 13;
const float DECALAGE_PIED = 5.0;         // semaines d'écart entre le plus précoce et le plus tardif
// Avant LISIÈRE NUE ③ : 0.85. Il faut > 1 : h01 peut valoir 1, et l'hiver ne laisse plus rien.
const float DEGARNI_MAX = 1.02;          // part de couronne absente en plein hiver
const float ENVELOPPE_VITE = 1.4;        // l'enveloppe part avant les bouquets : les branches se voient en automne
const float SEC_BAS = 0.28;              // part de feuilles sèches en bas de couronne
const float SEC_HAUT = 0.10;             // ... et en haut
const float SEC_DEGARNI = 0.6;           // sous ce dégarnissement, les feuilles sèches sont tombées (débourrement)
const float PRAIRIE_LUM_MIN = 0.30;      // plus sombre : sous-bois, pas de fleurs

varying vec4 v_mod;
varying vec2 v_pos;

// Front asymétrique de WindWave.Envelope (montée 12 %, retour jusqu'à 65 %, repos).
float enveloppe(float u) {
	if (u < 0.12) { float x = u / 0.12; return x * x * (3.0 - 2.0 * x); }
	if (u < 0.65) { float x = (0.65 - u) / 0.53; return x * x; }
	return 0.0;
}

float risee(float n) {
	int i = int(mod(n, 4.0));
	return i == 0 ? risees.x : (i == 1 ? risees.y : (i == 2 ? risees.z : risees.w));
}

void vertex() {
	v_mod = COLOR;
	float amp = COLOR.g * AMP_MAX;
	if (vent_force > 0.0 && amp > 0.0) {
		float ph = COLOR.b;
		float f = vent_force;
		float cyc = onde_f * temps - (dot(VERTEX, onde_k) + onde_c) - ph * 0.15;
		float n = floor(cyc);
		float fond = 0.6 * min(f, 1.2);
		float sway = 0.08 * f * sin(2.6 * (0.8 + 0.4 * ph) * temps + ph * 6.2831853);
		float flex = clamp(f * (fond + 0.8 * enveloppe(cyc - n) * risee(n)) + sway, 0.0, 1.0);
		// Calé au pixel INTERNE : la pièce glisse d'un nombre entier de px (Nearest net).
		VERTEX += round(vent_dir * amp * flex * zoom) / zoom;
	}
	// Brume de chaleur (⑥) : le végétal tremble d'1 px interne, jamais la roche (amp = 0).
	if (m_brume_chaude > 0.01 && amp > 0.0) {
		float s = sin(TIME * 2.5 + VERTEX.y * 0.25 + COLOR.b * 6.2831853);
		VERTEX.x += round(s * 1.5 * m_brume_chaude) / zoom;
	}
	v_pos = VERTEX;   // après le vent : le grain d'un houppier suit le houppier
}

uint hache(int x, int y) {
	uint h = uint(x) * 0x9e3779b1u ^ uint(y) * 0x85ebca77u;
	h ^= h >> 15u; h *= 0x2c1b3c6du; h ^= h >> 12u;
	return h;
}

// TISSAGE en chevrons : cellules de 2 px de large × 3 px de haut, décalées d'1 px par
// colonne (diagonale), sens inversé toutes les 3 colonnes (chevron). Dans une cellule :
// rang haut éclairé (+1, une cellule sur deux), rang bas dans l'ombre (−1) ; ~1 cellule
// sur 8 creusée (−1 de plus) = les « tuiles retirées » du brief, au hash.
int tissage(ivec2 ip) {
	int cx = ip.x >> 1;
	int sens = (int(floor(float(cx) / 3.0)) & 1) == 0 ? 1 : -1;
	int y = ip.y + sens * cx;
	int cy = int(floor(float(y) / 3.0));
	int ly = y - 3 * cy;
	uint h = hache(cx, cy);
	int d = ly == 2 ? -1 : (ly == 0 && (h & 1u) == 0u ? 1 : 0);
	if ((h >> 4u & 7u) == 0u) d -= 1;
	return d;
}

// ROCHE : blocs 8×4 px en appareil (rang sur deux décalé de 4), joint = −1 (bas et
// gauche du bloc), arête haute +1, ~1 bloc sur 4 plus sombre, 1 sur 8 plus clair.
int roche(ivec2 ip) {
	int row = ip.y >> 2;
	int x = ip.x + ((row & 1) << 2);
	int col = x >> 3;
	int lx = x - (col << 3), ly = ip.y - (row << 2);
	if (ly == 3 || lx == 0) return -1;
	uint h = hache(col, row);
	int d = ly == 0 ? 1 : 0;
	if ((h & 3u) == 0u) d -= 1; else if ((h >> 2u & 7u) == 0u) d += 1;
	return d;
}

// ÉCORCE : stries verticales d'1 px (une colonne sur 4 creusée, au hash de la colonne,
// rompues tous les 3 à 6 px) — le fût ne se lit plus comme un aplat.
int ecorce(ivec2 ip) {
	uint h = hache(ip.x, ip.y / 5);
	return (h & 3u) == 0u ? -1 : ((h >> 2u & 7u) == 0u ? 1 : 0);
}

vec3 ton_lut(sampler2D table, int id, int ton) {
	return texelFetch(table, ivec2((id % PALETTES_PAR_LIGNE) * TEXELS_PAR_PALETTE + ton, id / PALETTES_PAR_LIGNE), 0).rgb;
}

float clarte(vec3 c) { return dot(c, vec3(0.3, 0.59, 0.11)); }

// La rampe d'arrivée, au ton le plus proche de la valeur d'origine.
vec3 rampe(sampler2D table, int id, float lum) {
	return ton_lut(table, id, int(clamp((lum - 0.12) / 0.8 * 4.0 + 0.5, 0.0, 4.0)));
}

float h01(int x, int y) { return float(hache(x, y) & 255u) / 255.0; }

// Bruit de valeur (4 hashes lissés) : des nappes aux contours organiques, sans blocs.
float bruit(vec2 p) {
	ivec2 i = ivec2(floor(p));
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h01(i.x, i.y), h01(i.x + 1, i.y), f.x),
			   mix(h01(i.x, i.y + 1), h01(i.x + 1, i.y + 1), f.x), f.y);
}

// Matrice de Bayer 4×4 : un voile en tramage, sans couleur hors palette.
float bayer(ivec2 p) {
	int x = p.x & 3, y = p.y & 3;
	int v = (y == 0) ? (x == 0 ? 0 : x == 1 ? 8 : x == 2 ? 2 : 10)
		: (y == 1) ? (x == 0 ? 12 : x == 1 ? 4 : x == 2 ? 14 : 6)
		: (y == 2) ? (x == 0 ? 3 : x == 1 ? 11 : x == 2 ? 1 : 9)
		: (x == 0 ? 15 : x == 1 ? 7 : x == 2 ? 13 : 5);
	return (float(v) + 0.5) / 16.0;
}

// Saison puis météo d'un texel de la lisière. Renvoie la couleur, alpha = texel présent.
vec4 lisiere(vec3 c, int id, int classe, bool fleur, bool pierre, bool enveloppe, ivec2 ip, float ph, float hauteur) {
	float l = clarte(c);
	float present = 1.0;
	float w = mod(semaine + (ph - 0.5) * DECALAGE_PIED, 52.0);
	// Grain en plaques : grosses taches + détail. Calculé seulement s'il sert.
	float grain = 2.0;
	if (m_seche + m_humide + m_givre + m_neige > 0.001) {
		vec2 q = vec2(ip);
		grain = smoothstep(0.2, 0.8, 0.75 * bruit(q / vec2(14.0, 8.0)) + 0.25 * h01(ip.x >> 1, ip.y >> 1));
	}
	if (classe == CLASSE_FEUILLU) {
		if (w < 2.0 || w >= 37.0) c = rampe(lut, r_terne, l);
		else if (w < 10.0) c = rampe(lut, r_tendre, l);
		else if (w >= 33.0) c = rampe(lut, ph < 0.5 ? r_roux : r_orange, l);
		else if (w >= 29.0) c = rampe(lut, ph < 0.4 ? r_orange : r_jaune, l);
		else if (ph < m_seche * 0.25) c = rampe(lut, r_jaune, l);   // canicule : quelques pieds jaunissent
		float degarni = w >= 33.0 ? smoothstep(33.0, 40.0, w) : 1.0 - smoothstep(0.0, 5.0, w);
		// L'enveloppe (fond plein du houppier) part la première : sans elle, plus de disque en hiver.
		float masque = h01(ip.x >> 2, ip.y >> 2);
		if (masque < degarni * (enveloppe ? ENVELOPPE_VITE : DEGARNI_MAX)) present = 0.0;
		// Marcescence : hêtre, charme et chêne gardent quelques feuilles rousses, plus en bas,
		// en touches de 2 px sur 2, plus ou moins selon le pied.
		if (!enveloppe && id != i_bouleau && degarni > SEC_DEGARNI
				&& h01(ip.x >> 1, ip.y >> 1) < mix(SEC_BAS, SEC_HAUT, hauteur) * (0.6 + 0.8 * ph)) {
			c = rampe(lut, r_roux, l + 0.1);
			present = 1.0;
		}
	} else if (classe == CLASSE_PRAIRIE) {
		// Rampe de la saison ; l'été garde sa couleur d'origine (r_sombre pour la pluie).
		bool ete = w >= 12.0 && w < 27.0;
		int rp = (w < 1.5 || w >= 38.0) ? r_paille : (w < 12.0 ? r_tendre : (ete ? r_sombre : r_regain));
		if (!ete) c = rampe(lut, rp, l);
		// Pluie : la prairie s'assombrit dans SA rampe, un hiver pluvieux ne reverdit pas.
		if (grain < m_humide) c = rampe(lut, rp, ete ? l : l - 0.2);
		if (grain < m_seche) c = rampe(lut, r_grille, l);
		// Avant LISIÈRE NUE ② : un pixel de fleur au printemps. C'était une vraie grille, lue
		// en quadrillage au F5 ; les fleurs viennent désormais des colonies du moteur.
		// if (w >= 1.5 && w < 12.0 && l > PRAIRIE_LUM_MIN && m_neige < 0.5) {
		// 	uint hf = hache(ip.x / 6, ip.y / 4);
		// 	if ((hf & 15u) == 0u && (ip.x % 6) == 3 && (ip.y % 4) == 2)
		// 		c = ton_lut(lut, (hf >> 4u & 1u) == 0u ? r_fleur_b : r_fleur_j, 3);
		// }
	} else if (fleur) {
		// Avant LISIÈRE NUE ② : float part = (w < 1.5 || w >= 36.0) ? 0.0 : (w >= 27.0 ? 0.3 : 1.0);
		// La part en fleur vient du pont, par couleur ; le hash du pied décale chaque fleur.
		float part = id == i_fleur_jaune ? f_jaune : f_blanc;
		if (ph >= part || m_neige > 0.5) present = 0.0;
	}
	if (classe != 0 || pierre) {
		if (classe != CLASSE_PRAIRIE && !pierre && grain < m_givre * 0.3 && l > 0.2) c = rampe(lut, r_givre, l + 0.2);
		if (classe == CLASSE_PRAIRIE && grain < m_givre * 0.4) c = rampe(lut, r_givre, l + 0.1);
		// Neige : pleine sur la prairie, sur les faces claires ailleurs.
		if (classe == CLASSE_PRAIRIE) { if (grain < m_neige * 1.1) c = rampe(lut, r_neige, l + 0.25); }
		else if (l > 0.18 && grain < m_neige * 0.75) c = rampe(lut, r_neige, l + 0.3);
	}
	// Brumes : tramage par nappes, jamais un voile uniforme sur tout le décor.
	if (m_brume_froide + m_brume_chaude > 0.001) {
		float v = bayer(ip);
		float nappe = smoothstep(0.4, 0.7, bruit(vec2(ip) / vec2(40.0, 14.0)));
		if (v < m_brume_froide * 0.3 * nappe * (1.0 - hauteur)) c = ton_lut(lut, r_brume_froide, 3);
		if ((classe != 0 || pierre) && v < m_brume_chaude * 0.22 * nappe) c = ton_lut(lut, r_brume_chaude, 3);
	}
	return vec4(c, present);
}

void fragment() {
	// texelFetch (accès tableau, sans filtrage) : un code est un ENTIER, un texel
	// voisin mêlé par le filtrage le rendrait faux (n° de palette, ton décalés).
	vec4 t = texelFetch(TEXTURE, ivec2(floor(UV * vec2(textureSize(TEXTURE, 0)))), 0);
	if (t.a < 0.5) {
		COLOR = vec4(0.0);
	} else {
		ivec3 o = ivec3(round(t.rgb * 255.0));
		if (o.b < 128) {
			// Filet : texel littéral (aucun aujourd'hui) → tel quel.
			COLOR = vec4(t.rgb * v_mod.r, v_mod.a);
		} else {
			int id = o.r + 256 * (o.g & 63);
			int classe = o.g >> 6;
			int ton = (o.b >> 4) & 7;
			int orient = o.b & 15;
			ivec2 ip = ivec2(floor(v_pos * zoom));
			bool pierre = orient == 10;
			bool fleur = orient == ORIENT_FLEUR;
			bool enveloppe = orient == 9 && classe == CLASSE_FEUILLU;
			if (orient == 9) {
				ton += tissage(ip);
			} else if (orient == 10) {
				ton += roche(ip);
				orient = int(v_mod.b * 16.0);   // face réelle (0..7) ou 8 = plat
			} else if (orient == 11 || orient == 12) {
				ton += ecorce(ip);
				orient = orient == 11 ? 4 : 0;
			}
			if (orient < 8) {
				float a = float(orient) * 0.78539816;
				float d = dot(vec2(cos(a), sin(a)), soleil);
				ton += d > SEUIL_ECLAT ? 2 : (d > SEUIL ? 1 : (d < -SEUIL ? -1 : 0));
			}
			ton = clamp(ton, 0, 4);
			vec4 l = lisiere(ton_lut(lut, id, ton), id, classe, fleur, pierre, enveloppe, ip, pierre ? 0.0 : v_mod.b, clamp(v_mod.g * 12.0, 0.0, 1.0));
			COLOR = vec4(l.rgb * v_mod.r, v_mod.a * l.a);
		}
	}
}
