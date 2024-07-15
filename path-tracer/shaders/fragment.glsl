#version 300 es
precision highp float;
in vec2 uv;
out vec4 fragColor;

uniform vec2 uResolution;
uniform float uFovTangent;
uniform vec3 uCameraPosition;
uniform mat3 uViewMatrix;
uniform uint uTime;

uniform sampler2D tex;



/*
	Constants
*/
// Hash
#define PI 3.14159265
#define PI_INV 0.318309886

#define HASH_NUMBER_1 1597334657U
#define HASH_NUMBER_2 2567812693U
#define HASH_NUMBER_3 3812015819U

#define SEED_MATRIX 31657.0
#define SEED_LIGHT 1024U

// Rendering
#define ERROR 0.0001
#define MINIMUM_DEPTH 2
#define GEOMETRIC_MEAN 2.0

// Objects
#define OBJ_SPHERE 0
#define OBJ_INFINITE_PLANE 1
#define OBJ_AABB 2

// Materials
#define MATERIAL_EMISSIVE 0
#define MATERIAL_SPECULAR 1

#define SKY_BOX 0.2*vec3(1.0, 1.0, 1.0)



/*
	Structures
*/
// Core
struct Ray {
	vec3 origin;
	vec3 dir;
};

struct Hit {
	vec3 origin;
	vec3 position;
	vec3 normal;
	bool isBackfacing;
};

struct Object {
	int type;
	float parameters[6];
	vec3 color;
	int material;
};

struct Light {
	vec3 position;
	vec2 dimensions;
	int object;
};

struct Material {
	int type;
	float parameters[2];
};



/*
	Global objects
*/
uint seed = 0U;

Object objects[11];
Hit hits[11];
int objectCounter = 0;

Light lights[3];
int lightCounter = 0;
float lightTotalArea = 0.0;

Material materials[4];
int materialCounter = 0;



/*
	Random
*/
// Random number generator (input: 2, output: 1)
/*float hash21(uvec2 q) {
	uvec2 m = uvec2(HASH_NUMBER_1, HASH_NUMBER_2);
	q *= m;
	uint n = (q.x^q.y)*HASH_NUMBER_3;
	return (1.0/float(0xffffffffU))*float(n);
}*/
// Random number generator (input: 3, output: 1)
float hash31(uvec3 q) {
	uvec3 m = uvec3(HASH_NUMBER_1, HASH_NUMBER_2, HASH_NUMBER_3);
	q *= m;
	uint n = (q.x^q.y^q.z)*m.x;
	return (1.0/float(0xffffffffU))*float(n);
}

// Random number generator (input: 3, output: 2)
vec2 hash32(uvec3 q) {
	uvec3 m = uvec3(HASH_NUMBER_1, HASH_NUMBER_2, HASH_NUMBER_3);
	q *= m;
	uvec2 n = (q.x^q.y^q.z)*m.xy;
	return (1.0/float(0xffffffffU))*vec2(n);
}

// Random number generator (input: 3, output: 3)
vec3 hash33(uvec3 q) {
	uvec3 m = uvec3(HASH_NUMBER_1, HASH_NUMBER_2, HASH_NUMBER_3);
	q *= m;
	uvec3 n = (q.x^q.y^q.z)*m;
	return (1.0/float(0xffffffffU))*vec3(n);
}



// xi \in [0, 1)
float xi1() {
	uvec3 hashInput = uvec3(gl_FragCoord.xy, SEED_MATRIX*(uViewMatrix[1][1] + 1.0)) + seed + uTime;
	seed++;
	return hash31(hashInput);
}

vec2 xi2() {
	uvec3 hashInput = uvec3(gl_FragCoord.xy, SEED_MATRIX*(uViewMatrix[1][1] + 1.0)) + seed + uTime;
	seed++;
	return hash32(hashInput);
}

