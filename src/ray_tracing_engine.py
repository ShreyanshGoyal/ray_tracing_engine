
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
# Setting the pixel count

def main(w,h,ambient,diffuse_c,specular_c,specular_k, depth_max):       
    def normalize(x): #check
        x /= np.linalg.norm(x) # np.linalg.norm returns the l2 norm for the matrix
        return x               # This is normalizing with the l2 norm

    def intersect_plane(O, D, P, N):
        # Every thing here is a 3x1 vector
        # Using Basic Geometry
        denom = np.dot(D, N)
        if np.abs(denom) < 1e-6: # This is because it means that the ray and the plane are almost parallel and hence no intersection
            return np.inf
        d = np.dot(P - O, N) / denom
        if d < 0:  # Because this is a ray
            return np.inf
        return d

    def intersect_sphere(O, D, S, R):
        # Return the distance from O to the intersection of the ray (O, D) with the
        # sphere (S, R), or +inf if there is no intersection.
        # O and S are 3D points, D (direction) is a normalized vector, R is a scalar.
        #Using parameterized form of a ray, solves a quadratic that gives the value both the intersection

        a = np.dot(D, D)
        OS = O - S
        b = 2 * np.dot(D, OS)
        c = np.dot(OS, OS) - R * R
        disc = b * b - 4 * a * c   # Evaluating if roots are real or not
        if disc > 0:
            distSqrt = np.sqrt(disc)
            q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
            t0 = q / a
            t1 = c / q
            t0, t1 = min(t0, t1), max(t0, t1)   # Sorts the parameter value
            if t1 >= 0:
                return t1 if t0 < 0 else t0  #Since the first intersection is needed, we always look for the smaller value
                #This may not be possible when the roots are of opposite sign, hence return larger only when smaller one is negative
        return np.inf

    def intersect(O, D, obj): # Depending on the obj whether sphere or plane returning the inersecting distance of O to intersection point on object
        if obj['type'] == 'plane':
            return intersect_plane(O, D, obj['position'], obj['normal'])
        elif obj['type'] == 'sphere':
            return intersect_sphere(O, D, obj['position'], obj['radius'])

    def get_normal(obj, M):
        # Find normal.
        if obj['type'] == 'sphere':
            N = normalize(M - obj['position']) #Normal the sphere is evaluated(based on current position and the center)
        elif obj['type'] == 'plane':
            N = obj['normal'] # normal of a plane returned from definition
        return N

    def get_color(obj, M):# color of object at point M
        color = obj['color']
        if not hasattr(color, '__len__'): # If there is no color attached, then use the color of M?
            color = color(M)
        return color

    def trace_ray(rayO, rayD):
        # Find first point of intersection with the scene.
        t = np.inf
        for i, obj in enumerate(scene):
            t_obj = intersect(rayO, rayD, obj)
            if t_obj < t:
                t, obj_idx = t_obj, i
        # Return None if the ray does not intersect any object.
        if t == np.inf:
            return
        # Find the object.
        obj = scene[obj_idx]
        # Find the point of intersection on the object.
        M = rayO + rayD * t
        # Find properties of the object.
        N = get_normal(obj, M)
        color = get_color(obj, M)
        toL = normalize(L - M)
        toO = normalize(O - M)
        ###############TO BE INCLUDEDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
        # Shadow: find if the point is shadowed or not.
        l = [intersect(M + N * .0001, toL, obj_sh)
                for k, obj_sh in enumerate(scene) if k != obj_idx]
        if l and min(l) < np.inf:
            return
        # Start computing the color.
        col_ray = ambient
        # Lambert shading (diffuse).
        col_ray += obj.get('diffuse_c', diffuse_c) * max(np.dot(N, toL), 0) * color
        # Blinn-Phong shading (specular).
        col_ray += obj.get('specular_c', specular_c) * max(np.dot(N, normalize(toL + toO)), 0) ** specular_k * color_light
        return obj, M, N, col_ray

    def add_sphere(position, radius, color):
        return dict(type='sphere', position=np.array(position),
            radius=np.array(radius), color=np.array(color), reflection=.5)  # This function returns a dictionary with sphere of given radius, center and color

    def add_plane(position, normal): # This function returns a dictionary of a defined plane
        return dict(type='plane', position=np.array(position),
            normal=np.array(normal),
            color=lambda M: (color_plane0
                if (int(M[0] * 2) % 2) == (int(M[2] * 2) % 2) else color_plane1),
            diffuse_c=.75, specular_c=.5, reflection=.25)

    # List of objects.
    color_plane0 = 1. * np.ones(3)
    color_plane1 = 0. * np.ones(3)
    scene = [add_sphere([.75, .1, 1.], .8, [0., 0., 1.]),
            add_sphere([-.75, .1, 2.25], .5, [0., 1., 0.]),
            add_sphere([-2.75, .1, 3.5], .8, [1., 0., 0.]),
            add_plane([0., -.5, 0.], [0., 1., 0.]),
        ]

    # Light position and color.
    L = np.array([5., 5.,-10.])
    color_light = np.ones(3)

    # Default light and material parameters.

    col = np.zeros(3)  # Current color.
    O = np.array([0., 0.35, -1.])  # Camera.
    Q = np.array([0., 0., 0.])  # Camera pointing to.
    img = np.zeros((h, w, 3))
    r = float(w) / h
    # Screen coordinates: x0, y0, x1, y1.
    S = (-1., -1. / r + .25, 1., 1. / r + .25)
    # S = (-1,-1,1,1)
    #S = (-1., -1. / r , 1., 1. / r )
    # Loop through all pixels.
    for i, x in tqdm(enumerate(np.linspace(S[0], S[2], w)),total = h):
        for j, y in enumerate(np.linspace(S[1], S[3], h)):
                col[:] = 0    # Set the color of the pixel to black
                Q[:2] = (x, y)    # Point the camera to the required point
                D = normalize(Q - O)  # DCS of the ray joining camera and point of interest
                depth = 0 # First, number of reflections is zero
                rayO, rayD = O, D  # Ray definition from camera to point of interest
                reflection = 1.
                # Loop through initial and secondary rays.
                while depth < depth_max:   # Implement recursive
                    traced = trace_ray(rayO, rayD)  # Returns object, point of intersection, normal at the point of intersection and color of ray
                    if not traced: # If traced is null
                        break
                    obj, M, N, col_ray = traced
                    # Reflection: create a new ray.
                    rayO, rayD = M + N * .0001, normalize(rayD - 2 * np.dot(rayD, N) * N) # Now the ray is reflected and initialized to OD for further
                    depth += 1 # Since another reflection has occured
                    col += reflection * col_ray
                    reflection *= obj.get('reflection', 1.) # Taking into account the reflection of objects
                img[h - j - 1, i, :] = np.clip(col, 0, 1)

    plt.imsave('src/output/fig.png', img)

if __name__ == '__main__':
    ambient = .05
    diffuse_c = 1.
    specular_c = 1.
    specular_k = 50
    max_depth = 5 # Max Number of Light Reflections
    width = 200 # Set the width of the image
    height = 300 # Set the height of the image
    main(width, height, ambient, diffuse_c, specular_c, specular_k, max_depth)
