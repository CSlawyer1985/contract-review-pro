"""
Contract Review Pro - 主入口
专业合同审核 Skill 的主入口文件
V1.2: 深度集成三观四步法和智能风险评分系统
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# 添加 scripts 目录到 Python 路径
scripts_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from review_config import ReviewConfig
from contract_analyzer import ContractAnalyzer
from risk_assessment import RiskAssessment
from clause_review import ClauseReviewer
from document_generator import DocumentGenerator
from sanguan_analysis import SanguanAnalysis
from intelligent_scoring import RiskScoringSystem


class ContractReviewPro:
    """合同审核系统主类"""

    def __init__(self, data_dir: str = None, methodology_file: str = None,
                 output_dir: str = None):
        """
        初始化合同审核系统

        Args:
            data_dir: 数据目录路径
            methodology_file: 方法学文件路径
            output_dir: 输出目录路径
        """
        # 默认路径
        base_dir = Path(__file__).parent
        self.data_dir = data_dir or str(base_dir / 'data')
        self.methodology_file = methodology_file or str(base_dir.parent.parent / '合同审核方法论体系_完整版.md')
        self.output_dir = output_dir or str(base_dir / 'output')

    def query_contract_type(self, contract_type: str) -> dict:
        """
        查询合同类型审核指引

        Args:
            contract_type: 合同类型名称（如"买卖合同"）

        Returns:
            审核指引字典
        """
        # 使用标准审核配置
        config = ReviewConfig('standard')
        analyzer = ContractAnalyzer(self.data_dir, self.methodology_file, config)

        return analyzer.analyze_contract_type(contract_type)

    def review_contract(self, contract_text: str, contract_name: str,
                       user_context: dict, review_depth: str = 'standard') -> dict:
        """
        审核具体合同

        Args:
            contract_text: 合同文本
            contract_name: 合同名称
            user_context: 用户上下文信息
                - party: 代表方（甲方/乙方）
                - position: 市场地位（强势/平等/弱势）
                - history: 过往交易
                - focus: 关注点
            review_depth: 审核深度（quick/standard/deep）

        Returns:
            审核结果字典，包含：
            - analysis_result: 合同分析结果
            - risk_report: 风险报告
            - opinion_file: 法律意见书路径
            - annotated_file: 批注版合同路径
        """
        # 初始化配置
        config = ReviewConfig(review_depth)

        # 初始化各个模块
        analyzer = ContractAnalyzer(self.data_dir, self.methodology_file, config)
        risk_assessor = RiskAssessment(self.data_dir, config)
        clause_reviewer = ClauseReviewer(self.data_dir)
        doc_generator = DocumentGenerator(self.output_dir)

        # 解析合同
        analysis_result = analyzer.parse_contract(contract_text)
        analysis_result['contract_name'] = contract_name
        analysis_result['review_config'] = config.get_review_scope()

        # 评估风险
        all_risks = []
        for clause_type, clauses in analysis_result['clauses'].items():
            for clause in clauses:
                risks = risk_assessor.assess_clause_risk(
                    clause['content'],
                    clause_type,
                    analysis_result['identified_type']
                )
                all_risks.extend(risks)

        risk_report = risk_assessor.generate_risk_report(all_risks)

        # 生成文档
        opinion_file = doc_generator.generate_legal_opinion(
            contract_name,
            analysis_result,
            risk_report,
            {**user_context, 'review_depth': config.config['name'],
             'review_scope': config.config['focus'],
             'risk_levels': config.config['check_categories']}
        )

        annotated_file = doc_generator.generate_annotated_contract(
            contract_name,
            contract_text,
            []  # 修订列表（未来可扩展）
        )

        return {
            'analysis_result': analysis_result,
            'risk_report': risk_report,
            'opinion_file': opinion_file,
            'annotated_file': annotated_file
        }

    def collect_review_feedback(self, review_result: dict, feedback: dict) -> str:
        """
        收集审核反馈数据 (V1.1新增功能)

        Args:
            review_result: 审核结果
            feedback: 用户反馈
                - risk_accuracy: 风险识别准确性 (1-5分)
                - suggestion_helpful: 建议是否有帮助 (True/False)
                - suggested_improvements: 建议改进内容
                - risks_corrected: 实际修正的风险点列表
                - additional_risks: 用户发现的风险点

        Returns:
            保存的数据文件路径
        """
        # 准备收集数据
        collection_data = {
            'timestamp': datetime.now().isoformat(),
            'contract_name': review_result['analysis_result'].get('contract_name', '未知'),
            'contract_type': review_result['analysis_result']['identified_type'],
            'review_depth': review_result['analysis_result']['review_config']['name'],
            'total_risks': review_result['risk_report']['total_risks'],
            'risk_breakdown': review_result['risk_report'].get('by_level', {}),
            'feedback': feedback
        }

        # 创建数据收集目录
        collection_dir = Path(self.output_dir).parent / 'data_collection'
        collection_dir.mkdir(exist_ok=True)

        # 保存为JSON
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = collection_dir / f'feedback_{timestamp_str}.json'

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)

        # 同时追加到CSV (便于统计分析)
        csv_file = collection_dir / 'feedback_summary.csv'
        file_exists = csv_file.exists()

        with open(csv_file, 'a', encoding='utf-8', newline='') as f:
            fieldnames = ['timestamp', 'contract_type', 'review_depth',
                         'total_risks', 'fatal_risks', 'important_risks',
                         'risk_accuracy', 'suggestion_helpful']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'timestamp': collection_data['timestamp'],
                'contract_type': collection_data['contract_type'],
                'review_depth': collection_data['review_depth'],
                'total_risks': collection_data['total_risks'],
                'fatal_risks': collection_data['risk_breakdown'].get('致命风险', 0),
                'important_risks': collection_data['risk_breakdown'].get('重要风险', 0),
                'risk_accuracy': feedback.get('risk_accuracy', ''),
                'suggestion_helpful': feedback.get('suggestion_helpful', '')
            })

        return str(json_file)

    def advanced_review_with_sanguan(self, contract_text: str, contract_name: str,
                                     user_context: dict, review_depth: str = 'standard') -> dict:
        """
        V1.2新功能: 使用三观四步法进行深度审核

        Args:
            contract_text: 合同文本
            contract_name: 合同名称
            user_context: 用户上下文信息
            review_depth: 审核深度

        Returns:
            包含三观四步法分析和智能评分的审核结果
        """
        # 基础审核
        basic_result = self.review_contract(contract_text, contract_name, user_context, review_depth)

        # V1.2: 三观四步法分析
        sanguan_analyzer = SanguanAnalysis()
        contract_type = basic_result['analysis_result']['identified_type']

        # 三维审查法
        commercial_analysis = sanguan_analyzer.analyze_commercial_dimension(contract_text, user_context)
        legal_analysis = sanguan_analyzer.analyze_legal_dimension(contract_text, contract_type)
        practical_analysis = sanguan_analyzer.analyze_practical_dimension(contract_text)

        # 四步法流程
        foursteps_analysis = sanguan_analyzer.apply_sanguan_foursteps(contract_text, user_context)

        # 智能风险评分
        scorer = RiskScoringSystem()
        scoring_result = scorer.calculate_comprehensive_risk_score(
            commercial_analysis, legal_analysis, practical_analysis
        )

        # 整合结果
        advanced_result = {
            'basic_review': basic_result,
            'sanguan_analysis': {
                'three_dimensions': {
                    'commercial': commercial_analysis,
                    'legal': legal_analysis,
                    'practical': practical_analysis
                },
                'four_steps': foursteps_analysis
            },
            'intelligent_scoring': scoring_result
        }

        return advanced_result

    def generate_advanced_opinion(self, advanced_result: dict, contract_name: str) -> str:
        """
        V1.2新功能: 生成包含三观四步法分析的法律意见书

        Args:
            advanced_result: advanced_review_with_sanguan的返回结果
            contract_name: 合同名称

        Returns:
            法律意见书文件路径
        """
        from datetime import datetime

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{contract_name}_深度审核意见书_{timestamp}.md"
        output_path = Path(self.output_dir) / 'opinions' / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 提取数据
        scoring = advanced_result['intelligent_scoring']
        sanguan = advanced_result['sanguan_analysis']
        basic = advanced_result['basic_review']

        # 生成Markdown报告
        content = f"""# {contract_name} 深度法律审核意见书 (三观四步法)

