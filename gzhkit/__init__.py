#!/usr/bin/env python3
"""gzhkit: gzh-team v4.0.0 共享核心库。

v4.0.0 重建：消除 v3.x 补丁摞补丁的重复逻辑与死代码。
所有门禁逻辑收敛到 gzhkit.gates 插件注册表，阈值收敛到 gzhkit.config，
41 个脚本瘦身为 CLI 垫片（文件名/参数/退出码与 v3.3.0 兼容）。
"""
__version__ = "4.0.0"
