import numpy as np
from collections import deque

# ----------------------
# 読み込み
# ----------------------
def load_building_points(filename):
    pts = []
    with open(filename) as f:
        for line in f:
            x,y,z = map(float, line.split())
            pts.append((int(x), int(y), z))
    return pts

# ----------------------
# 建物クラスタ
# ----------------------
HEIGHT_H = 30.0

def cluster_buildings(building_pts):
    xy2z = {}
    low_pts=[]
    for x,y,z in building_pts:
        if z>= 30.0:
            xy2z.setdefault((x,y), []).append(z)
        else:
            low_pts.append((x,y,z))
    visited = set()
    clusters = []

    for (x,y) in xy2z:
        if (x,y) in visited:
            continue

        q = deque([(x,y)])
        visited.add((x,y))
        cluster = []

        while q:
            cx, cy = q.popleft()
            for z in xy2z[(cx,cy)]:
                cluster.append((cx,cy,z))

            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    nx, ny = cx+dx, cy+dy
                    if (nx,ny) in xy2z and (nx,ny) not in visited:
                        visited.add((nx,ny))
                        q.append((nx,ny))

        clusters.append(cluster)

    return clusters, low_pts

# ----------------------
# 地面なし高さ推定
# ----------------------
def building_height_noground(cluster):
    zs = np.array([z for _,_,z in cluster])
    bottom = np.percentile(zs, 5)
    top    = np.percentile(zs, 95)
    return top - bottom, bottom, top

# ----------------------
# Main
# ----------------------
HEIGHT_TH = 50.0

building_pts = load_building_points("building8.dat")
clusters, low_pts = cluster_buildings(building_pts)

voxel_boxes = []      # ボクセル用
delaunay_pts = []     # ドロネー用
delaunay_pts_tmp = []
#クラスターを考えよう


for cluster in clusters:
    h, bottom, top = building_height_noground(cluster)

    if h >= HEIGHT_TH:
        xs = [x for x,_,_ in cluster]
        ys = [y for _,y,_ in cluster]

        xmin, xmax = min(xs), max(xs)+1
        ymin, ymax = min(ys), max(ys)+1
        
        z_cut = bottom  # デフォルト

        zs_under = [
            z for x,y,z in low_pts
            if xmin <= x < xmax and ymin <= y < ymax
]

        if zs_under:
            z_cut = min(zs_under)


        voxel_boxes.append(
            (xmin, ymin, z_cut, xmax, ymax, top)
        )
        
    else:
        delaunay_pts_tmp.extend(cluster)
# voxel直下の低層点を削除しつつ Delaunay に追加
remaining_low_pts = []
for x, y, z in delaunay_pts_tmp:
    keep = True
    for xmin, ymin, zmin, xmax, ymax, zmax in voxel_boxes:
        if xmin <= x < xmax and ymin <= y < ymax and z < zmin:
            keep = False  # voxel直下 →削除
            break
    if keep:
        remaining_low_pts.append((x, y, z))

# 最終的な Delaunay 点群
delaunay_pts = remaining_low_pts + [
    (x, y, z) for x, y, z in low_pts
    if all(not (xmin <= x < xmax and ymin <= y < ymax and z < zmin)
           for xmin, ymin, zmin, xmax, ymax, zmax in voxel_boxes)
]



# ----------------------
# 保存
# ----------------------
with open("voxel.dat", "w") as f:
    for xmin, ymin, zmin, xmax, ymax, zmax in voxel_boxes:
        f.write(f"{xmin} {ymin} {zmin} {xmax} {ymax} {zmax}\n")

with open("delaunay.dat", "w") as f:
    for x,y,z in delaunay_pts:
        f.write(f"{x} {y} {z}\n")

print("Voxel buildings:", len(voxel_boxes))
print("Delaunay points:", len(delaunay_pts))

