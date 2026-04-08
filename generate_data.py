import json
import os
import numpy as np
from scipy.optimize import linear_sum_assignment


def generate_real_datasets():
    # --- 1. 配置区 ---
    # 强制对齐规则：指定犬种固定到特定网格ID
    MANUAL_MAPPING = {
        "柴犬": "G_30_130",
        "秋田犬": "G_40_140"
    }

    # 各大洲配置
    continents_config = {
        "asia": {"geo_key": "Asia", "name_cn": "亚洲", "source": "./assets/raw_models/asia/asia.json"},
        "europe": {"geo_key": "Europe", "name_cn": "欧洲", "source": "./assets/raw_models/europe/europe.json"},
        "north_america": {"geo_key": "North America", "name_cn": "北美",
                          "source": "./assets/raw_models/north_america/north_america.json"},
        "south_america": {"geo_key": "South America", "name_cn": "南美",
                          "source": "./assets/raw_models/south_america/south_america.json"},
        "africa": {"geo_key": "Africa", "name_cn": "非洲", "source": "./assets/raw_models/africa/africa.json"},
        "australia": {"geo_key": "Australia", "name_cn": "大洋洲",
                      "source": "./assets/raw_models/australia/australia.json"}
    }

    # --- 2. 加载网格基础数据 ---
    grid_assets_path = './assets/continent_grid_assets.json'
    if not os.path.exists(grid_assets_path):
        print(f"❌ 错误：找不到网格文件 {grid_assets_path}")
        return

    with open(grid_assets_path, 'r', encoding='utf-8') as f:
        land_slots = json.load(f)

    # 建立全局网格查找表
    all_grid_lookup = {}
    reserved_grid_ids = set(MANUAL_MAPPING.values())
    for cont, slots in land_slots.items():
        for s in slots:
            gid = f"G_{s['boundary'][0]}_{s['boundary'][2]}"
            all_grid_lookup[gid] = s

    # 确保输出目录存在
    output_dir = "gene_dog_info"
    os.makedirs(output_dir, exist_ok=True)

    # --- 3. 遍历大洲处理数据 ---
    for file_key, cfg in continents_config.items():
        if not os.path.exists(cfg["source"]):
            print(f"⚠️  跳过 {cfg['name_cn']}: 找不到源 JSON")
            continue

        with open(cfg["source"], 'r', encoding='utf-8') as f:
            raw_dogs = json.load(f)

        # 筛选当前大洲可用的闲置网格
        available_slots = [
            s for s in land_slots.get(cfg["geo_key"], [])
            if f"G_{s['boundary'][0]}_{s['boundary'][2]}" not in reserved_grid_ids
        ]

        dogs_to_match = []
        manual_results = []

        for dog_item in raw_dogs:
            # A. 提取犬种名称
            old_path = dog_item.get("模型文件", "")
            dog_name = os.path.splitext(os.path.basename(old_path))[0]

            # B. 核心优化：物理路径检查与高亮提示
            target_model_path = f"./assets/compressed/{file_key}/{dog_name}_ultra.glb"
            if not os.path.exists(target_model_path):
                # 使用 ANSI 转义码实现终端红色加粗显示
                print(f"\033[1;31m🔥 缺失模型文件:\033[0m [{cfg['name_cn']}] {dog_name} -> 路径: {target_model_path}")

            # C. 基础字段更新
            dog_item.update({
                "犬种": dog_name,
                "模型文件": target_model_path,
                "真实经纬度": dog_item.get("经纬度", [0, 0])
            })

            # D. 区分手动指派与自动分配
            if dog_name in MANUAL_MAPPING:
                gid = MANUAL_MAPPING[dog_name]
                slot = all_grid_lookup.get(gid)
                if slot:
                    dog_item.update({
                        "经纬度": slot["center"],
                        "网格ID": gid
                    })
                    manual_results.append(dog_item)
            else:
                dogs_to_match.append(dog_item)

        # --- 4. 匈牙利算法：全局最优地理匹配 ---
        if dogs_to_match and available_slots:
            # 构建代价矩阵 (Cost Matrix): 狗狗与网格中心的欧氏距离
            cost_matrix = np.array([
                [np.linalg.norm(np.array(d["真实经纬度"]) - np.array(s["center"]))
                 for s in available_slots]
                for d in dogs_to_match
            ])

            # 执行指派优化
            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            for i, j in zip(row_ind, col_ind):
                target_dog = dogs_to_match[i]
                target_slot = available_slots[j]
                target_dog.update({
                    "经纬度": target_slot["center"],
                    "网格ID": f"G_{target_slot['boundary'][0]}_{target_slot['boundary'][2]}"
                })

            final_data = manual_results + dogs_to_match
        else:
            final_data = manual_results

        # --- 5. 写入最终 JSON ---
        output_file = os.path.join(output_dir, f"{file_key}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)

        print(f"✅ {cfg['name_cn']} 处理完成，输出至: {output_file}")


if __name__ == "__main__":
    generate_real_datasets()