---

## 一、智能风险评分

- **综合评分**: {scoring['comprehensive_score']}/100
- **风险等级**: {scoring['risk_level']}
- **审核时间**: {datetime.now().strftime('%Y年%m月%d日')}

### 各维度评分

| 维度 | 评分 | 等级 |
|------|------|------|
| 商业维度 | {scoring['dimension_scores']['commercial']} | {'优秀' if scoring['dimension_scores']['commercial'] >= 80 else '良好' if scoring['dimension_scores']['commercial'] >= 60 else '中等'} |
| 法律维度 | {scoring['dimension_scores']['legal']} | {'优秀' if scoring['dimension_scores']['legal'] >= 80 else '良好' if scoring['dimension_scores']['legal'] >= 60 else '中等'} |
| 实务维度 | {scoring['dimension_scores']['practical']} | {'优秀' if scoring['dimension_scores']['practical'] >= 80 else '良好' if scoring['dimension_scores']['practical'] >= 60 else '中等'} |

### 风险分布

{self._format_risk_distribution(scoring['risk_distribution'])}

### 关键风险

{self._format_key_risks(scoring['key_risks'])}

### 综合建议

{self._format_recommendations(scoring['recommendations'])}

---

## 二、三维审查法分析

### 2.1 商业维度分析

**评级**: {sanguan['three_dimensions']['commercial']['rating']}

