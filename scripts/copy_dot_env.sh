if [ ! -f "../tac-2/app/server/.env" ]; then
    echo "Error: ../tac-2/app/server/.env does not exist"
    exit 1
fi

cp ../tac-2/app/server/.env app/server/.env

echo "Successfully copied ../tac-2/app/server/.env to .env"