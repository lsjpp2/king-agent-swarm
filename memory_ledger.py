#!/usr/bin/env python3
"""
KAF Memory Ledger — 结构化记忆后端（可选 SQLite ledger）
参考 cursor/minisqlite 的极小 API 理念：
- 极小 API：open/execute/query
- COW 式事务（sqlite3 默认）：落盘前可回滚
- WAL 模式：并发读不阻塞写，快照 pinning
- 双向兼容 SQLite 文件格式：可被标准 sqlite3 / minisqlite 工具查询

用 Python 标准库 sqlite3 实现，零外部依赖。

v5.2 进化（方向4·共享持久化）：
- 默认 db 落在共享层 ${KAF_SHARED_DIR}/.memory_ledger.db，所有 agent 可读写同一本账。
- 与 memory_integrity.py 职责去重（不重复）：
    * memory_integrity.py = 每 agent 的「文件指纹」（文件长什么样，防覆盖丢失）
    * memory_ledger.py    = 共享的「操作审计」（谁/何时/改了什么，可追溯）
  两者互补：指纹回答"文件是否被篡改"，账本回答"这次变更是否可追溯"。

表：
  operation_log(id, agent, action, target, before_hash, after_hash, ts)
  fingerprints(rel_path PK, sha256, size, registered_at)
  drift(id, rel_path, expected, actual, detected_at)

Usage:
    from memory_ledger import MemoryLedger
    led = MemoryLedger()                       # 默认共享账本
    led = MemoryLedger(db_path="local.db")     # 指定本地账本
    led.record_operation("workbuddy", "write", "MEMORY.md", before, after)
    led.register_fingerprint("MEMORY.md", sha256, size)
    led.verify()                 # 双路校验（SQLite 表 + 实际文件）
    led.drift_check()
    led.query("SELECT * FROM operation_log")
"""
import os
import hashlib
import sqlite3
from datetime import datetime


class MemoryLedger:
    """结构化记忆 ledger：可追溯的共享操作日志 + 指纹 + 漂移记录"""

    # v5.2 方向4：共享账本根（所有 agent 可读写同一本账）
    SHARED_ROOT = os.environ.get("KAF_SHARED_DIR") or os.path.join(os.path.expanduser("~"), "kaf-shared")
    SHARED_LEDGER = os.path.join(SHARED_ROOT, ".memory_ledger.db")

    def __init__(self, db_path=None, memory_dir=None):
        self.memory_dir = memory_dir or self._find_memory_dir()
        # 默认优先用共享账本；否则退化为本地隐藏账本
        if db_path is None and os.path.exists(self.SHARED_ROOT):
            self.db_path = self.SHARED_LEDGER
        else:
            self.db_path = db_path or os.path.join(self.memory_dir, ".memory_ledger.db")
        self._init_db()

    def _find_memory_dir(self):
        candidates = [
            self.SHARED_ROOT,
            os.path.expanduser("~/.workbuddy"),
            os.path.join(os.getcwd(), ".workbuddy", "memory"),
            os.path.join(os.path.expanduser("~"), "workbuddy-workspace", ".workbuddy", "memory"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return candidates[-1]

    def _init_db(self):
        """建表 + 启用 WAL（并发读不阻塞写）"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS operation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT,
                    action TEXT,
                    target TEXT,
                    before_hash TEXT,
                    after_hash TEXT,
                    ts TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS fingerprints (
                    rel_path TEXT PRIMARY KEY,
                    sha256 TEXT,
                    size INTEGER,
                    registered_at TEXT
                );
                CREATE TABLE IF NOT EXISTS drift (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rel_path TEXT,
                    expected TEXT,
                    actual TEXT,
                    detected_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
        finally:
            conn.close()

    # ---- 极小 API（参考 minisqlite: open / execute / query）----
    def execute(self, sql):
        """运行任意 SQL（建表/迁移/批处理），COW 事务包裹"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(sql)
            conn.commit()
        finally:
            conn.close()

    def query(self, sql):
        """查询，返回 {columns, rows}（只读，不修改）"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            cur = conn.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()
            return {"columns": cols, "rows": rows}
        finally:
            conn.close()

    # ---- 记忆完整性能力（向后兼容 memory_integrity.py）----
    def _sha256(self, filepath):
        if not os.path.exists(filepath):
            return None
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def record_operation(self, agent, action, target, before_hash=None, after_hash=None):
        """记录一次记忆操作（可追溯：谁/做了什么/前后指纹）"""
        if before_hash is None and os.path.exists(target):
            before_hash = self._sha256(target)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "INSERT INTO operation_log(agent,action,target,before_hash,after_hash) VALUES(?,?,?,?,?)",
                (agent, action, target, before_hash, after_hash))
            conn.commit()
        finally:
            conn.close()

    def register_fingerprint(self, rel_path, sha256, size):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "INSERT OR REPLACE INTO fingerprints(rel_path,sha256,size,registered_at) VALUES(?,?,?,?)",
                (rel_path, sha256, size, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()

    def verify(self):
        """双路校验：当前文件哈希 vs fingerprints 表"""
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute("SELECT rel_path, sha256 FROM fingerprints")
            rows = cur.fetchall()
        finally:
            conn.close()
        passed, failed, missing = [], [], []
        for rel, expected in rows:
            fp = os.path.join(self.memory_dir, rel)
            if not os.path.exists(fp):
                missing.append(rel)
                continue
            actual = self._sha256(fp)
            if actual == expected:
                passed.append(rel)
            else:
                failed.append({"file": rel, "expected": expected[:16], "actual": actual[:16]})
        return {
            "passed": passed,
            "failed": failed,
            "missing": missing,
            "summary": f"{len(passed)}通过/{len(failed)}失败/{len(missing)}缺失",
        }

    def drift_check(self):
        """Drift 检测：未授权变更 -> 记录到 drift 表并告警"""
        res = self.verify()
        if res["failed"] or res["missing"]:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                for f in res["failed"]:
                    conn.execute("INSERT INTO drift(rel_path,expected,actual) VALUES(?,?,?)",
                                 (f["file"], f.get("expected", "?"), f.get("actual", "?")))
                for m in res["missing"]:
                    conn.execute("INSERT INTO drift(rel_path,expected,actual) VALUES(?,?,?)",
                                 (m, "exists", "missing"))
                conn.commit()
            finally:
                conn.close()
            return {"drifted": True, "detail": res, "action": "block_and_alert"}
        return {"drifted": False, "summary": res["summary"]}


if __name__ == "__main__":
    led = MemoryLedger()
    print(f"MemoryLedger 就绪: {led.db_path}")
    print(f"  WAL 模式: 并发读不阻塞写")
    print(f"  表: operation_log / fingerprints / drift")
