# Copyright 2017 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import operator

import pyparsing as pp


class Condition:

    def __init__(self, t):
        self.value = t[0]

    def __call__(self, context):
        return self.value[1](self.value[0], self.value[2], context)

    def __str__(self):
        return ' '.join(map(str, self.value))

    __repr__ = __str__


class Identifier:

    def __init__(self, t):
        self.value = t[0]

    def __call__(self, context):
        return str(context.get(self.value[1:], ''))

    def __str__(self):
        return self.value

    __repr__ = __str__


class Operator:
    operators = {
        '==': operator.eq,
        '!=': operator.ne,
        '<=': operator.le,
        '<': operator.lt,
        '>=': operator.ge,
        '>': operator.gt,
    }

    def __init__(self, t):
        self.value = t[0]

    def __call__(self, arg1, arg2, context):
        assert self.value in self.operators
        return self.operators[self.value](arg1(context), arg2(context))

    def __str__(self):
        return self.value

    __repr__ = __str__


class Value:

    def __init__(self, t):
        self.value = t[0]

    def __call__(self, context):
        return self.value

    def __str__(self):
        return self.value

    __repr__ = __str__


class BinOp:

    def __init__(self, t):
        self.args = t[0][0::2]

    def __call__(self, context):
        return self.evalop(a(context) for a in self.args)

    def __str__(self):
        sep = ' %s  ' % self.reprsymbol
        return '(' + sep.join(map(str, self.args)) + ')'

    __repr__ = __str__


class And(BinOp):
    reprsymbol = 'and'
    evalop = all


class Or(BinOp):
    reprsymbol = 'or'
    evalop = any


_condition_expression = None


def _get_condition_expression():
    global _condition_expression
    if not _condition_expression:
        operator = pp.Regex('==|!=|>=|>|<=|<').setName('operator')
        operator.setParseAction(Operator)

        identifier = pp.Word('$', pp.alphanums + '_', min=2).setName('identifier')
        identifier.setParseAction(Identifier)

        value = pp.Word(pp.alphanums + '_-').setName('value')
        value.setParseAction(Value)

        comparison_term = identifier | value

        condition = pp.Group(comparison_term + operator + comparison_term).setName('condition')
        condition.setParseAction(Condition)

        _condition_expression = pp.operatorPrecedence(
            condition, [
                ('and', 2, pp.opAssoc.LEFT, And),
                ('or', 2, pp.opAssoc.LEFT, Or),
            ])
    return _condition_expression


def evaluate_condition(condition, context):
    if condition is None:
        return True
    expr = _get_condition_expression()
    try:
        parse_results = expr.parseString(condition, parseAll=True)
    except pp.ParseException as e:
        raise ValueError(
            "condition '%s' failed to parse: %s" % (condition, e))
    return parse_results[0](context)
