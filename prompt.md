# CRD 3‑D Validation – Robust Minimal‑Change Prompt (Multi‑Rule, Explicit + Implicit Requirements)

## System
You are a senior ANTLR/HOL engineer and Python geomatics developer working on the
CommonRoad Scenario‑Designer (CRD) validator. Your job is to **extend validation logic for
3‑D scenarios** with **minimal changes** to a fixed set of Python files, without modifying
the grammar. **Be deterministic** and return **compile‑ready** code. Wrap code in fenced blocks
(`python`, `yaml`).

**Non‑negotiable constraints**  
- Do **NOT** modify `Formula.g4` or any ANTLR artifacts. Set `antlr_patch: "NO_CHANGE"`.
- Apply code changes **only** to these Python files (and in this order when outputting full files):
  1) `crdesigner/verification_repairing/verification/formula_ids.py`
  2) `crdesigner/verification_repairing/verification/groups_handler.py`
  3) `crdesigner/verification_repairing/verification/hol/formula_collection.py`
  4) `crdesigner/verification_repairing/verification/hol/functions/predicates/lanelet_predicates.py`
- Prefer **extensions** (optional keyword parameters with safe defaults) of existing predicates and
  helpers over broad refactors. Keep public call sites stable unless strictly necessary.
- Keep **2‑D behavior bit‑for‑bit identical**: when Z is missing, predicates must **gracefully pass**
  (return True) and never raise.
- Use **robust geometry** practices: validate/fix Shapely geometries (`make_valid` or `buffer(0)`),
  guard `GEOSException`, and never propagate exceptions from predicates.
- Logging must use `log3d = logging.getLogger("crdesigner.verification.3d")` with informative messages.

---

## User – Step 0 (Output contract)
For every reply, follow this contract:

1) Output a YAML object with two keys:
   - `antlr_patch`: **exactly** `"NO_CHANGE"`
   - `python_patch`: a **unified diff** containing only the edits for the four files above.

2) Then output **full replacement files** for the same four files, in the exact order listed in
“Non‑negotiable constraints”.

3) End with a short **post‑check** bullet list asserting all acceptance criteria (see Step 5).

Do not include any other file changes. Do not add new modules. Do not alter import paths other than
what is needed within the same four files. Do you understand clearly?

---

## User – Step 1 (Summarise current code + 3‑D XML sample)

**Goal**  Upgrade the validator so it fully understands 3‑D CRD XML (bridges, tunnels, stacked
intersections, vertical clearance, ramps, splits/merges), while keeping 2‑D behavior intact.

For **each** pasted file produce a YAML item:

```yaml
file: <filename>
outline:          # 1‑line purpose per grammar rule or function
z_assumptions:    # anything that ignores or strips z (e.g. [:, :2], 2‑D‑only logic)
```

Please summarise separately (large files → multiple chunks). Keep appending until I say
**END OF FILES**. While I’m pasting, **do not** propose code — just acknowledge with
a cumulative counter, e.g., “Indexed N files”.

Files may include (not exhaustive):

- Formula.g4
- formula_collection.py
- formula.py
- FormulaVisitor.py
- general_functions.py
- intersection_functions.py
- intersection_predicates.py
- lanelet_functions.py
- lanelet_predicates.py
- traffic_light_functions.py
- traffic_light_predicates.py
- traffic_sign_functions.py
- builtin_functions.py
- builtin_predicates.py
- formula_manager.py
- formula_ids.py
- groups_handler.py

---

## User – Step 2 (Ingest natural‑language rules → explicit + implicit requirements)

I will describe new/changed validation rules in **free text** (English or Chinese).  
Your first task in this step is to **extract a structured set of requirements** from the text, including
both **explicit** and **implicit** constraints needed for robust and terminating validation.

### 2.1 Produce a structured Requirements block
Convert the free text to the following YAML (expand with multiple items if the user gives several rules):
```yaml
requirements:
  - id: <snake_case_identifier>
    kind: lanelet | lanelet_pair | network
    status: new | extend | new_or_extend
    description: |
      <one-paragraph description in plain English>
    thresholds:
      # numeric thresholds or booleans you infer or the user gave; propose safe defaults if missing
      # e.g., min_clearance_m: 7.0, eps_same_layer_m: 0.20, area_tol_m2: 1e-3, length_tol_m: 1e-3, max_grade_pct: 8.0
    semantics:
      # map semantics for implementers; pick only what applies
      xy_overlap_required: true|false          # if false, skip heavy geometry when XY disjoint
      pass_if_either_2d: true|false            # if any lanelet lacks Z, treat as pass (preserve 2-D behavior)
      ignore_self_pair: true|false             # never compare a lanelet with itself
      treat_same_layer_if_gap_lt_m: <float>    # vertical gap below this => consider same layer
      small_overlap_is_noise:
        area_tol_m2: <float>                   # ignore tiny area overlaps
        length_tol_m: <float>                  # or tiny boundary overlaps
      topology_guard:
        require_predecessor_successor: true|false
        require_adjacent: true|false
      z_sampling_strategy: mean_center | endpoint | nearest_to_xy_intersection
      degenerate_guard:
        zero_length_xy_pass: true              # if Δs≈0 then pass and log (avoid division by zero)
      error_policy:
        on_exception_pass: true                # never fail on exceptions; log at debug/warn
        log_details: true
```
**Important:** If the text is vague (e.g., “上下坡不能太陡” / “gradients shouldn’t be steep”),  
derive a conservative default (`max_grade_pct: 8.0`) and record it under `thresholds`.

### 2.2 Map to code locations (minimal‑change anchors)
Design where to patch for each requirement:
- `formula_ids.py`: add enum members to `LaneletFormulaID` **only** for rules we will expose.
- `groups_handler.py`: add the new IDs to suitable default groups (preserve existing priorities).
- `hol/formula_collection.py`: add concise formula strings that call predicates, e.g.  
  `"vertical_clearance_stacked": "(l1 != l2) -> Is_vertical_clearance_sufficient(l1, l2) || l1, l2 in L"`.
- `hol/functions/predicates/lanelet_predicates.py`: **extend existing predicates** via optional kwargs,
  or introduce **small new helpers** in this file **only**.

Identify **anchors** to search instead of line numbers, e.g., function names:
`is_polylines_intersection`, `is_polyline_self_intersection`, `are_intersected_lanelets`,
`is_adj_type`, `is_correct_left_right_boundary_assignment`, `has_predecessor`, etc.

### 2.3 Implicit‑requirements checklist (apply generically, not just for “grade”)
When designing each predicate, incorporate the following robustness rules unless clearly inapplicable:
1) **2‑D → pass:** If any required Z is missing, return `True` and log a debug note.  
2) **XY gating:** If `xy_overlap_required` and polygons **do not** overlap in XY (area/length below tol), return `True`.  
3) **Self‑pair skip:** If `l1.lanelet_id == l2.lanelet_id`, return `True`.  
4) **Same‑layer epsilon:** If `|Δz| < eps_same_layer_m`, treat as **same layer** and return `True` unless the rule forbids it.  
5) **Small overlap noise:** If overlap area `< area_tol_m2` **and** overlap length `< length_tol_m`, return `True`.  
6) **Degeneracy guards:** Avoid division by zero; if `Δs < 0.01 m`, skip that segment.  
7) **Geometry validity:** Use `make_valid` if available; else `buffer(0)` fallback. Guard `GEOSException`.  
8) **Error policy:** On any exception, **return True** and log a warning—validation must not crash.  
9) **Determinism:** Do not use random choices; keep code path deterministic.  
10) **No recursion / no unbounded loops** inside predicates; do not change verification control flow.

### 2.4 Examples of rule interpretation (generic)
- “**Elevated bridges must not be too close vertically when overlapping** ”:  
  `lanelet_pair`, `xy_overlap_required: true`, compute `Δz` using `mean_center` or `nearest_to_xy_intersection`, pass if `Δz ≥ min_clearance_m` or if either lanelet lacks Z; ignore tiny overlaps (ramp noses) via `area_tol_m2` / `length_tol_m`; treat `|Δz| < eps_same_layer_m` as same layer → pass.
- “**Grade within limit**”:  
  `lanelet`, compute grade over **all internal segments**; ignore `Δs < 0.01 m`; ‘2‑D → pass’; return `max( |dz/ds| ) ≤ max_grade_pct`.
- “**Predecessor vertical step**”:  
  `lanelet_pair`, `topology_guard.require_predecessor_successor: true`, compare last→first endpoints; ‘2‑D → pass’; threshold `max_step_m`.

