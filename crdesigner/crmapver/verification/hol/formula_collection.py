from typing import Dict


class GeneralFormulas:
    formulas: Dict[str, str] = {'unique_id_all': '!(E k2 in M. (k1 != k2 & el_id(k1) = el_id(k2))) || k1 in M'}
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {}


class LaneletFormulas:
    formulas: Dict[str, str] = {'unique_id_la': 'A l2 in L. (l1 != l2 -> lanelet_id(l1) != lanelet_id(l2)) || l1 in L',

                                'same_vertices_size': 'size(left_polyline(l)) = size(right_polyline(l)) || l in L',

                                'vertices_more_than_one': '(size(left_polyline(l)) > 1 & size(right_polyline(l)) > 1) '
                                                          '|| l in L',

                                'existence_left_adj': '(Has_left_adj_ref(l1)) -> E l2 in L. (Has_left_adj(l1, '
                                                      'l2)) || l1 in L',

                                'existence_right_adj': '(Has_right_adj_ref(l1)) -> E l2 in L. (Has_right_adj(l1, '
                                                       'l2)) || l1 in L',

                                'existence_predecessor': 'E l2 in L. (lanelet_id(l2) = p_id) || l1 in L, '
                                                         'p_id in predecessors(l1)',

                                'existence_successor': 'E l2 in L. (lanelet_id(l2) = s_id) || l1 in L, '
                                                       's_id in successors(l1)',

                                'polylines_intersection': '!(Is_polylines_intersection(left_polyline(l), '
                                                          'right_polyline(l))) || l in L',

                                'left_self_intersection': '!(Is_polyline_self_intersection(left_polyline(l))) || l in'
                                                          ' L',

                                'right_self_intersection': '!(Is_polyline_self_intersection(right_polyline(l))) || l '
                                                           'in L',

                                'connections_predecessor': '(Has_predecessor(l1, l2)) -> are_predecessor_connections('
                                                           'l1, l2) || l1, l2 in L',

                                'connections_successor': '(Has_successor(l1, l2)) -> are_successor_connections(l1, '
                                                         'l2) || l1, l2 in L',

                                'potential_predecessor': '(!(Has_predecessor(l1, l2))) -> !('
                                                         'are_predecessor_connections(l1, l2)) || l1, '
                                                         'l2 in L',

                                'potential_successor': '(!(Has_successor(l1, l2))) -> !(are_successor_connections(l1,'
                                                       ' l2)) || l1, l2 in L',

                                'non_predecessor_as_successor': '(lanelet_id(l1) != lanelet_id(l2) & Has_successor(l1, '
                                                                'l2) & !(Has_predecessor(l1, l2))) -> !('
                                                                'are_predecessor_connections(l1, '
                                                                'l2)) || l1, l2 in L',

                                'non_successor_as_predecessor': '(lanelet_id(l1) != lanelet_id(l2) & '
                                                                'Has_predecessor(l1, l2) & !(Has_successor(l1, '
                                                                'l2))) -> !('
                                                                'are_successor_connections(l1, l2)) || l1, l2 in L',

                                'referenced_intersecting_lanelets': '(Are_intersected_lanelets(l1, '
                                                                    'l2)) -> (Has_left_adj(l1, '
                                                                    'l2) | Has_right_adj(l1, l2) | Has_predecessor('
                                                                    'l1, l2) | Has_successor('
                                                                    'l1, l2)) || l1, l2 in L',

                                'existence_traffic_signs': 'E t in TS. (traffic_sign_id(t) = t_id) || l in L, '
                                                           't_id in traffic_signs(l)',

                                'existence_traffic_lights': 'E t in TL. (traffic_light_id(t) = t_id) || l in L, '
                                                            't_id in traffic_lights(l)',

                                'zero_or_two_points_stop_line': '(Has_stop_line(l)) -> (Has_start_point(stop_line(l)) '
                                                                '<-> Has_end_point('
                                                                'stop_line(l))) || l in L',

                                'polylines_left_same_dir_parallel_adj': '(Has_left_adj(l1, l2) & Is_adj_type(l1, l2, '
                                                                        '"parallel") & '
                                                                        'Is_left_adj_same_direction(l1)) -> '
                                                                        'Are_similar_polylines('
                                                                        'left_polyline(l1), right_polyline(l2)) || '
                                                                        'l1, l2 in L',

                                'polylines_right_same_dir_parallel_adj': '(Has_right_adj(l1, l2) & Is_adj_type(l1, '
                                                                         'l2, "parallel") & '
                                                                         'Is_right_adj_same_direction(l1)) -> '
                                                                         'Are_similar_polylines('
                                                                         'right_polyline(l1), left_polyline(l2)) || '
                                                                         'l1, l2 in L',

                                'polylines_left_opposite_dir_parallel_adj': '(Has_left_adj(l1, l2) & Is_adj_type(l1, '
                                                                            'l2, "parallel") & !('
                                                                            'Is_left_adj_same_direction(l1))) -> '
                                                                            'Are_similar_polylines('
                                                                            'reverse(left_polyline(l1)), '
                                                                            'left_polyline(l2)) || l1, l2 in L',

                                'polylines_right_opposite_dir_parallel_adj': '(Has_right_adj(l1, '
                                                                             'l2) & Is_adj_type(l1, l2, "parallel") & '
                                                                             '!('
                                                                             'Is_right_adj_same_direction(l1))) -> '
                                                                             'Are_similar_polylines('
                                                                             'reverse(right_polyline(l1)), '
                                                                             'right_polyline(l2)) || l1, l2 in L',

                                'potential_left_same_dir_parallel_adj': '(Are_similar_polylines('
                                                                        'left_polyline(l1), right_polyline(l2))) -> ('
                                                                        'Has_left_adj(l1, '
                                                                        'l2) & Is_adj_type(l1, l2, "parallel") & '
                                                                        'Is_left_adj_same_direction('
                                                                        'l1)) || l1, l2 in L',

                                'potential_right_same_dir_parallel_adj': '(Are_similar_polylines('
                                                                         'right_polyline(l1), left_polyline(l2))) -> '
                                                                         '(Has_right_adj(l1, '
                                                                         'l2) & Is_adj_type(l1, l2, "parallel") & '
                                                                         'Is_right_adj_same_direction(l1)) || l1, '
                                                                         'l2 in L',

                                'potential_left_opposite_dir_parallel_adj': '(Are_similar_polylines('
                                                                            'reverse(left_polyline(l1)), '
                                                                            'left_polyline(l2))) -> ('
                                                                            'Has_left_adj(l1, l2) & Is_adj_type(l1, '
                                                                            'l2, "parallel") & !('
                                                                            'Is_left_adj_same_direction(l1))) || l1, '
                                                                            'l2 in L',

                                'potential_right_opposite_dir_parallel_adj': '(Are_similar_polylines('
                                                                             'reverse(right_polyline(l1)), '
                                                                             'right_polyline(l2))) -> ('
                                                                             'Has_right_adj(l1, l2) & Is_adj_type(l1, '
                                                                             'l2, "parallel") & !('
                                                                             'Is_right_adj_same_direction(l1))) || '
                                                                             'l1, l2 in L',

                                'connections_left_merging_adj': '(Has_left_adj(l1, l2) & Is_adj_type(l1, '
                                                                'l2, "merging")) -> are_left_merging_adj_connections('
                                                                'l1, l2) || l1, l2 in L',

                                'connections_right_merging_adj': '(Has_right_adj(l1, l2) & Is_adj_type(l1, '
                                                                 'l2, "merging")) -> '
                                                                 'are_right_merging_adj_connections(l1, l2) || l1, '
                                                                 'l2 in L',

                                'potential_left_merging_adj': '(are_left_merging_adj_connections(l1, '
                                                              'l2)) -> (Has_left_adj(l1, l2) & Is_adj_type(l1, l2, '
                                                              '"merging")) || l1, l2 in L',

                                'potential_right_merging_adj': '(are_right_merging_adj_connections(l1, '
                                                               'l2)) -> (Has_right_adj(l1, l2) & Is_adj_type(l1, l2, '
                                                               '"merging")) || l1, '
                                                               'l2 in L',

                                'connections_left_forking_adj': '(Has_left_adj(l1, l2) & Is_adj_type(l1, '
                                                                'l2, "forking")) -> are_left_forking_adj_connections('
                                                                'l1, l2) || l1, l2 in L',

                                'connections_right_forking_adj': '(Has_right_adj(l1, l2) & Is_adj_type(l1, '
                                                                 'l2, "forking")) -> '
                                                                 'are_right_forking_adj_connections(l1, l2) || l1, '
                                                                 'l2 in L',

                                'potential_left_forking_adj': '(are_left_forking_adj_connections(l1, '
                                                              'l2)) -> (Has_left_adj(l1, l2) & Is_adj_type(l1, l2, '
                                                              '"forking")) || l1, l2 in L',

                                'potential_right_forking_adj': '(are_right_forking_adj_connections(l1, '
                                                               'l2)) -> (Has_right_adj(l1, l2) & Is_adj_type(l1, l2, '
                                                               '"forking")) || l1, '
                                                               'l2 in L',

                                'included_stop_line_traffic_signs': '(Has_stop_line(l)) -> (A s_id1 in '
                                                                    'stop_line_traffic_signs(stop_line(l)). '
                                                                    '(traffic_sign_id(s) = s_id1 -> E s_id2 in '
                                                                    'traffic_signs(l). s_id1 = '
                                                                    's_id2)) || l in L, s in TS',

                                'included_stop_line_traffic_lights': '(Has_stop_line(l)) -> (A t_id1 in '
                                                                     'stop_line_traffic_lights(stop_line('
                                                                     'l)). (traffic_light_id(t) = t_id1 -> E t_id2 in '
                                                                     'traffic_lights(l). '
                                                                     't_id1 = t_id2)) || l in L, t in TL'}
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {
        'are_predecessor_connections(l1, l2)': 'Are_equal_vertices(start_vertex(left_polyline(l1)), end_vertex('
                                               'left_polyline(l2))) & Are_equal_vertices(start_vertex(right_polyline('
                                               'l1)), end_vertex(right_polyline(l2)))',

        'are_successor_connections(l1, l2)': 'Are_equal_vertices(end_vertex(left_polyline(l1)), start_vertex('
                                             'left_polyline(l2))) & Are_equal_vertices(end_vertex(right_polyline('
                                             'l1)), start_vertex(right_polyline(l2)))',

        'are_left_merging_adj_connections(l1, l2)': 'Are_equal_vertices(end_vertex(left_polyline(l1)), end_vertex('
                                                    'left_polyline(l2))) & Are_equal_vertices(end_vertex('
                                                    'right_polyline(l1)), end_vertex(right_polyline(l2))) & '
                                                    'Are_equal_vertices(start_vertex(left_polyline(l1)), '
                                                    'start_vertex(right_polyline(l2)))',

        'are_right_merging_adj_connections(l1, l2)': 'Are_equal_vertices(end_vertex(left_polyline(l1)), end_vertex('
                                                     'left_polyline(l2))) & Are_equal_vertices(end_vertex('
                                                     'right_polyline(l1)), end_vertex(right_polyline(l2))) & '
                                                     'Are_equal_vertices(start_vertex(right_polyline(l1)), '
                                                     'start_vertex(left_polyline(l2)))',

        'are_left_forking_adj_connections(l1, l2)': 'Are_equal_vertices(start_vertex(left_polyline(l1)), '
                                                    'start_vertex(left_polyline(l2))) & Are_equal_vertices('
                                                    'start_vertex(right_polyline(l1)), start_vertex(right_polyline('
                                                    'l2))) & Are_equal_vertices(end_vertex(left_polyline(l1)), '
                                                    'end_vertex(right_polyline(l2)))',

        'are_right_forking_adj_connections(l1, l2)': 'Are_equal_vertices(start_vertex(left_polyline(l1)), '
                                                     'start_vertex(left_polyline(l2))) & Are_equal_vertices('
                                                     'start_vertex(right_polyline(l1)), start_vertex(right_polyline('
                                                     'l2))) & Are_equal_vertices(end_vertex(right_polyline(l1)), '
                                                     'end_vertex(left_polyline(l2)))'}


