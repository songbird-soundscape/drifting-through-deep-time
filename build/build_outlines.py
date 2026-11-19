"""Build the map's outline layers from published data.

Writes two files that index.html loads after the map is up:
  data/crust.b64  Merdith et al. (2021) continental polygons (continental crust out to the
                  continent-ocean boundary, including Greater India), each tied to the page's
                  plate index and valid-time window.
  data/coast.b64  Natural Earth 1:50m coastlines, each vertex tied to the plate and appearance
                  age of the nearest map cell, so the line moves exactly with the dots.

Sources (build/sources/):
  ne_50m_coastline.geojson   Natural Earth 1:50m coastline (public domain), nvkelso/natural-earth-vector
  merdith2021_ContinentalPolygons.zip -> merdith2021_continents/ContinentalPolygons/shapes_continents.gpml
                             Merdith et al. 2021 layer from the GPlates model registry (repo.gplates.org)
  gws_pid_tracks.json        cache: positions from the GPlates Web Service (MERDITH2021) of one point
                             per plate ID, every 10 Myr 0-1000 Ma, used to check plate assignments.
                             Rebuilt with --refresh (needs network).

Format of both outputs: base64 of zlib-deflated little-endian Int16 array.
  crust: repeated [n, plate, begin, end, lon0, lat0, lon1, lat1, ...]  (lon/lat x100, ages in Ma)
  coast: repeated [n, lon0, lat0, plate0, vf0, lon1, ...]                (lon/lat x100)

Usage:  python -I build/build_outlines.py [--refresh]
"""
import base64, collections, json, os, sys, urllib.parse, urllib.request, zlib
import numpy as np
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, 'sources')
sys.path.insert(0, HERE)
import gpml  # noqa: E402

COAST_TOL = 0.04   # deg, Douglas-Peucker tolerance for coastlines (~4 km)
CRUST_TOL = 0.08   # deg, for continental polygons (~9 km)
MATCH_MAX = 1.0    # deg, max 0-540 Ma disagreement allowed when checking a plate assignment


def load_page():
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    a = s.find('PK = ')
    PK, _ = json.JSONDecoder().raw_decode(s[a + 5:])
    raw = lambda k: zlib.decompress(base64.b64decode(PK[k]))
    d = dict(
        lon=np.frombuffer(raw('lon'), np.int16) / 100, lat=np.frombuffer(raw('lat'), np.int16) / 100,
        kind=np.frombuffer(raw('kind'), np.uint8), plate=np.frombuffer(raw('plate'), np.uint16),
        vf=np.frombuffer(raw('vf'), np.uint16), NP=PK['nplates'])
    d['Q'] = (np.frombuffer(raw('Q'), np.int16) / 32767).reshape(len(PK['times']), d['NP'], 4)
    return d


def xyz(lo, la):
    lo, la = np.radians(lo), np.radians(la)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


def rot(q, v):
    w, u = q[..., 0], q[..., 1:]
    t = 2 * np.cross(u, v)
    return v + w[..., None] * t + np.cross(u, t)


def dp(pts, tol):
    """Douglas-Peucker simplification of an (n,2) array; keeps endpoints."""
    if len(pts) < 3: return pts
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1: continue
        a, b = pts[i], pts[j]; seg = b - a; L = np.hypot(*seg)
        p = pts[i + 1:j] - a
        d = np.abs(seg[0] * p[:, 1] - seg[1] * p[:, 0]) / L if L > 0 else np.hypot(p[:, 0], p[:, 1])
        k = int(d.argmax())
        if d[k] > tol:
            keep[i + 1 + k] = True; stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return pts[keep]


def tracks(F, refresh):
    path = os.path.join(SRC, 'gws_pid_tracks.json')
    pids = sorted(set(f['pid'] for f in F)); pt = {}
    for f in F: pt.setdefault(f['pid'], f['rings'][0][0])
    if refresh or not os.path.exists(path):
        times = list(range(0, 1001, 10)); C = {}
        for t in times:
            body = urllib.parse.urlencode({'points': ','.join(f'{pt[p][0]},{pt[p][1]}' for p in pids),
                                           'pids': ','.join(map(str, pids)), 'time': t, 'model': 'MERDITH2021'}).encode()
            C[str(t)] = json.load(urllib.request.urlopen('https://gws.gplates.org/reconstruct/reconstruct_points/', body, timeout=180))['coordinates']
        json.dump({'pids': pids, 'points': [pt[p] for p in pids], 'tracks': C}, open(path, 'w'))
    d = json.load(open(path))
    if 'pids' not in d:   # older cache: keyed by time only, same pid order as above
        d = {'pids': pids, 'points': [pt[p] for p in pids], 'tracks': d}
    return d


