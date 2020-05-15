import unittest
from swampymud.util.validate import validate, META_SCHEMA, check_schema, format_error

class TestValidate(unittest.TestCase):
    """test case for the validator function"""

    def test_empty_schema(self):
        """empty schema should validate anything"""
        schema = {}
        data = {"foo": "bar", 42: "meaning of life"}
        self.assertEqual(validate(data, schema), None)

    def test_str_schema(self):
        """simple schema for an item with type"""
        schema = {"type": str}
        data1 = "foo"
        err1 = ["foo"]
        err2 = {"foo": "bar"}
        self.assertEqual(validate(data1, schema), None)
        self.assertEqual(validate(err1, schema),
                         "Invalid type <class 'list'>, expected <class 'str'>")
        self.assertEqual(validate(err2, schema),
                         "Invalid type <class 'dict'>, expected <class 'str'>")

    def test_schema_with_check(self):
        """test a schema with a check function"""
        def checker(data):
            if data > 42:
                return "Data should not be greater than 42"
        schema = {"type": int, "check": checker}
        data1 = 12
        err1 = 32.434
        err2 = "meme"
        err3 = 434234
        self.assertEqual(validate(data1, schema), None)
        self.assertEqual(validate(err1, schema),
                         "Invalid type <class 'float'>, expected <class 'int'>")
        self.assertEqual(validate(err2, schema),
                         "'>' not supported between instances of 'str' and 'int'")
        self.assertEqual(validate(err3, schema),
                         "Data should not be greater than 42")

    def test_list_schema(self):
        """a list schema should apply its subschema to all of its items"""
        def checker(data):
            if data > 42:
                raise Exception("Data should not be greater than 42")
        inner_schema = {"type": int, "check": checker}
        schema = {
            "items": inner_schema
        }
        all_good = list(range(10, 20))
        one_bad = [0, 50, 25]
        two_bad = [0.0, 10, "meme"]
        self.assertEqual(validate(all_good, schema), None)
        self.assertEqual(validate(one_bad, schema), {1: "Data should not be greater than 42"})
        self.assertEqual(validate(two_bad, schema), {
            0: "Invalid type <class 'float'>, expected <class 'int'>",
            2: "'>' not supported between instances of 'str' and 'int'"
        })

    def test_dict_schema(self):
        """a dict schema should apply itself to underlying values as necessary"""
        def checker(amt):
            if amt < 100:
                raise Exception("Must be greater than 100")
        schema = {
            "properties": {
                "name": {
                    "type": str,
                    "required": False
                },
                "weight": {
                    "check": checker
                }
            }
        }
        all_good = {"name": "jim", "weight": 120}
        self.assertEqual(validate(all_good, schema), None)

        no_name_but_good = {"weight": 3203}
        self.assertEqual(validate(no_name_but_good, schema), None)

        bad_name = {"name": 1000, "weight": 120}
        self.assertEqual(validate(bad_name, schema), {
            "name": "Invalid type <class 'int'>, expected <class 'str'>"
        })

        missing_weight = {"name": "jim"}
        self.assertEqual(validate(missing_weight, schema), {
            "weight": "Missing required field"
        })

        bad_weight = {"weight": 90}
        self.assertEqual(validate(bad_weight, schema), {
            "weight": "Must be greater than 100"
        })

        bad_weight_type = {"weight": "meme"}
        self.assertEqual(validate(bad_weight_type, schema), {
            "weight": "'<' not supported between instances of 'str' and 'int'"
        })

        unused_field = {"weight": 3213, "whoops": 37}
        self.assertEqual(validate(unused_field, schema), {
            "whoops": "Unused field"
        })

        everything_wrong = {"weight": 90, "name": ["hi"], "extra": "whoops"}
        self.assertEqual(validate(everything_wrong, schema), {
            "extra": "Unused field",
            "weight": "Must be greater than 100",
            "name": "Invalid type <class 'list'>, expected <class 'str'>"
        })

    def test_recursive(self):
        """test if schemas can apply themselves recursively"""
        father = {
            "required": False,
            "properties": {
                "name": {
                    "type": str
                }
            }
        }
        son_schema = {"required": False, "type": list, "items": father}
        father["properties"]["sons"] = son_schema
        no_kids = {"name": "Bill"}
        one_kid = {"name": "Bill", "sons": [{"name": "Jeff"}]}
        two_kid = {"name": "Bill", "sons": [{"name": "Jeff"}, {"name": "Jim"}]}
        self.assertEqual(validate(no_kids, father), None)
        self.assertEqual(validate(one_kid, father), None)
        self.assertEqual(validate(two_kid, father), None)
        nameless_kid = {"name": "Bill", "sons": [{}]}
        self.assertEqual(validate(nameless_kid, father), {
            "sons": {0: {"name": "Missing required field"}}
        })
        bad_types = {"name": 32, "sons": "Bill"}
        self.assertEqual(validate(bad_types, father), {
            "name": "Invalid type <class 'int'>, expected <class 'str'>",
            "sons": "Invalid type <class 'str'>, expected <class 'list'>"
        })
        grandsons = {
            "name": "Grandpa",
            "sons": [
                {
                    "name": "Junior",
                    "sons": [
                        {
                            "name": "Little Billy"
                        },
                        {
                            "name": "Andrew"
                        }
                    ]
                },
                {
                    "name": "Uncle William",
                    "sons": [
                        "Matt"
                    ]
                }
            ]
        }
        self.assertEqual(validate(grandsons, father), None)
        bad_grandpa = {
            "name": "Grandpa",
            "sons": [
                {
                    "name": "Junior",
                    "sons": [
                        {
                            "name": 2
                        },
                        {
                            "name": "Little One",
                            "last name": "Juniorivich"
                        }
                    ]
                },
                {
                }
            ]
        }
        error = validate(bad_grandpa, father)
        self.assertEqual(error, {
            "sons": {
                0: {
                    "sons": {
                        0: {
                            "name": "Invalid type <class 'int'>, expected <class 'str'>"
                        },
                        1: {
                            "last name": "Unused field"
                        }
                    }
                },
                1: {
                    "name": "Missing required field"
                }
            }
        })
        formatted = '''At key 'sons':
  At index '0':
    At key 'sons':
      At index '0':
        At key 'name':
          With '2': Invalid type <class 'int'>, expected <class 'str'>
      At index '1':
        At key 'last name':
          With 'Juniorivich': Unused field
  At index '1':
    At key 'name':
      Missing required field'''
        self.assertEqual(format_error(bad_grandpa, error), formatted)
    def test_matcher(self):
        """schemas should match using the 'match' and 'choices' fields"""
        def check_int(value):
            if int(value) != 3:
                raise Exception("Value should be 3")
        int_like = {"check": check_int}
        list_of_int = {"items": int_like}
        schema = {
            "match": type,
            "choices": {
                int: int_like,
                float: int_like,
                str: int_like,
                list: list_of_int,
            }
        }
        # check for a simple integer
        self.assertEqual(validate(3, schema), None)
        # check for a float
        self.assertEqual(validate(3.0, schema), None)
        # check for a string
        self.assertEqual(validate("3", schema), None)
        # check for a list
        self.assertEqual(validate([], schema), None)
        self.assertEqual(validate(["3", 3.0, 3, 3], schema), None)
        # bad integer
        self.assertEqual(validate(4, schema), "Value should be 3")
        # bad float
        self.assertEqual(validate(4.2, schema), "Value should be 3")
        # bad string
        self.assertEqual(validate("5", schema), "Value should be 3")
        # cannot parse string
        self.assertEqual(validate("ab", schema), "invalid literal for int() with base 10: 'ab'")
        # cannot handle a dict value
        self.assertEqual(validate({3: "3"}, schema),
            "Has value '<class 'dict'>', expected one of [<class 'int'>, <class 'float'>, <class 'str'>, <class 'list'>]"
        )
        self.assertEqual(validate(["ab", 3, 3, 4, "3"], schema), {
            0: "invalid literal for int() with base 10: 'ab'",
            3: "Value should be 3"
        })

    def test_recursive_matcher(self):
        """test that matcher can work recursively"""
        def check_int(value):
            if int(value) != 3:
                raise Exception("Value should be 3")
        int_like = {"check": check_int}
        schema = {
            "match": type,
            "choices": {
                int: int_like,
                float: int_like,
                str: int_like
            }
        }
        # allow schema to recursively accept lists of itself
        schema["choices"][list] = { "items": schema }
        self.assertEqual(validate([], schema), None)
        self.assertEqual(validate(3, schema), None)
        self.assertEqual(validate([3, "3", 3.0], schema), None)
        self.assertEqual(validate([3, "3", 3.0, [3, 3, [3, 3]]], schema), None)
        self.assertEqual(validate([3, "3", 3.0, [3, 7]], schema), {
            3: {1: "Value should be 3"}
        })

    def test_check_schema(self):
        """testing the 'check schema' function"""
        # test no schema provided
        self.assertEqual(check_schema(3), "argument of type 'int' is not iterable")
        # empty schema is valid
        self.assertEqual(check_schema({}), None)
        # schema was type is valid
        self.assertEqual(check_schema({"type": str}), None)
        # schema with bad type is invalid
        self.assertEqual(check_schema({"type": 3}), {'type': 'Field must be valid type'})
        # schema with properties is valid
        self.assertEqual(check_schema({"properties": {}}), None)
        self.assertEqual(check_schema({"properties": {"foo": {"type": str}}}), None)
        self.assertEqual(check_schema({"properties": {"foo": {"type": 3}}}), {
            "properties": {"foo": {"type": 'Field must be valid type'}}
        })
        self.assertEqual(check_schema({"properties": {}, "choices": {}}), "Cannot have fields 'properties' and 'choices' in same schema")
        self.assertEqual(check_schema({"match": {}, "items": {}}), "Cannot have fields 'items' and 'match' in same schema")
        self.assertEqual(check_schema({"items": {"type": str}}), None)
        self.assertEqual(check_schema({"items": {"type": 3}}), {"items": {"type": "Field must be valid type"}})
        self.assertEqual(check_schema({"match": int, "choices": {2: {"type": int}, 3: {"type": int}}}), None)
        self.assertEqual(check_schema({"match": int, "choices": {2: {"type": int}, 3: {"type": 3}}}), {
            "choices": { 3: {"type": "Field must be valid type"}}
        })
        self.assertEqual(check_schema({"properties": {"name": {"required": 3}}}), {
            "properties": {"name" : {"required": "Invalid type <class 'int'>, expected <class 'bool'>"}}
        })
