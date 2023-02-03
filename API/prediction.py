import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from fastapi import APIRouter , Depends
from pydantic import BaseModel
from joblib import load
from access import decode_token
from sqlalchemy.orm import Session
from databases import start_session , add_to_predictions_table , Predictions , select_engine
from datetime import datetime , timezone

router = APIRouter(tags = ["Prediction"])

model = load("output_data/model.pkl")
scaler = load("output_data/scaler.pkl")

def get_team_info(team : str , home_or_away : str , season : str = "2022-2023"):
    engine = select_engine()
    team_stats_df = pd.read_sql(sql = f"SELECT * FROM FIFA WHERE team = '{team}' AND season = '{season}'" , con = engine).drop(columns = ["id" , "season" , "division" , "team"])
    team_results_df = pd.read_sql(sql = f"SELECT * FROM matches_results WHERE (home_team = '{team}' OR away_team = '{team}') AND season = '{season}'" , con = engine).sort_values(by = "date")

    temp = pd.DataFrame(dtype = "float")
    temp_df = team_results_df.copy()
    index_max = temp_df.index.max()
    new_index_max = index_max + 1
    
    if home_or_away == "home":
        temp_df.loc[new_index_max , "home_team"] = team
        temp_df.loc[new_index_max , "away_team"] = np.nan
    elif home_or_away == "away":
        temp_df.loc[new_index_max , "home_team"] = np.nan
        temp_df.loc[new_index_max , "away_team"] = team
    else:
        raise ValueError
        
    temp_df.loc[new_index_max , "season"] = season
    temp_df.loc[new_index_max , "full_time_result"] = "H"
    index = temp_df.index

    for i in index:

        if temp_df.loc[i , "home_team"] == team:        
            temp.loc[i , "FTGS"] = temp_df.loc[i , "full_time_home_goals"]
            temp.loc[i , "FTGC"] = temp_df.loc[i , "full_time_away_goals"]
            temp.loc[i , "S"] = temp_df.loc[i , "home_shots"]
            temp.loc[i , "ST"] = temp_df.loc[i , "home_shots_on_target"]
        
        elif temp_df.loc[i , "away_team"] == team:        
            temp.loc[i , "FTGS"] = temp_df.loc[i , "full_time_away_goals"]
            temp.loc[i , "FTGC"] = temp_df.loc[i , "full_time_home_goals"]
            temp.loc[i , "S"] = temp_df.loc[i , "away_shots"]
            temp.loc[i , "ST"] = temp_df.loc[i , "away_shots_on_target"]
        
        else:        
            raise ValueError

    temp_1 = temp.rolling(1 , min_periods = 1).mean().shift(fill_value = 0)
    temp_3 = temp.rolling(3 , min_periods = 1).mean().shift(fill_value = 0)
    temp_5 = temp.rolling(5 , min_periods = 1).mean().shift(fill_value = 0)
    temp_40 = temp.rolling(40 , min_periods = 1).mean().shift(fill_value = 0)

    index_home = temp_df[(temp_df["season"] == season) & (temp_df["home_team"] == team)].index
    temp_1_home = temp.loc[index_home].rolling(1 , min_periods = 1).mean().shift(fill_value = 0)
    temp_3_home = temp.loc[index_home].rolling(3 , min_periods = 1).mean().shift(fill_value = 0)
    temp_5_home = temp.loc[index_home].rolling(5 , min_periods = 1).mean().shift(fill_value = 0)
    temp_20_home = temp.loc[index_home].rolling(20 , min_periods = 1).mean().shift(fill_value = 0)

    index_away = temp_df[(temp_df["season"] == season) & (temp_df["away_team"] == team)].index
    temp_1_away = temp.loc[index_away].rolling(1 , min_periods = 1).mean().shift(fill_value = 0)
    temp_3_away = temp.loc[index_away].rolling(3 , min_periods = 1).mean().shift(fill_value = 0)
    temp_5_away = temp.loc[index_away].rolling(5 , min_periods = 1).mean().shift(fill_value = 0)
    temp_20_away = temp.loc[index_away].rolling(20 , min_periods = 1).mean().shift(fill_value = 0)

    if temp_df.loc[new_index_max , "home_team"] == team:        
        
        temp_df.loc[new_index_max , "home_Full time goals scored (1 game)"] = temp_1.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "home_Full time goals conceded (1 game)"] = temp_1.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "home_Shots (1 game)"] = temp_1.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "home_Shots on target (1 game)"] = temp_1.loc[new_index_max , "ST"]
        
        temp_df.loc[new_index_max , "home_Full time goals scored (home or away) (1 game)"] = temp_1_home.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "home_Full time goals conceded (home or away) (1 game)"] = temp_1_home.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "home_Shots (home or away) (1 game)"] = temp_1_home.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "home_Shots on target (home or away) (1 game)"] = temp_1_home.loc[new_index_max , "ST"]

        temp_df.loc[new_index_max , "home_Full time goals scored (3 games)"] = temp_3.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "home_Full time goals conceded (3 games)"] = temp_3.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "home_Shots (3 games)"] = temp_3.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "home_Shots on target (3 games)"] = temp_3.loc[new_index_max , "ST"]
        
        temp_df.loc[new_index_max , "home_Full time goals scored (home or away) (3 games)"] = temp_3_home.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "home_Full time goals conceded (home or away) (3 games)"] = temp_3_home.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "home_Shots (home or away) (3 games)"] = temp_3_home.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "home_Shots on target (home or away) (3 games)"] = temp_3_home.loc[new_index_max , "ST"]

        temp_df.loc[new_index_max , "home_Full time goals scored (5 games)"] = temp_5.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "home_Full time goals conceded (5 games)"] = temp_5.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "home_Shots (5 games)"] = temp_5.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "home_Shots on target (5 games)"] = temp_5.loc[new_index_max , "ST"]
        
        temp_df.loc[new_index_max , "home_Full time goals scored (home or away) (5 games)"] = temp_5_home.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "home_Full time goals conceded (home or away) (5 games)"] = temp_5_home.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "home_Shots (home or away) (5 games)"] = temp_5_home.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "home_Shots on target (home or away) (5 games)"] = temp_5_home.loc[new_index_max , "ST"]

        temp_df.loc[new_index_max , "home_Full time goals scored (home or away) (20 games)"] = temp_20_home.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "home_Full time goals conceded (home or away) (20 games)"] = temp_20_home.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "home_Shots (home or away) (20 games)"] = temp_20_home.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "home_Shots on target (home or away) (20 games)"] = temp_20_home.loc[new_index_max , "ST"]
        
        temp_df.loc[new_index_max , "home_Full time goals scored (40 games)"] = temp_40.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "home_Full time goals conceded (40 games)"] = temp_40.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "home_Shots (40 games)"] = temp_40.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "home_Shots on target (40 games)"] = temp_40.loc[new_index_max , "ST"]

    elif temp_df.loc[new_index_max , "away_team"] == team:       
        
        temp_df.loc[new_index_max , "away_Full time goals scored (1 game)"] = temp_1.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "away_Full time goals conceded (1 game)"] = temp_1.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "away_Shots (1 game)"] = temp_1.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "away_Shots on target (1 game)"] = temp_1.loc[new_index_max , "ST"]

        temp_df.loc[new_index_max , "away_Full time goals scored (home or away) (1 game)"] = temp_1_away.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "away_Full time goals conceded (home or away) (1 game)"] = temp_1_away.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "away_Shots (home or away) (1 game)"] = temp_1_away.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "away_Shots on target (home or away) (1 game)"] = temp_1_away.loc[new_index_max , "ST"]

        temp_df.loc[new_index_max , "away_Full time goals scored (3 games)"] = temp_3.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "away_Full time goals conceded (3 games)"] = temp_3.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "away_Shots (3 games)"] = temp_3.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "away_Shots on target (3 games)"] = temp_3.loc[new_index_max , "ST"]

        temp_df.loc[new_index_max , "away_Full time goals scored (home or away) (3 games)"] = temp_3_away.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "away_Full time goals conceded (home or away) (3 games)"] = temp_3_away.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "away_Shots (home or away) (3 games)"] = temp_3_away.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "away_Shots on target (home or away) (3 games)"] = temp_3_away.loc[new_index_max , "ST"]
        
        temp_df.loc[new_index_max , "away_Full time goals scored (5 games)"] = temp_5.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "away_Full time goals conceded (5 games)"] = temp_5.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "away_Shots (5 games)"] = temp_5.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "away_Shots on target (5 games)"] = temp_5.loc[new_index_max , "ST"]

        temp_df.loc[new_index_max , "away_Full time goals scored (home or away) (5 games)"] = temp_5_away.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "away_Full time goals conceded (home or away) (5 games)"] = temp_5_away.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "away_Shots (home or away) (5 games)"] = temp_5_away.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "away_Shots on target (home or away) (5 games)"] = temp_5_away.loc[new_index_max , "ST"]

        temp_df.loc[new_index_max , "away_Full time goals scored (home or away) (20 games)"] = temp_20_away.loc[i , "FTGS"]
        temp_df.loc[new_index_max , "away_Full time goals conceded (home or away) (20 games)"] = temp_20_away.loc[i , "FTGC"]
        temp_df.loc[new_index_max , "away_Shots (home or away) (20 games)"] = temp_20_away.loc[i , "S"]
        temp_df.loc[new_index_max , "away_Shots on target (home or away) (20 games)"] = temp_20_away.loc[i , "ST"]
        
        temp_df.loc[new_index_max , "away_Full time goals scored (40 games)"] = temp_40.loc[new_index_max , "FTGS"]
        temp_df.loc[new_index_max , "away_Full time goals conceded (40 games)"] = temp_40.loc[new_index_max , "FTGC"]
        temp_df.loc[new_index_max , "away_Shots (40 games)"] = temp_40.loc[new_index_max , "S"]
        temp_df.loc[new_index_max , "away_Shots on target (40 games)"] = temp_40.loc[new_index_max , "ST"]

    else:
        raise ValueError
        
    temp = pd.Series(dtype = "float")
    index = temp_df.index

    for i in index:

        if temp_df.loc[i , "home_team"] == team:
            if temp_df.loc[i , "full_time_result"] == "H":       
                temp.loc[i] = 3
            elif temp_df.loc[i , "full_time_result"] == "D":
                temp.loc[i] = 1
            elif temp_df.loc[i , "full_time_result"] == "A":
                temp.loc[i] = 0
            else:
                raise ValueError
        
        elif temp_df.loc[i , "away_team"] == team:        
            if temp_df.loc[i , "full_time_result"] == "A":       
                temp.loc[i] = 3
            elif temp_df.loc[i , "full_time_result"] == "D":
                temp.loc[i] = 1
            elif temp_df.loc[i , "full_time_result"] == "H":
                temp.loc[i] = 0
            else:
                raise ValueError
        
        else:        
            raise ValueError

    temp_1 = temp.rolling(1 , min_periods = 1).mean().shift(fill_value = 0)
    temp_3 = temp.rolling(3 , min_periods = 1).mean().shift(fill_value = 0)
    temp_5 = temp.rolling(5 , min_periods = 1).mean().shift(fill_value = 0)
    temp_40 = temp.rolling(40 , min_periods = 1).mean().shift(fill_value = 0)

    index_home = temp_df[(temp_df["season"] == season) & (temp_df["home_team"] == team)].index
    temp_1_home = temp.loc[index_home].rolling(1 , min_periods = 1).mean().shift(fill_value = 0)
    temp_3_home = temp.loc[index_home].rolling(3 , min_periods = 1).mean().shift(fill_value = 0)
    temp_5_home = temp.loc[index_home].rolling(5 , min_periods = 1).mean().shift(fill_value = 0)
    temp_20_home = temp.loc[index_home].rolling(20 , min_periods = 1).mean().shift(fill_value = 0)

    index_away = temp_df[(temp_df["season"] == season) & (temp_df["away_team"] == team)].index
    temp_1_away = temp.loc[index_away].rolling(1 , min_periods = 1).mean().shift(fill_value = 0)
    temp_3_away = temp.loc[index_away].rolling(3 , min_periods = 1).mean().shift(fill_value = 0)
    temp_5_away = temp.loc[index_away].rolling(5 , min_periods = 1).mean().shift(fill_value = 0)
    temp_20_away = temp.loc[index_away].rolling(20 , min_periods = 1).mean().shift(fill_value = 0)

    if temp_df.loc[new_index_max , "home_team"] == team:        
        temp_df.loc[new_index_max , "home_Points (1 game)"] = temp_1.loc[new_index_max]
        temp_df.loc[new_index_max , "home_Points (3 games)"] = temp_3.loc[new_index_max]
        temp_df.loc[new_index_max , "home_Points (5 games)"] = temp_5.loc[new_index_max]
        temp_df.loc[new_index_max , "home_Points (40 games)"] = temp_40.loc[new_index_max]

        temp_df.loc[new_index_max , "home_Points (home or away) (1 game)"] = temp_1_home.loc[new_index_max]
        temp_df.loc[new_index_max , "home_Points (home or away) (3 games)"] = temp_3_home.loc[new_index_max]
        temp_df.loc[new_index_max , "home_Points (home or away) (5 games)"] = temp_5_home.loc[new_index_max]
        temp_df.loc[new_index_max , "home_Points (home or away) (20 games)"] = temp_20_home.loc[new_index_max]

    elif temp_df.loc[new_index_max , "away_team"] == team:       
        temp_df.loc[new_index_max , "away_Points (1 game)"] = temp_1.loc[new_index_max]
        temp_df.loc[new_index_max , "away_Points (3 games)"] = temp_3.loc[new_index_max]
        temp_df.loc[new_index_max , "away_Points (5 games)"] = temp_5.loc[new_index_max]
        temp_df.loc[new_index_max , "away_Points (40 games)"] = temp_40.loc[new_index_max]

        temp_df.loc[new_index_max , "away_Points (home or away) (1 game)"] = temp_1_away.loc[new_index_max]
        temp_df.loc[new_index_max , "away_Points (home or away) (3 games)"] = temp_3_away.loc[new_index_max]
        temp_df.loc[new_index_max , "away_Points (home or away) (5 games)"] = temp_5_away.loc[new_index_max]
        temp_df.loc[new_index_max , "away_Points (home or away) (20 games)"] = temp_20_away.loc[new_index_max]

    else:
        raise ValueError
    
    temp_df = temp_df.drop(columns = team_results_df.columns)
    temp_df = temp_df.loc[temp_df.index.max()]
    temp_df.name = team
    team_stats_df = team_stats_df.iloc[0]
    team_stats_df.name = team

    return pd.concat([team_stats_df , temp_df])

