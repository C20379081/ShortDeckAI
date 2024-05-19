import dill
import os
import time

# Method used to retrieve the saved trained data 
def retrieve_save(saveDir="Saves"):
    try:
        # Check if the save directory exists
        if not os.path.exists(saveDir):
            print(f"Save directory not there")
            return None, 0
        # List all files in the save directory that match the required pattern
        saves = [s for s in os.listdir(saveDir) if s.startswith("sets") and s.endswith(".p")]
        if not saves:
            print(f"No save files found")
            return None, 0
        # Sort the save files by extracting the iteration number and converting it to an integer
        saves.sort(key=lambda x: int(x.split("sets")[1].split(".p")[0]))
        # Construct the path to the most recent save file
        latest_save_path = os.path.join(saveDir, saves[-1])
        # Load the contents of the most recent save file
        with open(latest_save_path, "rb") as file:
            data = dill.load(file)
        # Extract the iteration number from the file name
        iteration_number = int(saves[-1].split("sets")[1].split(".p")[0])
        return data, iteration_number

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, 0

