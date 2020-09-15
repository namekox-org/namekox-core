#! -*- coding: utf-8 -*-

# author: forcemain@163.com


import inspect


from functools import partial
from types import FunctionType


from .extension import Extension


class Entrypoint(Extension):
    method_name = None

    def __init__(self, *args, **kwargs):
        pass

    def bind(self, container, name):
        ins = super(Entrypoint, self).bind(container, name)
        ins.method_name = ins.obj_name
        return ins

    def bind_sub_providers(self, obj, container):
        providers = inspect.getmembers(self, is_entrypoint_provider)
        for name, provider in providers:
            setattr(obj, name, provider.bind(container, name))
        return obj

    @classmethod
    def decorator(cls, *args, **kwargs):
        def register_entrypoint(cls_args, cls_kwargs, func):
            entrypoint = cls(*cls_args, **cls_kwargs)
            entrypoints = getattr(func, 'entrypoints', set())
            entrypoints.add(entrypoint)
            setattr(func, 'entrypoints', entrypoints)
            return func
        if len(args) == 1 and isinstance(args[0], FunctionType):
            return register_entrypoint((), {}, args[0])
        return partial(register_entrypoint, args, kwargs)


class EntrypointProvider(Extension):
    def bind_sub_providers(self, obj, container):
        providers = inspect.getmembers(self, is_entrypoint_provider)
        for name, provider in providers:
            setattr(obj, name, provider.bind(container, name))
        return obj


def is_entrypoint(obj):
    return isinstance(obj, Entrypoint)


def is_entrypoint_provider(obj):
    return isinstance(obj, EntrypointProvider)


def ls_entrypoint_provider(obj):
    for name, provider in inspect.getmembers(obj, is_entrypoint_provider):
        for name, sub_provider in ls_entrypoint_provider(provider):
            yield sub_provider.bind(obj.container, name)
        yield provider.bind(obj.container, name)