def get_prediction_input(home_team : str , away_team : str , home_odd_bookmaker : float , away_odd_bookmaker : float):
    df_home = get_team_info(team = home_team , home_or_away = "home")
    df_away = get_team_info(team = away_team , home_or_away = "away")
    df_home.index = [x.replace("home_" , "") for x in df_home.index]
    df_away.index = [x.replace("away_" , "") for x in df_away.index]
    pd.concat([df_home , df_away] , axis = 1).to_csv("output_data/prediction_input.csv")
    df = df_home - df_away
    df["Cote"] = away_odd_bookmaker - home_odd_bookmaker
    df = df.to_frame().transpose()
    scaler = load("output_data/scaler.pkl")
    df_scaled = pd.DataFrame(scaler.transform(df) , index = df.index , columns = df.columns)
    return df_scaled

@router.post("/prediction" , name = "Get model prediction")
async def prediction(home_team : str , away_team : str , home_odd_bookmaker : float , away_odd_bookmaker : float , game_date : str , user = Depends(decode_token) , session = Depends(start_session)):
    game = get_prediction_input(home_team = home_team , away_team = away_team , home_odd_bookmaker = home_odd_bookmaker , away_odd_bookmaker = away_odd_bookmaker)
    probs = model.predict_proba(game)[0]
    odds = np.round(1 / probs , 2)
    game_date = datetime.strptime(game_date , "%Y-%m-%d")
    prediction = Predictions(username = user.get("username") , home_team = home_team , away_team = away_team , game_date = game_date , home_odd_predicted = odds[2] , draw_odd_predicted = odds[1] , away_odd_predicted = odds[0] , prediction_date = datetime.now(timezone.utc))
    add_to_predictions_table(prediction = prediction , session = session)
    
    return {
        f"Cote victoire {home_team}" : odds[2] ,
         "Cote match nul" : odds[1] ,
          f"Cote victoire {away_team}" : odds[0]
    }