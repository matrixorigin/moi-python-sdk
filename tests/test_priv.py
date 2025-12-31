"""Tests for Privilege and TableRowColExpression JSON serialization."""

import json
import pytest
from moi.models import (
    TableRowColExpression,
    AuthorityCodeAndRule,
    TableRowColRule,
    ObjPrivResponse,
)


class TestTableRowColExpression_JSON:
    """Test TableRowColExpression JSON serialization and deserialization."""

    def test_single_expression_value(self):
        """Test single expression value."""
        expr = TableRowColExpression(
            operator="=",
            expression=["100"],
            match_type="i",
        )
        json_str = '{"operator":"=","expression":["100"],"match_type":"i"}'
        
        # Test marshaling
        json_data = json.dumps(expr.__dict__)
        assert json.loads(json_data) == json.loads(json_str)
        
        # Test unmarshaling
        unmarshaled = TableRowColExpression(**json.loads(json_str))
        assert expr.operator == unmarshaled.operator
        assert expr.expression == unmarshaled.expression
        assert expr.match_type == unmarshaled.match_type

    def test_multiple_expression_values(self):
        """Test multiple expression values."""
        expr = TableRowColExpression(
            operator="in",
            expression=["IT", "HR", "Finance"],
            match_type="c",
        )
        json_str = '{"operator":"in","expression":["IT","HR","Finance"],"match_type":"c"}'
        
        # Test marshaling
        json_data = json.dumps(expr.__dict__)
        assert json.loads(json_data) == json.loads(json_str)
        
        # Test unmarshaling
        unmarshaled = TableRowColExpression(**json.loads(json_str))
        assert expr.operator == unmarshaled.operator
        assert expr.expression == unmarshaled.expression
        assert expr.match_type == unmarshaled.match_type

    def test_regexp_like_operator(self):
        """Test regexp_like operator."""
        expr = TableRowColExpression(
            operator="regexp_like",
            expression=["^test.*"],
            match_type="i",
        )
        json_str = '{"operator":"regexp_like","expression":["^test.*"],"match_type":"i"}'
        
        # Test marshaling
        json_data = json.dumps(expr.__dict__)
        assert json.loads(json_data) == json.loads(json_str)
        
        # Test unmarshaling
        unmarshaled = TableRowColExpression(**json.loads(json_str))
        assert expr.operator == unmarshaled.operator
        assert expr.expression == unmarshaled.expression
        assert expr.match_type == unmarshaled.match_type

    def test_like_operator_with_multiple_patterns(self):
        """Test like operator with multiple patterns."""
        expr = TableRowColExpression(
            operator="like",
            expression=["%test%", "%demo%"],
            match_type="i",
        )
        json_str = '{"operator":"like","expression":["%test%","%demo%"],"match_type":"i"}'
        
        # Test marshaling
        json_data = json.dumps(expr.__dict__)
        assert json.loads(json_data) == json.loads(json_str)
        
        # Test unmarshaling
        unmarshaled = TableRowColExpression(**json.loads(json_str))
        assert expr.operator == unmarshaled.operator
        assert expr.expression == unmarshaled.expression
        assert expr.match_type == unmarshaled.match_type

    def test_comparison_operators(self):
        """Test comparison operators."""
        expr = TableRowColExpression(
            operator=">=",
            expression=["100"],
            match_type="n",
        )
        json_str = '{"operator":">=","expression":["100"],"match_type":"n"}'
        
        # Test marshaling
        json_data = json.dumps(expr.__dict__)
        assert json.loads(json_data) == json.loads(json_str)
        
        # Test unmarshaling
        unmarshaled = TableRowColExpression(**json.loads(json_str))
        assert expr.operator == unmarshaled.operator
        assert expr.expression == unmarshaled.expression
        assert expr.match_type == unmarshaled.match_type

    def test_not_equal_operator(self):
        """Test not equal operator."""
        expr = TableRowColExpression(
            operator="!=",
            expression=["deleted"],
            match_type="c",
        )
        json_str = '{"operator":"!=","expression":["deleted"],"match_type":"c"}'
        
        # Test marshaling
        json_data = json.dumps(expr.__dict__)
        assert json.loads(json_data) == json.loads(json_str)
        
        # Test unmarshaling
        unmarshaled = TableRowColExpression(**json.loads(json_str))
        assert expr.operator == unmarshaled.operator
        assert expr.expression == unmarshaled.expression
        assert expr.match_type == unmarshaled.match_type

    def test_empty_expression_array(self):
        """Test empty expression array."""
        expr = TableRowColExpression(
            operator="=",
            expression=[],
            match_type="i",
        )
        json_str = '{"operator":"=","expression":[],"match_type":"i"}'
        
        # Test marshaling
        json_data = json.dumps(expr.__dict__)
        assert json.loads(json_data) == json.loads(json_str)
        
        # Test unmarshaling
        unmarshaled = TableRowColExpression(**json.loads(json_str))
        assert expr.operator == unmarshaled.operator
        assert expr.expression == unmarshaled.expression
        assert expr.match_type == unmarshaled.match_type