vec3 xi3() {
	uvec3 hashInput = uvec3(gl_FragCoord.xy, SEED_MATRIX*(uViewMatrix[1][1] + 1.0)) + seed + uTime;
	seed++;
	return hash33(hashInput);
}



/*
	Color
*/
vec4 encodeColor(vec3 color) {
	float x = max(max(color.r, color.g), color.b);
	if (x <= 0.0)
		return vec4(0.0);
	x = ceil(log(x)/log(1.1));	// minimum x where: max(r, g, b) <= 1.1^x
	return vec4(
		color/pow(1.1, x),
		clamp(0.0, 127.0 + x, 255.0)/255.0
	);
}



vec3 decodeColor(vec4 pixel) {
	if (pixel.a <= 0.0)
		return vec3(0.0);
	float x = 255.0*pixel.a - 127.0;
	return pow(1.1, x)*pixel.rgb;
}



/*
	Material
*/
vec3 fresnel(vec3 color, float cosine) {
	float x = 1.0 - cosine;
	float x5 = x*x*x*x*x;
	return color + (1.0 - color)*x5;
}

float ggxD(float cosine, float a2) {
	float c2 = cosine*cosine;
	float d = c2*(a2 - 1.0) + 1.0;
	return PI_INV*a2/(d*d);
}

/*float ggxV(vec3 light, vec3 normal, vec3 view, float a2) {
	float nl = dot(normal, light);
	float nv = dot(normal, view);

	float gl = nl + sqrt(a2 + (1.0 - a2)*nl*nl);
	float gv = nv + sqrt(a2 + (1.0 - a2)*nv*nv);
	return 1.0f/(gl*gv);
}*/

float smithSchlickV(vec3 light, vec3 normal, vec3 view, float k) {
	float nl = dot(normal, light);
	float nv = dot(normal, view);

	float gl = nl*(1.0 - k) + k;
	float gv = nv*(1.0 - k) + k;
	return 1.0f/(4.0*gl*gv);
}

vec3 cookTorrance(vec3 light, vec3 normal, vec3 view, vec3 color, int mPtr) {
	// Setting up variables
	vec3 halfVector = normalize(light + view);
	float nh = dot(normal, halfVector);
	float hv = dot(halfVector, view);
	float alpha = materials[mPtr].parameters[0];
	alpha *= alpha;

	// Getting D and G terms
	float D = ggxD(nh, alpha*alpha);
	float V = smithSchlickV(light, normal, view, alpha/2.0);
	float f = materials[mPtr].parameters[1];

	if (0.0 <= f) {
		// Dielectric
		vec3 F = fresnel(vec3(f), hv);
		return color*(1.0 - F)*PI_INV + D*V*F;
	} else {
		// Metal
		vec3 F = fresnel(color, hv);
		return D*V*F;
	}
}



/*
	Camera
*/
// generate a ray for this pixel
Ray generateRay() {
	vec2 pos = (2.0*(gl_FragCoord.xy + xi2())- uResolution.xy)/uResolution.y;	// randomized fragment position
	vec3 pixel = vec3(uFovTangent*pos, -1.0);	// disturbed direction

	Ray ray;
	ray.origin = uCameraPosition;
	ray.dir = normalize(uViewMatrix*pixel);
	return ray;
}



/*
	Shapes
*/
void createHit(vec3 origin, vec3 position, vec3 normal, bool isBackfacing, out Hit hit) {
	hit.origin = origin;
	hit.position = position;
	hit.normal = normal;
	hit.isBackfacing = isBackfacing;
}

void createHitFromRay(Ray ray, float t, vec3 normal, bool isBackfacing, out Hit hit) {
	createHit(ray.origin, ray.origin + t*ray.dir, normal, isBackfacing, hit);
}



// Sphere
void createSphere(vec3 position, float radius, out Object obj) {
	obj.parameters[0] = position.x;
	obj.parameters[1] = position.y;
	obj.parameters[2] = position.z;
	obj.parameters[3] = radius;
}