Return the Requirements YAML plus a short mapping table:
`id │ predicate_to_call │ formula_string │ files_to_patch │ anchors`.

---

## User – Step 3 (Patch plan → unified diffs)

Produce the **unified diffs** for only the four allowed files.

**Implementation policy** (apply to **every** new/extended rule):
- `formula_ids.py`: add enum members in `LaneletFormulaID` only.
- `groups_handler.py`: append the new IDs to appropriate default groups.
- `hol/formula_collection.py`: insert formula strings that call your predicates. Embed numeric thresholds
  directly if helpful, or rely on sensible default kwargs in the predicate.
- `hol/functions/predicates/lanelet_predicates.py`: implement or extend predicates with kwargs such as
  `min_clearance_m: float = 7.0`, `eps_same_layer_m: float = 0.2`, `area_tol_m2: float = 1e-3`,
  `length_tol_m: float = 1e-3`, `max_grade_pct: float = 8.0`, `max_step_m: float = 0.5`.
  Follow the **implicit‑requirements checklist** from Step 2.3.

**Shapely safety pattern:**  
- Build polygons from `lanelet.polygon.shapely_object`, run `_clean_poly = make_valid(poly) or poly.buffer(0)`,
  then compute intersections; catch `GEOSException`; on exception return `True` (skip) and log.

**2‑D compatibility:**  
- When `shape[1] < 3` for any required array, **return True** immediately with a debug log.

---

## User – Step 4 (Full files)
Output **full replacement files** for the same four files, in this exact order:
1. `crdesigner/verification_repairing/verification/formula_ids.py`  
2. `crdesigner/verification_repairing/verification/groups_handler.py`  
3. `crdesigner/verification_repairing/verification/hol/formula_collection.py`  
4. `crdesigner/verification_repairing/verification/hol/functions/predicates/lanelet_predicates.py`

---

## User – Step 5 (Post‑check – acceptance criteria)
Finish with a bullet list affirming:
- No grammar edits; `antlr_patch` is exactly `"NO_CHANGE"`.
- Only the four files were modified; **no new modules** created.
- 2‑D behavior remains **bit‑for‑bit identical** on legacy maps (Z missing ⇒ pass).
- Each new formula ID appears in `LaneletFormulaID` and is referenced in `groups_handler.py`.
- Each formula string in `formula_collection.py` calls a predicate implemented/extended in
  `lanelet_predicates.py` with robust kwargs defaults.
- Shapely geometries are validated; `GEOSException` guarded; on exception predicates **pass** and log.
- Logging uses `crdesigner.verification.3d` with informative context.
- Predicates are **pure** (no side effects), deterministic, terminate, and avoid divisions by zero.

---

## User – Step 6 (Iterate on new or changed natural‑language rules)
If I later provide more free‑text rules or update thresholds (e.g., “minimum vertical clearance 7 m
for overlapping elevated lanelets”, “grade ≤ 6% on ramps”), repeat Steps 2→5 and recompute the minimal
diffs, still touching **only** the four files. Maintain backward compatibility and robustness guarantees.

---

## Output style reminders
- Keep diffs minimal and focused.
- Use **explicit anchors** in your plan (function names or obvious comments) rather than line numbers.
- Don’t duplicate existing 2‑D rules; extend them via kwargs when possible.
- Be conservative with thresholds if not specified; prefer **skipping** on ambiguity rather than
false positives.
- All code must be **deterministic** and **import‑clean**.




-----------------------------------------------------------------------------------------
hol_spec/Formula.g4
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

 --------------------------------------------------------------------------------------------
 crdesigner\verification_repairing\verification\hol\formula_collection.py
from typing import Dict


class GeneralFormulas:
    formulas: Dict[str, str] = {
        "unique_id_all": "!(E k2 in M. (k1 != k2 & el_id(k1) = el_id(k2))) || k1 in M"
    }
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {}


