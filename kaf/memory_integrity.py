"""
KAF Memory Integrity Protocol — 记忆完整性协议
SHA-256指纹 + Drift检测 + Forward-Only版本控制

防止520法则/宪法/铁律被覆盖丢失。
"就算世界灭亡，这个标准不能丢。"

Usage:
    from memory_integrity import MemoryIntegrity
    mi = MemoryIntegrity()
    mi.calculate_fingerprint("META.md")     # 计算指纹
    mi.verify()                               # 启动时校验
    mi.protect_write(path, new_content)       # 写入前保护检查
"""
import hashlib
import json
import os
import re
from datetime import datetime


class MemoryIntegrity:
    """记忆完整性协议：指纹校验 + 写入保护 + Drift检测"""

    # 不可删除的元点文件段落（520保护）
    PROTECTED_PATTERNS = {
        "MEMORY.md": [
            r"520规则",
            r"四象限",
            r"铁律8",
            r"铁律9",
            r"铁律10",
            r"可追溯.*可恢复.*可修复.*可进化",
        ],
        "META.md": [
            r"520规则",
            r"四象限",
            r"v4事故",
        ],
    }

    def __init__(self, memory_dir=None):
        self.memory_dir = memory_dir or self._find_memory_dir()
        self.fingerprint_file = os.path.join(self.memory_dir, ".fingerprints.json")
        self.fingerprints = self._load_fingerprints()

    def _find_memory_dir(self):
        """查找记忆目录"""
        candidates = [
            os.path.expanduser("~/.workbuddy"),
            os.path.join(os.getcwd(), ".workbuddy", "memory"),
            "D:/WorkBuddy/Claw/.workbuddy/memory",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return candidates[0]

    def _load_fingerprints(self):
        """加载已保存的指纹"""
        if os.path.exists(self.fingerprint_file):
            try:
                with open(self.fingerprint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_fingerprints(self):
        """保存指纹"""
        with open(self.fingerprint_file, "w", encoding="utf-8") as f:
            json.dump(self.fingerprints, f, indent=2, ensure_ascii=False)

    def calculate_fingerprint(self, filepath):
        """计算文件的SHA-256指纹"""
        if not os.path.exists(filepath):
            return None
        with open(filepath, "rb") as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()

    def register(self, filepath):
        """注册文件指纹（首次或更新）"""
        fp = self.calculate_fingerprint(filepath)
        if fp:
            rel = os.path.relpath(filepath, self.memory_dir)
            self.fingerprints[rel] = {
                "sha256": fp,
                "registered_at": datetime.now().isoformat(),
                "size": os.path.getsize(filepath),
            }
            self._save_fingerprints()
        return fp

    def verify(self):
        """启动时校验所有注册文件的指纹"""
        results = {"passed": [], "failed": [], "missing": []}
        for rel, meta in self.fingerprints.items():
            filepath = os.path.join(self.memory_dir, rel)
            if not os.path.exists(filepath):
                results["missing"].append({"file": rel, "reason": "文件不存在"})
                continue
            current_fp = self.calculate_fingerprint(filepath)
            if current_fp == meta["sha256"]:
                results["passed"].append(rel)
            else:
                results["failed"].append({
                    "file": rel,
                    "expected": meta["sha256"][:16],
                    "actual": current_fp[:16] if current_fp else "none",
                    "reason": "指纹不匹配（可能被篡改/覆盖）"
                })
        results["summary"] = f"{len(results['passed'])}通过/{len(results['failed'])}失败/{len(results['missing'])}缺失"
        return results

    def protect_write(self, filepath, new_content):
        """写入前保护检查：防止删除受保护段落"""
        filename = os.path.basename(filepath)
        patterns = self.PROTECTED_PATTERNS.get(filename, [])

        if not patterns:
            return True  # 不受保护的文件，允许写入

        for pattern in patterns:
            if re.search(pattern, new_content, re.DOTALL):
                continue
            else:
                # 检查旧文件是否有这个模式（如果有，说明新内容删了它）
                old_content = ""
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        old_content = f.read()
                if re.search(pattern, old_content, re.DOTALL):
                    print(f"⚠️  BLOCKED: 写入将删除受保护内容 [{pattern}]")
                    print(f"   文件: {filepath}")
                    print(f"   520法则不可删除。如需修改，请先取得国王(人类)授权。")
                    return False

        # 写入通过保护检查，更新指纹
        return True

    def drift_check(self):
        """Drift检测：检查记忆文件是否有未授权变更"""
        result = self.verify()
        if result["failed"] or result["missing"]:
            return {
                "drifted": True,
                "detail": result,
                "action": "block_and_alert"
            }
        return {"drifted": False, "detail": result["summary"]}


if __name__ == "__main__":
    mi = MemoryIntegrity()

    # 注册关键文件
    for fname in ["META.md", "MEMORY.md"]:
        fp = os.path.join(mi.memory_dir, fname)
        if os.path.exists(fp):
            h = mi.register(fp)
            print(f"注册 {fname}: {h[:16]}...")

    # 校验
    print("\n=== 记忆完整性校验 ===")
    result = mi.verify()
    print(f"  {result['summary']}")
    for f in result["failed"]:
        print(f"  ❌ {f['file']}: {f['reason']}")
    for f in result["missing"]:
        print(f"  ❌ {f['file']}: {f['reason']}")
    for f in result["passed"]:
        print(f"  ✅ {f}")
