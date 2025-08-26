## To run this backend app, you will need these requirements:
- Include a .secret folder  in the hydrosens folder, the .secret contains the json file 
of your GEE key.
- In the /hydrosens/data folder (Create one if you have not had), you will need to:
    + Include these files, they can be found in the hydrosens original repo: 
        CN_lookup.csv
        sol_texture.class_usda.tt_m_250m_b0..0cm_1950..2017_v0.2
        VIS_speclib_landsat.csv
        VIS_speclib_sentinel.csv
    + Create a /shape folder if you have not had
- To run the backend, use:
    docker-compose up --build (Windows)
    docker compose up --build (Mac)
- The application consists of two sub-containers:
    hydrosens: Can be access through localhost:5000
    api-app: Can be access through localhost:5050