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


/*
    Debanding
*/
vec3 from_linear(const vec3 linear_rgb) {
    const bvec3 cutoff = lessThan(linear_rgb.rgb, vec3(0.0031308));
    const vec3 higher = vec3(1.055) * pow(linear_rgb.rgb, vec3(1.0 / 2.4)) - vec3(0.055);
    const vec3 lower = linear_rgb.rgb * vec3(12.92);
    return mix(higher, lower, cutoff);
}

vec3 to_linear(const vec3 srgb) {
    const bvec3 cutoff = lessThan(srgb.rgb, vec3(0.04045));
    const vec3 higher = pow((srgb.rgb + vec3(0.055)) / vec3(1.055), vec3(2.4));
    const vec3 lower = srgb.rgb / vec3(12.92);
    return mix(higher, lower, cutoff);
}

vec3 interleaved_gradient_noise_3(const vec2 uv) {
    const float phi_inv = 0.61803398875;
    const vec3 rgb_terms = vec3(6.029, -6.029, 2.518);
    return fract(phi_inv * (uv.x + uv.y * rgb_terms));
}

vec3 dithering_2_colors(const vec3 linear, const float count) {
    const vec3 srgb = from_linear(linear);

    // Compute upper and lower bounds
    vec3 lower = floor(count * srgb);
    vec3 upper = lower + 1.0;

    // Convert it to linear sRGB so we get a proper gradient
    upper = to_linear(upper / count);
    lower = to_linear(lower / count);

    // Add noise
    const vec2 p = vec2(gl_GlobalInvocationID.xy);
    const vec3 edge = (linear - lower) / (upper - lower);
    const vec3 noise_step = step(1.0 - edge, interleaved_gradient_noise_3(p));
    return mix(lower, upper, noise_step);
}



void main() {
	vec4 pixel = texture(tex, uv);
	vec3 color = decodeColor(pixel);



	//color = doTonemapping(color, ROOT);

	const float SLOPE = 0.6;
    const float DESATURATION = 0.2;
    color = neutral_tone_mapping(color, SLOPE, DESATURATION);
    color = oklab_chroma_fallback(color);


    // Add noise
    const float count = 256.0;
    color = dithering_2_colors(color, count - 1.0);


	color = linear2Gamma(color);
	fragColor = vec4(color.gbr, 1.0);
}
