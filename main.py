"""
Contract Review Pro - 主入口 V3.0
专业合同审核 Skill，支持工作区配置、7步工作流、终稿三件套
"""

import sys
import json
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

scripts_dir = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from review_config import ReviewConfig, ClientConfig
from contract_analyzer import ContractAnalyzer
from risk_assessment import RiskAssessment
from clause_review import ClauseReviewer
from document_generator import DocumentGenerator
from sanguan_analysis import SanguanAnalysis
from intelligent_scoring import RiskScoringSystem
from revision_router import RevisionRouter
from clause_extractor import ClauseExtractor


class ContractReviewSession:
    """7 步有状态审核会话（V3.0 新增）"""

    def __init__(self, contract_path: str, workspace_path: Optional[str] = None,
                 client_name: Optional[str] = None, depth: str = "standard"):
        self.base_dir = Path(__file__).parent
        self.data_dir = str(self.base_dir / "data")
        self.contract_path = Path(contract_path)
        self.contract_name = self.contract_path.stem
        self.workspace_path = workspace_path

        # Step 0: 识别客户
        client_config = None
        if client_name and workspace_path:
            client_config = ClientConfig.load_from_workspace(workspace_path, client_name)
        elif workspace_path:
            # 尝试从合同文本匹配关联主体
            pass  # 需读取合同后识别

        self.config = ReviewConfig(depth, client_config=client_config,
                                   workspace_path=workspace_path)
        self.state = {"step": 0, "client_name": client_name}

        print(f"审查会话已建立: {self.contract_name}")

    def execute_workflow(self, contract_text: str, user_context: Dict) -> Dict:
        """执行完整 7 步工作流"""
        results = {}

        # Step 1: 建立 review-state
        self.state["step"] = 1
        self.state["review_state"] = {
            "source": str(self.contract_path),
            "client": self.state.get("client_name", "未识别"),
            "started_at": datetime.now().isoformat(),
        }

        # Step 2: 通读合同 + Step 3: 效力审查优先
        self.state["step"] = 3
        analyzer = ContractAnalyzer(self.data_dir, "", self.config)
        analysis = analyzer.parse_contract(contract_text)
        results["analysis"] = analysis

        if analysis.get("validity_review", {}).get("blocking_count", 0) > 0:
            results["validity_warning"] = analysis["validity_review"]

        # Step 4: 法律问题清单
        self.state["step"] = 4
        results["issue_checklist"] = self._build_issue_checklist(analysis)

        # Step 5: 知识库研究标记（提醒 AI 执行）
        self.state["step"] = 5
        results["kb_research_needed"] = True

        # Step 6: 逐条审核（正反两面法）
        self.state["step"] = 6
        risk_assessor = RiskAssessment(self.data_dir, self.config)
        reviewer = ClauseReviewer(self.data_dir)
        router = RevisionRouter(self.data_dir)

        all_risks = []
        for clause_type, clauses in analysis.get("clauses", {}).items():
            for clause in clauses:
                risks = risk_assessor.assess_clause_risk(
                    clause["content"], clause_type, analysis.get("identified_type", "")
                )
                dual = reviewer.review_clause_dual(clause["content"], clause_type)
                for risk in risks:
                    risk["dual_review"] = dual
                    decision = router.determine_revision_method(risk.get("description", ""))
                    risk["revision_method"] = decision.method
                all_risks.extend(risks)

        risk_report = risk_assessor.generate_risk_report(all_risks)
        results["risk_report"] = risk_report

        # 评分
        scorer = RiskScoringSystem()
        if risk_report.get("radar_data"):
            results["scoring"] = scorer.calculate_dimension_weighted_score(risk_report["radar_data"])

        # Step 7: 条款提取
        self.state["step"] = 7
        lib = self.config.get_clause_library_path()
        if lib:
            extractor = ClauseExtractor(lib)
            candidates = extractor.scan_for_candidates(
                [{"type": ct, "text": c.get("content", "")}
                 for ct, cls in analysis.get("clauses", {}).items() for c in cls],
                analysis.get("identified_type", "")
            )
            results["clause_candidates"] = candidates

        self.state["completed"] = True
        return results

    def _build_issue_checklist(self, analysis: Dict) -> List[Dict]:
        items = []
        gate_result = analysis.get("gate_checks", {})
        for gate_name, gate in gate_result.get("gates", {}).items():
            if not gate.get("pass", True):
                items.append({"gate": gate_name, "issues": gate.get("missing", gate.get("items", []))})
        return items

    def generate_outputs(self, results: Dict, user_context: Dict, output_dir: str) -> Dict[str, str]:
        """生成终稿三件套"""
        doc_gen = DocumentGenerator(output_dir)
        outputs = {}

        # 法律意见书
        outputs["opinion"] = doc_gen.generate_legal_opinion_docx(
            self.contract_name, results.get("analysis", {}),
            results.get("risk_report", {}), user_context,
            author=self.config.author
        )

        # 法律分析
        outputs["analysis_doc"] = doc_gen.generate_legal_analysis_docx(
            self.contract_name, results.get("analysis", {}),
            results.get("risk_report", {})
        )

        # 批注版合同
        if self.contract_path.exists():
            annotated = doc_gen.generate_annotated_contract_docx(
                self.contract_name, str(self.contract_path),
                results.get("risk_report", {}),
                author=self.config.author, initials=self.config.initials
            )
            if annotated:
                outputs["annotated"] = annotated

        return outputs


