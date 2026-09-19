# Vibe Remote Buddy 机型库

声明式遥控器配置与贡献入口。初始发布 **0.1.0**，格式 **1**，每份资源从 revision **1** 开始。

本仓库不包含固件、录音、设备地址或个人绑定信息。**当前应用尚未实现此格式的下载/加载，不可把这些文件直接覆盖进旧版 resources/remotes。**

## 已转换的数据

| 机型ID | 语音配置 | 键表 | 证据 |
|---|---|---|---|
| unicom.sample-28 | hid-ico.v1 | 独立28键布局/普通键表 | 原内置实测Map与映射 |
| cmcc.sample-28 | hid-ico.v1 | 独立28键布局/普通键表 | 保存的逐键验证与GATT记录 |
| xiaomi.rc003 | atvv.rc003 | 原内置映射，13键 | CRC/长度已知，完整Map待补采 |
| xiaomi.legacy-32ba | xiaomi.hid-msbc | 12键 | 保存的逐键验证与GATT记录 |

`sample-28` 表示手头已验证样本，不声称覆盖整个运营商品牌。联通、移动普通键16个相同、11个不同，共享语音配置，不共享完整键表。语音键状态由driver负责，普通键表不重复模拟开关麦。

## 文件组织

- `voices/<id>/<revision>.json`：引用固件已实现的语音驱动API。
- `keys/...`：report/usage到物理button ID的映射。
- `models/...`：物理button的语义、名字、默认动作、布局。
- `fingerprints/...`：扫描线索及连接后必须核对的特征；精确引用机型、键表和语音配置。
- `catalog.json`：库版本、资源路径、长度和SHA-256；用于未来下载器。
- `schemas/`：严格JSON Schema；`tools/validate.py`另校验引用与数据一致性。

没有外部脚本、任意写蓝牙命令或下载可执行代码的能力。新增协议必须先由固件实现driver。

## 校验

```sh
python -m pip install -r requirements.txt
python tools/validate.py --write-index
python tools/validate.py
```

格式细节见 [FORMAT.md](FORMAT.md)，贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。
