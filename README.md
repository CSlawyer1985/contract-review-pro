# Contract Review Pro V3.0

专业合同审核 Claude Skill — 将合同审核工作区成熟方法论编码为可执行流程。

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)]()
[![Author](https://img.shields.io/badge/author-陈石律师-orange.svg)](https://github.com/CSlawyer1985)
[![Claude](https://img.shields.io/badge/Claude-Skill-purple.svg)](https://claude.ai/)

7步工作流 | 5类审查门禁 | 15风险标签 | 六维度评价 | 终稿三件套 | Track Changes + Comments

---

## V3.0 更新摘要

本次升级将合同审核工作区的成熟实践系统性地编码进 Skill，核心变化：

| 维度 | V2.1 | V3.0 |
|------|------|------|
| 工作流 | 隐式4步 | **7步有状态工作流**（客户识别→review-state→通读→效力优先→问题清单→逐条审核→条款提取） |
| 门禁体系 | 单一检查清单 | **5类强制门禁**（效力/主体/条款/一致性/输出），效力审查优先于条款优化 |
| 风险标签 | 四级严重度 | **15标签体系**（效力与合规5 + 交易结构与履行5 + 争议解决与文本5） |
| 风险评价 | 三维度评分 | **六维度评价**（定性/敞口/概率/可规避性/商业权衡/紧迫性）+ **8维度雷达图** |
| 修订方式 | 凭感觉选择 | **路由决策树 + 4问自检**，21条路由规则，8条常用条款默认 Track Changes |
| 条款审查 | 单层检查 | **正反两面法**（正面→反面→救济执行） |
| 条款库 | 内置 CSV | **引用工作区105条款库**（索引匹配，三步匹配法） |
| 客户配置 | 无 | **ClientConfig** 自动识别客户并加载偏好，未命中不套用 |
| 输出 | Markdown + 简单批注 | **终稿三件套**（批注版合同 + 5模块法律意见书 + 法律分析），全部 .docx |
| 条款提取 | 无 | **Step 7 自动提取**，扫描值得入库的条款写法 |
| 代码规模 | ~3,000行 | ~4,500行（+2新模块，8模块重度扩展） |
| 数据文件 | 4个CSV | 6个CSV（新增 risk_labels + revision_routing，原有4个全部扩展列） |

### 架构升级

```
V2.1:  ContractReviewPro 类 → quick_review() → Markdown 输出

V3.0:  ContractReviewSession（有状态会话）
       ├── Step 0: ClientConfig.load_from_workspace()
       ├── Step 1-2: ContractAnalyzer.parse_contract()
       ├── Step 3: ContractAnalyzer.run_validity_review() + run_gate_checks()
       ├── Step 5: 知识库研究（AI 执行，skill 提供路由）
       ├── Step 6: ClauseReviewer.review_clause_dual()
       │           RiskAssessment.evaluate_risk_dimensions()
       │           RevisionRouter.determine_revision_method()
       │           RiskScoringSystem.calculate_dimension_weighted_score()
       ├── Step 7: ClauseExtractor.scan_for_candidates()
       └── Output: DocumentGenerator → 终稿三件套 .docx
```

---

## 支持的合同类型（30种）

覆盖中国大陆民商事合同的主要类型，按业务领域分为七大类别：

### 物权与买卖类（5种）

买卖合同、租赁合同、赠与合同、土地承包合同、商品房买卖合同

### 服务与承揽类（8种）

服务合同（通用）、承揽合同、委托合同、中介合同、仓储合同、物业服务合同、特许经营合同、旅游合同

### 公司与组织类（5种）

股权转让合同、增资扩股协议、对赌协议、一致行动协议、合伙合同

### 金融与证券类（4种）

借款合同、担保合同、保险合同、证券服务合同

### 劳动与人事类（3种）

劳动合同、劳务派遣合同、竞业限制协议

### 技术类（2种）

技术开发合同、技术转让合同

### 建设工程类（3种）

建设工程合同、工程监理合同、勘察设计合同

> 每种合同类型对应专属的风险模板、审查清单和条款标准，可自动匹配。详见 `data/contract_types.csv`。

---

## 核心工作流（7步）

1. **Step 0 — 识别客户**：文本匹配关联主体 → 加载 `.claude/client-rules/` → 提取结构化配置
2. **Step 1 — 建立 review-state**：源文件、客户、起草方、交易结构、风险预分类（8维度1-5分）、法律问题清单
3. **Step 2 — 通读合同**：完整阅读，梳理主体/标的/价款/交付/结算/违约/解除/担保/争议/附件
4. **Step 3 — 效力审查优先**：5项检查（名实不符/关联交易/格式条款/审批登记/成立要素），发现问题先处理效力再谈条款
5. **Step 4 — 列出法律问题清单**：需研究的实质性法律问题，标注风险标签
6. **Step 5 — 知识库研究**：每个问题至少检索2个来源，读取 `knowledge-routing.md` 确定路径
7. **Step 6 — 逐条审核**：正反两面法 × 六维度评价 × 路由决策树
8. **Step 7 — 条款提取**：扫描候选条款 → 输出到 `candidates/`，禁止直接写入正式库

---

## 审查门禁（5类）

| 门禁 | 检查内容 |
|------|---------|
| `gate_validity` | 名实不符、关联交易、格式条款、审批登记、成立要素 |
| `gate_subject` | 主体适格、签章、授权委托、表见代理、一人公司、担保决议 |
| `gate_clause` | 价款支付、交付验收、违约责任、解除清算、担保保险、送达争议 |
| `gate_consistency` | 正文与附件、金额数量、期限条件、定义用法 |
| `gate_output` | 三件套完整性 |

---

## 修订方式路由决策树

```
错别字/笔误/标点/日期格式/法律名称过时 → Track Changes 直接修订
对我方有利且可直接落地的增补条款 → Track Changes 直接补充：
  · 实现债权费用、送达确认、签章生效、声明与保证
  · 限制收款方式、反商业贿赂、独立关系声明、一人公司补充
条款矛盾/文本不一致 → Comments 指出矛盾，给出倾向性建议
商业取舍/重大风险/对方可能不接受 → Comments 列出方案
事实待核 → Comments 标注
多方案需客户选择 → Comments 列出方案并标注倾向
```

**4问自检**（每条审核意见必问）：
1. 我能替客户直接改吗？→ 能则 Track Changes
2. 涉及商业判断吗？→ 是则 Comments
3. 对方大概率会接受吗？→ 是则 Track Changes（标注告知客户）
4. 有多个合理方案吗？→ 是则 Comments，列出方案

---

## 风险标签体系（15标签）

**效力与合规类**：`合同效力` `格式条款` `主体授权` `关联交易` `合规审查`

**交易结构与履行类**：`价款与支付` `交付与验收` `违约责任` `解除与终止` `担保与增信`

**争议解决与文本类**：`争议解决` `知识产权与保密` `定义与附件` `文本一致性` `文字与格式`

---

## 风险评价六维度

1. **风险定性** — 风险类型
2. **风险敞口** — 最坏情况下损失
3. **发生概率** — 基于规则明确程度、当地口径、类案趋势
4. **可规避性** — 能否通过结构调整或条款修改消除
5. **商业权衡** — 结合客户目标和替代方案判断
6. **紧迫性** — 立即处理 / 近期处理 / 持续观察 / 远期风险

---

## 终稿三件套

`output/` 默认产出（全部 `.docx`）：

1. **批注版合同** — Track Changes + Comments，走 Document Library 三步法（unpack→编辑→pack），禁止 python-docx 裸 API
2. **法律意见书（5模块）** — 风险总览（数量卡片+雷达图+类型分布+综合等级）→ 合同基本信息 → 逐条审核意见（表格）→ 总体评价与签约利弊分析 → 法律依据清单
3. **法律分析** — 内部参考，修订点对应的法条/司法解释/指导案例/类案裁判规则

核心原则：**律师分析利弊，客户做决定。** 禁止以"建议签署""不建议签署"替代利弊分析。

---

## 数据规模

- **合同类型**：30种，覆盖7大业务领域
- **风险点模板**：124个，每个含15标签标注、8维度归类、六维度占位、默认修订方式
- **审查检查清单**：53项，按5类门禁分组，标注可自动检测项
- **标准条款**：18类模板，含工作区条款库索引、触发条件和插入优先级
- **路由规则**：21条，覆盖错别字到多方案选择的完整决策链
- **代码规模**：~4,500行，12个核心模块

---

## 项目结构

```
contract-review-pro/
├── SKILL.md                    # AI 面向指令文档
├── main.py                     # 主入口 + ContractReviewSession
├── skill.json                  # Skill 元数据（V3.0）
├── README.md                   # 本文件
│
├── scripts/                    # 核心模块（12个）
│   ├── review_config.py        # 审核配置 + ClientConfig
│   ├── contract_analyzer.py    # 合同解析 + 效力审查 + 门禁
│   ├── risk_assessment.py      # 风险评估 + 六维度 + 雷达图
│   ├── clause_review.py        # 正反两面法 + 条款库匹配
│   ├── revision_router.py      # 路由决策树 + 4问自检 ★新
│   ├── clause_extractor.py     # 自动条款提取 ★新
│   ├── intelligent_scoring.py  # 8维度评分 + 六维度综合
│   ├── sanguan_analysis.py     # 三观四步法深度分析
│   ├── document_generator.py   # 三件套 docx 生成
│   └── docx_generator.py       # Track Changes + Comments
│
├── data/                       # 数据文件（6个CSV）
│   ├── contract_types.csv      # 30种合同类型
│   ├── risk_templates.csv      # 124个风险点
│   ├── clause_standards.csv    # 18类标准条款
│   ├── review_checklists.csv   # 53项检查清单
│   ├── risk_labels.csv         # 15标签体系 ★新
│   └── revision_routing.csv    # 21条路由规则 ★新
│
└── output/                     # 终稿输出目录
```

---

## 快速开始

### 基础用法（向后兼容）

```python
from main import quick_review

result = quick_review(
    contract_text=contract_text,
    contract_name='A公司B公司买卖合同',
    user_context={'party': '甲方', 'position': '平等'},
    review_depth='standard'
)
```

### V3.0 新入口（工作区集成）

```python
from main import review_with_workspace_config

result = review_with_workspace_config(
    contract_path='/path/to/contract.docx',
    workspace_path='/Users/CS/Trae/个人工作/合同审核',
    client_name='示例客户',          # 可选，自动识别备选
    user_context={'party': '甲方'},
    depth='standard'
)
# result['outputs'] → {'opinion': ..., 'analysis_doc': ..., 'annotated': ...}
```

---

## 条款库使用

条款库位于工作区 `.claude/clauses/`（105个条款，15+业务领域），Skill 通过索引引用而非复制。

**三步匹配法**：
1. 理解场景（合同类型、当事人关系、风险等级）
2. 匹配写法（基础版 vs 强化版，按标的额和对方资信选择）
3. 适配调整（变量替换、表述统一、删去不适用内容）

禁止不经适配直接复制条款文本。Skill 独立运行时使用自带 CSV 数据作为降级方案。

---

## 硬约束

1. 禁止跳过通读直接审核
2. 禁止跳过实质性法律问题研究
3. 禁止跳过效力审查
4. 禁止先写审核意见后补法律依据
5. 禁止修改原始合同
6. 禁止用 python-docx 裸 API 生成批注版合同
7. 禁止将 .md 作为终稿交付
8. 禁止从零写批注脚本
9. 禁止将应 Track Changes 的增补条款降级为 Comments
10. 禁止在未命中客户规则时套用其他客户偏好

---

## 版本历史

| 版本 | 日期 | 关键变化 |
|------|------|---------|
| V1.1 | 2025-01 | 三观四步法集成、扩展到30种合同类型 |
| V1.2 | 2025-01 | 智能风险评分系统、深度审核功能 |
| V2.0 | 2026-01 | 智能输出目录、详细批注版合同、风险可视化 |
| V2.1 | 2026-04 | Word Track Changes + Comments、OOXML 原生修订标记 |
| **V3.0** | **2026-05** | **7步工作流、5类门禁、15标签、六维度评价、终稿三件套、路由决策树、条款自动提取** |

---

## 适用场景

- **律师应急审查**：快速识别重大风险，5-10分钟完成关键条款审查
- **企业法务标准审核**：全面风险评估，30-60分钟产出完整审核意见
- **重大交易深度尽调**：三观四步法完整分析，1-2小时出具专业法律意见书
- **法学教学辅助**：展示合同审核方法论，辅助理解三观四步法和三维审查法

---

## 免责声明

本 Skill 提供的合同审核仅供参考，不构成正式法律意见。AI 生成内容必须经专业法律人士审核。使用本系统产生的法律后果由使用者承担。

---

## 作者

**陈石（CS）** — 浙江海泰律师事务所高级合伙人

**专业领域**：建筑房地产、公司法、投融资及商事争议解决，执业年限15+年。

**学术与技术背景**：
- 著作《赋能法律人：AI 底层思维与应用范式》（2025年12月出版），系统探讨 AI 与法律的深度融合应用
- 在全国各地及通过互联网举办 AI 与法律应用主题讲座，harness Engineering 在法律场景的结构化应用
- 结合哲学、控制论、社会进化论等跨学科视角构建法律 AI 方法论

**主要成果**：
- China Lawyer Analyst Skill — 专业中国法律分析 Claude Skill
- Excellent Judgment Doc Skill — 优秀裁判文书生成与质量评判工具
- Contract Review Pro — 专业合同审核 AI 系统
- Case Type Guide System — 类案办案要件指南智能辅助系统

**联系方式**：
- GitHub: [CSlawyer1985](https://github.com/CSlawyer1985)
- Email: chenshi@hightac.com
- 地址: 浙江海泰律师事务所



---

**Made with ❤️ by 陈石（CS）**