bool castRaySphere(Ray ray, Object obj, out Hit hit) {
	vec3 position = vec3(obj.parameters[0], obj.parameters[1], obj.parameters[2]);
	float radius = obj.parameters[3];
	/*
		Math:
		
		Sphere:
		(x - c)'(x - c) = r^2
		x = o + td
		m = o - c
		t^2 + 2d'mt + m'm = r^2
		
		Algebra:
		t^2 + 2bt + c = 0
		t = -b +- sqrt(b^2 - c)
		D = b^2 - c
		D = (d'm)^2 - m'm + r^2
	*/
	vec3 m = ray.origin - position;
	float b = dot(ray.dir, m);
	float c = dot(m, m) - radius*radius;
	float discriminant = b*b - c;
	
	// no collision
	if (discriminant < 0.0)
		return false;
	
	float sqrt = sqrt(discriminant);	// guaranteed to be valid
	float tp = -b + sqrt;
	if (tp < 0.0)						// solution point behind ray
		return false;
	
	// collision: 0 <= tp is guaranteed
	hit.origin = ray.origin;
	float tm = -b - sqrt;
	
	if (tm < 0.0) {	// back-face
		hit.isBackfacing = true;
		hit.position = ray.origin + (tp - ERROR)*ray.dir;
	} else {			// front-face
		hit.isBackfacing = false;
		hit.position = ray.origin + (tm - ERROR)*ray.dir;
	}

	hit.normal = normalize(hit.position - position);
	return true;
}



// Infinite Plane
void createInfinitePlane(vec3 position, vec3 normal, out Object obj) {
	obj.parameters[0] = position.x;
	obj.parameters[1] = position.y;
	obj.parameters[2] = position.z;
	obj.parameters[3] = normal.x;
	obj.parameters[4] = normal.y;
	obj.parameters[5] = normal.z;
}

bool castRayInfinitePlane(Ray ray, Object obj, out Hit hit) {
	vec3 position = vec3(obj.parameters[0], obj.parameters[1], obj.parameters[2]);
	vec3 normal = vec3(obj.parameters[3], obj.parameters[4], obj.parameters[5]);
	/*
		n'(x - p) = 0
		x = o + td
		n'(o + td - p) = 0
		n'(o - p) + tn'd = 0
		tn'd = n'(p - o)
		t = n'(p - o)/(n'd)
		x = o + (n'(p - o)/(n'd))d
		
		backface <=> n'(o - p) < 0
		backface <=> 0 < n'(p - o)
	*/
	float numerator = dot(normal, position - ray.origin);
	float denominator = dot(normal, ray.dir);
	
	if (denominator == 0.0)
		return false;
	
	float t = numerator/denominator;
	
	if (t < 0.0) {
		return false;
	} else {
		createHitFromRay(ray, t - ERROR, normal, 0.0 < numerator, hit);
		return true;
	}
}



// Axis-Aligned Bounding Box
void createAabb(vec3 position, vec3 dimensions, out Object obj) {
	obj.parameters[0] = position.x;
	obj.parameters[1] = position.y;
	obj.parameters[2] = position.z;
	obj.parameters[3] = dimensions.x;
	obj.parameters[4] = dimensions.y;
	obj.parameters[5] = dimensions.z;
}

