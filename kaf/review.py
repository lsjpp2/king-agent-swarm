#!/usr/bin/env python3
"""
KAF Multi-perspective Review — 多视角审查（低相关视角叠加）
参考 Cursor《智能体蜂群与新的模型经济学》(2026-07-20)：
- 没有任何单一视角能发现所有问题，但低相关视角叠加可像自动驾驶那样达到高于人类的可靠性
- 审查成本远低于被审查工作（worker 占 ~90% token），投入回报高

本模块提供审查"编排"：生成各正交视角的审查任务（交给不同 agent / 不同模型执行），
并叠加结论。实际审查执行由各 agent 完成（agent 写给 agent）。

Usage:
    from review import MultiReview
    mr = MultiReview()
    mr.suggest("path/to/artifact.py")   # 返回各视角审查任务清单
    mr.summarize(results)               # 叠加各视角结论 -> verdict

CLI:
    python review.py path/to/artifact.py [security correctness style economics]
"""
import sys
import os
import json


# 低相关视角：关注点正交，叠加覆盖更全面（每个视角可由不同模型/训练/个性运行）
PERSPECTIVES = {
    "security": {
        "focus": "安全：注入/越权/密钥泄露/不安全反序列化/命令注入",
        "prompt": "仅从安全角度审查以下产物，列出具体风险与修复建议，不要评价其他方面。",
    },
    "correctness": {
        "focus": "正确性：逻辑错误/边界条件/空值/并发/数据一致性",
        "prompt": "仅从正确性角度审查以下产物，列出 bug 与边界遗漏，不要评价其他方面。",
    },
    "style": {
        "focus": "风格：可读性/命名/结构/是否符合项目约定",
        "prompt": "仅从代码风格与可维护性角度审查，列出改进点，不要评价其他方面。",
    },
    "economics": {
        "focus": "经济性：是否用对了模型/是否过度设计/是否可用更便宜方案",
        "prompt": "仅从成本-质量经济性角度审查，指出是否浪费前沿模型或过度工程，不要评价其他方面。",
    },
}


class MultiReview:
    """多视角审查编排器"""

    def __init__(self, perspectives=None):
        self.perspectives = perspectives or list(PERSPECTIVES.keys())

    def suggest(self, artifact_path):
        """生成各视角的审查任务（建议派给不同模型/个性以最大化视角低相关性）"""
        if not os.path.exists(artifact_path):
            return {"error": f"文件不存在: {artifact_path}"}
        tasks = []
        for p in self.perspectives:
            spec = PERSPECTIVES.get(p, {})
            tasks.append({
                "perspective": p,
                "focus": spec.get("focus", ""),
                "prompt": spec.get("prompt", ""),
                "artifact": artifact_path,
                "assign_to": "low_correlation_agent",
            })
        return {
            "artifact": artifact_path,
            "review_count": len(tasks),
            "principle": "低相关视角叠加 > 单一完美视角；审查成本远低于被审查工作（worker 占 90% token）",
            "tasks": tasks,
        }

    def summarize(self, results):
        """叠加各视角结论。results: list of {perspective, severity, findings}"""
        summary = {"blockers": [], "warnings": [], "passed": []}
        for r in results:
            p = r.get("perspective")
            sev = r.get("severity", "warning")
            findings = r.get("findings", [])
            if sev == "blocker":
                summary["blockers"].append({p: findings})
            elif sev == "warning":
                summary["warnings"].append({p: findings})
            else:
                summary["passed"].append(p)
        verdict = "BLOCK" if summary["blockers"] else ("REVIEW" if summary["warnings"] else "PASS")
        summary["verdict"] = verdict
        summary["principle"] = "任一 blocker 视角即否决；多 warning 需人工复核；全 passed 放行"
        return summary

    # v5.2 进化（方向3·审查闭环）：BLOCK 结论自动写回共享 Field Guide（铁律/review_findings.md）
    SHARED_ROOT = os.environ.get("KAF_SHARED_DIR") or os.path.join(os.path.expanduser("~"), "kaf-shared")
    REVIEW_FINDINGS = os.path.join(SHARED_ROOT, "铁律", "review_findings.md")

    def commit(self, results):
        """审查闭环：叠加结论；若为 BLOCK，写回共享铁律/review_findings.md（Field Guide 双向化）。"""
        summary = self.summarize(results)
        if summary["verdict"] == "BLOCK":
            wb = self._write_back(summary, results)
            summary["written"] = wb.get("written", False)
            summary["written_path"] = wb.get("path")
        return summary

    def _write_back(self, summary, results):
        """把 BLOCK 级发现写入共享铁律/review_findings.md（agent 写给 agent 的可溯源意外记录）。"""
        from datetime import datetime
        os.makedirs(os.path.dirname(self.REVIEW_FINDINGS), exist_ok=True)
        lines = [f"\n## 审查发现 {datetime.now().isoformat(timespec='seconds')}",
                 f"- verdict: **BLOCK**（已触发写回）"]
        for b in summary["blockers"]:
            for p, findings in b.items():
                lines.append(f"- 视角[{p}] blockers:")
                for f in findings:
                    lines.append(f"  - {f}")
        lines.append("- 建议：沉淀为铁律/skill，防止复发（Field Guide 双向化）")
        content = "\n".join(lines) + "\n"
        mode = "a" if os.path.exists(self.REVIEW_FINDINGS) else "w"
        with open(self.REVIEW_FINDINGS, mode, encoding="utf-8") as fh:
            fh.write(content)
        return {"written": True, "path": self.REVIEW_FINDINGS}


def main():
    if len(sys.argv) < 2:
        print("Usage: python review.py <artifact_path> [perspective...]")
        print("       python review.py commit <findings.json>   # 审查闭环：BLOCK 写回共享铁律")
        return 1
    if sys.argv[1] == "commit":
        if len(sys.argv) < 3:
            print("  Usage: python review.py commit <findings.json>")
            return 1
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            results = json.load(f)
        mr = MultiReview()
        out = mr.commit(results)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    path = sys.argv[1]
    persp = sys.argv[2:] or None
    mr = MultiReview(persp)
    out = mr.suggest(path)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
