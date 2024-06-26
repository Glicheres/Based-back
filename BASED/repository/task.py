from datetime import date, datetime
from enum import IntEnum, StrEnum
from typing import Optional

from asyncpg import Pool
from pydantic import BaseModel

from BASED.repository.helpers import build_model_sql


class TaskStatusEnum(StrEnum):
    to_do = "to_do"
    in_progress = "in_progress"
    done = "done"


class DependencyTypeEnum(StrEnum):
    depends_of = "depends_of"
    dependent_for = "dependent_for"
    self = "self"


class TaskStatusOrder(IntEnum):
    to_do = 1
    in_progress = 2
    done = 3


class TaskCreate(BaseModel):
    status: TaskStatusEnum
    title: str | None
    description: str | None
    deadline: date
    responsible_user_id: int
    days_for_completion: int


class ShortTask(BaseModel):
    id: int
    title: str


class Task(BaseModel):
    id: int
    responsible_user_id: int
    status: TaskStatusEnum
    title: str | None
    description: str | None
    deadline: date
    days_for_completion: int
    actual_start_date: date | None
    actual_finish_date: date | None
    actual_completion_days: int | None
    is_archived: bool
    created_timestamp: datetime


class TaskDepends(BaseModel):
    task_id: int
    depends_task_id: int
    created_timestamp: datetime


class TaskWithDependency(BaseModel):
    id: int
    dependency_type: DependencyTypeEnum
    responsible_user_id: int
    title: str | None
    deadline: date


class TaskRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create(self, task_create_model: TaskCreate) -> Task:
        model_build = build_model_sql(task_create_model)
        sql = f"""
            insert into "task" ({model_build.field_names})
            values ({model_build.placeholders})
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, *model_build.values)

        return Task(**dict(row))

    async def get_by_id(self, id_: int) -> Optional[Task]:
        sql = """
            select * from "task"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)

        if not row:
            return

        return Task(**dict(row))

    async def update_task_data(
        self,
        task_id: int,
        title: str | None,
        description: str | None,
        deadline: date,
        responsible_user_id: int,
        days_for_completion: int,
    ) -> Optional[Task]:
        """
        Обновляет основные данные о задаче.
        """
        sql = """
            update "task"
            set "title" = $2, "description" = $3, "deadline" = $4,
            "responsible_user_id" = $5, "days_for_completion" = $6
            where "id" = $1
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(
                sql,
                task_id,
                title,
                description,
                deadline,
                responsible_user_id,
                days_for_completion,
            )

        if not row:
            return

        return Task(**dict(row))

    async def update_task_status(
        self, task_id: int, new_status: TaskStatusEnum
    ) -> Optional[Task]:
        """
        Изменяет статус задачи.
        """
        sql = """
            update "task" set "status" = $2
            where "id" = $1
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, task_id, new_status)

        if not row:
            return

        return Task(**dict(row))

    async def update_task_start_finish_dates(
        self,
        task_id: int,
        new_start_date: date | None,
        new_finish_date: date | None,
    ) -> bool:
        """
        Обновляет фактическую дату начала и фактическую дату окончания
        в соответсвуии с переданными значениями.
        Возвращает True в случае успеха, False если задача не найдена.
        """
        actual_completion_days = None
        if new_start_date is not None and new_finish_date is not None:
            actual_completion_days = (
                new_finish_date - new_start_date
            ).days + 1

        sql = """
            update "task"
            set "actual_start_date" = $2,
                "actual_finish_date" = $3,
                "actual_completion_days" = $4
            where "id" = $1
            returning 1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(
                sql,
                task_id,
                new_start_date,
                new_finish_date,
                actual_completion_days,
            )

        return bool(row)

    async def get_task_depends(self, id_: int) -> list[TaskDepends] | None:
        """
        Показывает зависимости задачи
        """
        sql = """
        SELECT * from "task_depends"
        WHERE "task_id" = $1
        """
        async with self._db.acquire() as c:
            data = await c.fetch(sql, id_)

        return [TaskDepends(**dict(row)) for row in data]

    async def get_tasks_dependent_of(
        self, dependent_task_id: int
    ) -> list[TaskDepends]:
        """
        Получение всех задач, от которых зависит данная.
        """
        sql = """
                SELECT * from "task_depends"
                WHERE "depends_task_id" = $1
                """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql, dependent_task_id)

        return [TaskDepends(**dict(row)) for row in rows]

    async def add_task_depends(self, id_: int, depends_id: int) -> None:
        """
        Добавляет зависимость задач
        """
        sql = """
        INSERT INTO "task_depends" (task_id, depends_task_id)
        VALUES ($1, $2)
        ON CONFLICT (task_id, depends_task_id) DO NOTHING
        """
        async with self._db.acquire() as c:
            await c.execute(sql, id_, depends_id)

    async def update_task_archive_status(
        self, task_id: int, archive_status: bool
    ) -> bool:
        """
        Изменяет статус архивации для задачи.
        """
        sql = """
            update "task"
            set "is_archived" = $2
            where "id" = $1
            returning 1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, task_id, archive_status)

        return bool(row)

    async def update_task_deadline(
        self, task_id: int, new_deadline: date
    ) -> bool:
        """
        Изменяет текущий дедлайн по задаче.
        """
        sql = """
            update "task"
            set "deadline" = $2
            where "id" = $1
            returning 1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, task_id, new_deadline)

        return bool(row)

    async def get_all_short_tasks(self) -> list[ShortTask]:
        """
        Получает всех пользователей.
        """
        sql = """
            SELECT *
            FROM "task"
        """
        async with self._db.acquire() as c:
            data = await c.fetch(sql)

        return [ShortTask(**dict(i)) for i in data]

    async def get_tasks_ordered_by_deadline(self) -> list[Task]:
        """
        Получает задачи отсортированные по дедлайнам и статусам.
        """
        sql = """
            select * from "task"
            where not "is_archived"
            order by "deadline"
        """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql)

        return [Task(**dict(row)) for row in rows]

    async def del_tasks_depends(self, id_: int, depends_id: int) -> bool:
        """
        Получает всех пользователей.
        """
        sql = """
            DELETE FROM "task_depends"
            WHERE "task_id" = $1 AND "depends_task_id" = $2
            RETURNING TRUE
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_, depends_id)
        if not row:
            return False
        return True

    async def get_all_task_dependencies(
        self, task_id: int
    ) -> list[TaskWithDependency]:
        sql = """
            select "id", 'depends_of' as "dependency_type",
             "title", "deadline", "responsible_user_id"
            from "task_depends" join "task"
            on "task_depends"."task_id" = "task"."id"
            where "depends_task_id" = $1
            union
            select "id", 'dependent_for' as "dependency_type",
             "title", "deadline", "responsible_user_id"
            from "task_depends" join "task"
            on "task_depends"."depends_task_id" = "task"."id"
            where "task_id" = $1
            union
            select "id", 'self' as "dependency_type",
             "title", "deadline", "responsible_user_id"
            from "task"
            where "id" = $1
            order by "deadline"
        """
        async with self._db.acquire() as c:
            rows = await c.fetch(sql, task_id)

        return [TaskWithDependency(**dict(row)) for row in rows]

    async def del_responsible_user_id(self, user_id: int) -> bool:
        """
        Удаляет ответственного
        """
        sql = """
               update "task"
               set "responsible_user_id" = NULL
               where "responsible_user_id" = $1
               returning 1
           """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, user_id)

        return bool(row)