class LaneletFormulas:
    formulas: Dict[str, str] = {
        "same_vertices_size": "size(left_polyline(l)) = size(right_polyline(l)) || l in L",
        "vertices_more_than_one": "(size(left_polyline(l)) > 1 & size(right_polyline(l)) > 1) "
        "|| l in L",
        "existence_left_adj": "(Has_left_adj_ref(l1)) -> E l2 in L. (Has_left_adj(l1, "
        "l2)) || l1 in L",
        "existence_right_adj": "(Has_right_adj_ref(l1)) -> E l2 in L. (Has_right_adj(l1, "
        "l2)) || l1 in L",
        "existence_predecessor": "E l2 in L. (lanelet_id(l2) = p_id) || l1 in L, "
        "p_id in predecessors(l1)",
        "existence_successor": "E l2 in L. (lanelet_id(l2) = s_id) || l1 in L, "
        "s_id in successors(l1)",
        "polylines_intersection": "!(Is_polylines_intersection(left_polyline(l), "
        "right_polyline(l))) || l in L",
        "left_self_intersection": "!(Is_polyline_self_intersection(left_polyline(l))) || l in" " L",
        "right_self_intersection": "!(Is_polyline_self_intersection(right_polyline(l))) || l "
        "in L",
        "connections_predecessor": "(Has_predecessor(l1, l2)) -> are_predecessor_connections("
        "l1, l2) || l1, l2 in L",
        "connections_successor": "(Has_successor(l1, l2)) -> are_successor_connections(l1, "
        "l2) || l1, l2 in L",
        "potential_predecessor": "(!(Has_predecessor(l1, l2))) -> !("
        "are_predecessor_connections(l1, l2)) || l1, "
        "l2 in L",
        "potential_successor": "(!(Has_successor(l1, l2))) -> !(are_successor_connections(l1,"
        " l2)) || l1, l2 in L",
        "non_predecessor_as_successor": "(lanelet_id(l1) != lanelet_id(l2) & Has_successor(l1, "
        "l2) & !(Has_predecessor(l1, l2))) -> !("
        "are_predecessor_connections(l1, "
        "l2)) || l1, l2 in L",
        "non_successor_as_predecessor": "(lanelet_id(l1) != lanelet_id(l2) & "
        "Has_predecessor(l1, l2) & !(Has_successor(l1, "
        "l2))) -> !("
        "are_successor_connections(l1, l2)) || l1, l2 in L",
        "referenced_intersecting_lanelets": "(Are_intersected_lanelets(l1, "
        "l2)) -> (Has_left_adj(l1, "
        "l2) | Has_right_adj(l1, l2) | Has_predecessor("
        "l1, l2) | Has_successor("
        "l1, l2)) || l1, l2 in L",
        "existence_traffic_signs": "E t in TS. (traffic_sign_id(t) = t_id) || l in L, "
        "t_id in traffic_signs(l)",
        "existence_traffic_lights": "E t in TL. (traffic_light_id(t) = t_id) || l in L, "
        "t_id in traffic_lights(l)",
        "zero_or_two_points_stop_line": "(Has_stop_line(l)) -> (Has_start_point(stop_line(l)) "
        "<-> Has_end_point("
        "stop_line(l))) || l in L",
        "polylines_left_same_dir_parallel_adj": "(Has_left_adj(l1, l2) & Is_adj_type(l1, l2, "
        '"parallel") & '
        "Is_left_adj_same_direction(l1, l2)) -> "
        "Are_similar_polylines("
        "left_polyline(l1), right_polyline(l2)) || "
        "l1, l2 in L",
        "polylines_right_same_dir_parallel_adj": "(Has_right_adj(l1, l2) & Is_adj_type(l1, "
        'l2, "parallel") & '
        "Is_right_adj_same_direction(l1, l2)) -> "
        "Are_similar_polylines("
        "right_polyline(l1), left_polyline(l2)) || "
        "l1, l2 in L",
        "polylines_left_opposite_dir_parallel_adj": "(Has_left_adj(l1, l2) & Is_adj_type(l1, "
        'l2, "parallel") & '
        "Is_left_adj_opposite_direction(l1, "
        "l2)) -> Are_similar_polylines("
        "reverse(left_polyline(l1)), "
        "left_polyline(l2)) || l1, l2 in L",
        "polylines_right_opposite_dir_parallel_adj": "(Has_right_adj(l1, "
        'l2) & Is_adj_type(l1, l2, "parallel") & '
        "Is_right_adj_opposite_direction(l1, "
        "l2)) -> Are_similar_polylines("
        "reverse(right_polyline(l1)), "
        "right_polyline(l2)) || l1, l2 in L",
        "potential_left_same_dir_parallel_adj": "(Are_similar_polylines("
        "left_polyline(l1), right_polyline(l2))) -> ("
        "Has_left_adj(l1, "
        'l2) & Is_adj_type(l1, l2, "parallel") & '
        "Is_left_adj_same_direction("
        "l1, l2)) || l1, l2 in L",
        "potential_right_same_dir_parallel_adj": "(Are_similar_polylines("
        "right_polyline(l1), left_polyline(l2))) -> "
        "(Has_right_adj(l1, "
        'l2) & Is_adj_type(l1, l2, "parallel") & '
        "Is_right_adj_same_direction(l1, l2)) || l1, "
        "l2 in L",
        "potential_left_opposite_dir_parallel_adj": "(Are_similar_polylines("
        "reverse(left_polyline(l1)), "
        "left_polyline(l2))) -> ("
        "Has_left_adj(l1, l2) & Is_adj_type(l1, "
        'l2, "parallel") & !('
        "Is_left_adj_same_direction(l1, "
        "l2))) || l1, l2 in L",
        "potential_right_opposite_dir_parallel_adj": "(Are_similar_polylines("
        "reverse(right_polyline(l1)), "
        "right_polyline(l2))) -> ("
        "Has_right_adj(l1, l2) & Is_adj_type(l1, "
        'l2, "parallel") & '
        "Is_right_adj_opposite_direction(l1, "
        "l2)) || l1, l2 in L",
        "connections_left_merging_adj": "(Has_left_adj(l1, l2) & Is_adj_type(l1, "
        'l2, "merging")) -> are_left_merging_adj_connections('
        "l1, l2) || l1, l2 in L",
        "connections_right_merging_adj": "(Has_right_adj(l1, l2) & Is_adj_type(l1, "
        'l2, "merging")) -> '
        "are_right_merging_adj_connections(l1, l2) || l1, "
        "l2 in L",
        "potential_left_merging_adj": "(are_left_merging_adj_connections(l1, "
        "l2)) -> (Has_left_adj(l1, l2) & Is_adj_type(l1, l2, "
        '"merging")) || l1, l2 in L',
        "potential_right_merging_adj": "(are_right_merging_adj_connections(l1, "
        "l2)) -> (Has_right_adj(l1, l2) & Is_adj_type(l1, l2, "
        '"merging")) || l1, '
        "l2 in L",
        "connections_left_forking_adj": "(Has_left_adj(l1, l2) & Is_adj_type(l1, "
        'l2, "forking")) -> are_left_forking_adj_connections('
        "l1, l2) || l1, l2 in L",
        "connections_right_forking_adj": "(Has_right_adj(l1, l2) & Is_adj_type(l1, "
        'l2, "forking")) -> '
        "are_right_forking_adj_connections(l1, l2) || l1, "
        "l2 in L",
        "potential_left_forking_adj": "(are_left_forking_adj_connections(l1, "
        "l2)) -> (Has_left_adj(l1, l2) & Is_adj_type(l1, l2, "
        '"forking")) || l1, l2 in L',
        "potential_right_forking_adj": "(are_right_forking_adj_connections(l1, "
        "l2)) -> (Has_right_adj(l1, l2) & Is_adj_type(l1, l2, "
        '"forking")) || l1, '
        "l2 in L",
        "included_stop_line_traffic_signs": "(Has_stop_line(l)) -> (A s_id1 in "
        "stop_line_traffic_signs(stop_line(l)). "
        "(traffic_sign_id(s) = s_id1 -> E s_id2 in "
        "traffic_signs(l). s_id1 = "
        "s_id2)) || l in L, s in TS",
        "included_stop_line_traffic_lights": "(Has_stop_line(l)) -> (A t_id1 in "
        "stop_line_traffic_lights(stop_line("
        "l)). (traffic_light_id(t) = t_id1 -> E t_id2 in "
        "traffic_lights(l). "
        "t_id1 = t_id2)) || l in L, t in TL",
        "stop_line_references": "(Has_stop_line(l)) -> "
        "(size(stop_line_traffic_signs(stop_line(l))) > 0 | "
        "size(stop_line_traffic_lights(stop_line(l))) > 0) || l in L",
        "conflicting_lanelet_directions": "lanelet_id(l1) != lanelet_id(l2) & "
        "!(Has_left_adj(l1, l2) | Has_left_adj(l2, l1) |"
        " Has_right_adj(l1, l2) | Has_right_adj(l2, l1)) & "
        "!(are_left_merging_adj_connections(l1, l2) | "
        "are_right_merging_adj_connections(l1, l2) | "
        "are_left_forking_adj_connections(l1, l2) | "
        "are_right_forking_adj_connections(l1, l2) | "
        "are_left_merging_adj_connections(l2, l1) | "
        "are_right_merging_adj_connections(l2, l1) | "
        "are_left_forking_adj_connections(l2, l1) | "
        "are_right_forking_adj_connections(l2, l1)) -> "
        "(!(are_conflicting_connections(l1, l2)))"
        "|| l1, l2 in L",
        "left_right_boundary_assignment": "Is_correct_left_right_boundary_assignment(l) "
        "|| l in L",
    }
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {
        "are_predecessor_connections(l1, l2)": "Are_equal_vertices(start_vertex(left_polyline(l1)), end_vertex("
        "left_polyline(l2))) & Are_equal_vertices(start_vertex(right_polyline("
        "l1)), end_vertex(right_polyline(l2)))",
        "are_successor_connections(l1, l2)": "Are_equal_vertices(end_vertex(left_polyline(l1)), start_vertex("
        "left_polyline(l2))) & Are_equal_vertices(end_vertex(right_polyline("
        "l1)), start_vertex(right_polyline(l2)))",
        "are_conflicting_connections(l1, l2)": "Are_equal_vertices(end_vertex(left_polyline(l1)), end_vertex("
        "right_polyline(l2))) & Are_equal_vertices(end_vertex(right_polyline("
        "l1)), end_vertex(left_polyline(l2))) | "
        "Are_equal_vertices(end_vertex(left_polyline(l1)), end_vertex("
        "left_polyline(l2))) & Are_equal_vertices(end_vertex(right_polyline("
        "l1)), end_vertex(right_polyline(l2)))",
        "are_left_merging_adj_connections(l1, l2)": "lanelet_id(l1) != lanelet_id(l2) & "
        "Are_equal_vertices(end_vertex(left_polyline(l1)), end_vertex("
        "left_polyline(l2))) & Are_equal_vertices(end_vertex("
        "right_polyline(l1)), end_vertex(right_polyline(l2))) & "
        "Are_equal_vertices(start_vertex(left_polyline(l1)), "
        "start_vertex(right_polyline(l2)))",
        "are_right_merging_adj_connections(l1, l2)": "lanelet_id(l1) != lanelet_id(l2) & "
        "Are_equal_vertices(end_vertex(left_polyline(l1)), end_vertex("
        "left_polyline(l2))) & Are_equal_vertices(end_vertex("
        "right_polyline(l1)), end_vertex(right_polyline(l2))) & "
        "Are_equal_vertices(start_vertex(right_polyline(l1)), "
        "start_vertex(left_polyline(l2)))",
        "are_left_forking_adj_connections(l1, l2)": "lanelet_id(l1) != lanelet_id(l2) & "
        "Are_equal_vertices(start_vertex(left_polyline(l1)), "
        "start_vertex(left_polyline(l2))) & Are_equal_vertices("
        "start_vertex(right_polyline(l1)), start_vertex(right_polyline("
        "l2))) & Are_equal_vertices(end_vertex(left_polyline(l1)), "
        "end_vertex(right_polyline(l2)))",
        "are_right_forking_adj_connections(l1, l2)": "lanelet_id(l1) != lanelet_id(l2) & "
        "Are_equal_vertices(start_vertex(left_polyline(l1)), "
        "start_vertex(left_polyline(l2))) & Are_equal_vertices("
        "start_vertex(right_polyline(l1)), start_vertex(right_polyline("
        "l2))) & Are_equal_vertices(end_vertex(right_polyline(l1)), "
        "end_vertex(left_polyline(l2)))",
    }


class TrafficSignFormulas:
    formulas: Dict[str, str] = {
        "at_least_one_traffic_sign_element": "size(traffic_sign_elements(t)) > 0 || t in TS",
        "referenced_traffic_sign": "E l in L. (Has_traffic_sign(l, t)) || t in TS",
        "maximal_distance_from_lanelet": "E l in L. (Has_traffic_sign(l, "
        "t) & distance_to_lanelet(t, l) <= 10.0) || t "
        "in TS",
    }
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {}