def plate_errors(T, P):
    """err[i, idx] = max angular mismatch (deg, 0-540 Ma) between GWS track of pid i and page plate idx."""
    times = [int(t) for t in T['tracks'] if int(t) <= 540]
    v = xyz(*np.array(T['points']).T)                       # (npid,3)
    E = np.zeros((len(T['pids']), P['NP']))
    for t in times:
        g = xyz(*np.array(T['tracks'][str(t)]).T)            # (npid,3)
        r = rot(P['Q'][t // 5][None, :, :], v[:, None, :])   # (npid,NP,3)
        E = np.maximum(E, np.degrees(np.arccos(np.clip((r * g[:, None, :]).sum(-1), -1, 1))))
    return E


def build_crust(P, F, T):
    E = plate_errors(T, P); pidrow = {p: i for i, p in enumerate(T['pids'])}
    land = np.isin(P['kind'], (0, 1)); C = np.c_[P['lon'], P['lat']]
    out, stats = [], collections.Counter()
    for f in F:
        if 'mask' in f['name'].lower(): stats['skip mask'] += 1; continue
        e = E[pidrow[f['pid']]]
        best = int(e.argmin())
        idx = best
        r0 = np.array(f['rings'][0])
        if r0[:, 0].max() - r0[:, 0].min() < 180:
            m = land & Path(r0).contains_points(C)
            if m.sum() >= 3:
                maj = collections.Counter(P['plate'][m]).most_common(1)[0][0]
                if e[maj] <= MATCH_MAX: idx = int(maj); stats['cells'] += 1   # follow the dots when the motion agrees
                else: stats['model (cells disagree)'] += 1
            else: stats['model (no cells)'] += 1
        else: stats['model (crosses 180)'] += 1
        if e[idx] > MATCH_MAX: stats['poor match kept'] += 1
        begin = int(min(4000, f['begin'])) if f['begin'] != float('inf') else 4000
        end = int(max(0, f['end'])) if f['end'] != float('-inf') else 0
        for ring in f['rings'][:1]:   # outer ring only
            r = dp(np.array(ring), CRUST_TOL)
            if len(r) < 4: continue
            out += [len(r), idx, begin, end] + [v for p in np.round(r * 100).astype(int) for v in p]
            stats['verts'] += len(r); stats['polys'] += 1
    return np.array(out, np.int16), stats


def build_coast(P):
    d = json.load(open(os.path.join(SRC, 'ne_50m_coastline.geojson')))
    land = np.where(np.isin(P['kind'], (0, 1)))[0]
    V = xyz(P['lon'][land], P['lat'][land])
    out, stats = [], collections.Counter()
    for f in d['features']:
        g = f['geometry']; lines = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for ln in lines:
            r = dp(np.array(ln, float), COAST_TOL)
            if len(r) < 2: continue
            v = xyz(r[:, 0], r[:, 1])
            near = land[(v @ V.T).argmax(1)]                     # nearest land/shelf cell
            pl, vf = P['plate'][near], P['vf'][near]
            out.append(len(r))
            for (lo, la), p, a in zip(np.round(r * 100).astype(int), pl, vf): out += [lo, la, int(p), int(a)]
            stats['verts'] += len(r); stats['lines'] += 1
    return np.array(out, np.int16), stats


def write(name, arr):
    b = base64.b64encode(zlib.compress(arr.astype('<i2').tobytes(), 9))
    open(os.path.join(ROOT, 'data', name), 'wb').write(b)
    return len(b)


if __name__ == '__main__':
    P = load_page()
    F = gpml.read(os.path.join(SRC, 'merdith2021_continents', 'ContinentalPolygons', 'shapes_continents.gpml'))
    T = tracks(F, '--refresh' in sys.argv)
    crust, cs = build_crust(P, F, T); print('crust', dict(cs), write('crust.b64', crust), 'bytes')
    coast, ks = build_coast(P); print('coast', dict(ks), write('coast.b64', coast), 'bytes')
