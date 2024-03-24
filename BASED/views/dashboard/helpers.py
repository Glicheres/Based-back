from datetime import date, timedelta

from BASED.conf import TIME_RESERVE_COEF
from BASED.repository.task import Task, TaskStatusEnum, TaskStatusOrder
from BASED.views.dashboard.models import WarningModel, WarningTypeEnum


def get_warnings_list(task: Task) -> list[WarningModel]:
    warnings = []
    current_date = date.today()
    match task.status:
        case TaskStatusEnum.to_do:
            if current_date >= task.deadline - timedelta(
                days=task.days_for_completion
            ):
                warnings.append(
                    WarningModel(
                        type=WarningTypeEnum.start_hard, task_id=task.id
                    )
                )
            elif current_date >= task.deadline - timedelta(
                days=task.days_for_completion * TIME_RESERVE_COEF
            ):
                warnings.append(
                    WarningModel(
                        type=WarningTypeEnum.start_soft, task_id=task.id
                    )
                )
        case TaskStatusEnum.in_progress:
            days_in_work = (current_date - task.actual_start_date).days
            days_to_deadline = task.days_for_completion - days_in_work
            if days_to_deadline < 0:
                days_to_deadline = 0

            if current_date >= task.deadline - timedelta(
                days=days_to_deadline
            ):
                warnings.append(
                    WarningModel(
                        type=WarningTypeEnum.finish_hard, task_id=task.id
                    )
                )
            elif current_date >= task.deadline - timedelta(
                days=days_to_deadline * TIME_RESERVE_COEF
            ):
                warnings.append(
                    WarningModel(
                        type=WarningTypeEnum.finish_soft, task_id=task.id
                    )
                )

    if current_date > task.deadline:
        warnings.append(
            WarningModel(type=WarningTypeEnum.late_deadline, task_id=task.id)
        )

    return warnings


def get_status_order_number(status: TaskStatusEnum) -> int:
    match status:
        case TaskStatusEnum.to_do:
            return TaskStatusOrder.to_do.value
        case TaskStatusEnum.in_progress:
            return TaskStatusOrder.in_progress.value
        case TaskStatusEnum.done:
            return TaskStatusOrder.done.value