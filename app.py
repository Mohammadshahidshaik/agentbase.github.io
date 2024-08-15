from flask import Flask, request, jsonify, render_template
from model import RoomModel
from threading import Thread
import time

app = Flask(__name__)
model = None
auto_step_running = False
auto_step_thread = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/initialize', methods=['POST'])
def initialize():
    global model
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        width = data.get('width')
        height = data.get('height')
        day_night_cycle = data.get('day_night_cycle')
        preferences = data.get('preferences')

        if width is None or height is None or day_night_cycle is None or preferences is None:
            return jsonify({"error": "Missing parameters"}), 400

        print(f"Received initialization data: {data}")

        model = RoomModel(width, height, day_night_cycle, preferences)

        # Start the Mesa server
        start_mesa_server()

        return jsonify({"message": "Model initialized successfully"})
    except Exception as e:
        print(f"Error during initialization: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/step', methods=['POST'])
def step():
    global model
    try:
        if model is None:
            return jsonify({"error": "Model is not initialized"}), 400

        model.step()

        agents_data = []
        for agent in model.schedule.agents:
            agent_data = {
                "id": agent.unique_id,
                "type": agent.agent_type,
                "temperature": agent.temperature,
                "light": agent.light,
                "air_quality": agent.airQuality,
                "acoustics": agent.acoustics,
                "windowStatus": agent.windowStatus,
                "blindStatus": agent.blindStatus,
                "thermal_satisfaction": agent.thermalSatisfaction,
                "visual_satisfaction": agent.visualSatisfaction,
                "air_quality_satisfaction": agent.airQualitySatisfaction,
                "ieqpriority": agent.ieqpriority,
                "air_condition_status": agent.airConditionStatus,
                "artificial_light_status": agent.artificialLightStatus,
            }
            agents_data.append(agent_data)

        return jsonify(agents_data)
    except Exception as e:
        print(f"Error during step: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_conditions', methods=['GET'])
def get_conditions():
    global model
    try:
        if model is None:
            return jsonify({"error": "Model is not initialized"}), 400

        conditions = {
            "view": getattr(model.occupant, 'view', "no_view"),
            "temperature": model.occupant.temperature,
            "light": model.occupant.light,
            "acoustics": model.occupant.acoustics,
            "air_quality": model.occupant.airQuality,
            "window_status": model.occupant.windowStatus,
            "blind_status": model.occupant.blindStatus,
            "window_intention": model.occupant.windowIntention,
            "blind_intention": model.occupant.blindIntention,
            "artificialLightStatus": model.occupant.artificialLightStatus,
            "airConditionStatus": model.occupant.airConditionStatus,
            "windowStatus": model.occupant.windowStatus,
            "blindStatus": model.occupant.blindStatus,
            "current_step": model.current_step
        }
        return jsonify(conditions)
    except Exception as e:
        print(f"Error during get_conditions: {e}")
        return jsonify({"error": str(e)}), 500

def start_mesa_server():
    from model import main as start_mesa
    thread = Thread(target=start_mesa)
    thread.start()

def auto_step():
    global auto_step_running
    while auto_step_running:
        step()
        time.sleep(1)

@app.route('/start_auto_step', methods=['POST'])
def start_auto_step():
    global auto_step_running, auto_step_thread
    auto_step_running = True
    auto_step_thread = Thread(target=auto_step)
    auto_step_thread.start()
    return jsonify({"message": "Auto stepping started"})

@app.route('/stop_auto_step', methods=['POST'])
def stop_auto_step():
    global auto_step_running
    auto_step_running = False
    if auto_step_thread:
        auto_step_thread.join()
    return jsonify({"message": "Auto stepping stopped"})

if __name__ == '__main__':
    app.run(debug=True)
