# Day 8 Question 2 — AI-Assisted Pathfinding System

This project implements the Question 2 requirements:

- loads `Node_Info.txt` and `Graph_Path.txt`;
- computes shortest paths using edge `Distance`;
- visualises nodes, paths, building types, and the selected route;
- provides a public Flask web interface;
- protects editing with an editor password;
- includes repeatable automated tests and AI review notes.

## Project structure

```text
Day_8_Q2_Pathfinding/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── data/
│   ├── Node_Info.txt
│   └── Graph_Path.txt
├── src/
│   ├── auth.py
│   ├── map_loader.py
│   └── pathfinder.py
├── templates/
├── tests/
└── docs/
```

## Run with Docker Desktop

Open PowerShell in this folder:

```powershell
docker compose up --build -d
docker compose ps
```

Open:

```text
http://localhost:60003
```

Editor login:

```text
Password: bootcamp123
```

The password is configured in `docker-compose.yml`. Change it before sharing
the project publicly.

Stop the project:

```powershell
docker compose down
```

## Run without Docker

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` when running directly without Docker.

## Run verification

From PowerShell:

```powershell
python -m pytest -q
```

Or inside the running container:

```powershell
docker compose exec pathfinding-app python -m pytest -q
```

## Screenshot checklist

Capture these from your own computer:

1. Public map at `http://localhost:60003`.
2. Path result for start `0` and end `2`.
3. Failed editor login.
4. Successful editor login and protected editor page.
5. Command-line test result showing all tests passed.

## Important design choices

- Paths are undirected.
- Edge `Distance` is the pathfinding cost.
- Node coordinates are used only for visualisation.
- Blank and comment lines are ignored.
- Edits are saved immediately to the data files.
