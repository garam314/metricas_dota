import pandas as pd
import opendota
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Dota():
    def __init__(self, config:dict):
        self.ids = config['IDS']
        self.days = config['DAYS']
        self.__config = config
        self.df_heroes = pd.DataFrame()
        self.__client = opendota.OpenDota(data_dir='script_data\dota2_data')
        self.resume = pd.DataFrame()
        
        self.__get_heroes()
        self.__get_matchets()
    def __get_heroes(self):
        self.df_heroes = pd.DataFrame(self.__client.get_heroes())
        
    def __get_matchets(self):
        df_matches = pd.DataFrame()
        for id_player in self.ids:
            matches_pg = self.__client.get_player_matches(id_player, days=self.days, force=True)
            tmp_df = pd.DataFrame(matches_pg)
            df_matches = pd.concat([df_matches, tmp_df]).drop_duplicates(subset="match_id", keep="last")
            
        print("Obteniendo Matches: ", len(df_matches))
        rows = []
        for index, item in enumerate(df_matches.itertuples(), start=1):
            tmp_df = pd.DataFrame(self.__client.get_match(item.match_id, force=False)['players'])
            
            for id in self.ids:
                tmp_player_df = tmp_df.loc[tmp_df['account_id']==id]
                tmp_player_df =    tmp_player_df[['player_slot', 'team_number', 'team_slot', 'hero_id', 'hero_variant', 'item_0', 'item_1', 'item_2', 'item_3', 'item_4', 'item_5', 'backpack_0', 'backpack_1',
                                'backpack_2', 'item_neutral', 'item_neutral2', 'leaver_status', 'last_hits', 'denies', 'gold_per_min', 'xp_per_min', 'level',
                                'net_worth', 'aghanims_scepter', 'aghanims_shard', 'moonshard', 'hero_damage', 'tower_damage', 'hero_healing', 'gold', 'gold_spent','ability_upgrades_arr',
                                'is_subscriber', 'radiant_win', 'start_time', 'duration', 'cluster', 'lobby_type', 'game_mode', 'is_contributor','patch', 'isRadiant', 'win', 'lose',
                                'total_gold', 'total_xp', 'kills_per_min', 'kda', 'abandons', 'benchmarks', 'account_id', 'personaname', 'name', 'last_login', 'rank_tier', 'computed_mmr']]
                tmp_player_df['match_id'] = item.match_id
                rows.append(tmp_player_df)
            print(index, end='\r')

        self.df_resume = pd.concat(rows, ignore_index=True)
        
        #TIMESTAMP A FECHA
        self.df_resume['fecha'] = pd.to_datetime(self.df_resume['start_time'], unit='s', utc=True).dt.tz_convert('America/Santiago').dt.tz_localize(None)
        #OBTENER HEROE
        self.df_resume = self.df_resume.merge(self.df_heroes[['id', 'localized_name']], left_on='hero_id', right_on='id', how='left')
        
        self.df_resume['zone'] = self.df_resume['isRadiant'].map({True: 'Radiant', False: 'Dire'})
        self.df_resume['win'] = self.df_resume['win'].map({1: 'Win', 0: 'Lost'})
        
    def __get_damage(self):
        
        if self.__config['DAMAGE']['METRIC'].upper() == 'MEAN':
            df = self.df_resume[['personaname', 'hero_damage', 'tower_damage', 'hero_healing']].groupby(['personaname']).mean().reset_index()
        elif self.__config['DAMAGE']['METRIC'].upper() == 'MEDIAN':
            df = self.df_resume[['personaname', 'hero_damage', 'tower_damage', 'hero_healing']].groupby(['personaname']).median().reset_index()

        fig = go.Figure()

        fig.add_bar(
            x=df['personaname'],
            y=df['hero_damage'],
            name='Daño a Heroes',
            text=df['hero_damage'].round(1),
            textposition='outside'
        )
        fig.add_bar(
            x=df['personaname'],
            y=df['tower_damage'],
            name='Daño a Torres',
            text=df['tower_damage'].round(1),
            textposition='outside'
        )
        fig.add_bar(
            x=df['personaname'],
            y=df['hero_healing'],
            name='Curación Heroes',
            text=df['hero_healing'].round(1),
            textposition='outside'
        )

        fig.update_layout(
            barmode='group',
            xaxis_title = 'Manco',
            yaxis_title = 'Mediana',
            title = "Damage"
        )

        fig.update_yaxes(range=[0, df[['hero_damage', 'tower_damage', 'hero_healing']].max().max() * 1.5])
        fig.write_html(rf"{self.__config['DAMAGE']['PATH']}")
        
    def __get_gold(self):
        if self.__config['GOLD']['METRIC'].upper() == 'MEAN':
            df = self.df_resume[['personaname', 'total_gold', 'gold_spent']].groupby(['personaname']).mean().reset_index()
        elif self.__config['GOLD']['METRIC'].upper() == 'MEDIAN':
            df = self.df_resume[['personaname', 'total_gold', 'gold_spent']].groupby(['personaname']).median().reset_index()
            
        df['gold_unspent'] = df['total_gold'] - df['gold_spent']

        fig = make_subplots(
            rows=1,
            cols=len(self.ids),
            specs=[[{"type": "domain"}]*len(self.ids)],
        )
        for index, row in enumerate(df.itertuples(), start=1):
            tmp_fig = go.Pie(
                        labels=["Oro Gastado", "Oro No Gastado"],
                        values=[row.gold_spent, row.gold_unspent],
                        hole=0.5,
                        title=row.personaname
                    )
            fig.add_trace(tmp_fig, row=1, col=index)
        fig.update_layout(
            title="Oro Usado"
        )
        fig.write_html(rf"{self.__config['GOLD']['PATH']}")
        
    def __get_ploty_kda(self):
        if self.__config['KDA']['METRIC'].upper() == 'MEAN':
            df = self.df_resume[['personaname', 'zone', 'kda']].groupby(['personaname', 'zone']).mean().reset_index()
        elif self.__config['KDA']['METRIC'].upper() == 'MEDIAN':
            df = self.df_resume[['personaname', 'zone', 'kda']].groupby(['personaname', 'zone']).median().reset_index()

        fig = go.Figure()

        for zone, data in df.groupby("zone"):
            fig.add_bar(
                x=data["personaname"],
                y=data["kda"],
                name=zone,
                text=data["kda"].round(1),
                textposition="outside"
            )

        fig.update_layout(
            barmode='group',
            xaxis_title = 'Manco',
            yaxis_title = 'KDA',
            title='Evaluacion KDA'
        )
        fig.update_yaxes(range=[0, df['kda'].max() * 1.5])
        fig.write_html(rf"{self.__config['KDA']['PATH']}")
        
    def __get_last_hits(self):
        if self.__config['LH']['METRIC'].upper() == 'MEAN':
            df = self.df_resume[['personaname', 'last_hits', 'denies']].groupby(['personaname']).mean().reset_index()
        elif self.__config['LH']['METRIC'].upper() == 'MEDIAN':
            df = self.df_resume[['personaname', 'last_hits', 'denies']].groupby(['personaname']).median().reset_index()
            
        fig = go.Figure()
        fig.add_bar(
            x=df['personaname'],
            y=df['last_hits'],
            name='Últimos Golpes',
            text=df['last_hits'].round(1),
            textposition="outside"
        )

        fig.add_bar(
            x=df['personaname'],
            y=df['denies'],
            name='Denegadas',
            text=df['denies'].round(1),
            textposition="outside"
        )

        fig.update_layout(
            barmode='group',
            xaxis_title = 'Manco',
            yaxis_title = 'Mediana',
            title = "Ultimos Golpes"
        )
        fig.update_yaxes(range=[0, df[['last_hits', 'denies']].max().max() * 1.5])
        fig.write_html(rf"{self.__config['LH']['PATH']}")
        
    def __get_wins(self):
                    
        df = self.df_resume[['personaname', 'win']].groupby(['personaname', 'win']).value_counts().reset_index()    
        df['total'] = df.groupby('personaname')['count'].transform("sum")
        df["porcentaje"] = df['count']/df['total']

        fig = make_subplots(
            rows=1,
            cols=len(self.ids),
            specs=[[{"type": "domain"}]*len(self.ids)],
        )


        for index, (zone, data) in enumerate(df.groupby("personaname"), start=1):
            tmp_fig = go.Pie(
                        labels=data['win'].to_list(),
                        values=data['porcentaje'].to_list(),
                        hole=0.5,
                        title=zone
                    )
            fig.add_trace(tmp_fig, row=1, col=index)
        fig.write_html(rf"{self.__config['WINS']['PATH']}")
        
    def __get_scores(self):

        df = pd.json_normalize(self.df_resume['benchmarks'])
        df['personaname'] = self.df_resume['personaname']

        cols = df.filter(regex=r"\.pct$").columns
        medians = df[["personaname", *cols]]
        
        if self.__config['SCORES']['METRIC'].upper() == 'MEAN':
            medians = medians.groupby('personaname').mean()
        elif self.__config['SCORES']['METRIC'].upper() == 'MEDIAN':
            medians = medians.groupby('personaname').median()
            
        medians = medians.rename(columns={
        'gold_per_min.pct' :'GOLD x Min',
        'xp_per_min.pct' :'XP x Min',
        'kills_per_min.pct' :'KILLS x Min',
        'last_hits_per_min.pct' :'L.HITS x Min',
        'hero_damage_per_min.pct' :'H.DAM x Min',
        'hero_healing_per_min.pct' :'H. HEA x Min',
        'tower_damage.pct' :'T. DAM x Min'
        })

        fig = go.Figure(
            data=go.Heatmap(
                z=medians.values,
                x=medians.columns,
                y=medians.index,
                text=medians.round(2).values,
                texttemplate="%{text}",
                hovertemplate="Jugador: %{y}<br>Métrica: %{x}<br>Valor: %{z:.3f}<extra></extra>"
            )
        )
        fig.update_layout(
            title="Benchmarks por jugador",
            xaxis_title="Scores",
            yaxis_title="Manco"
        )

        fig.write_html(rf"{self.__config['SCORES']['PATH']}")
        
    def __get_profile_score(self):
        
        df = pd.json_normalize(self.df_resume['benchmarks'])
        df['personaname'] = self.df_resume['personaname']

        cols = df.filter(regex=r"\.pct$").columns
        medians = df[["personaname", *cols]]
        
        if self.__config['PROFILE']['METRIC'].upper() == 'MEAN':
            medians = medians.groupby('personaname').mean()
        elif self.__config['PROFILE']['METRIC'].upper() == 'MEDIAN':
            medians = medians.groupby('personaname').median()
            
        medians = medians.rename(columns={
        'gold_per_min.pct' :'GOLD x Min',
        'xp_per_min.pct' :'XP x Min',
        'kills_per_min.pct' :'KILLS x Min',
        'last_hits_per_min.pct' :'L.HITS x Min',
        'hero_damage_per_min.pct' :'H.DAM x Min',
        'hero_healing_per_min.pct' :'H. HEA x Min',
        'tower_damage.pct' :'T. DAM x Min'
        })
        
        fig = go.Figure()

        for player in medians.index:
            fig.add_trace(go.Scatterpolar(
                r=medians.loc[player].tolist(),
                theta=medians.columns.tolist(),
                fill='toself',
                name=player
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title="Perfil de métricas por Manco"
        )

        fig.write_html(rf"{self.__config['PROFILE']['PATH']}")
        

    
    def get_graph(self):
        self.__get_damage()
        self.__get_gold()
        self.__get_ploty_kda()
        self.__get_last_hits()
        self.__get_wins()
        self.__get_scores()
        self.__get_profile_score()