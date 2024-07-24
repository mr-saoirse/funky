from inspect import getmembers, isfunction, isclass, ismethod, ismodule
import types
import typing
from pydantic import BaseModel, Field
from enum import Enum


class TypeInfo(BaseModel):
    name: str = Field(description="parameter name")
    type: typing.Type = Field(
        description="the python type resolve from precedence of required"
    )
    args: tuple | typing.Type = Field(description="All type options in union types")
    input: typing.Any = Field(
        description="The full annotation input that we are mapping"
    )
    is_required: bool = Field(description="required or not")
    is_list: bool = Field(description="is a collection/list type or not")
    enum_options: typing.Optional[typing.List[str]] = Field(
        description="enums can provide option hints", default_factory=list
    )

    def to_json_schema(cls) -> dict:
        return {}


def get_class_and_instance_methods(cls):
    """inspect the methods on the type for methods"""
    methods = []
    class_methods = []

    for name, member in getmembers(cls):
        if isfunction(member) or ismethod(member):
            # Check if the method belongs to the class and not inherited
            if member.__qualname__.startswith(cls.__name__):
                if isinstance(member, types.FunctionType):
                    methods.append(getattr(cls, name))
                elif isinstance(member, types.MethodType):
                    class_methods.append(getattr(cls, name))

    return methods + class_methods


def resolve_signature_types(fn: typing.Callable, **kwargs):
    """given a function, resolve all signature annotations in out opinionated way"""
    return [resolve_named_type(k, v) for k, v in typing.get_type_hints(fn).items()]


def resolve_named_type(name: str, t: type, **kwargs):
    """a simple opinionated type mapping - we may pass some precedence for different modes
    the tuple that comes from `typing.get_type_hints` is passed in
    """

    def apply_precedence(t):
        """a primitive reduction - just reduce the inner most left type for now
        Example
            #this is a non required list of type string
            typing.Optional[typing.List[str | dict]]

        ultimately json stuff is sent over the wire so for now we want our functions
        to be well behaved and parse the inputs via coercian
        """
        if isinstance(t, tuple):
            t = t[0]
        args = typing.get_args(t)
        if len(args) > 0:
            t = args[0]
            return apply_precedence(t)
        return t

    args = typing.get_args(t)
    required = types.NoneType not in typing.get_args(t)
    contains_list = False
    for item in args:
        if typing.get_origin(item) in {list, typing.List}:
            contains_list = True

    """generate the summary object"""
    args = args or t
    T = apply_precedence(args)

    """handle enum types and options"""
    enum_options = []
    if isclass(T) and issubclass(T, Enum):
        enum_options = [member.value for member in T]
        if len(enum_options):
            T = type(enum_options[0])

    return TypeInfo(
        name=name,
        type=T,
        args=args,
        is_required=required,
        is_list=contains_list,
        input=t,
        enum_options=enum_options,
    )