bool castRayAabb(Ray ray, Object obj, out Hit hit) {
	vec3 position = vec3(obj.parameters[0], obj.parameters[1], obj.parameters[2]);
	vec3 dimensions = vec3(obj.parameters[3], obj.parameters[4], obj.parameters[5]);

	vec3 minus = (position - dimensions - ray.origin)/ray.dir;
	vec3 plus = (position + dimensions - ray.origin)/ray.dir;
	vec3 tMin3 = min(minus, plus);
	vec3 tMax3 = max(minus, plus);
	
	float tMin = tMin3.x;
	vec3 minNormal = vec3(-1.0, 0.0, 0.0);
	if (tMin < tMin3.y) {
		tMin = tMin3.y;
		minNormal = vec3(0.0, -1.0, 0.0);
	}
	if (tMin < tMin3.z) {
		tMin = tMin3.z;
		minNormal = vec3(0.0, 0.0, -1.0);
	}
	
	float tMax = tMax3.x;
	vec3 maxNormal = vec3(1.0, 0.0, 0.0);
	if (tMax3.y < tMax) {
		tMax = tMax3.y;
		maxNormal = vec3(0.0, 1.0, 0.0);
	}
	if (tMax3.z < tMax) {
		tMax = tMax3.z;
		maxNormal = vec3(0.0, 0.0, 1.0);
	}
	
	float t;
	if (tMax < tMin || tMax < 0.0)
		// no collision
		return false;
	if (tMin < 0.0) {
		// backface
		t = tMax - ERROR;
		hit.normal = sign(ray.dir)*maxNormal;
		hit.isBackfacing = true;
	} else {
		// frontface
		t = tMin - ERROR;
		hit.normal = sign(ray.dir)*minNormal;
		hit.isBackfacing = true;
	}

	hit.origin = ray.origin;
	hit.position = ray.origin + t*ray.dir;
	return true;
}



/*
	Scene
*/
void createObject(int type, vec3 color, int material) {
	objects[objectCounter].type = type;
	objects[objectCounter].color = color;
	objects[objectCounter].material = material;
	objectCounter++;
}

void createLight(vec3 position, vec2 dimensions) {
	lights[lightCounter].position = position;
	lights[lightCounter].dimensions = dimensions;
	lights[lightCounter].object = objectCounter;
	lightTotalArea += 4.0*dimensions.x*dimensions.y;
	lightCounter++;
}

int createMaterial(int type) {
	materials[materialCounter].type = type;
	materialCounter++;
	return materialCounter - 1;
}



