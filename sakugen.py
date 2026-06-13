import os

def reduce_points(input_filename):
    output_filename = "reduced_" + input_filename
    points = {}

    # 1. データの読み込み
    if not os.path.exists(input_filename):
        print(f"エラー: {input_filename} が見つかりません。")
        return

    with open(input_filename, 'r') as f:
        for line in f:
            parts = line.split()
            if len(parts) == 3:
                # 座標を浮動小数点として読み込み
                # 1m間隔なので、キーとして扱うために整数に丸める（誤差対策）
                x, y, z = map(float, parts)
                points[(round(x), round(y))] = z

    processed_points = set()
    reduced_data = []

    # 2. 4点集約ロジック
    # x, y を「左上の点」として、右(x+1)、下(y-1)、右下(x+1, y-1)を探す
    # ※座標系により上下の正負が逆の場合は y+1 に適宜変更してください
    for (x, y), z in points.items():
        # すでに他のグループとして処理済みの点はスキップ
        if (x, y) in processed_points:
            continue
        
        # 近傍3点の座標を定義
        p_right = (x + 1, y)
        p_bottom = (x, y - 1)
        p_bottom_right = (x + 1, y - 1)

        # 4点すべてが存在するか確認
        if p_right in points and p_bottom in points and p_bottom_right in points:
            # 4点のz値の平均を計算
            avg_z = (z + points[p_right] + points[p_bottom] + points[p_bottom_right]) / 4.0
            # 4点のx, yの平均（中心点）を計算
            avg_x = (x + (x + 1)) / 2.0
            avg_y = (y + (y - 1)) / 2.0
            
            # 結果を保存（左上の座標を基準にする場合は x, y, avg_z を使用）
            # 今回はご要望通り「左上の点を平均値に書き換える」形式にします
            reduced_data.append((float(x), float(y), avg_z))
            
            # 使用した4点を「処理済み」としてマーク
            processed_points.update([(x, y), p_right, p_bottom, p_bottom_right])
        else:
            # 4点揃わなかった場合、その点は今回は除外（またはそのまま維持）
            # 維持したい場合はここに append 処理を追加します
            pass

    # 3. ファイル書き出し
    with open(output_filename, 'w') as f:
        for pt in reduced_data:
            f.write(f"{pt[0]} {pt[1]} {pt[2]:.3f}\n")

    print(f"処理完了: {len(reduced_data)} 点に圧縮されました。")
    print(f"保存先: {output_filename}")

if __name__ == "__main__":
    fname = input("入力ファイル名を入力してください (例: ground.dat): ")
    reduce_points(fname)
