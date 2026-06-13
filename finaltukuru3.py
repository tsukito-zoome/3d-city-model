import numpy as np
from scipy.spatial import Delaunay
from scipy.spatial.qhull import QhullError
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

# ------------------------------------------
# 点群ファイル読み込み
# ------------------------------------------
def load_points(path):
    pts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            pts.append(list(map(float, line.split())))
    return np.array(pts)

# ------------------------------------------
# クラスタリング
# ------------------------------------------
def cluster_points(pts, eps=2.0, min_samples=5):
    if len(pts) < 3:
        return []

    db = DBSCAN(eps=eps, min_samples=min_samples).fit(pts[:, :2])
    labels = db.labels_

    clusters = []
    for lab in set(labels):
        if lab == -1:
            continue
        clusters.append(pts[labels == lab])
    return clusters

# ------------------------------------------
# 地面や建物の平滑化
# ------------------------------------------
def smooth_ground(points, k=10):
    if len(points) < k:
        return points

    nbrs = NearestNeighbors(n_neighbors=k).fit(points[:, :2])
    _, idx = nbrs.kneighbors(points[:, :2])

    out = points.copy()
    out[:, 2] = np.mean(points[idx][:, :, 2], axis=1)
    return out

# ------------------------------------------
# Delaunay を安全に実行
# ------------------------------------------
def safe_delaunay(points_xy):
    points_xy = np.unique(points_xy, axis=0)
    if len(points_xy) < 3 or np.std(points_xy[:, 0]) < 1e-6 or np.std(points_xy[:, 1]) < 1e-6:
        return None
    try:
        return Delaunay(points_xy).simplices
    except QhullError:
        return None
    except Exception:
        return None

# ------------------------------------------
# 三角形フィルタ
# ------------------------------------------
def filter_triangles(points, triangles, max_dist=2.0):
    if triangles is None:
        return []

    filtered = []
    for a, b, c in triangles:
        pa, pb, pc = points[a], points[b], points[c]
        if (np.linalg.norm(pa[:2] - pb[:2]) < max_dist and
            np.linalg.norm(pb[:2] - pc[:2]) < max_dist and
            np.linalg.norm(pc[:2] - pa[:2]) < max_dist):
            filtered.append([a, b, c])
    return filtered

# ------------------------------------------
# VRML 出力
# ------------------------------------------
def write_vrml(output_file, shapes):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#VRML V2.0 utf8\n")
        for pts, tri, color in shapes:
            if len(tri) == 0:
                continue
            f.write("Shape {\n")
            f.write(" appearance Appearance {\n")
            f.write(f"  material Material {{ diffuseColor {color} }}\n")
            f.write(" }\n")
            f.write(" geometry IndexedFaceSet {\n")
            f.write("  coord Coordinate {\n")
            f.write("   point [\n")
            for x, y, z in pts:
                f.write(f"    {x} {y} {z},\n")
            f.write("   ]\n")
            f.write("  }\n")
            f.write("  coordIndex [\n")
            for a, b, c in tri:
                f.write(f"    {a} {b} {c} -1,\n")
            f.write("  ]\n")
            f.write(" }\n")
            f.write("}\n")
    print(f"VRMLを書き出しました → {output_file}")

# ------------------------------------------
# メイン処理
# ------------------------------------------
def main():
    ground_file = input("地面点群ファイル名: ")
    building_file = input("建物点群ファイル名: ")
    output_file = input("VRML 出力ファイル名: ")

    ground_pts = load_points(ground_file)
    building_pts = load_points(building_file)

    shapes = []

    # ---- 地面処理 ----
    print("地面処理中...")
    for cluster in cluster_points(ground_pts, eps=2.0, min_samples=5):
        if len(cluster) < 3:
            continue
        cluster = smooth_ground(cluster, k=10)
        cluster = np.unique(cluster, axis=0)
        tri = safe_delaunay(cluster[:, :2])
        tri = filter_triangles(cluster, tri)
        if len(tri) == 0:
            continue
        shapes.append((cluster, tri, "1 0 0"))

    # ---- 建物処理（全体平滑化） ----
    print("建物処理中（全体平滑化）...")
    for cluster in cluster_points(building_pts, eps=2.0, min_samples=10):
        if len(cluster) < 3:
            continue
        cluster = np.unique(cluster, axis=0)

        # 建物全体を平滑化
        cluster = smooth_ground(cluster, k=10)

        tri = safe_delaunay(cluster[:, :2])
        tri = filter_triangles(cluster, tri)
        if len(tri) == 0:
            continue

        shapes.append((cluster, tri, "0 1 0"))

    write_vrml(output_file, shapes)

if __name__ == "__main__":
    main()