void createScene() {
	// Emissive material
	int emissiveMaterial = createMaterial(MATERIAL_EMISSIVE);

	// Diffuse Material
	int diffuseMaterial = createMaterial(MATERIAL_SPECULAR);
	materials[diffuseMaterial].parameters[0] = 1.0;	// roughness
	materials[diffuseMaterial].parameters[1] = 0.0;	// dielectric

	// Dielectric Material
	int dielectricMaterial = createMaterial(MATERIAL_SPECULAR);
	materials[dielectricMaterial].parameters[0] = 0.3;	// roughness
	materials[dielectricMaterial].parameters[1] = 0.5;	// dielectric

	// Metal Material
	int metalMaterial = createMaterial(MATERIAL_SPECULAR);
	materials[metalMaterial].parameters[0] = 0.3;	// roughness
	materials[metalMaterial].parameters[1] = -1.0;	// dielectric



	// Sphere 0
	createSphere(
		vec3(0.0, 0.0, 1.0),
		1.0,
		objects[objectCounter]
	);
	createObject(
		OBJ_SPHERE,
		vec3(1.0, 0.0, 0.0),
		dielectricMaterial
	);

	// Sphere 1
	createSphere(
		vec3(1.0, 1.0, 2.0),
		0.2,
		objects[objectCounter]
	);
	createObject(
		OBJ_SPHERE,
		vec3(1.0, 1.0, 0.0),
		metalMaterial
	);



	float t = 0.01;
	vec3 room = vec3(3.0, 3.0, 2.01);
	// Plane down
	createAabb(
		vec3(0.0, 0.0, -t),
		vec3(room.xy, t),
		objects[objectCounter]
	);
	createObject(
		OBJ_AABB,
		vec3(1.0, 1.0, 1.0),
		dielectricMaterial
	);

	// Plane up
	createAabb(
		vec3(0.0, 0.0, 2.0*room.z + t),
		vec3(room.xy, t),
		objects[objectCounter]
	);
	createObject(
		OBJ_AABB,
		vec3(1.0, 1.0, 1.0),
		diffuseMaterial
	);

	// Plane left
	createAabb(
		vec3(0.0, -(room.y + t), room.z),
		vec3(room.x, t, room.z),
		objects[objectCounter]
	);
	createObject(
		OBJ_AABB,
		vec3(1.0, 0.0, 0.0),
		diffuseMaterial
	);

	// Plane right
	createAabb(
		vec3(0.0, (room.y + t), room.z),
		vec3(room.x, t, room.z),
		objects[objectCounter]
	);
	createObject(
		OBJ_AABB,
		vec3(0.0, 1.0, 0.0),
		diffuseMaterial
	);

	// Plane back
	createAabb(
		vec3(-(room.x + t), 0.0, room.z),
		vec3(t, room.yz),
		objects[objectCounter]
	);
	createObject(
		OBJ_AABB,
		vec3(1.0, 1.0, 1.0),
		metalMaterial
	);



	// Axis-Aligned Bounding Box 0
	createAabb(
		vec3(-1.0, -2.0, 1.0),
		vec3(0.5, 0.5, 1.0),
		objects[objectCounter]
	);
	createObject(
		OBJ_AABB,
		vec3(0.0, 0.0, 1.0),
		dielectricMaterial
	);



	// Axis-Aligned Bounding Box left (Light)
	/*createAabb(
		vec3(0.0, -2.0, 4.0),
		vec3(0.8, 0.8, 0.0),
		objects[objectCounter]
	);
	createLight(
		vec3(0.0, -2.0, 4.0),
		vec2(0.8, 0.8)
	);
	createObject(
		OBJ_AABB,
		16.0*vec3(1.0, 0.0, 0.0),
		emissiveMaterial
	);*/

	// Axis-Aligned Bounding Box center (Light)
	createAabb(
		vec3(0.0, 0.0, 4.0),
		vec3(1.0, 1.0, 0.0),
		objects[objectCounter]
	);
	createLight(
		vec3(0.0, 0.0, 4.0),
		vec2(1.0, 1.0)
	);
	createObject(
		OBJ_AABB,
		16.0*vec3(1.0, 1.0, 1.0),
		emissiveMaterial
	);

	// Axis-Aligned Bounding Box right (Light)
	/*createAabb(
		vec3(0.0, 2.0, 4.0),
		vec3(0.8, 0.8, 0.0),
		objects[objectCounter]
	);
	createLight(
		vec3(0.0, 2.0, 4.0),
		vec2(0.8, 0.8)
	);
	createObject(
		OBJ_AABB,
		16.0*vec3(0.0, 0.0, 1.0),
		emissiveMaterial
	);*/
}



/*
	Rendering
*/
int getShortestHit(Ray ray, int i, int s) {
	// Getting data from the i-th object
	int type = objects[i].type;

	// Computing the i-th Hit
	switch (type) {
	case OBJ_SPHERE:
		if (!castRaySphere(ray, objects[i], hits[i]))
			return s;
		break;
	case OBJ_INFINITE_PLANE:
		if (!castRayInfinitePlane(ray, objects[i], hits[i]))
			return s;
		break;
	case OBJ_AABB:
		if (!castRayAabb(ray, objects[i], hits[i]))
			return s;
		break;
	}

	// Compare the i-th Hit with the current shortest Hit
	if (s < 0)
		return i;
	vec3 sDelta = hits[s].position - hits[s].origin;
	vec3 iDelta = hits[i].position - hits[i].origin;
	float sDist2 = dot(sDelta, sDelta);
	float iDist2 = dot(iDelta, iDelta);
	return iDist2 < sDist2 ? i : s;
}



int castRay(Ray ray) {
	int s = -1;

	for (int i = 0; i < objectCounter; i++) {
		s = getShortestHit(ray, i, s);
	}

	return s;
}



