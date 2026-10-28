# Mesh Check for Roblox（Blender 插件）

在导出之前，按 **Roblox 的导入限制**检查你的模型，免得之后被 Studio 或 Marketplace 拒绝。每一条限制都来自 Roblox 官方的 [创作者文档](https://github.com/Roblox/creator-docs)，最近一次核对是 **2026-10-28**。每个问题旁边都有一个 ? 按钮，可以打开对应规则的 Roblox 页面。

支持 Blender 4.2 及以上版本，在 Blender 5.2 中测试过。

## 检查内容

| 检查项 | 规则（Roblox 文档） | 级别 |
|---|---|---|
| 三角面预算 | 普通网格 20,000；刚性饰品和分层饰品 4,000。按应用修改器后的结果计算，与导出一致 | 错误 |
| 饰品尺寸 | 按饰品类型（帽子、头发、脸部、颈部、肩部、前、后、腰部）和身体比例（Normal、Slender、Classic）的最大尺寸（stud） | 错误 |
| 零厚度 | 网格必须有体积 | 错误 |
| 骨骼影响 | 每个顶点最多受 4 根骨骼影响 | 错误 |
| 笼体 | 分层饰品需要 `名称_InnerCage` 和 `名称_OuterCage`；找不到对应网格的笼体会被标出 | 错误 / 警告 |
| 贴图尺寸 | 饰品贴图最大 2048×2048（Marketplace）；普通网格的贴图超过 1024 会被标出 | 错误 / 警告 |
| 封闭性 | 没有开放边或非流形边 | 警告 |
| N-gon | 尽量使用四边面 | 警告 |
| UV | 有 UV 贴图、只有一套 UV、所有 UV 都在 0–1 内 | 警告 |
| 材质 | 每个网格一个材质 | 警告 |
| 变换 | 未应用的旋转或缩放 | 警告 |
| 场景单位 | 单位系统设为 None，这样 1 个 Blender 单位 = 1 stud | 警告 |

## 安装

1. 从 [Releases](../../releases) 下载 `mesh_check_rbx-1.0.0.zip`。
2. 在 Blender 中：**编辑 → 偏好设置 → 获取扩展**，点 ⌄ 菜单 → **从磁盘安装...**，选择这个 zip。
3. 打开 3D 视图侧边栏（**N**）→ **Roblox** 标签，选择资产类型，点击 **Check for Roblox**。

## Pro 版

[**Mesh Check Pro**](https://kettlewick.gumroad.com/l/mesh-check-pro-roblox) 额外提供：

- **一键修复**：应用旋转/缩放（子物体位置不变）、只把 N-gon 三角化、把骨骼影响限制为 4 并重新归一化、删除多余的 UV 贴图、设置 stud 单位、缩小过大的贴图。也可以 **全部修复**。
- **为 Roblox 导出 FBX**：使用 Roblox 导出指南里的设置（路径模式 Copy、嵌入贴图、FBX 单位缩放、不加末端骨骼、不烘焙动画），自动包含笼体和骨架。
- **报告**：Markdown 或 JSON 格式。
- **命令行（用于 CI）**：`blender -b model.blend --python cli.py -- --preset RIGID --fix --json report.json --export out.fbx`，仍有错误时退出码为 1。
- 22 个在真实 Blender 中运行的自动测试，包括 FBX 导出再导入的往返测试。

Pro 版同样是 GPL 授权（所有 Blender 插件都必须如此）。购买支付的是额外的工具、Roblox 修改限制时的更新，以及支持。

## 运行测试

```bash
pip install bpy==5.2.3   # 作为 Python 模块的 Blender（Python 3.13）
python tests/test_checks.py
```

## 许可与说明

GPL-3.0-or-later（见 `LICENSE`）。与 Roblox Corporation 无关联，也未获其认可。借助 AI 编程助手编写，然后按上面所说在真实 Blender 中测试。

更多免费 Roblox 工具：[模拟器节奏计算器](https://2328312928-commits.github.io/roblox-luau-skill/)、[DataStore 限额](https://2328312928-commits.github.io/roblox-luau-skill/datastore-limits/)、[蛋概率检查器](https://2328312928-commits.github.io/roblox-luau-skill/odds/)。
