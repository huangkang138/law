# 律小智 AI 拆分素材

本目录保存依据 2026-09-08 确认角色正稿生成的透明 PNG 素材，作为 Rive 制作输入。

## 文件分组

- `character_master.png`：全身正稿（真实 Alpha）
- `head_reference.png`：头部近景参考（真实 Alpha）
- `body_base.png`、`head_base.png`、`hair_back.png`、`hair_front.png`：原始基础层
- `head_base_v2.png`：保留原头型与耳朵，只缩短并收窄脖子的修正版
- `head_base_v3.png`：基于短脖子版本，将低对比度肤色鼻部阴影直接融合进脸底图；Rive 拼装优先使用此文件
- `eyebrow_*.png`：normal / think / serious
- `eyes_*.png`：normal / happy / think / serious / surprise / closed
- `mouth_*.png`：closed / small / medium / large / smile / serious

## 使用边界

- 这些文件是 AI 生成的独立源素材，不是手工分层 PSD。
- 各组画布尺寸不同，导入 Rive 前需统一到同一 Artboard，并人工校准缩放、位置、边缘和锚点。
- 当前未生成 `.riv` 文件，也未把这套新角色接入前端运行组件。
- `body_base.png` 未包含胸前独立徽章层；耳机和徽章增强层可在确认需要后补充。
- `head_base.png` 保留作为原始素材；`head_base_v2.png`、`head_base_v3.png` 与其画布同为 `1254×1254`。`v2` 解决原脖子过长、下端外扩和领口衔接生硬的问题，`v3` 在此基础上把鼻子直接合入脸部。

## 建议 Rive 层级

```text
hair_back
body_base
head_base_v3
eyes_*
eyebrow_*
mouth_*
hair_front
```

同一组表情层只显示一个状态；`eyes_closed` 用于 blink，`mouth_closed/small/medium/large` 用于 speaking。