vec3 sampleLight(vec3 origin, vec3 normal, out vec3 dir) {
	// xi \in [0.0, 1.0)^3
	vec3 xi = xi3();

	// Chooses a light
	float random = lightTotalArea*xi.z;	// random \in [0.0, lightTotalArea)
	int i = 0;							// light pointer (used later to sample point and check visibility)
	vec2 dims;							// dimensions of the chosen light (used later to sample point)
	while (i < lightCounter) {	// testing each light
		dims = lights[i].dimensions;	// getting dimensions of the current light
		float area = 4.0*dims.x*dims.y;		// computing area of the current light

		if (random < area)
			break;			// break if area is chosen

		random -= area;	// continue searching
		i++;
	}


	// Sample on that light
	vec2 x = 2.0*xi.xy - 1.0;	// x \in [-1.0, 1.0)^2
	vec3 position = lights[i].position + vec3(x*dims, 0.0);	// sampled point
	vec3 diff = position - origin;	// used later to compute the squared distance
	dir = normalize(diff);	// from origin to sampled point (used later)

	// Cast
	Ray ray;
	ray.origin = origin;
	ray.dir = dir;
	int ptr = castRay(ray);	// casted object pointer

	// Check visibility
	if (ptr != lights[i].object)	// if casted object is not the chosen light
		return vec3(0.0);	// return black

	/*	
		           t
		     dA*(-n w)
		dw = ---------
		            2
		       ||p||
	*/
	float dw = -dot(dir, hits[ptr].normal)/dot(diff, diff);
	return dot(dir, normal)*lightTotalArea*dw*objects[ptr].color;	// n'w dw
}



/*vec3 ggxSample(vec3 normal, vec3 view, int mPtr, out float pdf) {
	float a2 = materials[mPtr].parameters[0];
	a2 *= a2;
	a2 *= a2;

	// Householder basis
	float sigma = 0.0 < normal.z ? -1.0 : 1.0;
	vec3 v = normalize(normal - vec3(0.0, 0.0, sigma));

	// GGX Sampling
	vec2 xi = xi2();
	float c2 = (1.0 - xi.y)/(xi.y*(a2 - 1.0) + 1.0);
	float cosTheta = sqrt(c2);
	float sinTheta = sqrt(max(0.0, 1.0 - c2));
	vec3 halfVector = normal;/*
		sinTheta*cos(2.0*PI*xi.x)*(vec3(1.0, 0.0, 0.0) - 2.0*v.x*v) +
		sinTheta*sin(2.0*PI*xi.x)*(vec3(0.0, 1.0, 0.0) - 2.0*v.y*v) +
		cosTheta*normal
	;

	// GGX PDF
	float hv = dot(halfVector, view);
	float d = c2*(a2 - 1.0) + 1.0;
	pdf = PI_INV*PI_INV*a2/(d*d);

	// GGX vector
	return -reflect(view, normal);
}*/



vec3 sampleMalley(vec3 normal, out float pdf) {
	// Householder basis
	float sigma = 0.0 < normal.x ? -1.0 : 1.0;
	vec3 v = normalize(normal - vec3(sigma, 0.0, 0.0));
	/*mat3 H;
	H[0] = vec3(1.0, 0.0, 0.0) - 2.0*v.x*v;
	H[1] = vec3(0.0, 1.0, 0.0) - 2.0*v.y*v;
	H[2] = vec3(0.0, 0.0, 1.0) - 2.0*v.z*v;*/

	// Malley's sampling
	vec2 xi = xi2();
	float sinTheta = sqrt(xi.y);
	float cosTheta = sqrt(1.0 - xi.y);
	pdf = cosTheta*PI_INV;
	
	//return sigma*H*vec3(cosTheta, sinTheta*cos(2.0*PI*xi.x), sinTheta*sin(2.0*PI*xi.x));
	return
		cosTheta*normal +
		sinTheta*cos(2.0*PI*xi.x)*(vec3(0.0, 1.0, 0.0) - 2.0*v.y*v) +
		sinTheta*sin(2.0*PI*xi.x)*(vec3(0.0, 0.0, 1.0) - 2.0*v.z*v)
	;
}



