from enum import Enum
import logging
import json
import os


logger = logging.getLogger(__name__)
class PlayerMode(Enum):
    IDLE = 'IDLE'
    INIT = 'INIT'
    READY = 'READY'
    STOP = "STOP"

class Player():
    def __init__(self, telegram_id, username, data_folder : str):
        self.telegram_id = telegram_id
        self.name = username
        self.data_folder = data_folder
        if not self.load_player():
            self.status : PlayerMode = PlayerMode.INIT
            self.ex_status = [
                {'sha': 0, 'status': True},]
            self.save_player()
        
    def get_status(self) -> PlayerMode:
        return self.status
    
    def get_name(self) -> PlayerMode:
        return self.name
    
    def get_telegram_id(self):
        return self.telegram_id

    def set_status(self, status : PlayerMode):
        self.status = status
        self.save_player()
    
    def find_exercise_by_sha(self, sha):
        for exercise in self.ex_status:
            if exercise['sha'] == sha:
                return exercise
        return None 
    
    def get_ex_status(self, sha : int):
        exercise = self.find_exercise_by_sha(sha)
        if exercise: 
            return exercise['status']
        else:
            return True 

    def set_ex_status(self, sha : int, status : bool):
        exercise = self.find_exercise_by_sha(sha)
        if exercise:
            exercise['status']=status
        else:
            self.ex_status.append( {'sha': sha, 'status': status})
            self.save_player()

    def get_json(self):
        return json.dumps({
            'telegram_id': self.telegram_id,
            "name" : self.name,
            'status': self.status.value,
            'ex_status': self.ex_status
        })

    def load_json(self, json_str):
        data = json.loads(json_str)
        self.telegram_id = data['telegram_id']
        self.name = data['name']
        self.status = PlayerMode(data['status'])
        self.ex_status = data['ex_status']

            
    def save_player(self):
        player_json = self.get_json()
        file_path = os.path.join(self.data_folder, f"player_{self.telegram_id}.json")
        with open(file_path, 'w') as file:
            file.write(player_json)
    
    def load_player(self):
        file_path = os.path.join(self.data_folder, f"player_{self.telegram_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                player_json = file.read()
                self.load_json(player_json)
                return True
        else:
            return False
    