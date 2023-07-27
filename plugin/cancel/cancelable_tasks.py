from talon import Module, actions
from typing import Callable
possible_canceled_actions = []

mod = Module()
@mod.action_class
class Actions:

    def cancelable_tasks_append(callable: Callable):
        """Append a task that can be canceled"""
        global possible_canceled_tasks
        possible_canceled_actions.append(callable)

    def cancelable_tasks_cancel():
        """Cancel running tasks that have been added to the task callbacks"""
        global possible_canceled_actions
        for callback in possible_canceled_actions:
            callback()