class ContractReviewPro:
    """合同审核系统主类（向后兼容）"""

    def __init__(self, data_dir: str = None, methodology_file: str = None,
                 output_dir: str = None, use_current_dir: bool = True,
                 workspace_path: str = None, client_name: str = None):
        base_dir = Path(__file__).parent
        self.data_dir = data_dir or str(base_dir / 'data')
        self.methodology_file = methodology_file or ""
        self.workspace_path = workspace_path

        if use_current_dir:
            self.output_dir = Path.cwd()
        elif output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.cwd()

        # 客户配置
        client_config = None
        if client_name and workspace_path:
            client_config = ClientConfig.load_from_workspace(workspace_path, client_name)
        self.client_config = client_config

        print(f"Contract Review Pro V3.0 | 输出: {self.output_dir}")

    def query_contract_type(self, contract_type: str) -> dict:
        """查询合同类型审核指引"""
        config = ReviewConfig('standard')
        analyzer = ContractAnalyzer(self.data_dir, self.methodology_file, config)
        return analyzer.analyze_contract_type(contract_type)

    def review_contract(self, contract_text: str, contract_name: str,
                       user_context: dict, review_depth: str = 'standard') -> dict:
        """
        审核具体合同 (优化版)
        
        优化点：
        1. 输出目录使用当前工作目录
        2. 批注版合同更加详细
        """
        # 初始化配置
        config = ReviewConfig(review_depth)

        # 初始化各个模块
        analyzer = ContractAnalyzer(self.data_dir, self.methodology_file, config)
        risk_assessor = RiskAssessment(self.data_dir, config)
        clause_reviewer = ClauseReviewer(self.data_dir)
        doc_generator = DocumentGenerator(str(self.output_dir))  # 使用优化后的输出目录

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

        # 生成详细批注版合同
        annotated_file = doc_generator.generate_detailed_annotated_contract(
            contract_name,
            contract_text,
            analysis_result,
            risk_report,
            user_context
        )

        return {
            'analysis_result': analysis_result,
            'risk_report': risk_report,
            'opinion_file': opinion_file,
            'annotated_file': annotated_file
        }

    def get_supported_contract_types(self) -> list:
        """获取支持的合同类型列表"""
        import pandas as pd
        contract_types_file = Path(self.data_dir) / 'contract_types.csv'
        df = pd.read_csv(contract_types_file, encoding='utf-8')
        return df['contract_type'].tolist()


# ============ 便捷函数 ============

def quick_review(contract_text: str, contract_name: str, user_context: dict,
                review_depth: str = 'standard', output_dir: str = None,
                workspace_path: str = None, client_name: str = None) -> dict:
    """快速审核合同（向后兼容，新增工作区支持）"""
    system = ContractReviewPro(
        output_dir=output_dir, use_current_dir=(output_dir is None),
        workspace_path=workspace_path, client_name=client_name
    )
    return system.review_contract(contract_text, contract_name, user_context, review_depth)


def review_with_workspace_config(contract_path: str, workspace_path: str,
                                 client_name: str = None, user_context: dict = None,
                                 depth: str = "standard", output_dir: str = None) -> Dict:
    """
    使用工作区配置审核合同（V3.0 新入口）

    Args:
        contract_path: 合同文件路径（.txt 或 .docx）
        workspace_path: 合同审核工作区路径
        client_name: 客户简称（可选，自动识别的备选）
        user_context: 用户上下文 {party, position, history, focus}
        depth: 审核深度
        output_dir: 输出目录（默认当前目录）

    Returns:
        完整审核结果
    """
    # 读取合同
    with open(contract_path, "r", encoding="utf-8") as f:
        contract_text = f.read()

    contract_name = Path(contract_path).stem
    output_dir = output_dir or str(Path.cwd())

    # 建立会话并执行 7 步工作流
    session = ContractReviewSession(contract_path, workspace_path, client_name, depth)
    results = session.execute_workflow(contract_text, user_context or {})

    # 生成终稿三件套
    outputs = session.generate_outputs(results, user_context or {}, output_dir)

    return {
        "analysis": results.get("analysis", {}),
        "risk_report": results.get("risk_report", {}),
        "scoring": results.get("scoring", {}),
        "clause_candidates": results.get("clause_candidates", []),
        "outputs": outputs,
        "session_state": session.state,
    }


if __name__ == '__main__':
    # 测试代码
    print("=== Contract Review Pro V3.0 测试 ===\n")
    
    # 获取支持的合同类型
    system = ContractReviewPro()
    types = system.get_supported_contract_types()
    print(f"✅ 共支持 {len(types)} 种合同类型")
    print(f"📁 输出目录: {system.output_dir}\n")
