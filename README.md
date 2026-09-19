# Vibe Remote Buddy 机型库

机型默认配置与实测识别资料。库版本 **0.2.0**，格式 **2**。

每个资源只有一个当前文件，修改原文件并递增 revision；历史由 Git 保存，不堆积版本目录。公共库不保存个人 override、设备地址、绑定、录音或固件。

## 现有样本

| 机型 | 定义文件 | 实测范围 |
|---|---|---|
| 联通28键样本 | [unicom-28-key.json](models/operators/unicom-28-key.json) | 内置实测 Map、原始键表 |
| 移动28键样本 | [cmcc-28-key.json](models/operators/cmcc-28-key.json) | 完整 Map、保存的逐键验证 |
| 小米 Remote 2 Pro / RC003 | [remote-2-pro-rc003.json](models/xiaomi/remote-2-pro-rc003.json) | 完整 Map、8个报告引用、ATVV；键表来自内置实现 |
| 旧款小米2717:32BA样本 | [legacy-2717-32ba.json](models/xiaomi/legacy-2717-32ba.json) | 完整 Map、保存的逐键验证 |

这些名称不宣称覆盖整个品牌。联通和移动共用 ICO 协议及三列28键布局，但实测普通键16个相同、11个不同，因此分别保存键表与默认配置。RC003 [补采记录](evidence/xiaomi.rc003.md)保留来源与未采项目。

## 目录

- `models/`：机型定义，连接协议、键表、布局和默认设置。
- `fingerprints/`：连接后识别依据；名字仅作为搜索线索。
- `protocols/`：引用固件已实现的语音驱动。
- `keymaps/`：原始键码对应哪个物理按钮。
- `layouts/`：可复用几何布局，不包含个人功能配置。
- `defaults/`：每个物理按钮的默认名称和动作。
- `schemas/`：公共资源和本地 override 的独立格式。
- `tools/resolve.py`：识别、覆盖合并的可执行参考契约。

桌面应用通过独立机型库入口下载此库，验证后同步至支持 catalog API 2 的接收器（固件 0.10.0 起）。发布包自带离线快照。旧版 resources/remotes 是本地适配资源目录，不要把此库直接覆盖进去。已绑定遥控器使用自己的配置快照，更新库不会改变个人按键设置。

```sh
python -m pip install -r requirements.txt
python tools/validate.py --write-index
python tools/validate.py
python -m unittest discover -s tests -v
```

完整设计见 [FORMAT.md](FORMAT.md)，贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。
