# 每日科技日报生成任务

## 任务说明

使用 `tech-daily-generator` Skill 读取 `tech-daily/` 目录下最近的 JSON 文件，从 6 个角色中选择一位生成对应的科技日报。

## 核心要求

- **必须调用** `tech-daily-generator` Skill
- **必须读取** SKILL.md 并按照规范执行
- **必须指定** `--role` 参数选择一位角色
- **严禁直接生成HTML**，必须调用 Skill 生成
- **超时设置**: Skill 执行超时时间为 **15分钟**
- **单次单角色**: 每次调用只生成一位角色的日报

---

## 执行步骤

### 步骤1: 确定输入文件

查找 `./tech-daily/` 目录下最新的 JSON 文件作为输入：
```bash
ls -t ./tech-daily/*.json | head -1
```

### 步骤2: 选择角色并调用 Skill

6 个可选角色：

| 角色参数 | 说明 |
|----------|------|
| `cto_insight` | CTO洞察版，关注战略价值与商业影响 |
| `developer_practice` | 开发者实践版，关注技术细节与工具更新 |
| `tech_enthusiast` | 科技爱好者版，通俗科普与生活影响 |
| `investment_analysis` | 投资分析版，关注市场机会与风险评估 |
| `academic_research` | 学术研究员版，关注理论基础与研究创新 |
| `user_research` | 用户研究版，关注用户体验与设计趋势 |

调用示例：
```
skill: "tech-daily-generator"
args: "<JSON文件路径> --role cto_insight --output ./tech-daily/"
```

### 步骤3: 执行 Skill（带15分钟超时）

调用 Skill 时设置超时时间为15分钟：
```
skill: "tech-daily-generator"
args: "<JSON文件路径> --role <角色名> --output ./tech-daily/ --timeout 15m"
```

### 步骤4: 提交已生成的日报

提交生成的 HTML 文件：
```bash
git add tech-daily/<角色名>.html
git commit -m "Auto-generate daily report (<角色名>): $(date +'%Y-%m-%d %H:%M')"
```

如需生成多个角色版本，重复步骤2-4，每次指定不同角色。

---

### 验证清单

- [ ] 使用了 tech-daily-generator Skill
- [ ] 输入路径正确（`./tech-daily/` 下最新 JSON 文件）
- [ ] 输出路径正确（直接生成到 `./tech-daily/` 覆盖旧文件）
- [ ] 指定了 `--role` 参数
- [ ] 生成的HTML每条新闻都有内容摘要(summary)，禁止直接输出难懂的原文
- [ ] 每条新闻附近的源链接(source link near the news)可点击且跳转正确
- [ ] 底部链接(links at the bottom)可点击且跳转正确
- [ ] **15分钟超时后提交了已生成的日报**
