#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAF v5.3 — 国王身份动态解析 (Deployer = King)

解决旧版"国王硬编码为山禾"的狭隘性：

  本地作者环境(山禾)  -> 默认回退 "山禾"（本机主权人就是山禾）
  远程新手复制技能    -> 默认回退 "当前 OS 用户" 或 "operator"（使用者即国王）

解析优先级（任一命中即返回，不再下探）：
  1. 环境变量 KAF_KING            —— 显式最高优先，部署者一句话覆盖
  2. 配置文件 kaf_config.json     —— 字段 king
  3. 本地作者环境检测             —— USERPROFILE/HOME 含"山禾" 或 USERNAME==山禾 → "山禾"
  4. 远程/新用户                  —— 当前 OS 用户(USERNAME/USER)；为空 → "operator"

设计原则：国王不是某个写死的名字，而是"当前部署者/使用者"。
作者把自己的环境标记为 king，但绝不垄断"国王"这个语义。
"""
import os
import json


def _load_config_king():
    """从 kaf_config.json 读取 king（candidate: cwd / kaf 包目录）。"""
    candidates = [
        os.path.join(os.getcwd(), "kaf_config.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "kaf_config.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                king = (cfg.get("king") or "").strip()
                if king:
                    return king
            except Exception:
                pass
    return None


def _is_author_env():
    """检测是否作者(山禾)的本地环境。"""
    up = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
    un = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    return ("山禾" in up) or (un == "山禾")


def resolve_king():
    """返回当前部署者/使用者身份（国王）。"""
    # 1) 环境变量最高优先
    env = (os.environ.get("KAF_KING") or "").strip()
    if env:
        return env
    # 2) 配置文件
    cfg = _load_config_king()
    if cfg:
        return cfg
    # 3) 本地作者环境 -> 山禾
    if _is_author_env():
        return "山禾"
    # 4) 远程/新用户 -> 当前 OS 用户，兜底 operator
    return os.environ.get("USERNAME") or os.environ.get("USER") or "operator"


def describe_resolution():
    """返回 (king, source) 便于诊断/日志。"""
    if (os.environ.get("KAF_KING") or "").strip():
        return resolve_king(), "env:KAF_KING"
    if _load_config_king():
        return resolve_king(), "config:kaf_config.json"
    if _is_author_env():
        return "山禾", "author_env(本地作者)"
    un = os.environ.get("USERNAME") or os.environ.get("USER")
    if un:
        return un, "os_user"
    return "operator", "fallback:operator"


if __name__ == "__main__":
    king, src = describe_resolution()
    print("=== KAF v5.3 King Resolution ===")
    print(f"  当前国王(King): {king}")
    print(f"  解析来源(source): {src}")
    print("  优先级: env:KAF_KING > kaf_config.json > 本地作者(山禾) > 当前OS用户/operator")
