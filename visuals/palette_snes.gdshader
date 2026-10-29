// SYMBIOSE — palette_snes.gdshader (sprint JARDIN VIVANT, T1)
// ⚠️ DÉBRANCHÉ au sprint CASSÉ À L'ÉCRAN ③ (remplacé par la palette indexée des plantes,
// palette_indexee.gdshader) ; gardé, joignable par le banc du seuil (--capture-palette=1).
// Quantification SNES de l'image du monde : chaque pixel du SubViewport
// 960×540 est ramené à la PALETTE MAÎTRE (Palette16.Maitre, ~32 couleurs),
// avec un tramage ordonné Bayer 4×4 entre ses deux couleurs les plus proches.
// Posé sur le SubViewportContainer (cf. PaletteSnes.cs) : HUD et étiquettes,
// hors SubViewport, ne passent PAS ici (voulu : texte net).
//
// 📖 Pédagogie (analogie embarqué) : c'est un CNA ~5 bits avec dithering. Une
// couleur qui tombe ENTRE deux niveaux de la palette n'est pas arrondie
// brutalement (aplats + marches d'escalier) : on alterne les deux niveaux selon
// un motif fixe (matrice de Bayer) dont la densité suit la position de la
// couleur entre eux. L'œil moyenne → un dégradé avec 32 couleurs seulement.
// Le motif est FIXE (indexé par le pixel) : déterministe, aucun bruit animé.
//
// Distance PERCEPTUELLE : OKLab (Björn Ottosson, 2020) — l'écart euclidien y
// suit à peu près ce que l'œil perçoit, contrairement au RVB brut qui confond
// facilement deux verts. La palette arrive déjà convertie (pal_lab, calculée
// une fois en C#) : seul le pixel est converti ici.

shader_type canvas_item;

// Capacité 48 (pal_n = entrées utilisées) : la palette peut grandir un peu
// sans toucher au shader.
const int PAL_MAX = 48;
uniform vec3 pal_srgb[48];          // couleurs affichées (sRGB 0..1)
uniform vec3 pal_lab[48];           // mêmes couleurs en OKLab (distance)
uniform int pal_n = 34;             // entrées réellement utilisées
// Les ACCENTS (fleurs/fruits, en fin de palette à partir de cet index) ne
// servent jamais de PARTENAIRE de tramage : sinon une argile ombrée se moucheté
// de rouge-fruit (constaté T1). Un accent n'apparaît que comme couleur la plus
// proche — là où le dessin l'a voulu (une fleur, un fruit) — et n'est pas tramé.
uniform int pal_accents = 30;
// 0 = arrondi pur (aplats) ; 1 = tramage plein. « Léger » ≈ 0.5 : on ne trame
// que la bande médiane entre deux couleurs, les zones proches d'une couleur
// de palette restent unies (lisibilité pixel-art).
uniform float tramage : hint_range(0.0, 1.0) = 0.5;
// VISION (sol qui respire ⑧) : 0 = jeu normal ; 1 = vision ; 2 = overdose. On
// étire la CHROMA en OKLab AVANT la quantification → les couleurs choisies dans
// la palette sont plus vives, mais restent DES COULEURS DE LA PALETTE.
uniform float vision = 0.0;

// Matrice de Bayer 4×4 (seuils 0..15) — l'ordre classique, ligne par ligne.
const float BAYER[16] = float[16](
	0.0, 8.0, 2.0, 10.0,
	12.0, 4.0, 14.0, 6.0,
	3.0, 11.0, 1.0, 9.0,
	15.0, 7.0, 13.0, 5.0);

vec3 srgb_vers_oklab(vec3 c) {
	vec3 lin = mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c));
	vec3 lms = vec3(
		0.4122214708 * lin.r + 0.5363325363 * lin.g + 0.0514459929 * lin.b,
		0.2119034982 * lin.r + 0.6806995451 * lin.g + 0.1073969566 * lin.b,
		0.0883024619 * lin.r + 0.2817188376 * lin.g + 0.6299787005 * lin.b);
	lms = pow(max(lms, vec3(0.0)), vec3(1.0 / 3.0));
	return vec3(
		0.2104542553 * lms.x + 0.7936177850 * lms.y - 0.0040720468 * lms.z,
		1.9779984951 * lms.x - 2.4285922050 * lms.y + 0.4505937099 * lms.z,
		0.0259040371 * lms.x + 0.7827717662 * lms.y - 0.8086757660 * lms.z);
}

void fragment() {
	vec4 src = texture(TEXTURE, UV);
	vec3 p = srgb_vers_oklab(src.rgb);
	p.yz *= 1.0 + 0.45 * vision;   // chroma ×1,45 (vision) / ×1,9 (overdose)
	p.x = min(p.x * (1.0 + 0.05 * vision), 1.0);

	// i1 = la couleur la plus proche (toutes) ; i2 = la plus proche des
	// NON-accents hors i1 (le partenaire de tramage).
	int i1 = 0;
	float d1 = 1e9;
	for (int i = 0; i < PAL_MAX; i++) {
		if (i >= pal_n) break;
		vec3 d = p - pal_lab[i];
		float dd = dot(d, d);
		if (dd < d1) { d1 = dd; i1 = i; }
	}
	int i2 = i1;
	float d2 = 1e9;
	for (int i = 0; i < PAL_MAX; i++) {
		if (i >= pal_accents || i >= pal_n) break;
		if (i == i1) continue;
		vec3 d = p - pal_lab[i];
		float dd = dot(d, d);
		if (dd < d2) { d2 = dd; i2 = i; }
	}
	if (i1 >= pal_accents) i2 = i1;   // un accent reste un aplat net

	// Position t ∈ [0,1] du pixel sur le segment i1→i2 (0 = pile sur i1).
	vec3 e = pal_lab[i2] - pal_lab[i1];
	float t = clamp(dot(p - pal_lab[i1], e) / max(dot(e, e), 1e-6), 0.0, 1.0);

	// Seuil de Bayer indexé par le PIXEL INTERNE (960×540), pas par le pixel
	// écran : le motif suit la grille pixel-art (gros pixels 2×2 à l'écran).
	ivec2 px = ivec2(floor(UV / TEXTURE_PIXEL_SIZE));
	float bayer = (BAYER[(px.y & 3) * 4 + (px.x & 3)] + 0.5) / 16.0;
	float seuil = mix(0.5, bayer, tramage);

	COLOR = vec4(t > seuil ? pal_srgb[i2] : pal_srgb[i1], src.a);
}