class TestAuthorityCodeAndRule_JSON:
    """Test AuthorityCodeAndRule JSON serialization and deserialization."""

    def test_with_rule_list_containing_expression_array(self):
        """Test with rule list containing expression array."""
        auth = AuthorityCodeAndRule(
            code="DT8",
            black_column_list=["salary", "ssn"],
            rule_list=[
                TableRowColRule(
                    column="department",
                    relation="and",
                    expression_list=[
                        TableRowColExpression(
                            operator="=",
                            expression=["IT"],
                            match_type="i",
                        ),
                    ],
                ),
            ],
        )
        json_str = '{"code":"DT8","black_column_list":["salary","ssn"],"rule_list":[{"column":"department","relation":"and","expression_list":[{"operator":"=","expression":["IT"],"match_type":"i"}]}]}'
        
        # Test marshaling
        json_data = json.dumps(auth.__dict__, default=lambda o: o.__dict__)
        assert json.loads(json_data) == json.loads(json_str)
        
        # Test unmarshaling (simplified - would need custom deserializer for full support)
        data = json.loads(json_str)
        unmarshaled = AuthorityCodeAndRule(
            code=data["code"],
            black_column_list=data["black_column_list"],
            rule_list=[
                TableRowColRule(
                    column=rule["column"],
                    relation=rule["relation"],
                    expression_list=[
                        TableRowColExpression(**expr)
                        for expr in rule["expression_list"]
                    ],
                )
                for rule in data["rule_list"]
            ],
        )
        assert auth.code == unmarshaled.code
        assert auth.black_column_list == unmarshaled.black_column_list
        assert len(auth.rule_list) == len(unmarshaled.rule_list)
        assert auth.rule_list[0].column == unmarshaled.rule_list[0].column
        assert len(auth.rule_list[0].expression_list) == len(unmarshaled.rule_list[0].expression_list)
        assert auth.rule_list[0].expression_list[0].expression == unmarshaled.rule_list[0].expression_list[0].expression

    def test_with_multiple_expressions_in_rule(self):
        """Test with multiple expressions in rule."""
        auth = AuthorityCodeAndRule(
            code="DT9",
            black_column_list=None,
            rule_list=[
                TableRowColRule(
                    column="id",
                    relation="and",
                    expression_list=[
                        TableRowColExpression(
                            operator="in",
                            expression=["1", "2", "3"],
                            match_type="n",
                        ),
                        TableRowColExpression(
                            operator=">",
                            expression=["0"],
                            match_type="n",
                        ),
                    ],
                ),
            ],
        )
        json_str = '{"code":"DT9","black_column_list":null,"rule_list":[{"column":"id","relation":"and","expression_list":[{"operator":"in","expression":["1","2","3"],"match_type":"n"},{"operator":">","expression":["0"],"match_type":"n"}]}]}'
        
        # Test marshaling
        json_data = json.dumps(auth.__dict__, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else None)
        assert json.loads(json_data) == json.loads(json_str)

    def test_without_rule_list(self):
        """Test without rule list."""
        auth = AuthorityCodeAndRule(
            code="DT10",
            black_column_list=[],
            rule_list=None,
        )
        json_str = '{"code":"DT10","black_column_list":[],"rule_list":null}'
        
        # Test marshaling
        json_data = json.dumps(auth.__dict__, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else None)
        assert json.loads(json_data) == json.loads(json_str)