vec3 traceRay() {
	// Cast ray from camera
	Ray ray = generateRay();
	int ptr = castRay(ray);

	// Skybox
	if (ptr < 0)
		return vec3(0.0);
	
	// Emissive
	if (materials[objects[ptr].material].type == MATERIAL_EMISSIVE)
		return objects[ptr].color;
	
	// Specular
	if (materials[objects[ptr].material].type == MATERIAL_SPECULAR) {
		vec3 light;
		vec3 normal = hits[ptr].normal;
		vec3 view = -ray.dir;
		vec3 radiance = sampleLight(hits[ptr].position, hits[ptr].normal, light);
		return radiance*cookTorrance(
			light,
			normal,
			view,
			objects[ptr].color,
			objects[ptr].material
		);
	}
}



vec3 tracePath() {
	// Setting variables up
	vec3 transmittance = vec3(1.0);
	vec3 color = vec3(0.0, 0.0, 0.0);

	/*
		Cast the first ray from the camera
	*/
	Ray ray = generateRay();
	int ptr = castRay(ray);

	// Skybox
	if (ptr < 0)
		return SKY_BOX;

	// Emissive
	if (materials[objects[ptr].material].type == MATERIAL_EMISSIVE)
		return objects[ptr].color;
	
	/*
		Specular
	*/
	// MIS variables
	float accumulatedWeight = 1.0;

	// Constructing the path
	int i = 0;
	while (true) {
		// BRDF variables
		vec3 light;
		vec3 normal = hits[ptr].normal;
		vec3 view = -ray.dir;

		// MIS variables
		float lightPDF = 1.0/(lightTotalArea);
		float malleyPDF;
		ray.dir = sampleMalley(normal, malleyPDF);	// computes the malleyPdf and the new ray direction

		/*
			Sampling the light
		*/
		// Saving previous data before casting ray
		ray.origin = hits[ptr].position;	// the ray for BRDF is ready!

		// Computing color
		vec3 lightColor = sampleLight(ray.origin, normal, light);	// computes the light vector and the sampled light color
		lightColor *= transmittance*cookTorrance(	// computes the BRDF
			light,
			normal,
			view,
			objects[ptr].color,
			objects[ptr].material
		);

		// Veach Heuristic
		float totalWeight = lightPDF*lightPDF + malleyPDF*malleyPDF;
		float lightWeight = (lightPDF*lightPDF)/totalWeight;
		float malleyWeight = (malleyPDF*malleyPDF)/totalWeight;

		color += accumulatedWeight*lightWeight*lightColor;
		/*if (malleyWeight == 0.0)
			accumulatedWeight = 0.0;
		else*/
		accumulatedWeight *= malleyWeight;

		/*
			Sampling the BRDF
		*/
		// Computing BRDF
		light = ray.dir;
		transmittance *= cookTorrance(
			light,
			normal,
			view,
			objects[ptr].color,
			objects[ptr].material
		);

		// Cast ray
		ptr = castRay(ray);
		vec3 k = accumulatedWeight*transmittance*dot(normal, light)/malleyPDF;

		// Skybox
		if (ptr < 0)
			return color + k*SKY_BOX;

		// Emissive
		if (materials[objects[ptr].material].type == MATERIAL_EMISSIVE)
			return color + k*objects[ptr].color;
		
		// Another Specular
		if (i < MINIMUM_DEPTH)
			i++;
		else {
			float xi = xi1();
			float q = 1.0/GEOMETRIC_MEAN;
			if (q <= xi)
				transmittance /= 1.0 - q;
			else
				break;
		}
	}

	return color;
}



/*
	Main
*/
void main() {
	// Initial configuration
	createScene();

	float i = float(uTime);
	vec3 color = (i/(i + 1.0))*decodeColor(texture(tex, uv));
	color += (1.0/(i + 1.0))*tracePath();

	// Render
	fragColor = encodeColor(color);
	//fragColor = vec4(tracePath(), 1.0);
}