from typing import Callable, Optional

from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblem, PlanningProblemSet
from PyQt6.QtCore import QObject, pyqtSignal

from crdesigner.common.logging import logger


class PlanningProblemSetModel(QObject):
    """
    This class is a model for the planning set of the scenario.
    :ivar _planing_set_changed: Signal that is emitted when the planning set has changed.
    """

    _planing_set_changed = pyqtSignal(bool)
    new_pps = pyqtSignal()

    def __init__(self, planing_problem_set: PlanningProblemSet = None):
        """Constructor of the planning set model. Initializes the planning set model, but with an empty planning set."""
        super().__init__()
        self._planing_problem_set: Optional[PlanningProblemSet] = planing_problem_set
        self.selected_pp_id: Optional[int] = -1

    @logger.log
    def set_planing_problem_set(self, planing_problem_set: PlanningProblemSet):
        """
        Sets the planning set of the model.
        :param planing_problem_set: The new planning set.
        """
        for pp in planing_problem_set.planning_problem_dict:
            if planing_problem_set.planning_problem_dict[pp].goal.lanelets_of_goal_position is None:
                state_list = planing_problem_set.planning_problem_dict[pp].goal.state_list
                new_gr = GoalRegion(state_list=state_list, lanelets_of_goal_position=dict())
                planing_problem_set.planning_problem_dict[pp].goal = new_gr

        self._planing_problem_set = planing_problem_set
        self.new_pps.emit()

    def get_pps(self) -> PlanningProblemSet:
        """
        Returns the planning set of the model.
        :return: The planning set of the model.
        """
        if self._planing_problem_set is None:
            self._planing_problem_set = PlanningProblemSet()
        return self._planing_problem_set

    def get_pp(self, pp_id: int) -> Optional[PlanningProblem]:
        """
        Returns the planning problem with the given id.
        :param pp_id: The id of the planning problem.
        :return: The planning problem with the given id or None if no planning problem with the given id exists.
        """
        planning_problem_set = self.get_pps()
        if pp_id in planning_problem_set.planning_problem_dict.keys():
            return planning_problem_set.planning_problem_dict[pp_id]
        return None

    def remove_pp(self, pp_id: int) -> None:
        """
        Removes the planning problem with the given id.
        :param pp_id: The id of the planning problem to remove.
        """
        planning_problem_set = self.get_pps()
        planning_problem_set.planning_problem_dict.pop(pp_id)
        self.notify_all()

    def get_selected_pp(self) -> Optional[PlanningProblem]:
        """
        Returns the selected planning problem.
        :return: The selected planning problem or None if no planning problem is selected.
        """
        if self.selected_pp_id == -1:
            return None

        return self.get_pp(self.selected_pp_id)

    def set_selected_pp_id(self, pp_id: int) -> None:
        """
        Sets the selected planning problem id.
        :param pp_id: The id of the planning problem to select.
        """
        self.selected_pp_id = pp_id
        self.notify_all()

    def clear(self):
        """Clears the planning set of the model."""
        self._planing_problem_set = None
        self.notify_all()

    def is_empty(self) -> bool:
        """
        Checks if the planning set is empty.
        :return: True if the planning set is empty, False otherwise.
        """
        return self._planing_problem_set is None

    @logger.log
    def add_planing_problem(self, planing_problem: PlanningProblem):
        """
        Adds a planning problem to the planning set.
        :param planing_problem: The planning problem to add.
        """
        self.get_pps().add_planning_problem(planing_problem)
        self.notify_all()

    def is_position_a_lanelet(self, ppi: int, current_goal_state_id: int) -> bool:
        """
        Checks whether the give id of the goal_state attribute postion is a key in the lanelets_of_goal_position

        :param ppi: ID of the current planning problem
        :param current_goal_state_id: Current id of the goal state
        :returns: Boolean value if it is a position of a lanelet
        """
        if self.get_pp(ppi).goal.lanelets_of_goal_position is not None:
            list_lanelets = self.get_pp(ppi).goal.lanelets_of_goal_position.keys()
            return current_goal_state_id in list_lanelets
        else:
            return False

    @logger.log
    def remove_lanelet_from_goals(self, ppi: int, current_goal_state_id: int) -> None:
        """
        Removes a lanelet from the dict lanelets_of_goal_position

        :param ppi: ID of the current planning problem
        :param current_goal_state_id: Current id of the goal state
        """
        if self.get_pp(ppi).goal.lanelets_of_goal_position is not None:
            if current_goal_state_id in self.get_pp(ppi).goal.lanelets_of_goal_position:
                self.get_pp(ppi).goal.lanelets_of_goal_position.pop(current_goal_state_id)

    def notify_all(self):
        """Notifies all observers of the model."""
        self._planing_set_changed.emit(False)

    def subscribe(self, callback: Callable[[], None]):
        """
        Subscribes a callback function to the model.
        :param callback: The callback function.
        """
        self._planing_set_changed.connect(callback)
