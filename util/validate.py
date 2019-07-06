'''module for validating pythonic data structures'''

def validate(data, schema):
    if "match" in schema:
        value = schema["match"](data)
        if not value in schema["choices"]:
            return "Has value '%s', expected one of %s" % (value, list(schema["choices"]))
        else:
            return validate(data, schema["choices"][value])
    if "check" in schema:
        try:
            result = schema["check"](data)
            if result:
                return result
        except Exception as ex:
            return str(ex)
    if "type" in schema:
        if schema["type"] is not type(data):
            return "Invalid type %s, expected %s" % (type(data), schema["type"])
    if isinstance(data, list) and "items" in schema:
        msgs = [validate(item, schema["items"]) for item in data]
        with_index = {
            index: msg for (index, msg) in enumerate(msgs) if msg is not None
        }
        if with_index:
            return with_index
    if isinstance(data, dict) and "properties" in schema:
        errors = {}
        for key in data:
            if key not in schema["properties"]:
                errors[key] = "Unused field"
        for key, subschema in schema["properties"].items():
            # if "required" is not provided by schema, assume field is required
            if (("required" not in subschema or subschema["required"])
                 and key not in data):
                 errors[key] = "Missing required field"
            if key in data:
                result = validate(data[key], subschema)
                if result:
                    errors[key] = result
        if errors:
            return errors


def _build_msg(data, error, indent, depth=0):
    '''create a well-formatted output statement
    this function assumes that error = validate(data, some_schema)
    returns a flat list of strings'''
    output = []
    if isinstance(data, list):
        for index, item in enumerate(data):
            if index in error:
                output.append("%sAt index '%s':" % (indent * depth, index))
                output.extend(_build_msg(item, error[index], indent, depth+1))
    elif isinstance(data, dict):
        for key in error:
            output.append("%sAt key '%s':" % (indent * depth, key))
            if key in data:
                output.extend(_build_msg(data[key], error[key], indent, depth+1))
            # error is a missing key error
            else:
                output.append("%s%s" % (indent * (depth+1), error[key]))
    else:
        output = ["%sWith '%s': %s" % (indent * depth, data, error)]
    return output


def format_error(data, errors, indent="  "):
    '''formats errors to match the structure of 'data'
    this function assumes that error = validate(data, some_schema)'''
    return "\n".join(_build_msg(data, errors, indent))


def check_schema(schema):
    '''validate a schema using the META_SCHEMA'''
    return validate(schema, META_SCHEMA)


def _check_callable(value):
    if not callable(value):
        raise Exception('Field must be callable')


def _check_type(value):
    if not isinstance(value, type):
        raise Exception('Field must be valid type')


def _check_conflicts(schema):
    incompatible = ["properties", "items", "match", "choices"]
    for item in incompatible:
        for conflict in incompatible:
            if item == conflict:
                continue
            # ignore "match" and "choices", as they can go together
            if set((item, conflict)) == set(("match", "choices")):
                continue
            if item in schema and conflict in schema:
                raise Exception("Cannot have fields '%s' and '%s' in same schema"
                                % (item, conflict))
    if "match" in schema:
        if "choices" not in schema:
            raise Exception("Field 'match' requires field 'choices'")
    else:
        if "choices" in schema:
            raise Exception("Field 'choices' requires field 'match'")


def _check_values(dic):
    errors = {}
    for (key, value) in dic.items():
        result = check_schema(value)
        if result:
            errors[key] = result
    if errors:
        return errors


META_SCHEMA = {
    "check": _check_conflicts,
    "required": False,
    "type": dict,
    "properties": {
        "match": {
            "required": False,
            "check": _check_callable
        },
        "choices": {
            "required": False,
            "type": dict,
            "check": _check_values
        },
        "check": {
            "required": False,
            "check": _check_callable
        },
        "type": {
            "required": False,
            "check": _check_type
        },
        "items": {
            # META_SCHEMA will be recursively inserted here
        },
        "properties": {
            "required": False,
            "type": dict,
            "check": _check_values
        },
        "required": {
            "required": False,
            "type": bool
        }
    },
}
# make the META_SCHEMA recursive
META_SCHEMA["properties"]["items"] = META_SCHEMA
