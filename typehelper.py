import ast
import json


def typecast(typestr: str, value: str):
    if typestr not in ["int", "float", "complex", "str", "list", "tuple", "range", "bytes", "dict", "bool", "set",
                       "frozenset"]:
        raise TypeError
    match typestr:
        case "int":
            return int(value)
        case "float":
            return float(value)
        case "complex":
            return complex(value)  # TODO: test if this already does the trick
        case "str":
            return str(value)
        case "list":
            # return value.split(",")  # find better split parameter
            return ast.literal_eval(value)  # TODO:literal_eval not safe??
        case "tuple":
            return json.loads(value)  # TODO:  test if this already does the trick
        case "bytes":
            return bytes(value)  # TODO:  test if this already does the trick
        case "dict":
            return json.loads(value)
        case "bool":
            return value == "True"
        case "set":
            return set(value)
        case "frozenset":
            return frozenset(set(value))  # TODO:  test if this already does the trick
