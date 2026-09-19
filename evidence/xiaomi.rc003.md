# RC003 实机补采记录

2026-09-19，接收器 buddy-0.9.2，从已绑定且 READY 的 RC003 正常连接导出；没有删绑定、没有进入适配模式。

- Report Map：86 字节，CRC32C `6bd7daad`。
- SHA256：`49011aec53ed525eafe37620ad2d2fa890e645aabc93e2344ea02abcca6aa144`。
- 完整原始字节见 [指纹修订版2](../fingerprints/xiaomi.rc003/2.json)。
- 脱敏采集记录（含此次连接的报告句柄和属性）见 [capture.json](xiaomi.rc003.capture.json)。
- 8 个 Report Reference：1/input、2/output、3/input、4/feature、5/feature、6/feature、7/feature、8/feature。
- ATVV 已实际发现：命令、音频和控制三个通道均存在。

报告引用按设备实际返回值保存，不能用 Report Map 中声明的 Input 类型覆盖 GATT Report Reference 的 Feature 类型。句柄属于此次连接证据，不是型号匹配条件。

本轮没有重新逐键按压，也没有采集 PnP/Model Number；键码表仍明确标为 existing-builtin-mapping。不得把以上记录称为这些字段的实测验证。v1 缺失的完整 Map 已由 v2 补齐，历史 v1 不改写。
