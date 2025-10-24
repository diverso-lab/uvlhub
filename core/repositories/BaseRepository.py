from typing import Generic, List, NoReturn, Optional, TypeVar, Union

import app

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: T):
        self.model = model
        self.session = app.db.session

    def create(self, commit: bool = True, **kwargs) -> T:
        instance: T = self.model(**kwargs)
        self.session.add(instance)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
        return instance

    def get_by_id(self, id: int) -> Optional[T]:
        instance: Optional[T] = self.model.query.get(id)
        return instance

    def get_by_column(self, column_name: str, value) -> List[T]:
        instances: List[T] = self.session.query(self.model).filter(getattr(self.model, column_name) == value).all()
        return instances

    def get_or_404(self, id: int) -> Union[T, NoReturn]:
        return self.model.query.get_or_404(id)

    def update(self, id: int, **kwargs) -> Optional[T]:
        instance: Optional[T] = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.session.commit()
            return instance
        return None

    def delete(self, id: int) -> bool:
        instance: Optional[T] = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False

    def delete_by_column(self, column_name: str, value) -> bool:
        instances: List[T] = self.get_by_column(column_name, value)
        if not instances:
            return False

        for instance in instances:
            self.session.delete(instance)
        self.session.commit()
        return True

    def count(self) -> int:
        return self.model.query.count()