class TestObjPrivResponse_JSON:
    """Test ObjPrivResponse JSON serialization and deserialization."""

    def test_complete_object_privilege_response(self):
        """Test complete object privilege response."""
        obj_priv = ObjPrivResponse(
            obj_id="123",
            obj_type="table",
            obj_name="employees",
            authority_code_list=[
                AuthorityCodeAndRule(
                    code="DT8",
                    black_column_list=["salary"],
                    rule_list=[
                        TableRowColRule(
                            column="department",
                            relation="and",
                            expression_list=[
                                TableRowColExpression(
                                    operator="=",
                                    expression=["IT"],
                                    match_type="i",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        json_str = '{"obj_id":"123","obj_type":"table","obj_name":"employees","authority_code_list":[{"code":"DT8","black_column_list":["salary"],"rule_list":[{"column":"department","relation":"and","expression_list":[{"operator":"=","expression":["IT"],"match_type":"i"}]}]}]}'
        
        # Test marshaling
        json_data = json.dumps(obj_priv.__dict__, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else None)
        assert json.loads(json_data) == json.loads(json_str)

    def test_with_multiple_authority_codes_and_expressions(self):
        """Test with multiple authority codes and expressions."""
        obj_priv = ObjPrivResponse(
            obj_id="456",
            obj_type="table",
            obj_name="orders",
            authority_code_list=[
                AuthorityCodeAndRule(
                    code="DT8",
                    black_column_list=None,
                    rule_list=[
                        TableRowColRule(
                            column="status",
                            relation="and",
                            expression_list=[
                                TableRowColExpression(
                                    operator="in",
                                    expression=["pending", "processing"],
                                    match_type="c",
                                ),
                            ],
                        ),
                    ],
                ),
                AuthorityCodeAndRule(
                    code="DT9",
                    black_column_list=["price"],
                    rule_list=[
                        TableRowColRule(
                            column="user_id",
                            relation="and",
                            expression_list=[
                                TableRowColExpression(
                                    operator="regexp_like",
                                    expression=["^user_\\d+$"],
                                    match_type="i",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        json_str = '{"obj_id":"456","obj_type":"table","obj_name":"orders","authority_code_list":[{"code":"DT8","black_column_list":null,"rule_list":[{"column":"status","relation":"and","expression_list":[{"operator":"in","expression":["pending","processing"],"match_type":"c"}]}]},{"code":"DT9","black_column_list":["price"],"rule_list":[{"column":"user_id","relation":"and","expression_list":[{"operator":"regexp_like","expression":["^user_\\\\d+$"],"match_type":"i"}]}]}]}'
        
        # Test marshaling
        json_data = json.dumps(obj_priv.__dict__, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else None)
        assert json.loads(json_data) == json.loads(json_str)


class TestTableRowColExpression_ExpressionArray:
    """Test Expression field as array in various scenarios."""

    def test_single_value(self):
        """Test single value."""
        expr = TableRowColExpression(
            operator="=",
            expression=["100"],
            match_type="i",
        )
        json_data = json.dumps(expr.__dict__)
        json_map = json.loads(json_data)
        assert isinstance(json_map["expression"], list)
        assert json_map["expression"] == ["100"]

    def test_multiple_values(self):
        """Test multiple values."""
        expr = TableRowColExpression(
            operator="in",
            expression=["IT", "HR", "Finance"],
            match_type="c",
        )
        json_data = json.dumps(expr.__dict__)
        json_map = json.loads(json_data)
        assert isinstance(json_map["expression"], list)
        assert json_map["expression"] == ["IT", "HR", "Finance"]

    def test_empty_array(self):
        """Test empty array."""
        expr = TableRowColExpression(
            operator="=",
            expression=[],
            match_type="i",
        )
        json_data = json.dumps(expr.__dict__)
        json_map = json.loads(json_data)
        assert isinstance(json_map["expression"], list)
        assert json_map["expression"] == []

    def test_numeric_values(self):
        """Test numeric values."""
        expr = TableRowColExpression(
            operator="in",
            expression=["1", "2", "3", "4", "5"],
            match_type="n",
        )
        json_data = json.dumps(expr.__dict__)
        json_map = json.loads(json_data)
        assert isinstance(json_map["expression"], list)
        assert json_map["expression"] == ["1", "2", "3", "4", "5"]

    def test_regex_patterns(self):
        """Test regex patterns."""
        expr = TableRowColExpression(
            operator="regexp_like",
            expression=["^test.*", ".*demo$", "pattern\\d+"],
            match_type="i",
        )
        json_data = json.dumps(expr.__dict__)
        json_map = json.loads(json_data)
        assert isinstance(json_map["expression"], list)
        assert len(json_map["expression"]) == 3
        assert "^test.*" in json_map["expression"]

