from project import create_app, create_worker

app = create_app()
create_worker(app)


