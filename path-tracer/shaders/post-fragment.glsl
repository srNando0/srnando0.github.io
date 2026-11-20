#version 300 es
precision highp float;
in vec2 uv;
out vec4 fragColor;

uniform sampler2D tex;



//#define ROOT 4.828427



vec3 decodeColor(vec4 pixel) {
	if (pixel.a <= 0.0)
		return vec3(0.0);
	float x = 255.0*pixel.a - 127.0;
	return pow(1.1, x)*pixel.rgb;
}



vec3 linear2Gamma(vec3 color) {
	bvec3 cutoff = lessThan(color.rgb, vec3(0.0031308));
	vec3 higher = vec3(1.055)*pow(color.rgb, vec3(1.0/2.4)) - vec3(0.055);
	vec3 lower = color.rgb * vec3(12.92);
	return mix(higher, lower, cutoff);
}



/*
vec3 doTonemapping(vec3 color, float r) {
	// define ACES-CG
	mat3 srgbToAp1 = mat3(
		0.612494198536834, 0.070594251610915, 0.020727335004178,
		0.338737251923843, 0.917671483736251, 0.106882231793044,
		0.048855526064502, 0.011704306146428, 0.872338062223856
	);
	mat3 ap1ToSrgb = mat3(
		1.707077341393391, -0.1310087341843325, -0.02450960122569158,
		-0.6199617703400125, 1.13899879428281, -0.1248238298364764,
		-0.08728719115306108, -0.007944958796604444, 1.149392018071762
	);
	
	vec3 c = srgbToAp1*color;
	vec3 n = r*r*c*c;
	vec3 u = vec3(1.0);
	vec3 d = (r*c + u)*(r*c + u) + u;
	vec3 t = ap1ToSrgb*(n/d);
	
	return t;
}
*/



/*
    Matrices
*/
// RGB
const mat3 SRGB_TO_XYZ = mat3(
    vec3( 0.41239079926595948,  0.21263900587151036,  0.01933081871559185),
    vec3( 0.35758433938387796,  0.71516867876775593,  0.11919477979462599),
    vec3( 0.18048078840183429,  0.07219231536073372,  0.95053215224966058)
);

const mat3 XYZ_TO_SRGB = mat3(
    vec3( 3.24096994190452134, -0.96924363628087983,  0.05563007969699361),
    vec3(-1.53738317757009346,  1.87596750150772067, -0.20397695888897656),
    vec3(-0.49861076029300328,  0.04155505740717561,  1.05697151424287856)
);

const mat3 SRGB_TO_REC2020 = mat3(
    vec3( 0.62740389593469908,  0.06909728935823208,  0.01639143887515028),
    vec3( 0.32928303837788369,  0.91954039507545875,  0.08801330787722576),
    vec3( 0.04331306568741723,  0.01136231556630918,  0.89559525324762397)
);

//const mat3 REC2020_TO_SRGB = mat3(
//    vec3( 1.66049100210843440, -0.12455047452159074, -0.01815076335490530),
//    vec3(-0.58764113878854953,  1.13289989712596022, -0.10057889800800738),
//    vec3(-0.07284986331988488, -0.00834942260436948,  1.11872966136291268)
//);


// Oklab
const mat3 OKLAB_M1 = mat3(
    vec3( 0.8189330101,  0.0329845436,  0.0482003018),
    vec3( 0.3618667424,  0.9293118715,  0.2643662691),
    vec3(-0.1288597137,  0.0361456387,  0.6338517070)
);

const mat3 OKLAB_M1_INV = mat3(
    vec3( 1.227013851103521, -0.040580178423281, -0.076381284505707),
    vec3(-0.557799980651822,  1.112256869616830, -0.421481978418013),
    vec3( 0.281256148966468, -0.071676678665601,  1.586163220440795)
);


const mat3 OKLAB_M2 = mat3(
    vec3( 0.2104542553,  1.9779984951,  0.0259040371),
    vec3( 0.7936177850, -2.4285922050,  0.7827717662),
    vec3(-0.0040720468,  0.4505937099, -0.8086757660)
);

const mat3 OKLAB_M2_INV = mat3(
    vec3( 0.999999998450520,  1.000000008881761,  1.000000054672411),
    vec3( 0.396337792173768, -0.105561342323656, -0.089484182094966),
    vec3( 0.215803758060759, -0.063854174771706, -1.291485537864092)
);


/*
    Tone mapping functions
*/
float compute_peak(const vec3 srgb) {
    const vec3 rec2020 = SRGB_TO_REC2020 * srgb;
    return max(max(rec2020.r, rec2020.g), rec2020.b);
}

vec3 threshold_bloom(vec3 srgb) {
    const float peak = max(compute_peak(srgb), 1.0);
    srgb *= (peak - 1.0) / peak;
    return srgb;
}

float decay_function(const float x) {
     return 1.0 / (1.0 + x);
    //return exp(-x);
}

float translated_reinhard(float value, const float slope, const float upper_limit) {
    /*
        Translated Reinhard
        /            / S(x - U) \\
        U|1 + (S - 1)d| -------- ||
        \            \ U(1 - S) //
    */
    value = (slope * (value - upper_limit)) / (upper_limit * (1.0 - slope)); //  inside decay function
    value = upper_limit * (1.0 + (slope - 1.0) * decay_function(value)); // outside decay function
    return value;
}

vec3 neutral_tone_mapping(vec3 srgb, const float slope, const float desaturation) {
    const float peak = compute_peak(srgb);

    // Color not bright enough
    if (peak <= 1.0)
        return slope * srgb;

    // Normalize color and get Lab coordinates
    srgb /= peak;

    // Desaturate using Oklab
    const vec3 white_lab = vec3(1.0, 0.0, 0.0);
    const float lambda = decay_function(desaturation * (peak - 1.0));
    vec3 lab = xyz_to_oklab(SRGB_TO_XYZ * srgb);
    lab = mix(white_lab, lab, lambda);
    srgb = XYZ_TO_SRGB * oklab_to_xyz(lab);

    // Do reinhard for value >= slope
    srgb *= translated_reinhard(peak, slope, 1.0);

    return srgb;
}


void main() {
	vec4 pixel = texture(tex, uv);
	vec3 color = decodeColor(pixel);


	//color = doTonemapping(color, ROOT);

	const float SLOPE = 0.6;
    const float DESATURATION = 0.2;
    color = neutral_tone_mapping(color, SLOPE, DESATURATION);
    color = oklab_chroma_fallback(color);


	color = linear2Gamma(color);
	fragColor = vec4(color, 1.0);
}
