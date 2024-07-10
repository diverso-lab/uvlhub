from sqlalchemy.exc import IntegrityError
from app import db


class BaseSeeder:
    priority = 10  # Default priority

    def __init__(self):
        self.db = db

    def run(self):
        raise NotImplementedError("The 'run' method must be implemented by the child class.")

    def seed(self, data):
        """
        Attempts to insert a list of model objects and returns them with their IDs assigned after insertion.
        Throws an exception if data insertion fails.

        :param data: List of model objects to insert.
        :return: List of model objects with IDs assigned.
        """
        if not data:
            return []

        model = type(data[0])
        if not all(isinstance(obj, model) for obj in data):
            raise ValueError("All objects must be of the same model.")

        try:
            self.db.session.add_all(data)
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            raise Exception(f"Failed to insert data into `{model.__tablename__}` table. Error: {e}")

        # After committing, the `data` objects should have their IDs assigned.
        return data
