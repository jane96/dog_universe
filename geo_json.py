import json
from shapely.geometry import shape, Point

# 1. 加载你获取到的 GeoJSON 文件
with open('./assets/earth_poly.json', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)


def generate_land_grids(step=10):
    land_slots = {}

    # 2. 遍历全球网格中心点 (10度步长)
    # 纬度从 -85 到 85 (避开极点)
    # 经度从 -175 到 175
    for lat_start in range(-90, 90, step):
        for lon_start in range(-180, 180, step):
            # 计算格子的几何中心点
            center_lat = lat_start + step / 2
            center_lon = lon_start + step / 2
            point = Point(center_lon, center_lat)  # Shapely 使用 (x, y) 即 (Lon, Lat)

            # 3. 检查这个点落在哪个大洲
            for feature in geojson_data['features']:
                polygon = shape(feature['geometry'])
                # 根据你的 GeoJSON 属性名修改，通常是 'CONTINENT' 或 'name'
                continent_name = feature['properties'].get('CONTINENT', 'Unknown')

                if polygon.contains(point):
                    if continent_name not in land_slots:
                        land_slots[continent_name] = []

                    land_slots[continent_name].append({
                        "center": [round(center_lat, 2), round(center_lon, 2)],
                        "boundary": [lat_start, lat_start + step, lon_start, lon_start + step]
                    })
                    break  # 找到所属洲后跳出，避免重复计算

    return land_slots


# 4. 执行并保存为资产清单
land_mapping = generate_land_grids(10)
with open('./assets/continent_grid_assets.json', 'w', encoding='utf-8') as f:
    json.dump(land_mapping, f, ensure_ascii=False, indent=2)

print("精准网格计算完成！")
for continent, slots in land_mapping.items():
    print(f"{continent}: 共有 {len(slots)} 个可用网格位")


""""
South America: 共有 14 个可用网格位
Australia: 共有 7 个可用网格位
Africa: 共有 25 个可用网格位
Asia: 共有 54 个可用网格位
North America: 共有 36 个可用网格位
Europe: 共有 15 个可用网格位
"""