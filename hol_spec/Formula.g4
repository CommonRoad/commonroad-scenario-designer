grammar Formula;

formula
 : expr (WITH dv=domain_vars)?
 ;

expr
 : <assoc=right> left=expr op=IMPL right=expr   #Implication
 | <assoc=right> left=expr op=EQ right=expr     #Equivalence
 |  xor_expr                                    #XorExpr
 ;

xor_expr
 : or_expr (op=XOR or_expr)*                    #Xor
 ;

or_expr
 : and_expr (op=OR and_expr)*                   #Or
 ;

and_expr
 : unary_expr (op=AND unary_expr)*                                                                  #And
 ;

unary_expr
  : op=NOT right=atom                                                                               #NotExpr
  | op=PREDICATE sig=terms_signature                                                                #Predicate
  | atom                                                                                            #AtomExpr
  | op=UNIVERSAL dv=domain_vars '.' right=expr                                                      #Universal
  | op=EXISTENTIAL dv=domain_vars '.' right=expr                                                    #Existential
  | op=COUNTING cop=(LESS_EQUAL|EQUAL|GREATER_EQUAL) num=INT_VALUE dv=domain_vars '.' right=expr    #Counting
  | left=term op=(EQUAL|UNEQUAL|LESS|GREATER|LESS_EQUAL|GREATER_EQUAL) right=term                   #BuiltInPredicate
 ;

term
 : te=FUNCTION sig=terms_signature                                                 #FunctionTerm
 | te=const                                                                        #ConstTerm
 | te=VAR                                                                          #VarTerm
 ;

terms_signature
 : term (',' term)* ')'                                                     #TermsSignature
 ;

const
 : val=STR_VALUE                                                            #StringConst
 | val=INT_VALUE                                                            #IntConst
 | val=FLOAT_VALUE                                                          #FloatConst
 ;

domain_vars
 : VAR (',' VAR)* IN domain (',' VAR (',' VAR)* IN domain)*                         #DomainVariables
 ;

domain
 : na=FIXED_DOMAIN                                                                  #FixedDomain
 | te=FUNCTION sig=terms_signature                                                  #DynamicDomain
 ;

atom
 : bool_                                           #Boolean
 | '(' content=expr+ ')'                           #Brackets
 ;

bool_
  : TRUE                    # TrueBoolean
  | FALSE                   # FalseBoolean
  ;

 TRUE                       : ('True'|'true');
 FALSE                      : ('False'|'false');

 NOT                        : ('!'|'not'|'NOT');

 UNIVERSAL                  : ('A'|'ALL');
 EXISTENTIAL                : ('E'|'EXISTS');
 COUNTING                   : ('C'|'COUNT');

 AND        	            : ('&'|'and'|'AND');
 OR         	            : ('|'|'or'|'OR');
 XOR                        : ('^'|'xor'|'XOR');
 IMPL       	            : '->';
 EQ                         : '<->';

 IN                         : 'in';

 EQUAL                      : '=';
 UNEQUAL                    : '!=';
 LESS                       : '<';
 GREATER                    : '>';
 LESS_EQUAL                 : '<=';
 GREATER_EQUAL              : '>=';

 WITH                       : '||';


 fragment LOWER_ALPHA_UNDERSCORE : [a-z]+([_]?[a-zA-Z0-9]+)*;
 fragment UPPER_ALPHA_UNDERSCORE : [A-Z]+([_]?[a-zA-Z0-9]+)*;

 PREDICATE                  : UPPER_ALPHA_UNDERSCORE'(';
 VAR		                : LOWER_ALPHA_UNDERSCORE;
 FUNCTION                   : LOWER_ALPHA_UNDERSCORE'(';
 FIXED_DOMAIN                     : [A-Z]+[A-Z]*[0-9]*;

 WS                         : [ \t\n]+ -> skip;       //Skip whitespaces

 STR_VALUE                  : '"' [a-zA-Z0-9]([_]?[a-zA-Z0-9]+)* '"';
 INT_VALUE                  : [0-9] | [1-9][0-9]+;
 FLOAT_VALUE                : INT_VALUE '.' INT_VALUE?;