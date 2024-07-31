
import hashlib

class Exercise():
    def __init__(self, file_path):
        self.exercises = []
        self.new_exercises = []
        self.load_exercises(file_path)


    def calculate_md5(self, input_string: str) -> str:
        md5_hash = hashlib.md5()
        md5_hash.update(input_string.encode('utf-8'))
        return md5_hash.hexdigest()

    def load_exercises(self, file_path='exercises'):
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        parts = line.split(';')
                        if len(parts) == 2:
                            exercise = {
                                'name': parts[0],
                                'reps': int(parts[1]),
                                'sha': self.calculate_md5(f"{line}")
                                }
                            
                            self.exercises.append(exercise)
        except FileNotFoundError:
            print("Exercises file not found. Starting with an empty list.")

    def get_exercise(self, number : int = None):
        if number:
            return self.exercises[number-1]
        else:
            return self.exercises
        
    def add_exercise(self, exercise_name : str, reps : int, overwrite : bool):
        exercise = {
            'name': exercise_name,
            'reps': reps,
            'sha': self.calculate_md5(f"{exercise_name};{reps}")
        }

        if overwrite:
            self.exercises.append(exercise)
        else:
            self.new_exercises.append(exercise)
    
    def merge_new(self):
        self.exercises = self.exercises + self.new_exercises
        self.new_exercises = []

    def save_exercises(file_path='exercises.txt'):
        global exercises

        with open(file_path, 'w') as file:
            for exercise in exercises:
                line = f"{exercise['name']};{exercise['player1_reps']}/{exercise['player2_reps']};{exercise['type']}\n"
                file.write(line)