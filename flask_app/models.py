from peewee import SqliteDatabase, Model, CharField, DateField

db = SqliteDatabase('users.db')


class User(Model):
    name = CharField()
    email = CharField()
    birthday = DateField()

    class Meta:
        database = db # This model uses the "people.db" database.