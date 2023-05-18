from app import db


class FMMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solver = db.Column(db.String(120))
    not_solver = db.Column(db.String(120))

    def __repr__(self):
        return f'FMMetrics<solver={self.solver}, not_solver={self.not_solver}>'
