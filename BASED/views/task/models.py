from datetime import date

from pydantic import BaseModel

from BASED.repository.task import DependencyTypeEnum, ShortTask, TaskStatusEnum


class TaskDependency(BaseModel):
    task_id: int
    depends_of_task_id: int


class CreationTaskDependencies(BaseModel):
    type: DependencyTypeEnum
    task_id: int


class TaskBody(BaseModel):
    title: str | None
    description: str | None
    deadline: date
    responsible_user_id: int
    days_for_completion: int
    dependencies: list[CreationTaskDependencies]


class CreateTaskResponse(BaseModel):
    created_task_id: int
    dependency_errors: list[TaskDependency]


class EditTaskBody(BaseModel):
    task_id: int
    task_data: TaskBody


class EditTaskResponse(BaseModel):
    dependency_errors: list[TaskDependency]


class UpdateTaskStatusBody(BaseModel):
    task_id: int
    new_status: TaskStatusEnum


class ListTaskDependency(BaseModel):
    dependencies: list[TaskDependency]


class ArchiveTaskBody(BaseModel):
    task_id: int


class EditTaskDeadlineBody(BaseModel):
    task_id: int
    new_deadline: date


class GetAllTasksResponse(BaseModel):
    tasks: list[ShortTask]