**主要发现**:
{self._format_findings(sanguan['three_dimensions']['commercial']['findings'])}

**识别的风险**:
{self._format_risks(sanguan['three_dimensions']['commercial']['risks'])}

**改进建议**:
{self._format_suggestions(sanguan['three_dimensions']['commercial']['suggestions'])}

### 2.2 法律维度分析

**评级**: {sanguan['three_dimensions']['legal']['rating']}

**主要发现**:
{self._format_findings(sanguan['three_dimensions']['legal']['findings'])}

**识别的风险**:
{self._format_risks(sanguan['three_dimensions']['legal']['risks'])}

**改进建议**:
{self._format_suggestions(sanguan['three_dimensions']['legal']['suggestions'])}

### 2.3 实务维度分析

**评级**: {sanguan['three_dimensions']['practical']['rating']}

**主要发现**:
{self._format_findings(sanguan['three_dimensions']['practical']['findings'])}

**识别的风险**:
{self._format_risks(sanguan['three_dimensions']['practical']['risks'])}

**改进建议**:
{self._format_suggestions(sanguan['three_dimensions']['practical']['suggestions'])}

---

## 三、三观四步法流程

{self._format_foursteps(sanguan['four_steps'])}

---

## 四、传统审核结果

{self._format_basic_review(basic)}

---

*本意见书由 Contract Review Pro V1.2 生成，融合了三观四步法和智能风险评分系统。*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(output_path)

    # ============ 格式化辅助方法 ============

    def _format_risk_distribution(self, distribution: dict) -> str:
        """格式化风险分布"""
        lines = ["\n| 风险等级 | 数量 |"]
        lines.append("|----------|------|")
        for level, count in distribution.items():
            lines.append(f"| {level} | {count} |")
        return '\n'.join(lines)

    def _format_key_risks(self, risks: list) -> str:
        """格式化关键风险"""
        if not risks:
            return "无关键风险"
        lines = []
        for risk in risks[:10]:  # 最多显示10个
            lines.append(f"\n#### [{risk['level']}] {risk['type']}")
            lines.append(f"- **描述**: {risk['description']}")
            lines.append(f"- **建议**: {risk['suggestion']}")
        return '\n'.join(lines)

    def _format_recommendations(self, recommendations: list) -> str:
        """格式化建议"""
        if not recommendations:
            return "无特殊建议"
        return '\n'.join(f"- {rec}" for rec in recommendations)

    def _format_findings(self, findings: list) -> str:
        """格式化发现"""
        if not findings:
            return "无"
        lines = []
        for finding in findings:
            lines.append(f"- **{finding.get('category', '发现')}**: {finding.get('content', '')} ({finding.get('significance', '')})")
        return '\n'.join(lines)

    def _format_risks(self, risks: list) -> str:
        """格式化风险"""
        if not risks:
            return "无"
        lines = []
        for risk in risks:
            lines.append(f"- **[{risk.get('level', '')}] {risk.get('risk_type', '')}**: {risk.get('description', '')}")
            lines.append(f"  - 建议: {risk.get('suggestion', '')}")
        return '\n'.join(lines)

    def _format_suggestions(self, suggestions: list) -> str:
        """格式化建议"""
        if not suggestions:
            return "无"
        return '\n'.join(f"- {s.get('content', '')}" for s in suggestions)

    def _format_foursteps(self, foursteps: dict) -> str:
        """格式化四步法"""
        lines = []
        for step_info in foursteps.get('steps', []):
            lines.append(f"\n### {step_info['step']}")
            for key, value in step_info['analysis'].items():
                if isinstance(value, dict):
                    lines.append(f"\n**{key}**:")
                    for k, v in value.items():
                        lines.append(f"- {k}: {v}")
                elif isinstance(value, list):
                    lines.append(f"\n**{key}**: {len(value)}项")
                else:
                    lines.append(f"\n**{key}**: {value}")
        return '\n'.join(lines)

    def _format_basic_review(self, basic: dict) -> str:
        """格式化基础审核结果"""
        return f"""
- **识别类型**: {basic['analysis_result']['identified_type']}
- **置信度**: {basic['analysis_result']['type_confidence']:.0%}
- **发现风险数**: {basic['risk_report']['total_risks']}个
- **法律意见书**: {basic['opinion_file']}
"""

    def get_supported_contract_types(self) -> list:
        """获取支持的合同类型列表"""
        import pandas as pd
        contract_types_file = Path(self.data_dir) / 'contract_types.csv'
        df = pd.read_csv(contract_types_file, encoding='utf-8')
        return df['contract_type'].tolist()

    def get_review_depth_options(self) -> dict:
        """获取审核深度选项"""
        return ReviewConfig.DEPTH_LEVELS


