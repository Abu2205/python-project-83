curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
which uv || { echo "uv not found in PATH"; exit 1; }
make install && psql -a -d $DATABASE_URL -f database.sql