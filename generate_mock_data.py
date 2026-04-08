import json
import os
import random


def generate_split_datasets():
    # --- 新增：精准指派映射表 ---
    # 格式: "犬种名": "网格ID(由经纬度左下角组成)"
    # 你可以根据需要在这里添加更多强制对齐的规则
    MANUAL_MAPPING = {
        "柴犬": "G_30_130",
        "秋田犬": "G_40_140"
    }

    # 2. 犬科分类清单 (修复 dog_groups 未使用的 Bug)
    dog_groups = ["牧羊犬", "獒犬类", "梗犬", "腊肠犬", "尖嘴犬", "嗅觉猎犬", "指示犬", "枪猎犬", "伴侣犬", "视觉猎犬"]

    # 1. 基础模版数据 (保持不变)
    template = {
        "模型文件": "./assets/尖嘴犬/柴犬_small_ultra.glb",
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
                     "西藏梗", "西藏猎犬", "塔兹猎犬", "巴基斯坦布利", "萨路基", "日本尖嘴", "北京犬", "巴哥", "八哥",
                     "台湾犬", "四国犬", "甲斐犬", "纪州犬", "北海道犬", "美系秋田", "中国细犬", "川东猎犬", "下司犬",
                     "重庆犬", "青川犬", "莱州红", "蒙古细犬", "哈萨克牧羊犬", "中亚牧羊犬", "高加索犬", "库达犬",
                     "印度尼基犬", "兰格尔獒", "巴基斯坦猎犬", "土耳其博兹犬", "卡拉巴赫犬", "以色列卡南犬", "菲律宾犬",
                     "西伯利亚雪橇犬", "印尼巴厘犬", "东洋犬"]
        },
        "europe": {
            "geo_key": "Europe", "name_cn": "欧洲",
            "list": ["边牧", "德牧", "贵宾", "罗威纳", "灵缇", "纽波利顿", "卡斯罗", "伯恩山", "圣伯纳", "杜宾",
                     "马林诺斯", "特武伦", "史奇派克", "荷兰牧羊", "维兹拉"]
        },
        "north_america": {
            "geo_key": "North America", "name_cn": "北美",
            "list": ["阿拉斯加", "波士顿梗", "澳牧", "拉布拉多", "切萨皮克湾猎犬", "纽芬兰", "圣约翰水犬", "切诺基犬",
                     "美国爱斯基摩犬", "蓝斑猎浣熊犬", "树丛猎浣熊犬", "美国水猎犬", "美系澳洲牧羊犬", "玩具贵宾",
                     "比特犬", "恶霸犬", "斯塔福郡梗", "卡他豪拉豹犬", "帕森拉塞尔梗", "威尔士梗", "美国无毛梗",
                     "奇努克犬", "卡罗莱纳犬", "阿拉帕哈蓝血斗牛犬", "黑褐浣熊犬", "红骨浣熊犬", "英国浣熊犬",
                     "山地费斯特犬", "拉塔费斯特犬", "普洛特猎犬", "麦克纳布牧羊犬", "挪威猎鹿犬(美系)", "银狐犬(美系)",
                     "玩具曼彻斯特梗", "美国猎狐犬", "克里凯犬"]
        },
        "south_america": {
            "geo_key": "South America", "name_cn": "南美",
            "list": ["阿根廷杜高", "巴西非勒", "秘鲁无毛犬", "乌拉圭西马龙犬", "穆奇奇犬", "智利猎狐梗", "巴西梗",
                     "委内瑞拉猎犬", "乌拉圭牧羊犬", "潘帕斯猎犬", "厄瓜多尔无毛犬", "巴西寻回犬", "秘鲁印加兰犬",
                     "巴塔哥尼亚牧羊犬"]
        },
        "africa": {
            "geo_key": "Africa", "name_cn": "非洲",
            "list": ["巴仙吉", "罗德西亚背脊犬", "南非獒", "法老王猎犬", "阿扎瓦克犬", "斯路基犬", "图莱亚尔棉犬",
                     "阿比西尼亚砂犬", "柏柏尔犬", "肯尼亚猎犬", "埃塞俄比亚狼犬", "非洲野犬(模拟犬种)", "埃及法老猎犬",
                     "马里梗", "沙地猎犬", "丛林犬", "贝都因猎犬", "尼罗河谷犬", "津巴布韦猎犬", "突尼斯坎根犬",
                     "阿尔及利亚猎犬", "摩洛哥猎犬", "撒哈拉灵缇", "喀麦隆隆獒", "阿非利加牧羊犬"]
        },
        "australia": {
            "geo_key": "Australia", "name_cn": "大洋洲",
            "list": ["澳洲牧牛犬", "卡尔比犬", "丝毛梗", "亨塔威犬", "澳洲梗", "澳洲野犬", "新西兰牧羊犬"]
        }
    }

    # 3. 读取之前生成的网格考位 JSON
    grid_assets_path = './assets/continent_grid_assets.json'
    if not os.path.exists(grid_assets_path):
        print(f"错误：找不到网格文件 {grid_assets_path}，请先运行网格生成脚本。")
        return

    with open(grid_assets_path, 'r', encoding='utf-8') as f:
        land_slots = json.load(f)

    # 建立 ID 索引，并标记哪些网格是被“预定”了的
    all_grid_lookup = {}
    reserved_grid_ids = set(MANUAL_MAPPING.values())

    for cont, slots in land_slots.items():
        for s in slots:
            gid = f"G_{s['boundary'][0]}_{s['boundary'][2]}"
            all_grid_lookup[gid] = s

    # 5. 执行生成
    if not os.path.exists("dist_assets"): os.makedirs("dist_assets")

    for file_key, cfg in continents_config.items():
        continent_data = []
        geo_key = cfg["geo_key"]

        # 获取当前大洲所有【未被其他品种预定】的闲置网格
        available_slots = [
            s for s in land_slots.get(geo_key, [])
            if f"G_{s['boundary'][0]}_{s['boundary'][2]}" not in reserved_grid_ids
        ]

        free_slot_ptr = 0 # 闲置网格指针

        for dog_name in cfg["list"]:
            target_slot = None

            # --- 逻辑 A：优先检查是否有指定坑位 ---
            if dog_name in MANUAL_MAPPING:
                target_gid = MANUAL_MAPPING[dog_name]
                target_slot = all_grid_lookup.get(target_gid)
                if target_slot:
                    print(f"✅ 精准对齐: {dog_name} -> {target_gid}")

            # --- 逻辑 B：如果没有指定，从闲置网格里按顺序拿一个 ---
            if not target_slot and free_slot_ptr < len(available_slots):
                target_slot = available_slots[free_slot_ptr]
                free_slot_ptr += 1

            if target_slot:
                item = json.loads(json.dumps(template))
                item.update({
                    "犬科": random.choice(dog_groups), # 修复：随机分配一个分类
                    "大洲": cfg["name_cn"],
                    "犬种": dog_name,
                    "经纬度": target_slot["center"],
                    "网格ID": f"G_{target_slot['boundary'][0]}_{target_slot['boundary'][2]}"
                })
                continent_data.append(item)

        # 保存文件
        with open(f"dist_assets/{file_key}.json", 'w', encoding='utf-8') as f:
            json.dump(continent_data, f, ensure_ascii=False, indent=2)

    print(f"\n数据生成完成！请检查 dist_assets 目录。")

if __name__ == "__main__":
    generate_split_datasets()