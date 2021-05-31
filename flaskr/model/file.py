from . import db

class File(db.Model):
    __tablename__ = 'files'

    name = db.Column(
        db.Text,
        primary_key = True,
        unique = True,
    )

    file = db.Column(
        db.String
    )