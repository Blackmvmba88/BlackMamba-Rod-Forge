from __future__ import annotations

from collections import defaultdict, deque

from .schemas import ProjectState, Task, TaskStatus


class DependencyError(RuntimeError):
    pass


class PartGraph:
    def __init__(self, tasks: dict[str, Task]):
        self.tasks = tasks
        self._validate_references()
        self._validate_acyclic()

    def _validate_references(self) -> None:
        known = set(self.tasks)
        missing: dict[str, list[str]] = {}
        for task in self.tasks.values():
            unknown = [dep for dep in task.dependencies if dep not in known]
            if unknown:
                missing[task.task_id] = unknown
        if missing:
            raise DependencyError(f"Unknown dependencies: {missing}")

    def _validate_acyclic(self) -> None:
        indegree = {task_id: 0 for task_id in self.tasks}
        dependents: dict[str, list[str]] = defaultdict(list)
        for task in self.tasks.values():
            for dep in task.dependencies:
                indegree[task.task_id] += 1
                dependents[dep].append(task.task_id)

        queue = deque(task_id for task_id, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for child in dependents[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(self.tasks):
            raise DependencyError("Task graph contains a cycle")

    def dependencies_satisfied(self, task: Task) -> bool:
        return all(self.tasks[dep].status == TaskStatus.COMPLETED for dep in task.dependencies)

    def next_viable(self, state: ProjectState) -> Task | None:
        for task in state.tasks.values():
            if task.status in {TaskStatus.PENDING, TaskStatus.READY, TaskStatus.NEEDS_REPAIR}:
                if self.dependencies_satisfied(task):
                    task.status = TaskStatus.READY
                    return task
        return None

    def unresolved_critical(self) -> list[Task]:
        return [
            task for task in self.tasks.values()
            if task.is_critical and task.status in {TaskStatus.FAILED, TaskStatus.BLOCKED}
        ]