class TrafficLightFormulas:
    formulas: Dict[str, str] = {
        "at_least_one_cycle_element": "size(cycle_elements(t)) > 0 || t in TL",
        "referenced_traffic_light": "E l in L. Has_traffic_light(l, t) || t in TL",
        "traffic_light_per_incoming": "(traffic_light_id(t) = t_id & Has_traffic_light(l1, t) "
        "& Has_traffic_light(l2, t)) -> E i in I, "
        "e in IE. (Has_incoming_element(i, e) "
        "& Has_incoming_lanelet(e, l1) "
        "& Has_incoming_lanelet(e, l2)) "
        "|| t in TS, l1 in L, l2 in L, t_id in traffic_lights("
        "l1)",
    }
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {}


class IntersectionFormulas:
    formulas: Dict[str, str] = {}
    # formulas: Dict[str, str] = {'at_least_two_incoming_elements': 'size(incoming_elements(i)) > 1 || i in I',
    #
    #                             'at_least_one_incoming_lanelet': '(Has_incoming_element(i, e)) -> size('
    #                                                              'incoming_lanelets(e)) > 0 || i in I, '
    #                                                              'e in IG',
    #
    #                             'existence_incoming_lanelets': '(Has_incoming_element(i, e)) -> '
    #                                                            'E l in L. (lanelet_id(l) = l_id) || i in I, e in IG, '
    #                                                            'l_id in incoming_lanelets(e)'}
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {}

---------------------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\hol\formula.py
import enum
from typing import Any, Dict, List