class TrafficSignFormulas:
    formulas: Dict[str, str] = {'unique_id_ts': 'A t2 in TS. (t1 != t2 -> '
                                                'traffic_sign_id(t1) != traffic_sign_id(t2)) || t1 in TS',
                                'at_least_one_traffic_sign_element': 'size(traffic_sign_elements(t)) > 0 || t in TS',

                                'referenced_traffic_sign': 'E l in L. (Has_traffic_sign(l, t)) || t in TS',

                                'maximal_distance_from_lanelet': 'E l in L. (Has_traffic_sign(l, '
                                                                 't) & distance_to_lanelet(t, l) <= 10.0) || t '
                                                                 'in TS'}
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {}


class TrafficLightFormulas:
    formulas: Dict[str, str] = {'unique_id_tl': 'A t2 in TL. (t1 != t2 -> '
                                                'traffic_light_id(t1) != traffic_light_id(t2)) || t1 in TL',
                                'at_least_one_cycle_element': 'size(cycle_elements(t)) > 0 || t in TL',

                                'referenced_traffic_light': 'E l in L. Has_traffic_light(l, t) || t in TL',

                                'traffic_light_per_incoming': '(traffic_light_id(t) = t_id & Has_traffic_light(l1, t) '
                                                              '& Has_traffic_light(l2, t)) -> E i in I, '
                                                              'e in IE. (Has_incoming_element(i, e) '
                                                              '& Has_incoming_lanelet(e, l1) '
                                                              '& Has_incoming_lanelet(e, l2)) '
                                                              '|| t in TS, l1 in L, l2 in L, t_id in traffic_lights('
                                                              'l1)'}
    domains: Dict[str, str] = {}
    subformulas: Dict[str, str] = {}


class IntersectionFormulas:
    formulas: Dict[str, str] = {}
    # formulas: Dict[str, str] = {'unique_id_in': 'A i2 in I. (i1 != i2 -> '
    #                                             'intersection_id(i1) != intersection_id(i2)) || i1 in I',
    #                             'at_least_two_incoming_elements': 'size(incoming_elements(i)) > 1 || i in I',
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
