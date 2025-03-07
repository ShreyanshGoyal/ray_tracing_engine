import argparse
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

def main(w, h, ambient, diffuse_c, specular_c, specular_k, depth_max, output_file):
    def normalize(x):
        x /= np.linalg.norm(x)
        return x

    def intersect_plane(O, D, P, N):
        denom = np.dot(D, N)
        if np.abs(denom) < 1e-6:
            return np.inf
        d = np.dot(P - O, N) / denom
        if d < 0:
            return np.inf
        return d

    def intersect_sphere(O, D, S, R):
        a = np.dot(D, D)
        OS = O - S
        b = 2 * np.dot(D, OS)
        c = np.dot(OS, OS) - R * R
        disc = b * b - 4 * a * c
        if disc > 0:
            distSqrt = np.sqrt(disc)
            q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
            t0 = q / a
            t1 = c / q
            t0, t1 = min(t0, t1), max(t0, t1)
            if t1 >= 0:
                return t1 if t0 < 0 else t0
        return np.inf

    def intersect(O, D, obj):
        if obj['type'] == 'plane':
            return intersect_plane(O, D, obj['position'], obj['normal'])
        elif obj['type'] == 'sphere':
            return intersect_sphere(O, D, obj['position'], obj['radius'])

    def get_normal(obj, M):
        if obj['type'] == 'sphere':
            return normalize(M - obj['position'])
        elif obj['type'] == 'plane':
            return obj['normal']

    def get_color(obj, M):
        color = obj['color']
        if not hasattr(color, '__len__'):
            color = color(M)
        return color

    def trace_ray(rayO, rayD):
        t = np.inf
        for i, obj in enumerate(scene):
            t_obj = intersect(rayO, rayD, obj)
            if t_obj < t:
                t, obj_idx = t_obj, i
        if t == np.inf:
            return
        obj = scene[obj_idx]
        M = rayO + rayD * t
        N = get_normal(obj, M)
        color = get_color(obj, M)
        toL = normalize(L - M)
        toO = normalize(O - M)

        l = [intersect(M + N * .0001, toL, obj_sh) for k, obj_sh in enumerate(scene) if k != obj_idx]
        if l and min(l) < np.inf:
            return

        col_ray = ambient
        col_ray += obj.get('diffuse_c', diffuse_c) * max(np.dot(N, toL), 0) * color
        col_ray += obj.get('specular_c', specular_c) * max(np.dot(N, normalize(toL + toO)), 0) ** specular_k * color_light
        return obj, M, N, col_ray

    def add_sphere(position, radius, color):
        return dict(type='sphere', position=np.array(position),
                    radius=np.array(radius), color=np.array(color), reflection=.5)

    def add_plane(position, normal):
        return dict(type='plane', position=np.array(position),
                    normal=np.array(normal),
                    color=lambda M: (color_plane0 if (int(M[0] * 2) % 2) == (int(M[2] * 2) % 2) else color_plane1),
                    diffuse_c=.75, specular_c=.5, reflection=.25)

    color_plane0 = 1. * np.ones(3)
    color_plane1 = 0. * np.ones(3)
    scene = [add_sphere([.75, .1, 1.], .8, [0., 0., 1.]),
             add_sphere([-.75, .1, 2.25], .5, [0., 1., 0.]),
             add_sphere([-2.75, .1, 3.5], .8, [1., 0., 0.]),
             add_plane([0., -.5, 0.], [0., 1., 0.])]

    L = np.array([5., 5., -10.])
    color_light = np.ones(3)

    col = np.zeros(3)
    O = np.array([0., 0.35, -1.])
    Q = np.array([0., 0., 0.])
    img = np.zeros((h, w, 3))
    r = float(w) / h
    S = (-1., -1. / r + .25, 1., 1. / r + .25)

    for i, x in tqdm(enumerate(np.linspace(S[0], S[2], w)), total=w):
        for j, y in enumerate(np.linspace(S[1], S[3], h)):
            col[:] = 0
            Q[:2] = (x, y)
            D = normalize(Q - O)
            depth = 0
            rayO, rayD = O, D
            reflection = 1.
            while depth < depth_max:
                traced = trace_ray(rayO, rayD)
                if not traced:
                    break
                obj, M, N, col_ray = traced
                rayO, rayD = M + N * .0001, normalize(rayD - 2 * np.dot(rayD, N) * N)
                depth += 1
                col += reflection * col_ray
                reflection *= obj.get('reflection', 1.)

            img[h - j - 1, i, :] = np.clip(col, 0, 1)

    plt.imsave(output_file, img)
    print(f"Image saved as {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ray Tracing Engine")
    parser.add_argument("--width", type=int, default=200, help="Width of the output image")
    parser.add_argument("--height", type=int, default=300, help="Height of the output image")
    parser.add_argument("--depth", type=int, default=5, help="Max number of light reflections")
    parser.add_argument("--ambient", type=float, default=0.05, help="Ambient lighting intensity")
    parser.add_argument("--diffuse", type=float, default=1.0, help="Diffuse lighting coefficient")
    parser.add_argument("--specular", type=float, default=1.0, help="Specular lighting coefficient")
    parser.add_argument("--specular_k", type=int, default=50, help="Specular exponent for reflection")
    parser.add_argument("--output", type=str, default="/src/output/output.png", help="Output file name")
    args = parser.parse_args()
    main(args.width, args.height, args.ambient, args.diffuse, args.specular, args.specular_k, args.depth, args.output)