from crdesigner.verification_repairing.verification.hol.context import Context
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.domain import (
    Domain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.dynamic import (
    DynamicDomain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.domain.fixed import (
    FixedDomain,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.expression import (
    Expression,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.symbols import (
    Symbol,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.term.variable import (
    Variable,
)
from crdesigner.verification_repairing.verification.hol.expression_tree.unary.bool.not_ import (
    Not,
)
from crdesigner.verification_repairing.verification.hol.functions.predicates import (
    builtin_predicates,
)
from crdesigner.verification_repairing.verification.hol.functions.term_functions import (
    builtin_functions,
)


class DomainName(enum.Enum):
    LANELETS = "L"
    TRAFFIC_SIGNS = "TS"
    TRAFFIC_LIGHTS = "TL"
    INTERSECTIONS = "I"
    INCOMING_GROUPS = "IG"
    TRAFFIC_LIGHT_CYCLE_ELEMENTS = "CE"
    OUTGOING_GROUPS = "OG"
    POLYLINES = "P"
    STOP_LINES = "SL"
    AREAS = "AR"
    ALL_ELEMENTS = "M"


class Formula:
    """
    Class representing a formula.
    """

    def __init__(
        self,
        formula_id: str,
        expr: Expression,
        free_vars: List[Variable],
        free_var_domains: List[Domain],
    ):
        """
        Constructor.

        :param formula_id: Formula ID.
        :param expr: Expression.
        :param free_vars: Free variables.
        :param free_var_domains: Domains of free variables.
        """

        self._formula_id = formula_id
        self._expr = expr
        self._free_vars = free_vars
        self._free_var_domains = free_var_domains

    @property
    def formula_id(self):
        return self._formula_id

    @formula_id.setter
    def formula_id(self, formula_id: str):
        self._formula_id = formula_id

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, expr: Expression):
        self._expr = expr

    @property
    def free_vars(self):
        return self._free_vars

    @free_vars.setter
    def free_vars(self, free_vars: List[Variable]):
        self._free_vars = free_vars

    @property
    def free_var_domains(self):
        return self._free_var_domains

    @free_var_domains.setter
    def free_var_domains(self, free_var_domains: List[Domain]):
        self._free_var_domains = free_var_domains

    def initialize(self, model: Context):
        """
        Initializes the domain values and the functions of predicates as well as term functions that
        are stored in the model.

        :param model: Model.
        """

        # built-in predicates
        for func_name in dir(builtin_predicates):
            predicate_func = getattr(builtin_predicates, func_name)
            if callable(predicate_func) and not func_name.startswith("__"):
                for symbol in Symbol:
                    if func_name == symbol.name.lower():
                        func_name = symbol.value
                model.add_predicate_func(func_name.capitalize(), predicate_func)

        # built-in functions
        for func_name in dir(builtin_functions):
            function_func = getattr(builtin_functions, func_name)
            if callable(function_func) and not func_name.startswith("__"):
                model.add_function_func(func_name, function_func)

        # initializes domains of free variables
        for domain in self._free_var_domains:
            if isinstance(domain, FixedDomain):
                if (
                    domain.domain_id in model.domain_vals.keys()
                    or domain.domain_id == DomainName.ALL_ELEMENTS.value
                ):
                    domain.values = model.domain_vals[domain.domain_id]
            elif isinstance(domain, DynamicDomain):
                if domain.domain_id in model.function_funcs.keys():
                    domain.func.func = model.function_funcs[domain.domain_id]

        self._expr.initialize(model)

    def to_string(self) -> str:
        """
        Converts formula to string representation.

        :return: String.
        """
        string = self._expr.to_string()
        for i, (var, domain) in enumerate(zip(self._free_vars, self._free_var_domains)):
            if i == 0:
                string += " || "
            string += (
                var.name
                + " in "
                + domain.to_string()
                + (", " if i < len(self._free_vars) - 1 else "")
            )

        return string

    def evaluate(self) -> bool:
        """
        Evaluates satisfiability of expression of formula.

        :return: Boolean indicates whether expression of formula is satisfied.
        """
        return self._expr.evaluate()

    def negate(self):
        """
        Negates the expression of formula.
        """
        if isinstance(self._expr, Not):
            self._expr = self._expr.expr
        else:
            self._expr = Not(self._expr)

    def update_free_variables(self, free_var_vals: Dict[str, Any]):
        """
        Updates values of free variables.

        :param free_var_vals: Values of free variables.
        """
        for var in self._free_vars:
            if var.name in free_var_vals.keys():
                var.val = free_var_vals[var.name]

        self._expr.update_variables(free_var_vals)

    def extract_free_variables(self) -> List[Variable]:
        """
        Extracts all free variables in formula.

        :return: Free variables.
        """
        pass  # TODO: Implement

----------------------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\hol\parser\gen\FormulaVisitor.py
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

----------------------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\hol\functions\term_functions\general_functions.py
from typing import Union

from commonroad.scenario.intersection import Intersection
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign


def el_id(element: Union[Lanelet, TrafficSign, TrafficLight, Intersection]) -> int:
    """
    Returns the ID of the given element.

    :param element: One of Lanelet, TrafficSign, TrafficLight, Intersection.
    :return: Element ID.
    """
    if type(element) is Lanelet:
        return element.lanelet_id
    if type(element) is TrafficSign:
        return element.traffic_sign_id
    if type(element) is TrafficLight:
        return element.traffic_light_id
    if type(element) is Intersection:
        return element.intersection_id
------------------------------------------------------------------------------------------------------
crdesigner\verification_repairing\verification\hol\functions\term_functions\lanelet_functions.py
from typing import List, Set

import numpy as np
from commonroad.scenario.lanelet import Lanelet, StopLine


def lanelet_id(lanelet: Lanelet) -> int:
    """
    Returns the ID of the lanelet.

    :param lanelet: Lanelet.
    :return: Lanelet ID.
    """
    return lanelet.lanelet_id


def left_adj(lanelet: Lanelet) -> int:
    """
    Returns the ID of the left adjacency.

    :param lanelet: Lanelet.
    :return: Lanelet ID.
    """
    return lanelet.adj_left


def right_adj(lanelet: Lanelet) -> int:
    """
    Returns the ID of the right adjacency.

    :param lanelet: Lanelet.
    :return: Lanelet ID.
    """
    return lanelet.adj_right


def left_polyline(lanelet: Lanelet) -> np.ndarray:
    """
    Returns the left polyline of the lanelet.

    :param lanelet: Lanelet.
    :return: Left polyline.
    """
    return lanelet.left_vertices


def right_polyline(lanelet: Lanelet) -> np.ndarray:
    """
    Returns the right polyline of the lanelet.

    :param lanelet: Lanelet.
    :return: Right polyline.
    """
    return lanelet.right_vertices


def start_vertex(polyline: np.ndarray) -> np.ndarray:
    """
    Returns the start vertex of the polyline.

    :param polyline: Polyline.
    :return: Start vertex.
    """
    return polyline[0]


def end_vertex(polyline: np.ndarray) -> np.ndarray:
    """
    Returns the end vertex of the polyline.

    :param polyline: Polyline.
    :return: End vertex.
    """
    return polyline[len(polyline) - 1]


def traffic_signs(lanelet: Lanelet) -> Set[int]:
    """
    Returns the IDs of all traffic signs referenced by the lanelet.

    :param lanelet: Lanelet.
    :return: IDs of traffic signs.
    """
    return lanelet.traffic_signs


def traffic_lights(lanelet: Lanelet) -> Set[int]:
    """
    Returns the IDs of all traffic lights referenced by the lanelet.

    :param lanelet: Lanelet.
    :return: IDs of traffic lights.
    """
    return lanelet.traffic_lights


def stop_line(lanelet: Lanelet) -> StopLine:
    """
    Returns the stop line of the lanelet.

    :param lanelet: Lanelet.
    :return: Stop line.
    """
    return lanelet.stop_line


def predecessors(lanelet: Lanelet) -> List[int]:
    """
    Returns the IDs of the predecessors of the lanelet.

    :param lanelet: Lanelet.
    :return: Predecessor IDs.
    """
    return lanelet.predecessor


def successors(lanelet: Lanelet) -> List[int]:
    """
    Returns the IDs of the successors of the lanelet.

    :param lanelet: Lanelet.
    :return: Successor IDs.
    """
    return lanelet.successor


def stop_line_traffic_signs(stop_line: StopLine) -> Set[int]:
    """
    Returns the IDs of the traffic signs of the stop line.

    :param stop_line: Stop line.
    :return: IDs of traffic signs.
    """
    return stop_line.traffic_sign_ref


def stop_line_traffic_lights(stop_line: StopLine) -> Set[int]:
    """
    Returns the IDs of the traffic lights of the stop line.

    :param stop_line: Stop line.
    :return: IDs of traffic lights.
    """
    return stop_line.traffic_light_ref

------------------------------------------------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\hol\functions\predicates\lanelet_predicates.py
import itertools
import logging
from collections import Counter

import numpy as np
from commonroad.scenario.lanelet import Lanelet, StopLine
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign
from commonroad_clcs.clcs import CurvilinearCoordinateSystem
from commonroad_clcs.config import CLCSParams, ResamplingParams
from commonroad_clcs.util import (
    chaikins_corner_cutting,
    compute_orientation_from_polyline,
    resample_polyline,
)
from shapely import LineString
from similaritymeasures import similaritymeasures

from crdesigner.common.config.lanelet2_config import Lanelet2Config


def has_left_adj_ref(lanelet: Lanelet) -> bool:
    """
    Checks whether the lanelet has a reference to a left adjacency.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a reference to a left adjacency.
    """
    return lanelet.adj_left is not None


def has_right_adj_ref(lanelet: Lanelet) -> bool:
    """
    Checks whether the lanelet has a reference to a right adjacency.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a reference to a right adjacency.
    """
    return lanelet.adj_right is not None


def has_left_adj(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as left adjacency.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as left adjacency.
    """
    return lanelet_0.adj_left == lanelet_1.lanelet_id


def has_right_adj(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether th first lanelet references the second lanelet as right adjacency.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as right adjacency.
    """
    return lanelet_0.adj_right == lanelet_1.lanelet_id


def is_left_adj_same_direction(lanelet: Lanelet, adj_lanelet: Lanelet) -> bool:
    """
    Checks whether the left adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the left adjacency of the lanelet has the same direction.
    """
    return (
        lanelet.adj_left_same_direction
        and np.linalg.norm(lanelet.left_vertices[0] - adj_lanelet.right_vertices[0]) < 1
        and np.linalg.norm(lanelet.left_vertices[-1] - adj_lanelet.right_vertices[-1]) < 1
    )


def is_left_adj_opposite_direction(lanelet: Lanelet, adj_lanelet: Lanelet) -> bool:
    """
    Checks whether the left adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the left adjacency of the lanelet has the same direction.
    """
    return (
        not lanelet.adj_left_same_direction
        and np.linalg.norm(lanelet.left_vertices[0] - adj_lanelet.left_vertices[-1]) < 1
        and np.linalg.norm(lanelet.left_vertices[-1] - adj_lanelet.left_vertices[0]) < 1
    )


def is_right_adj_same_direction(lanelet: Lanelet, adj_lanelet: Lanelet) -> bool:
    """
    Checks whether the right adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the right adjacency of the lanelet has the same direction.
    """
    return (
        lanelet.adj_right_same_direction
        and np.linalg.norm(lanelet.right_vertices[0] - adj_lanelet.left_vertices[0]) < 1
        and np.linalg.norm(lanelet.right_vertices[-1] - adj_lanelet.left_vertices[-1]) < 1
    )


def is_right_adj_opposite_direction(lanelet: Lanelet, adj_lanelet: Lanelet) -> bool:
    """
    Checks whether the right adjacency of the lanelet has the opposite direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the right adjacency of the lanelet has the same direction.
    """
    return (
        not lanelet.adj_right_same_direction
        and np.linalg.norm(lanelet.right_vertices[0] - adj_lanelet.right_vertices[-1]) < 1
        and np.linalg.norm(lanelet.right_vertices[-1] - adj_lanelet.right_vertices[0]) < 1
    )


def is_correct_left_right_boundary_assignment(lanelet: Lanelet) -> bool:
    """
    Checks whether the boundaries of two polylines are swapped.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the two boundaries should be swapped.
    """
    return not _wrong_left_right_boundary_side(
        lanelet.center_vertices, lanelet.left_vertices, lanelet.right_vertices
    )


def _wrong_left_right_boundary_side(
    center_vertices: np.ndarray,
    left_vertices: np.ndarray,
    right_vertices: np.ndarray,
    config: Lanelet2Config = Lanelet2Config(),
) -> bool:
    """
    Checks whether left and right boundary are swapped.

    :param center_vertices: Center vertices of lanelet.
    :param left_vertices: Left boundary of lanelet.
    :param right_vertices: Right boundary of lanelet.
    :returns: Boolean indicating whether boundaries are swapped.
    """
    left, right = None, None
    center_vertices = chaikins_corner_cutting(center_vertices, config.chaikins_initial_refinements)
    center_vertices = resample_polyline(center_vertices, config.resampling_initial_step)
    for eps, max_polyline_resampling_step in itertools.product(
        config.eps2_values, config.max_polyline_resampling_step_values
    ):
        try:
            if len(center_vertices) == 2:
                center_vertices = np.insert(
                    center_vertices, 1, (center_vertices[0] + center_vertices[1]) / 2, axis=0
                )
            cpar = CLCSParams(
                eps2=eps,
                resampling=ResamplingParams(
                    fixed_step=max_polyline_resampling_step, interpolation_type="linear"
                ),
            )
            ccs = CurvilinearCoordinateSystem(center_vertices, cpar, False)
            left = np.array(
                [ccs.convert_to_curvilinear_coords(vert[0], vert[1])[1] for vert in left_vertices]
            )
            right = np.array(
                [ccs.convert_to_curvilinear_coords(vert[0], vert[1])[1] for vert in right_vertices]
            )
            break
        except Exception:
            center_vertices = chaikins_corner_cutting(
                center_vertices, config.chaikins_repeated_refinements
            )
            center_vertices = resample_polyline(center_vertices, config.resampling_repeated_step)
            continue

    # >= since we use the function also for the lanelet2cr conversion where it might be
    # that start/ending vertices of forks/merges match
    return sum(left - right >= 0) / len(left) < config.perc_vert_wrong_side


def has_predecessor(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as predecessor.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as predecessor.
    """
    return lanelet_1.lanelet_id in lanelet_0.predecessor


def has_successor(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as successor.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as successor.
    """
    return lanelet_1.lanelet_id in lanelet_0.successor


def has_traffic_sign(lanelet: Lanelet, traffic_sign: TrafficSign) -> bool:
    """
    Checks whether the lanelet references the traffic sign.

    :param lanelet: Lanelet.
    :param traffic_sign: Traffic sign.
    :return: Boolean indicates whether the lanelet references the traffic sign.
    """
    return traffic_sign.traffic_sign_id in lanelet.traffic_signs


def has_traffic_light(lanelet: Lanelet, traffic_light: TrafficLight) -> bool:
    """
    Checks whether the lanelet references the traffic light.

    :param lanelet: Lanelet.
    :param traffic_light: Traffic light.
    :return: Boolean indicates whether the lanelet references the traffic light.
    """
    return traffic_light.traffic_light_id in lanelet.traffic_lights


def is_polylines_intersection(polyline_0: np.ndarray, polyline_1: np.ndarray) -> bool:
    """
    Checks whether two polylines intersect each other.

    :param polyline_0: First polyline.
    :param polyline_1: Second lanelet.
    :return: Boolean indicates whether two polylines intersect each other.
    """
    line_0 = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline_0]
    line_1 = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline_1]

    line_string_0 = LineString(line_0)
    line_string_1 = LineString(line_1)

    result = line_string_0.intersection(line_string_1)

    return not result.is_empty


def is_polyline_self_intersection(polyline: np.ndarray):
    """
    Checks whether the polyline intersects itself.

    :param polyline: Polyline.
    :return: Boolean indicates whether the polyline intersects itself.
    """
    line = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline]
    orientation = compute_orientation_from_polyline(
        polyline[:, :2]
    )  # function does not support 3d vertices
    orientation_dif = [
        abs(orientation[i + 1] - orientation[i]) for i in range(len(orientation) - 1)
    ]
    line_string = LineString(line)

    # shapely does not detect all cases of self-intersections:
    # second check: twice the same element
    # third check: 180 degree orientation change of line; visually line is perfect
    return (
        not line_string.is_simple
        or Counter(line).most_common(1)[0][1] > 1
        or np.isclose(np.max(orientation_dif), np.pi)
    )


def are_equal_vertices(vertex_0: np.ndarray, vertex_1: np.ndarray) -> bool:
    """
    Checks whether two vertices are equal.

    :param vertex_0: First vertex.
    :param vertex_1: Second vertex.
    :return: Boolean indicates whether two vertices are equal.
    """
    return np.linalg.norm(vertex_0 - vertex_1) < 1e-5  # TODO: Support config threshold


def are_intersected_lanelets(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first and the second lanelet intersect each other.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first and the second lanelet intersect each other.
    """
    result = lanelet_0.polygon.shapely_object.intersection(lanelet_1.polygon.shapely_object)

    return result.is_empty


def has_stop_line(lanelet: Lanelet):
    """
    Checks whether the lanelet has a stop line.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a stop line
    """
    return lanelet.stop_line is not None


def has_start_point(stop_line: StopLine) -> bool:
    """
    Checks whether the stop line has a start point.

    :param stop_line: Stop line.
    :return: Boolean indicates whether the stop line has a start point.
    """
    return stop_line.start is not None


def has_end_point(stop_line: StopLine) -> bool:
    """
    Checks whether the stop line has an end point.

    :param stop_line: Stop line.
    :return: Boolean indicates whether the stop line has an end point.
    """
    return stop_line.end is not None


def are_similar_polylines(polyline_0: np.ndarray, polyline_1: np.ndarray) -> bool:
    """
    Checks the similarity of two polylines.

    :param polyline_0: First polyline symbol.
    :param polyline_1: Second polyline symbol.
    :return: Boolean symbol indicates whether the two polylines are similar.
    """
    # initial or final vertices are not similar
    if not (
        (np.linalg.norm(polyline_0[0] - polyline_1[0]) < 1)
        and (np.linalg.norm((polyline_0[-1] - polyline_1[-1]) < 1))
        or (
            (np.linalg.norm(polyline_0[0] - polyline_1[-1]) < 1)
            and (np.linalg.norm(polyline_0[-1] - polyline_1[0]) < 1)
        )
    ):
        return False
    # length is completely different
    if (
        Lanelet._compute_polyline_cumsum_dist([polyline_0])[-1]
        - Lanelet._compute_polyline_cumsum_dist([polyline_1])[-1]
        > 50
    ):
        return False
    # all vertices are quite close
    if polyline_0.shape[0] == polyline_1.shape[0] and all(
        [dist < 0.01 for dist in np.linalg.norm(polyline_0 - polyline_1, axis=1)]
    ):
        return True
    return similaritymeasures.frechet_dist(polyline_0, polyline_1) < 1e-6
    # TODO: Use thresh of config and update parameter above in this function


def is_adj_type(lanelet: Lanelet, adj: Lanelet, exp_adj_type: str) -> bool:
    """
    Identifies the type of adjacency of lanelet. The types include parallel, merging, and forking adjacencies.

    :param lanelet: Lanelet.
    :param adj: Adjacency.
    :param exp_adj_type: Expected adjacent type.
    :return: Boolean indicates whether the expected adjacent type is equal to the computed type.
    """
    parallel, merging, forking = "parallel", "merging", "forking"

    is_left = lanelet.adj_left == adj.lanelet_id

    if is_left:
        is_same_dir = lanelet.adj_left_same_direction
    else:
        is_same_dir = lanelet.adj_right_same_direction

    if not is_same_dir:
        return parallel == exp_adj_type

    if is_left:  # TODO: Shift part to utils script to avoid duplications
        adj_poly = adj.right_vertices
    else:
        adj_poly = adj.left_vertices

    left_poly = lanelet.left_vertices
    right_poly = lanelet.right_vertices

    adj_size = len(adj_poly)
    lan_size = len(left_poly)

    left_start_dist = np.linalg.norm(left_poly[0] - adj_poly[0])
    left_end_dist = np.linalg.norm(left_poly[lan_size - 1] - adj_poly[adj_size - 1])

    right_start_dist = np.linalg.norm(right_poly[0] - adj_poly[0])
    right_end_dist = np.linalg.norm(right_poly[lan_size - 1] - adj_poly[adj_size - 1])

    if left_start_dist > right_start_dist and left_end_dist < right_end_dist:
        adj_type = forking if is_left else merging
    elif left_start_dist < right_start_dist and left_end_dist > right_end_dist:
        adj_type = merging if is_left else forking
    else:
        adj_type = parallel

    return adj_type == exp_adj_type

--------------------------------------------------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\hol\functions\term_functions\builtin_functions.py
from typing import Any

import numpy as np


def size(vals: Any) -> int:
    """
    Returns the size.

    :param vals: Values.
    :return: Size.
    """
    return len(vals) if vals is not None else 0


def index(vals: Any, i: int) -> Any:
    """
    Gets the element at index.

    :param vals: Values.
    :param i: Index.
    :return: Element at index.
    """
    return vals[i]


def reverse(vals: Any):
    """
    Reverse the sequence of elements.

    :param vals: Values.
    :return: Reversed values.
    """
    return np.flipud(vals)

------------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\hol\functions\predicates\builtin_predicates.py
from typing import Any, Iterable

from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign


def equal(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is equal to the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is equal to the second value.
    """
    return val_0 == val_1


def unequal(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is unequal to the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is unequal to the second value.
    """
    if (
        isinstance(val_0, Lanelet)
        or isinstance(val_0, TrafficSign)
        or isinstance(val_0, TrafficLight)
    ):
        return val_0 is not val_1
    else:
        return val_0 != val_1


def less(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is less than the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first values is less than the second value.
    """
    return val_0 < val_1


def greater(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is greater than the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is greater than the second value.
    """
    return val_0 > val_1


def less_equal(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is less than or equal to the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is less than or equal to the second value.
    """
    return val_0 <= val_1


def greater_equal(val_0: Any, val_1: Any) -> bool:
    """
    Checks whether the first value is greater than or equal to the second value.

    :param val_0: First value.
    :param val_1: Second value.
    :return: Boolean indicates whether the first value is greater than or equal to the second value.
    """
    return val_0 >= val_1


def contains(vals: Iterable[Any], val: Any) -> bool:
    """
    Checks whether value is contained by a set of values.

    :param vals: Values.
    :param val: Value.
    :return: Boolean indicates whether the value is contained by a set of values.
    """
    return val in vals

-----------------------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\hol\formula_manager.py
import warnings
from typing import Any, Dict, List, Set

from crdesigner.verification_repairing.verification.hol.formula import Formula
from crdesigner.verification_repairing.verification.hol.formula_collection import (
    GeneralFormulas,
    IntersectionFormulas,
    LaneletFormulas,
    TrafficLightFormulas,
    TrafficSignFormulas,
)
from crdesigner.verification_repairing.verification.hol.parser.parser import Parser


class FormulaManager:
    """
    Class representing the management of formulas.
    """

    def __init__(self):
        """
        Constructor.
        """
        self._formulas = []
        self._domains = {}

        self._collect_formulas()

    @property
    def formulas(self) -> List[Formula]:
        return self._formulas

    @formulas.setter
    def formulas(self, formulas: List[Formula]):
        self._formulas = formulas

    @property
    def domains(self) -> Dict[str, Set[Any]]:
        return self._domains

    @domains.setter
    def domains(self, domains: Dict[str, Set[Any]]):
        self._domains = domains

    def add_formula(self, formula: Formula):
        """
        Adds a formula. A formula is not stored if a formula with the same ID is already contained.

        :param formula: Formula.
        """
        for f in self._formulas:
            if f.formula_id == formula.formula_id:
                warnings.warn("Formula with ID {} is already stored!".format(formula.formula_id))
                return
        self._formulas.append(formula)

    def add_domain(self, domain_id: str, values: Set[Any]):
        """
        Adds a domain. A domain is not stored if a domain with the same ID is already contained.

        :param domain_id: Domain ID.
        :param values: Values.
        """
        if domain_id in self._domains.keys():
            warnings.warn("Domain with ID {} is already stored!".format(domain_id))
            return
        self._domains[domain_id] = values

    def _collect_formulas(self):
        for collection in [
            TrafficLightFormulas,
            TrafficSignFormulas,
            IntersectionFormulas,
            LaneletFormulas,
            GeneralFormulas,
        ]:
            for formula_id, formula in collection.formulas.items():
                for subformula_id, subformula in collection.subformulas.items():
                    formula = formula.replace(subformula_id, subformula)
                self._formulas.append(Parser.parse(formula, formula_id))

            for domain_id, values in collection.domains.items():
                self._domains[domain_id] = set(values)

------------------------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\formula_ids.py
import enum
from typing import List, Union

# All supported formulas are listed here. The formulas are divided into different types depending on the
# type of the CommonRoad element.


@enum.unique
class GeneralFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of all types of elements."""

    UNIQUE_ID = "unique_id_all"


@enum.unique
class LaneletFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of a lanelet."""

    UNIQUE_ID = "unique_id_la"
    SAME_VERTICES_SIZE = "same_vertices_size"
    VERTICES_MORE_THAN_ONE = "vertices_more_than_one"
    EXISTENCE_LEFT_ADJ = "existence_left_adj"
    EXISTENCE_RIGHT_ADJ = "existence_right_adj"
    EXISTENCE_PREDECESSOR = "existence_predecessor"
    EXISTENCE_SUCCESSOR = "existence_successor"
    CONNECTIONS_PREDECESSOR = "connections_predecessor"
    CONNECTIONS_SUCCESSOR = "connections_successor"
    POLYLINES_LEFT_SAME_DIR_PARALLEL_ADJ = "polylines_left_same_dir_parallel_adj"
    POLYLINES_LEFT_OPPOSITE_DIR_PARALLEL_ADJ = "polylines_left_opposite_dir_parallel_adj"
    POLYLINES_RIGHT_SAME_DIR_PARALLEL_ADJ = "polylines_right_same_dir_parallel_adj"
    POLYLINES_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ = "polylines_right_opposite_dir_parallel_adj"
    CONNECTIONS_LEFT_MERGING = "connections_left_merging_adj"
    CONNECTIONS_RIGHT_MERGING = "connections_right_merging_adj"
    CONNECTIONS_LEFT_FORKING = "connections_left_forking_adj"
    CONNECTIONS_RIGHT_FORKING = "connections_right_forking_adj"
    POTENTIAL_SUCCESSOR = "potential_successor"
    POTENTIAL_PREDECESSOR = "potential_predecessor"
    POTENTIAL_LEFT_SAME_DIR_PARALLEL_ADJ = "potential_left_same_dir_parallel_adj"
    POTENTIAL_LEFT_OPPOSITE_DIR_PARALLEL_ADJ = "potential_left_opposite_dir_parallel_adj"
    POTENTIAL_RIGHT_SAME_DIR_PARALLEL_ADJ = "potential_right_same_dir_parallel_adj"
    POTENTIAL_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ = "potential_right_opposite_dir_parallel_adj"
    POTENTIAL_LEFT_MERGING_ADJ = "potential_left_merging_adj"
    POTENTIAL_RIGHT_MERGING_ADJ = "potential_right_merging_adj"
    POTENTIAL_LEFT_FORKING_ADJ = "potential_left_forking_adj"
    POTENTIAL_RIGHT_FORKING_ADJ = "potential_right_forking_adj"
    NON_PREDECESSOR_AS_SUCCESSOR = "non_predecessor_as_successor"
    NON_SUCCESSOR_AS_PREDECESSOR = "non_successor_as_predecessor"
    POLYLINES_INTERSECTION = "polylines_intersection"
    LEFT_SELF_INTERSECTION = "left_self_intersection"
    RIGHT_SELF_INTERSECTION = "right_self_intersection"
    LANELET_TYPES_COMBINATION = "lanelet_types_combination"
    # NON_FOLLOWED_COMPOSABLE_LANELETS = 'non_followed_composable_lanelets'
    # REFERENCED_INTERSECTING_LANELETS = 'referenced_intersecting_lanelets'
    EXISTENCE_TRAFFIC_SIGNS = "existence_traffic_signs"
    EXISTENCE_TRAFFIC_LIGHTS = "existence_traffic_lights"
    EXISTENCE_STOP_LINE_TRAFFIC_SIGNS = "existence_stop_line_traffic_signs"
    EXISTENCE_STOP_LINE_TRAFFIC_LIGHTS = "existence_stop_line_traffic_lights"
    INCLUDED_STOP_LINE_TRAFFIC_SIGNS = "included_stop_line_traffic_signs"
    INCLUDED_STOP_LINE_TRAFFIC_LIGHTS = "included_stop_line_traffic_lights"
    ZERO_OR_TWO_POINTS_STOP_LINE = "zero_or_two_points_stop_line"
    STOP_LINE_POINTS_ON_POLYLINES = "stop_line_points_on_polylines"
    STOP_LINE_REFERENCES = "stop_line_references"
    CONFLICTING_LANELET_DIRECTIONS = "conflicting_lanelet_directions"
    LEFT_RIGHT_BOUNDARY_ASSIGNMENT = "left_right_boundary_assignment"


@enum.unique
class TrafficSignFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of a traffic sign."""

    AT_LEAST_ONE_TRAFFIC_SIGN_ELEMENT = "at_least_one_traffic_sign_element"
    REFERENCED_TRAFFIC_SIGN = "referenced_traffic_sign"
    GIVEN_ADDITIONAL_VALUE = "given_additional_value"
    VALUE_ADDITIONAL_VALUE_SPEED_SIGN = "valid_additional_value_speed_sign"
    MAXIMAL_DISTANCE_FROM_LANELET = "maximal_distance_from_lanelet"


@enum.unique
class TrafficLightFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of a traffic light."""

    AT_LEAST_ONE_CYCLE_ELEMENT = "at_least_one_cycle_element"
    # TRAFFIC_LIGHT_PER_INCOMING = 'traffic_light_per_incoming'
    REFERENCED_TRAFFIC_LIGHT = "referenced_traffic_light"
    NON_ZERO_DURATION = "non_zero_duration"
    UNIQUE_STATE_IN_CYCLE = "unique_state_in_cycle"
    CYCLE_STATE_COMBINATIONS = "cycle_state_combinations"
    # EXISTENCE_OUTGOING_RIGHT = 'existence_outgoing_right'
    # EXISTENCE_OUTGOING_STRAIGHT = 'existence_outgoing_straight'
    # EXISTENCE_OUTGOING_LEFT = 'existence_outgoing_left'


@enum.unique
class IntersectionFormulaID(enum.Enum):
    """The IDs of formulas that describe the properties of an intersection."""

    AT_LEAST_TWO_INCOMING_ELEMENTS = "at_least_two_incoming_elements"
    AT_LEAST_ONE_INCOMING_LANELET = "at_least_one_incoming_lanelet"
    EXISTENCE_IS_LEFT_OF = "existence_is_left_of"
    EXISTENCE_INCOMING_LANELETS = "existence_incoming_lanelets"
    INCOMING_INTERSECTION = "incoming_intersection"


FormulaID = Union[
    LaneletFormulaID,
    TrafficSignFormulaID,
    TrafficLightFormulaID,
    IntersectionFormulaID,
    GeneralFormulaID,
]
FormulaTypes = [
    LaneletFormulaID,
    TrafficSignFormulaID,
    TrafficLightFormulaID,
    IntersectionFormulaID,
    GeneralFormulaID,
]


def extract_formula_id(string: str) -> Union[None, FormulaID]:
    """
    Extracts ID of formula from string.

    :param string: String.
    :return: Formula ID; none if the string cannot be matched.
    """
    for formula_id in extract_formula_ids():
        if formula_id.value == string:
            return formula_id

    return None


def extract_formula_ids() -> List[FormulaID]:
    """
    Extracts all formula IDs.

    :return: Formula IDs.
    """
    formula_ids = []
    for formula_id_type in FormulaTypes:
        for formula_id in formula_id_type:
            formula_ids.append(formula_id)

    return formula_ids


def extract_formula_ids_from_strings(strings: List[str]) -> List[FormulaID]:
    """
    Extracts IDs of formulas from strings.

    :param strings: Strings.
    :return: Formula IDs.
    """
    ids = []

    for formula_id in extract_formula_ids():
        if formula_id.value in strings:
            ids.append(formula_id)

    return ids


def extract_formula_ids_by_type(formula_type: enum.EnumMeta) -> List[FormulaID]:
    """
    Extracts all IDs of formulas from a specific type.

    :param formula_type: Formula type.
    :return: Formula IDs of formula type.
    """
    formula_ids_of_type = []
    for formula_id_of_type in formula_type:
        formula_ids_of_type.append(formula_id_of_type)

    return formula_ids_of_type


def filter_formula_ids_by_type(
    formula_ids: List[FormulaID], formula_type: enum.EnumMeta
) -> List[FormulaID]:
    """
    Filters the IDs of formulas by a specific formula type.

    :param formula_ids: Formula IDs.
    :param formula_type: Formula type.
    :return: Formula IDs.
    """
    formula_ids_of_type = extract_formula_ids_by_type(formula_type)

    return list(set(formula_ids).intersection(set(formula_ids_of_type)))

----------------------------------------------------------------------------------

crdesigner\verification_repairing\verification\groups_handler.py
import dataclasses
from queue import PriorityQueue
from typing import List

from crdesigner.verification_repairing.verification.formula_ids import (
    FormulaID,
    GeneralFormulaID,
    IntersectionFormulaID,
    LaneletFormulaID,
    TrafficLightFormulaID,
    TrafficSignFormulaID,
)


@dataclasses.dataclass
class SpecificationGroup:
    priority: int
    formulas: List[FormulaID]


@dataclasses.dataclass
class GroupsHandler:
    """Class representing the handler of the specification groups."""

    groups: List[SpecificationGroup] = dataclasses.field(
        default_factory=lambda: [
            SpecificationGroup(
                priority=0,
                formulas=[
                    LaneletFormulaID.LEFT_RIGHT_BOUNDARY_ASSIGNMENT,
                    GeneralFormulaID.UNIQUE_ID,
                ],
            ),
            SpecificationGroup(
                priority=1,
                formulas=[
                    LaneletFormulaID.POLYLINES_INTERSECTION,
                    LaneletFormulaID.LEFT_SELF_INTERSECTION,
                    LaneletFormulaID.RIGHT_SELF_INTERSECTION,
                ],
            ),
            SpecificationGroup(
                priority=2,
                formulas=[
                    LaneletFormulaID.SAME_VERTICES_SIZE,
                    LaneletFormulaID.VERTICES_MORE_THAN_ONE,
                    TrafficLightFormulaID.AT_LEAST_ONE_CYCLE_ELEMENT,
                    IntersectionFormulaID.AT_LEAST_ONE_INCOMING_LANELET,
                    TrafficSignFormulaID.AT_LEAST_ONE_TRAFFIC_SIGN_ELEMENT,
                    LaneletFormulaID.STOP_LINE_REFERENCES,
                    LaneletFormulaID.CONFLICTING_LANELET_DIRECTIONS,
                ],
            ),
            SpecificationGroup(
                priority=15,
                formulas=[
                    LaneletFormulaID.EXISTENCE_SUCCESSOR,
                    LaneletFormulaID.EXISTENCE_PREDECESSOR,
                    LaneletFormulaID.EXISTENCE_LEFT_ADJ,
                    LaneletFormulaID.EXISTENCE_RIGHT_ADJ,
                    LaneletFormulaID.POTENTIAL_SUCCESSOR,
                    LaneletFormulaID.POTENTIAL_PREDECESSOR,
                    LaneletFormulaID.POTENTIAL_LEFT_SAME_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POTENTIAL_LEFT_OPPOSITE_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POTENTIAL_RIGHT_SAME_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POTENTIAL_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POTENTIAL_LEFT_MERGING_ADJ,
                    LaneletFormulaID.POTENTIAL_RIGHT_MERGING_ADJ,
                    LaneletFormulaID.POTENTIAL_LEFT_FORKING_ADJ,
                    LaneletFormulaID.POTENTIAL_RIGHT_FORKING_ADJ,
                    LaneletFormulaID.NON_PREDECESSOR_AS_SUCCESSOR,
                    LaneletFormulaID.NON_SUCCESSOR_AS_PREDECESSOR,
                    LaneletFormulaID.EXISTENCE_TRAFFIC_SIGNS,
                    LaneletFormulaID.EXISTENCE_TRAFFIC_LIGHTS,
                    LaneletFormulaID.EXISTENCE_STOP_LINE_TRAFFIC_SIGNS,
                    LaneletFormulaID.EXISTENCE_STOP_LINE_TRAFFIC_LIGHTS,
                    IntersectionFormulaID.EXISTENCE_IS_LEFT_OF,
                    IntersectionFormulaID.EXISTENCE_INCOMING_LANELETS,
                    IntersectionFormulaID.AT_LEAST_TWO_INCOMING_ELEMENTS,
                ],
            ),
            SpecificationGroup(
                priority=20,
                formulas=[
                    LaneletFormulaID.CONNECTIONS_SUCCESSOR,
                    LaneletFormulaID.CONNECTIONS_PREDECESSOR,
                    LaneletFormulaID.POLYLINES_LEFT_SAME_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POLYLINES_LEFT_OPPOSITE_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POLYLINES_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.POLYLINES_RIGHT_SAME_DIR_PARALLEL_ADJ,
                    LaneletFormulaID.CONNECTIONS_LEFT_MERGING,
                    LaneletFormulaID.CONNECTIONS_RIGHT_MERGING,
                    LaneletFormulaID.CONNECTIONS_LEFT_FORKING,
                    LaneletFormulaID.CONNECTIONS_RIGHT_FORKING,
                    LaneletFormulaID.LANELET_TYPES_COMBINATION,
                    LaneletFormulaID.INCLUDED_STOP_LINE_TRAFFIC_SIGNS,
                    LaneletFormulaID.INCLUDED_STOP_LINE_TRAFFIC_LIGHTS,
                    LaneletFormulaID.ZERO_OR_TWO_POINTS_STOP_LINE,
                    LaneletFormulaID.STOP_LINE_POINTS_ON_POLYLINES,
                    TrafficSignFormulaID.GIVEN_ADDITIONAL_VALUE,
                    TrafficSignFormulaID.VALUE_ADDITIONAL_VALUE_SPEED_SIGN,
                    TrafficSignFormulaID.MAXIMAL_DISTANCE_FROM_LANELET,
                    TrafficLightFormulaID.NON_ZERO_DURATION,
                    TrafficLightFormulaID.UNIQUE_STATE_IN_CYCLE,
                    TrafficLightFormulaID.CYCLE_STATE_COMBINATIONS,
                    IntersectionFormulaID.INCOMING_INTERSECTION,
                ],
            ),
        ]
    )

    _queue: PriorityQueue = dataclasses.field(default_factory=PriorityQueue)

    def __post_init__(self):
        # Builds the queue containing the specification groups ordered by their priorities.
        for group in self.groups:
            self._queue.put((group.priority, group.formulas))

    def is_next_group(self) -> bool:
        """
        Checks whether a further group is contained by the queue.

        :return: Boolean indicates whether a further group is contained.
        """
        return self._queue.qsize() != 0

    def next_group(self) -> List[FormulaID]:
        """
        Returns the next group with the highest order in the current queue.

        :return: Group of formula IDs.
        """
        return self._queue.get()[1]

----------------------------------------------------
END OF FILES