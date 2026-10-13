#!/usr/bin/env python3
"""gzhkit.gates: @register 门禁插件注册表（D2）。

新增门禁只需新建一个模块并用 @register 装饰 check 函数，
不再改编排器。插件接口：

    GATE_ID = 'g0'            # 注册名（小写，如 g0/h14）
    GATE_TITLE = '选题门禁'    # 显示名

    def add_arguments(parser):  # 可选：注册本门禁特有 CLI 参数
        ...

    def check(args, ctx) -> GateOutcome:  # 必需：执行检查
        ...

ctx（dict）由编排器按需填充：text / body / zh / path / verbose /
policy_mode / no_humanizer / level（分级放行）等。
"""
from ..report import GateOutcome  # noqa: F401  (插件 from gzhkit.gates import ...)

REGISTRY = {}


def register(gate_id, title):
    """插件注册装饰器。"""
    def deco(fn):
        fn.GATE_ID = gate_id
        fn.GATE_TITLE = title
        if gate_id in REGISTRY:
            raise ValueError('门禁 %r 重复注册' % gate_id)
        REGISTRY[gate_id] = fn
        return fn
    return deco


def get_gate(gate_id):
    return REGISTRY[gate_id]


def list_gates():
    return sorted(REGISTRY.items())
