docker compose up --build

docker compose exec server flask --app flaskr init-db

docker compose exec server flask create-admin admin@ admin@