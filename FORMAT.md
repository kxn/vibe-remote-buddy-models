# 格式 1

## 版本及更新

- `format_version`：解析契约主版本，不支持的版本必须拒绝，不能猜字段。
- `revision`：某个稳定资源ID的正整数修订号。已发布的 `<id>/1.json` 不修改，更新新增 `2.json`；引用用 `{id, revision}`，禁止隐式latest。
- `catalog_version`：机型库发布的SemVer；仅修正说明patch、新增机型minor、不兼容格式major。首版0.1.0。
- `driver_api`：固件对应driver的能力版本，不能用固件显示版本代替能力检查。
- `minimum_catalog_api`：未来应用目录加载器的最低API版本。目前应用未实现API1，不声称兼容。

发布tag固定catalog及所有资源。同步先下载并校验引用闭包和摘要，再原子替换本地索引。已绑定设备固定资源修订号；资源更新不能自动替换个人键位。旧修订继续保留。

## 指纹

`scan_hints` 仅筛选候选，name/prefix、广播company不是同款认证。
`required` 内所有字段须满足：Map长度/CRC、存在时的完整SHA256、PnP source/vendor/product、服务集合、report ID/type集合。服务和report集合表示必需的子集，特征handle不进入指纹。
缺失实读字段属于未确认，不得当通过；多条指纹可以指向同一配置。不同配置都通过时不能按文件顺序选，应让用户选择或执行区分键验证。

`captured-map`必须附hex、sha256，校验器验证真实摘要与CRC32C。RC003初始记录显式标记 `legacy-crc-needs-capture`，不能被加载器当作强指纹自动确认；补采后发布新revision，不伪造摘要。CRC32C采用Castagnoli、初始/最终异或ffffffff。

## 按钮及默认动作

button ID在机型内稳定，与标签和语义分开。`legacy_key`只是旧应用迁移线索；运行编译必须按semantic分配规范逻辑键，不能把legacy_key直接当最终语义。CMCC b14已明确修正为menu，原样本的静音动作改为窗口选择器；个人绑定配置不在本仓库，不被修改。

原始键表中的report_id是HID报告编号，usage按对应报告解析；编码方案目前仅hid-report-usage，不能泛化成所有HID设备解码器。voices记录引用固件驱动，不在资源中复制算法。语音键由该driver给出边沿。

`default=[kind,modifiers,value]`保留Buddy映射编码：0无动作；1键盘；2媒体；3语音快捷键；4应用动作；5语音预设。应用内置动作65534任务视图、65535窗口选择器；公共资源禁止个人动作编号。预设1豆包、2微信；修饰位沿用USB HID。旧样本的其他默认值保留，不能把版本策略差异当硬件差异。

布局x/y/width/height为百分数，画布width/height用于宽高比；button引用物理ID，cell是编辑器网格提示，不参与指纹。资源无图像时由应用根据布局生成。

## 来源与范围

四款数据从现有已使用资源、保存的脱敏验证信息及原内置映射转换。RC003键表属于内置实现来源，未声称每键有本次独立捕获。移动和旧小米的历史语音记录为16kHz、解码错误0、正常结束；不附私人录音，也不由peak字段推断音质。
