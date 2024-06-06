from typing import Generic, NoReturn, Optional, TypeVar, Union

import app

T = TypeVar('T')


class BaseRepository(Generic[T]):
    def __init__(self, model: T):
        self.model = model

    def create(self, **kwargs) -> T:
        instance: T = self.model(**kwargs)
        app.db.session.add(instance)
        app.db.session.commit()
        return instance

    def get_by_id(self, id: int) -> Optional[T]:
        instance: Optional[T] = self.model.query.get(id)
        return instance

    def get_or_404(self, id: int) -> Union[T, NoReturn]:
        return self.model.query.get_or_404(id)

    def update(self, id: int, **kwargs) -> Optional[T]:
        instance: Optional[T] = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            app.db.session.commit()
            return instance
        return None

    def delete(self, id: int) -> bool:
        instance: Optional[T] = self.get_by_id(id)
        if instance:
            app.db.session.delete(instance)
            app.db.session.commit()
            return True
        return False

    def count(self) -> int:
        return self.model.query.count()