# 便捷函数
def quick_query(contract_type: str) -> dict:
    """快速查询合同类型指引"""
    system = ContractReviewPro()
    return system.query_contract_type(contract_type)


def quick_review(contract_text: str, contract_name: str, user_context: dict,
                review_depth: str = 'standard') -> dict:
    """快速审核合同"""
    system = ContractReviewPro()
    return system.review_contract(contract_text, contract_name, user_context, review_depth)


def advanced_review(contract_text: str, contract_name: str, user_context: dict,
                   review_depth: str = 'standard') -> tuple:
    """
    V1.2新功能: 三观四步法深度审核

    Returns:
        (审核结果, 深度意见书文件路径)
    """
    system = ContractReviewPro()
    result = system.advanced_review_with_sanguan(contract_text, contract_name, user_context, review_depth)
    opinion_file = system.generate_advanced_opinion(result, contract_name)
    return result, opinion_file


if __name__ == '__main__':
    # 测试代码
    print("=== Contract Review Pro 测试 ===\n")

    system = ContractReviewPro()

    # 测试1：获取支持的合同类型
    print("=== 支持的合同类型 ===")
    types = system.get_supported_contract_types()
    print(f"共支持 {len(types)} 种合同类型:")
    for i, ct in enumerate(types, 1):
        print(f"  {i}. {ct}")
    print()

    # 测试2：查询合同类型指引
    print("=== 查询买卖合同审核指引 ===")
    result = system.query_contract_type('买卖合同')
    print(f"合同类型: {result['contract_type']}")
    print(f"分类: {result['category']}")
    print(f"核心风险: {result['core_risks']}")
    print(f"风险点数量: {len(result['risks'])}")
    print()

    # 测试3：审核一份简单合同
    print("=== 审核测试合同 ===")
    sample_contract = """
    买卖合同

    甲方：A公司
    乙方：B公司

    第一条 标的物
    本合同标的物为一批货物。

    第二条 价款
    总价款100万元。

    第三条 违约责任
    任何一方违约应承担责任。
    """

    user_context = {
        'party': '甲方',
        'position': '平等',
        'history': '无',
        'focus': '付款安全'
    }

    review_result = system.review_contract(
        sample_contract,
        '测试买卖合同',
        user_context,
        'quick'  # 使用快速审核
    )

    print(f"识别类型: {review_result['analysis_result']['identified_type']}")
    print(f"提取条款数: {review_result['analysis_result']['total_clauses']}")
    print(f"发现风险数: {review_result['risk_report']['total_risks']}")
    print(f"法律意见书: {review_result['opinion_file']}")
    print(f"批注版合同: {review_result['annotated_file']}")
