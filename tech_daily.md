# 每日科技日报生成任务

## 任务说明
使用 tech-daily-generator Skill 读取 `tech-daily/` 目录下最近的 JSON 文件，生成 6 个角色版本的科技日报。

## 核心要求

- **必须调用** `./tech-daily-generator/` Skill
- **必须读取** SKILL.md 并按照规范执行
- **必须**采用Subagents 并行处理6个角色
- **严禁直接生成HTML**，必须调用 subagent 生成

---

## 执行步骤

### 步骤1: 确定输入文件
查找 `./tech-daily/` 目录下最新的 JSON 文件作为输入：
```bash
ls -t ./tech-daily/*.json | head -1
```

### 步骤2: 读取 Skill 规范并执行
```bash
cat ./tech-daily-generator/SKILL.md
```

调用 tech-daily-generator Skill，参数：
- **输入文件**: `./tech-daily/` 目录下最新的 JSON 文件（如上一步获取）
- **输出目录**: `./tech-daily/`（直接覆盖现有 HTML 文件）

按照 SKILL.md 规范启动6个subagent处理各角色日报。

### 步骤3: 验证生成结果
- [ ] 使用了 tech-daily-generator Skill
- [ ] 输入路径正确（`./tech-daily/` 下最新 JSON 文件）
- [ ] 输出路径正确（直接生成到 `./tech-daily/` 覆盖旧文件）
- [ ] 调用了 subagents 并行处理6个角色
- [ ] 生成的HTML每条新闻都有内容摘要(summary)，禁止直接输出难懂的原文
- [ ] 每条新闻附近的源链接(source link near the news)可点击且跳转正确
- [ ] 底部链接(links at the bottom)可点击且跳转正确
