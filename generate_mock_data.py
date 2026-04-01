import json
import os
import random

def generate_split_datasets():
    # 1. 基础模版数据 (保持不变)
    template = {
        "模型文件": "./assets/尖嘴犬/柴犬tc.glb",
        "犬科": "尖嘴犬",
        "精确产地": "区域样板中心",
        "基础信息": {
            "英文名": "Sample Dog", "别名": "样板犬", "体型分类": "中型犬", "寿命": "12-15年", "FCI编号": "999"
        },
        "体型外貌": {
            "肩高": "35-45 cm", "体重": "10-15 kg", "被毛": "双层被毛", "毛色": "多样", "头部": "标准型", "眼睛": "机敏"
        },
        "工作用途": "伴侣犬",
        "饲养指南": {
            "运动需求": "中等", "训练难度": "中等", "grooming": "常规护理", "适合人群": "大众", "饲养环境": "不限"
        },
        "文化历史": "该数据为大洲网格化测试生成的 Mock 数据。",
        "参考价格": "5000-8000元"
    }

    # 2. 品种配置清单 (仅保留品种列表，坐标计算将交给网格 JSON)
    continents_config = {
        "asia": {
            "geo_key": "Asia", "name_cn": "亚洲",
            "list": ["西施犬", "松狮", "沙皮", "秋田", "柴犬", "土佐", "珍岛犬", "丰山犬", "泰国脊背", "曼谷犬",
                     "富国岛犬", "阿富汗猎犬", "迦南犬", "坎高", "阿克巴什", "奇皮派拉", "穆德霍尔", "藏獒", "拉萨犬",
                     "西藏梗", "西藏猎犬", "塔兹猎犬", "巴基斯坦布利", "萨路基", "日本尖嘴", "北京犬", "巴哥", "西施",
                     "八哥", "台湾犬"]
        },
        "europe": {
            "geo_key": "Europe", "name_cn": "欧洲",
            "list": ["边牧", "德牧", "贵宾", "罗威纳", "灵缇", "纽波利顿", "卡斯罗", "伯恩山", "圣伯纳", "杜宾",
                     "马林诺斯", "特武伦", "史奇派克", "荷兰牧羊", "考克尔", "维兹拉", "可蒙犬", "普利犬", "大白熊",
                     "波尔多", "法斗", "巴吉度", "寻血猎犬", "爱尔兰猎狼", "凯利蓝梗", "苏俄猎狼", "芬兰尖嘴",
                     "挪威伦德", "西班牙獒", "加那利", "波兰低地", "捷克狼犬", "萨摩耶", "哈士奇", "黑梗", "蝴蝶犬"]
        },
        "north_america": {
            "geo_key": "North America", "name_cn": "北美",
            "list": ["阿拉斯加", "波士顿梗", "澳牧", "拉布拉多", "切萨皮克湾猎犬", "纽芬兰", "圣约翰", "切萨皮克",
                     "切诺基", "美国爱斯基摩", "蓝tick猎犬", "库恩猎犬", "美国水猎犬", "澳洲牧羊(美系)", "玩具贵宾",
                     "比特犬", "恶霸犬", "斯塔福", "切萨皮克", "卡他豪拉", "波士顿", "帕森梗", "威尔士梗", "美国无毛梗",
                     "奇努克"]
        },
        "south_america": {
            "geo_key": "South America", "name_cn": "南美",
            "list": ["阿根廷杜高", "巴西非勒", "秘鲁无毛", "奇马龙", "穆奇奇", "智利梗", "巴西梗", "委内瑞拉猎犬",
                     "乌拉圭牧羊", "潘帕斯猎犬", "厄瓜多尔无毛", "巴西寻回", "杜高", "非勒", "秘鲁印加", "智利鼠梗",
                     "巴拿马犬", "玻利维亚犬", "哥伦比亚猎犬", "南美灰狼犬"]
        },
        "africa": {
            "geo_key": "Africa", "name_cn": "非洲",
            "list": ["巴仙吉", "罗德西亚背脊", "南非獒", "法老王", "阿扎瓦克", "斯路基", "图莱亚尔", "阿比西尼亚",
                     "柏柏尔", "肯尼亚猎犬", "斯路基", "埃塞俄比亚狼犬", "非洲野狗(模拟)", "埃及猎犬", "马里梗",
                     "沙猎犬", "丛林犬", "贝都因猎犬", "尼罗河犬", "津巴布韦猎犬"]
        },
        "australia": {
            "geo_key": "Australia", "name_cn": "大洋洲",
            "list": ["澳洲牧牛犬", "卡尔比", "丝毛梗", "亨塔威", "斐济猎犬", "澳洲梗", "丁格犬(Dingo)", "新西兰赫丁",
                     "库利犬", "特宁菲尔德梗", "澳洲猎猪犬", "波利尼西亚犬"]
        }
    }

    # 3. 读取之前生成的网格考位 JSON
    grid_assets_path = './assets/continent_grid_assets.json'
    if not os.path.exists(grid_assets_path):
        print(f"错误：找不到网格文件 {grid_assets_path}，请先运行网格生成脚本。")
        return

    with open(grid_assets_path, 'r', encoding='utf-8') as f:
        land_slots = json.load(f)

    # 4. 创建存储目录
    output_dir = "dist_assets"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 5. 开始合并并生成文件
    dog_groups = [
        "牧羊犬和牧牛犬",
        "獒犬类",
        "梗犬",
        "腊肠犬",
        "尖嘴犬和原始犬",
        "嗅觉猎犬",
        "指示犬",
        "枪猎犬",
        "伴侣犬",
        "视觉猎犬"
    ]
    for file_key, cfg in continents_config.items():
        continent_data = []
        geo_key = cfg["geo_key"]

        # 获取该大洲在 GeoJSON 判定下的合法坑位
        available_slots = land_slots.get(geo_key, [])

        if not available_slots:
            print(f"警告：网格文件中没有大洲 '{geo_key}' 的数据")
            continue

        for index, dog_name in enumerate(cfg["list"]):
            # 如果品种数超过了坑位数，循环使用坑位（或者你也可以选择跳过）
            if index >= len(available_slots):
                break
            slot_index = index % len(available_slots)
            target_slot = available_slots[slot_index]

            # 生成条目
            item = json.loads(json.dumps(template))  # 深拷贝
            item.update({
                "犬科": dog_groups[random.randint(0, 9)],
                "大洲": cfg["name_cn"],
                "犬种": dog_name,
                "经纬度": target_slot["center"],  # 使用 Geo 算出来的中心点
                "网格边界": target_slot["boundary"]  # 方便前端调试
            })
            item["基础信息"]["英文名"] = f"Specimen"
            continent_data.append(item)

        # 写入独立文件
        file_path = os.path.join(output_dir, f"{file_key}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(continent_data, f, ensure_ascii=False, indent=2)

        print(f"已成功对齐网格生成: {file_path} (数量: {len(continent_data)})")


if __name__ == "__main__":
    generate_split_datasets()