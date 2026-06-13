import numpy as np

MISSING = -9999.99
TH_STD = 0.6      # 文京区推奨：壁を検出する基準
DILATE_ITER = 2   # 膨張回数（屋根を建物扱いにする）


# ------------------------------
# 1. 読み込み（1mメッシュDSM）
# ------------------------------
def load_points(filename):
    points = []
    groundmap = {}

    with open(filename) as f:
        for line in f:
            x, y, z = map(float, line.split())
            if z == MISSING:
                continue

            gx = int(x)
            gy = int(y)

            points.append((gx, gy, z))
            groundmap[(gx, gy)] = z

    return points, groundmap


# ------------------------------
# 2. 勾配ベース分類（壁だけ検出）
# ------------------------------
H_THRESHOLD = 5.0 #屋根判定の高さ差
jimen = 2.0 #地面の最低基準
def classify_gradient(points, groundmap):
    ground_pts = []
    building_pts = []

    for x, y, z in points:
        neigh = []

        for dx in range(-1,2):
            for dy in range(-1,2):
                nx, ny = x + dx, y + dy
                if (nx,ny) in groundmap:
                    neigh.append(groundmap[(nx,ny)])

        if len(neigh) < 4:
            continue
        max_diff = 0.0
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x+dx, y+dy
                if (nx,ny) in groundmap:
                    diff = abs(z - groundmap[(nx,ny)])
                    max_diff = max(max_diff, diff)


        std = np.std(neigh)
        dz=z-np.percentile(neigh,5)
        med = np.median(neigh)
        mad = np.median(np.abs(neigh - med))

        if abs(z - med) < 1.0 and mad < 0.5:
            ground_pts.append((x,y,z))
        elif max_diff < 2.0:
        	ground_pts.append((x, y, z))
        elif z < jimen:
        	ground_pts.append((x, y, z))
        elif dz > H_THRESHOLD or std > 0.7:
            building_pts.append((x, y, z))   # 壁
        else:
            ground_pts.append((x, y, z))     # 平坦 → 地面と仮定

    return ground_pts, building_pts

# ------------------------------
# 3. 膨張処理（屋根を建物扱いにする）
# ------------------------------
def dilate_buildings(building_set, iterations=2):
    # building_set = {(x,y)}
    for _ in range(iterations):
        new_set = set(building_set)
        for (x, y) in building_set:
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    nx, ny = x+dx, y+dy
                    new_set.add((nx, ny))
        building_set = new_set
    return building_set


# ------------------------------
# 4. 膨張後に再分類
# ------------------------------
H=10.0
def correct_classification(points, building_xy):
    corrected_ground = []
    corrected_building = []

    for (x,y,z) in points:
        if (x,y) in building_xy:
            corrected_building.append((x,y,z))
        else:
            if z > H:
                corrected_building.append((x,y,z))
            else:
                corrected_ground.append((x,y,z))
            

    return corrected_ground, corrected_building


# ------------------------------
# 5. 保存
# ------------------------------
def save_points(filename, pts):
    with open(filename, "w") as f:
        for x, y, z in pts:
            f.write(f"{x} {y} {z}\n")


# ------------------------------
# Main
# ------------------------------
def ground_building_detection(input_file):
    print("Loading...")
    points, groundmap = load_points(input_file)

    print("Gradient classification...")
    ground_pts, building_pts = classify_gradient(points, groundmap)

    print("Initial building:", len(building_pts))

    print("Dilating building regions...")
    building_xy = {(x,y) for (x,y,z) in building_pts}
    building_xy = dilate_buildings(building_xy, iterations=DILATE_ITER)

    print("Correcting classification...")
    final_ground, final_building = correct_classification(points, building_xy)
    

    print("Saving...")
    save_points("ground1.dat", final_ground)
    save_points("building1.dat", final_building)

    print("Done.")
    print("Ground:", len(final_ground))
    print("Building:", len(final_building))


if __name__ == "__main__":
    ground_building_detection("1hkn.dat")

