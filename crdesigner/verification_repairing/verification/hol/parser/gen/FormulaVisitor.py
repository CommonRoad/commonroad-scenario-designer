# Generated from Formula.g4 by ANTLR 4.9.3
from antlr4 import *

from ...expression_tree.atomic.bool import Bool
from ...expression_tree.atomic.predicate import Predicate
from ...expression_tree.binary.bool.equivalence import Equivalence
from ...expression_tree.binary.bool.implication import Implication
from ...expression_tree.domain.dynamic import DynamicDomain
from ...expression_tree.domain.fixed import FixedDomain
from ...expression_tree.nary.bool.and_ import And
from ...expression_tree.nary.bool.or_ import Or
from ...expression_tree.nary.bool.xor import Xor
from ...expression_tree.term.constant import Constant
from ...expression_tree.term.function import Function
from ...expression_tree.term.variable import Variable
from ...expression_tree.unary.bool.not_ import Not
from ...expression_tree.unary.first_order.counting import Counting
from ...expression_tree.unary.first_order.existential import Existential
from ...expression_tree.unary.first_order.universal import Universal

if __name__ is not None and "." in __name__:
    from .FormulaParser import FormulaParser
else:
    from FormulaParser import FormulaParser

# This class defines a complete generic visitor for a parse tree produced by FormulaParser.


class FormulaVisitor(ParseTreeVisitor):
    def visitFormula(self, ctx: FormulaParser.FormulaContext):
        expr = self.visit(ctx.expr())

        free_vars, free_var_domains = [], []
        if ctx.dv is not None:
            free_vars, free_var_domains = self.visit(ctx.dv)

        return expr, free_vars, free_var_domains

    def visitEquivalence(self, ctx: FormulaParser.EquivalenceContext):
        left_expr = self.visit(ctx.left)
        right_expr = self.visit(ctx.right)

        return Equivalence(left_expr, right_expr)

    def visitXorExpr(self, ctx: FormulaParser.XorExprContext):
        return self.visit(ctx.xor_expr())

    def visitImplication(self, ctx: FormulaParser.ImplicationContext):
        left_expr = self.visit(ctx.left)
        right_expr = self.visit(ctx.right)

        return Implication(left_expr, right_expr)

    def visitXor(self, ctx: FormulaParser.XorContext):
        symbols = ["^", "xor", "XOR"]
        if ctx.op is None or ctx.op.text not in symbols:
            return self.visitChildren(ctx)

        exprs = []
        for child in ctx.children:
            if child.getText() not in symbols:
                exprs.append(self.visit(child))

        return Xor(exprs)

    def visitOr(self, ctx: FormulaParser.OrContext):
        symbols = ["|", "or", "OR"]
        if ctx.op is None or ctx.op.text not in symbols:
            return self.visitChildren(ctx)

        exprs = []
        for child in ctx.children:
            if child.getText() not in symbols:
                exprs.append(self.visit(child))

        return Or(exprs)

    def visitAnd(self, ctx: FormulaParser.AndContext):
        symbols = ["&", "and", "AND"]
        if ctx.op is None or ctx.op.text not in symbols:
            return self.visitChildren(ctx)

        exprs = []
        for child in ctx.children:
            if child.getText() not in symbols:
                exprs.append(self.visit(child))

        return And(exprs)

    def visitNotExpr(self, ctx: FormulaParser.NotExprContext):
        expr = self.visit(ctx.right)

        return Not(expr)

    def visitAtomExpr(self, ctx: FormulaParser.AtomExprContext):
        return self.visit(ctx.atom())

    def visitPredicate(self, ctx: FormulaParser.PredicateContext):
        name = ctx.op.text[:-1]
        terms = self.visit(ctx.sig)

        return Predicate(name, terms)

    def visitUniversal(self, ctx: FormulaParser.UniversalContext):
        expr = self.visit(ctx.right)
        vars, domains = self.visit(ctx.dv)

        return Universal(expr, vars, domains)

    def visitExistential(self, ctx: FormulaParser.ExistentialContext):
        expr = self.visit(ctx.right)
        vars, domains = self.visit(ctx.dv)

        return Existential(expr, vars, domains)

    def visitCounting(self, ctx: FormulaParser.CountingContext):
        expr = self.visit(ctx.right)
        vars, domains = self.visit(ctx.dv)

        if ctx.cop.text == "<=":
            count_type = Counting.CountType.LESS_EQUAL
        elif ctx.cop.text == "=":
            count_type = Counting.CountType.EQUAL
        else:
            count_type = Counting.CountType.GREATER_EQUAL

        num = int(ctx.num.text)

        return Counting(expr, vars, domains, count_type, num)

    def visitBuiltInPredicate(self, ctx: FormulaParser.BuiltInPredicateContext):
        left_term = self.visit(ctx.left)
        right_term = self.visit(ctx.right)

        return Predicate(ctx.op.text, [left_term, right_term])

    def visitVarTerm(self, ctx: FormulaParser.VarTermContext):
        return Variable(ctx.te.text)

    def visitConstTerm(self, ctx: FormulaParser.ConstTermContext):
        return self.visit(ctx.te)

    def visitFunctionTerm(self, ctx: FormulaParser.FunctionTermContext):
        name = ctx.te.text[:-1]
        terms = self.visit(ctx.sig)

        return Function(name, terms)

    def visitTermsSignature(self, ctx: FormulaParser.TermsSignatureContext):
        terms = []
        for child in ctx.children:
            if child.getText() == "," or child.getText() == ")":
                continue
            terms.append(self.visit(child))

        return terms

    def visitDomainVariables(self, ctx: FormulaParser.DomainVariablesContext):
        vars, domains = [], []
        next_domain = False
        num_vars = 0
        for child in ctx.children:
            if child.getText() == ",":
                continue
            if child.getText() == "in":
                next_domain = True
                continue

            if next_domain:
                for _ in range(num_vars):
                    domains.append(self.visit(child))
                next_domain = False
                num_vars = 0
            else:
                vars.append(Variable(child.getText()))
                num_vars += 1

        return vars, domains

    def visitFixedDomain(self, ctx: FormulaParser.FixedDomainContext):
        return FixedDomain(ctx.na.text)

    def visitDynamicDomain(self, ctx: FormulaParser.DynamicDomainContext):
        name = ctx.te.text[:-1]
        terms = self.visit(ctx.sig)
        func = Function(name, terms)

        return DynamicDomain(name, func)

    def visitStringConst(self, ctx: FormulaParser.StringConstContext):
        return Constant(ctx.val.text.replace('"', ""))

    def visitIntConst(self, ctx: FormulaParser.IntConstContext):
        return Constant(int(ctx.val.text))

    def visitFloatConst(self, ctx: FormulaParser.FloatConstContext):
        return Constant(float(ctx.val.text))

    def visitBoolean(self, ctx: FormulaParser.BooleanContext):
        return self.visit(ctx.bool_())

    def visitBrackets(self, ctx: FormulaParser.BracketsContext):
        return self.visit(ctx.content)

    def visitTrueBoolean(self, _):
        return Bool(True)

    def visitFalseBoolean(self, _):
        return Bool(False)


del FormulaParser
