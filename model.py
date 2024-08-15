from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import SingleGrid
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
import pandas as pd
import openstudio
import os
import subprocess
import time

class EnvironmentalAgent(Agent):

    def __init__(self, unique_id, model, agent_type, occupant=None,config=None):
        super().__init__(unique_id, model)
        self.agent_type = agent_type
        self.config = config or {}
        
        self.preferredTemperature = config.get('preferred_temperature', 22)
        self.preferredLight = config.get('preferred_light', 44)
        self.preferredAirQuality = config.get('preferred_air_quality', 70)
        self.preferredAcoustics = config.get('preferred_acoustics', 37)
        self.preferredBlindStatus = "Close"
        
        self.blindAttitude = config.get('blind_attitude', 3)
        self.blindPercievedNorm = config.get('blind_perceived_norm', 3)
        self.blindPercievedBehavioralControl = config.get('blind_perceived_behavioral_conditions', 3)
        
        self.preferredWindowStatus = "Close"
        self.windowAttitude = config.get('window_attitude', 3)
        self.windowPercievedNorm = config.get('window_perceived_norm', 3)
        self.windowPercievedBehavioralControl = config.get('window_perceived_behavioral_conditions', 3)
        
        self.preferredVisualSatisfaction = "Sufficient_Light_With_View"
        self.temperature = 0
        self.light = 0
        self.airQuality = 0
        self.acoustics = 0
        self.windowStatus = "Closed"
        self.blindStatus = "Closed"
        self.thermalSatisfaction = "Thermally_Satisfied"
        self.visualSatisfaction = "Sufficient_Light_With_View"
        self.airQualitySatisfaction = "Air_Quality_Satisfied"
        self.windowIntention = 0  # Initialize this attribute
        self.blindIntention = 0  # Initialize this attribute
        self.ieqpriority = "Thermal_Comfort"
        self.airConditionStatus = "Off"
        self.artificialLightStatus = "Off"
        self.name = f"{agent_type.capitalize()} {unique_id}"

        #     self.preferredVisualSatisfaction = "Sufficient_Light_With_View"

    def move(self):
        if self.agent_type == "occupant":
            possible_steps = self.model.grid.get_neighborhood(
                self.pos, moore=True, include_center=False)
            new_position = self.random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)

    def update_state(self, environmental_data):
        if self.agent_type == "occupant":
            if 'occupant' in environmental_data:
                self.airQuality = environmental_data['occupant']
        if 'Light' in environmental_data:
            self.light = environmental_data['Light']
            self.artificialLightStatus = "On" if self.light != self.preferredLight else "Off"
            # print(f"Preferred light: {self.preferredLight}")
            # print(f"New light: {self.light}")
        if 'Temperature' in environmental_data:
            self.temperature = environmental_data['Temperature']
            # print(f"New Temperature: {self.temperature}")
            # print(f"Preferred Temperature: {self.preferredTemperature}")
        if 'Air Quality' in environmental_data:
            self.airQuality = int(environmental_data['Air Quality'])
            # print(f"New air quality: {self.airQuality}")
            # print(f"Preferred air quality: {self.preferredAirQuality}")
        if 'Acoustics' in environmental_data:
            self.acoustics = int(environmental_data['Acoustics'])
        if 'skyCondition' in environmental_data:
            self.skyCondition = str(environmental_data['skyCondition'])
        if 'season' in environmental_data:
            self.season = str(environmental_data['season'])
        if 'windCondition' in environmental_data:
            self.windCondition = str(environmental_data['windCondition'])
            # print(f"New acoustics: {self.acoustics}")
            # print(f"Preferred acoustics: {self.preferredAcoustics}")
        # if 'Window' in environmental_data:
        #     self.windowStatus = environmental_data['Window']
        #     # print(f"Preferred window status: {self.preferredWindowStatus}")
        #     # print(f"New window status: {self.windowStatus}")
        # if 'Blind' in environmental_data:
        #     self.blindStatus = environmental_data['Blind']
        #     # print(f"Preferred blind status: {self.preferredBlindStatus}")
            # print(f"New blind status: {self.blindStatus}")

    def adjust_light(self):
        if self.agent_type == "light" and self.preferredLight is not None:
            print(f"light: {self.light}, Preferred light: {self.preferredLight}")
            while self.light != self.preferredLight:
                if self.light < self.preferredLight:
                    self.light += 1  # Increment light
                    return self.light
                elif self.light > self.preferredLight:
                    self.light -= 1  # Decrement light
                    return self.light
            print(f"Current light: {self.light}, Preferred light: {self.preferredLight}")

    def check_thermal_satisfaction(self):
        if self.agent_type == "temperature" and self.preferredTemperature is not None:
            print(f"Temperature: {self.temperature}, Preferred Temperature: {self.preferredTemperature}")
            if self.temperature == self.preferredTemperature:
                self.thermalSatisfaction = "Thermally_Satisfied"
            elif self.temperature < self.preferredTemperature:
                self.thermalSatisfaction = "Thermally_Cold"  # Increment temperature by 1
            elif self.temperature > self.preferredTemperature:
                self.thermalSatisfaction = "Thermally_Hot"  # Decrement temperature by 1
            print(f"Current Temperature: {self.temperature}, Preferred Temperature: {self.preferredTemperature}")

    def check_light(self):
        if not hasattr(self, 'skyCondition'):
            self.skyCondition = None
        if (self.blindStatus == "closed"):
            self.light= 10
        if (self.blindStatus == "tilted" and self.skyCondition == "Cloudy" ):
            self.light= self.light /2
        if (self.blindStatus == "tilted" and self.skyCondition == "Sunny" ):
            self.light= self.light /2

        if (self.blindStatus == "Opened" and self.skyCondition == "Cloudy" ):
            self.light= self.light
    
        if (self.blindStatus == "Opened" and self.skyCondition == "Sunny" ):
            self.light= self.light
    
        if (self.artificialLightStatus == "On"):
            self.light = self.preferredLight
        # print(f"light: {self.light}")
        return self.light

    def check_temperature(self):
        self.adjust_window_status()
        self.adjust_blind_status()
        self.AcDecisionMaking()
        if (self.windowStatus == "Closed" and self.blindStatus == "Closed"):
            self.temperature = self.temperature
    
        if (self.windowStatus == "Opened" and self.blindStatus == "Closed" and self.season == "Winter"):
            self.temperature = self.temperature
            self.airConditionStatus = "Off"

        if (self.windowStatus == "Opened" and self.blindStatus == "Closed" and self.season == "Summer"):
            self.temperature = self.temperature + 5
            self.airConditionStatus = "Off"
    
        if (self.windowStatus == "Opened" and self.blindStatus == "Opened" and self.skyCondition == "Cloudy" and 
        self.season == "Winter"):
            self.temperature = self.temperature -5
            self.airConditionStatus = "Off"

        if (self.windowStatus == "Opened" and self.blindStatus == "Opened" and self.skyCondition == "Sunny" and 
    self.season == "Winter"):
            self.temperature = self.temperature - 3
            self.airConditionStatus = "Off"
    
        if (self.windowStatus == "Opened" and self.blindStatus == "Opened" and self.skyCondition == "Cloudy" and 
    self.season == "Summer" and self.windCondition == "Not_Windy"):
            self.temperature = self.temperature+3
            self.airConditionStatus = "Off"
    
        if (self.windowStatus == "Opened" and self.blindStatus == "Opened" and self.skyCondition == "Sunny" and 
    self.season == "Summer" and self.windCondition == "Not_Windy"):
            self.temperature = self.temperature+5
            self.airConditionStatus = "Off"
    
        if (self.windowStatus == "Opened" and self.blindStatus == "Opened" and self.skyCondition == "Cloudy" and 
        self.season == "Summer" and self.windCondition == "Windy"):
            self.temperature = self.temperature+2
            self.airConditionStatus = "Off"
    
        if (self.windowStatus == "Opened" and self.blindStatus == "Opened" and self.skyCondition == "Sunny" and 
    self.season == "Summer" and self.windCondition == "Windy"):
            self.temperature = self.temperature+3
            self.airConditionStatus = "Off"
    
        if (self.windowStatus == "Closed" and self.blindStatus == "Opened" and self.skyCondition == "Cloudy"):
            self.temperature = self.temperature
            self.airConditionStatus = "Off"
    
        if (self.windowStatus == "Closed" and self.blindStatus == "Opened" and self.skyCondition == "Sunny"):
            self.temperature = self.temperature+2
            self.airConditionStatus = "Off"
    
    
        if (self.airConditionStatus == "On"):

            self.temperature = self.preferredTemperature;

    def check_air_quality(self):
        if self.agent_type == "air_quality" and self.preferredAirQuality is not None:
            print(f"air quality: {self.airQuality}, Preferred air quality: {self.preferredAirQuality}")
            # while self.airQuality != self.preferredAirQuality:
                # if self.airQuality > self.preferredAirQuality:
                #     self.windowStatus = 'Opened'
                #     self.airQuality -= 1  # Example decrement
                # elif self.airQuality < self.preferredAirQuality:
                #     self.windowStatus = 'Closed'
                #     self.airQuality += 1  # Example increment
            if (self.airQuality <= 35):
                self.airQualitySatisfaction = "Air_Quality_Satisfied"
            if (self.airQuality > 35):
                self.airQualitySatisfaction = "Air_Quality_Dissatisfied"
            print(f"Current air quality: {self.airQuality}, Preferred air quality: {self.preferredAirQuality}")
            return self.airQualitySatisfaction
        
    def adjust_acoustics(self):
        if self.agent_type == "acoustics" and self.preferredAcoustics is not None:
            print(f"Acoustics: {self.acoustics}, Preferred Acoustics: {self.preferredAcoustics}")
            max_iterations = 1000  # Limit the number of iterations
            iteration = 0
            while self.acoustics != self.preferredAcoustics and iteration < max_iterations:
                self.acoustics = self.preferredAcoustics
            #     if self.acoustics > self.preferredAcoustics:
            #         self.windowStatus = 'Closed'
            #         self.acoustics -= 1  # Example decrement
            #     elif self.acoustics < self.preferredAcoustics:
            #         self.windowStatus = 'Opened'
            #         self.acoustics += 1  # Example increment
            #     iteration += 1
            #     print(f"Iteration {iteration}: Acoustics = {self.acoustics}")
            # if iteration >= max_iterations:
            #     print("Reached maximum iterations. Exiting loop to avoid infinite run.")
            print(f"Current Acoustics: {self.acoustics}, Preferred Acoustics: {self.preferredAcoustics}")

    def adjust_window_status(self):
        self.calculate_windowIntention()
        # print(f"window intention: {self.windowIntention}")
        if self.agent_type == "window" and self.preferredWindowStatus is not None:
            print(f"window status: {self.windowStatus}, Preferred window status: {self.preferredWindowStatus}")
            # if self.windowStatus != self.preferredWindowStatus:
            #     self.windowStatus = self.preferredWindowStatus
            if (self.windowIntention >= 4 and self.windowStatus == "Closed"):
                self.windowStatus = "Open"

            if (self.windowIntention < 4 and self.windowStatus == "Closed"):
                self.windowStatus = "Close"
            print(f"window status: {self.windowStatus}, Preferred window status: {self.preferredWindowStatus}")
            return self.windowStatus
        
    def calculate_windowIntention(self):
        self.windowIntention = (self.windowAttitude + self.windowPercievedNorm + self.windowPercievedBehavioralControl) / 3
        return self.windowIntention

    def adjust_blind_status(self):
        self.calculate_blindIntention()
        # print(f"blind intention: {self.blindIntention}")
        # if self.agent_type == "blind" and self.preferredBlindStatus is not None:
        #     print(f"blind status: {self.blindStatus}, Preferred blind status: {self.preferredBlindStatus}")
            # if self.blindStatus != self.preferredBlindStatus:
            #     self.blindStatus = self.preferredBlindStatus
            
            
        if (self.blindIntention >= 4 and self.blindStatus == "closed" and 
    self.visualSatisfaction == "Dim_Light_With_No_View"):
            self.blindStatus = "Opened"

        if (self.blindIntention >= 4 and self.blindStatus == "Opened" and
    self.visualSatisfaction == "Bright_Light_With_View"):
            self.blindStatus = "tilted"

        if (self.blindIntention >= 4 and self.blindStatus == "closed" and
    self.visualSatisfaction == "Dim_Light_With_No_View"):
            self.blindStatus = "tilted"

        if (self.blindIntention >= 4 and self.blindStatus == "tilted" and
    self.visualSatisfaction == "Bright_Light_With_View"):
            self.blindStatus = "closed"

        if (self.blindIntention < 4 and self.blindStatus == "closed"):
            self.blindStatus = "closed"

        if (self.blindIntention < 4 and self.blindStatus == "Opened"):

            self.blindStatus = "Opened"
        # print(f"blind status: {self.blindStatus}, Preferred blind status: {self.preferredBlindStatus}")
        return self.blindStatus

    def calculate_blindIntention(self):
        self.blindIntention = (self.blindAttitude + self.blindPercievedNorm + self.blindPercievedBehavioralControl) / 3
        return self.blindIntention

    def check_blind_status(self):
        if self.blindStatus != "Close":
            self.view = "View"
        else:
            self.view = "No_View"

    def check_ieq_priority(self):
        if (self.thermalSatisfaction == "Thermally_Satisfied" and self.ieqpriority == "Thermal_Comfort"):
            self.ieqprioritycondition = True
        if (self.thermalSatisfaction == "Thermally_Hot" and self.ieqpriority == "Thermal_Comfort"):
            self.ieqprioritycondition = True
        if (self.thermalSatisfaction == "Thermally_Cold" and self.ieqpriority == "Thermal_Comfort"):
            self.ieqprioritycondition = True
        if (self.visualSatisfaction == "Bright_Light_With_View" and self.ieqpriority == "Visual_Comfort"):
            self.ieqprioritycondition = True
        if (self.visualSatisfaction == "Dim_Light_With_View" and self.ieqpriority == "Visual_Comfort"):
            self.ieqprioritycondition = True
        if (self.visualSatisfaction == "Dim_Light_With_No_View" and self.ieqpriority == "Visual_Comfort"):
            self.ieqprioritycondition = True
        if (self.acousticalSatisfaction == "Acoustically_Dissatisfied" and self.ieqpriority == "Acoustical_Comfort"):
            self.ieqprioritycondition = True
        if (self.airQualitySatisfaction == "Air_Quality_Dissatisfied" and self.ieqpriority == "AirQuality_Comfort"):
            self.ieqprioritycondition = True

    def thermal_dissatisfaction(self):
        if (self.ieqpriority == "Thermal_Comfort" and
                self.thermalSatisfaction == "Thermally_Cold" and
                self.windowStatus == "Opened"):
            if (self.thermalSatisfaction == "Thermally_Hot" and
                    self.ieqpriority == "Thermal_Comfort" and
                    self.windowStatus == "Closed" and
                    self.beliefTowardsOperatingWindow_Temperature == "Improve_Temperature" and
                    self.windowIntention >= 4):
                self.windowStatus = "Opened"
            if (self.thermalSatisfaction == "Thermally_Cold" and self.ieqpriority == "Thermal_Comfort" and
                    self.windowStatus == "Opened" and
                    self.beliefTowardsOperatingWindow_Temperature == "Improve_Temperature" and
                    self.windowIntention >= 4):
                self.windowStatus = "Closed"
        if (self.ieqpriority == "Thermal_Comfort" and
                self.thermalSatisfaction == "Thermally_Cold" and
                self.windowStatus == "Closed" and
                self.blindStatus == "closed" and
                self.skyCondition == "Sunny"):
            if (self.thermalSatisfaction == "Thermally_Hot" and
                    self.ieqpriority == "Thermal_Comfort" and
                    self.blindStatus == "Opened" and
                    self.beliefTowardsAdjustingBlind_Temperature == "Improve_Temperature" and
                    self.blindIntention >= 4):
                self.blindStatus = "closed"
            if (self.thermalSatisfaction == "Thermally_Cold" and
                    self.ieqpriority == "Thermal_Comfort" and
                    self.blindStatus == "closed" and
                    self.beliefTowardsAdjustingBlind_Temperature == "Improve_Temperature" and
                    self.blindIntention >= 4):
                self.blindStatus = "Opened"
            if (self.thermalSatisfaction == "Thermally_Satisfied" and
                    self.visualSatisfaction == "Dim_Light_With_No_View" and
                    self.ieqpriority != "Visual_Comfort" and
                    self.blindStatus == "closed" and
                    self.skyCondition == "Cloudy" and
                    self.beliefTowardsAdjustingBlind_Light == "Improve_Light" and
                    self.blindIntention >= 4):
                self.blindStatus = "Opened"
            else:
                self.blindStatus = self.blindStatus
        if (self.ieqpriority == "Thermal_Comfort" and
                self.thermalSatisfaction == "Thermally_Hot" and
                self.windowStatus == "Closed"):
            if (self.thermalSatisfaction == "Thermally_Hot" and
                    self.ieqpriority == "Thermal_Comfort" and
                    self.windowStatus == "Closed" and
                    self.beliefTowardsOperatingWindow_Temperature == "Improve_Temperature" and
                    self.windowIntention >= 4):
                self.windowStatus = "Opened"
            if (self.thermalSatisfaction == "Thermally_Cold" and self.ieqpriority == "Thermal_Comfort" and
                    self.windowStatus == "Opened" and
                    self.beliefTowardsOperatingWindow_Temperature == "Improve_Temperature" and
                    self.windowIntention >= 4):
                self.windowStatus = "Closed"
        if (self.ieqpriority == "Thermal_Comfort" and
                self.thermalSatisfaction == "Thermally_Hot" and
                self.windowStatus == "Closed" and
                self.blindStatus == "Opened" and
                self.skyCondition == "Sunny"):
            if (self.thermalSatisfaction == "Thermally_Hot" and
                    self.ieqpriority == "Thermal_Comfort" and
                    self.blindStatus == "Opened" and
                    self.beliefTowardsAdjustingBlind_Temperature == "Improve_Temperature" and
                    self.blindIntention >= 4):
                self.blindStatus = "closed"
            if (self.thermalSatisfaction == "Thermally_Cold" and
                    self.ieqpriority == "Thermal_Comfort" and
                    self.blindStatus == "closed" and
                    self.beliefTowardsAdjustingBlind_Temperature == "Improve_Temperature" and
                    self.blindIntention >= 4):
                self.blindStatus = "Opened"
            if (self.thermalSatisfaction == "Thermally_Satisfied" and
                    self.visualSatisfaction == "Dim_Light_With_No_View" and
                    self.ieqpriority != "Visual_Comfort" and
                    self.blindStatus == "closed" and
                    self.skyCondition == "Cloudy" and
                    self.beliefTowardsAdjustingBlind_Light == "Improve_Light" and
                    self.blindIntention >= 4):
                self.blindStatus = "Opened"
            else:
                self.blindStatus = self.blindStatus

    def visual_satisfaction(self):
        self.adjust_blind_status()
        if self.blindStatus == "closed" and float(self.light) <= 50:
            self.visualSatisfaction = "Dim_Light_With_No_View"
        elif self.blindStatus == "closed" and float(self.light) > 50:
            self.visualSatisfaction = "Bright_Light_With_View"
        elif self.blindStatus == "Opened" and float(self.light) <= 50:
            self.visualSatisfaction = "Dim_Light_With_View"
        elif self.blindStatus == "Opened" and float(self.light) > 50:
            self.visualSatisfaction = "Sufficient_Light_With_View"
        elif self.blindStatus == "tilted" and float(self.light) <= 50:
            self.visualSatisfaction = "Dim_Light_With_View"
        elif self.blindStatus == "tilted" and 50 < float(self.light) <= 100:
            self.visualSatisfaction = "Sufficient_Light_With_View"
        elif self.blindStatus == "tilted" and float(self.light) > 100:
            self.visualSatisfaction = "Bright_Light_With_View"
        return self.visualSatisfaction
        
    def visual_dissatisfaction(self):
        if (self.visualSatisfaction == "Bright_Light_With_View" and self.blindStatus == "Opened"):
            self.blindStatus = "closed"
            # self.visualSatisfaction = "Bright_Light_With_View"
        if (self.visualSatisfaction == "Dim_Light_With_No_View" and self.blindStatus == "closed"):
            self.blindStatus = "Opened"
            # self.visualSatisfaction = "Dim_Light_With_No_View"

    def AcDecisionMaking(self):
        if (self.temperature != self.preferredTemperature):

            self.airConditionStatus = "On"
            self.windowStatus = "Closed"
            self.temperature = self.preferredTemperature
            self.thermalSatisfaction = "Thermally_Satisfied"
            # print(f"temeprature : {self.temperature}")

        if (self.airConditionStatus == "Off"):
            self.check_temperature()
        return self.temperature

    def IEQ_conditiions1(self):
        self.check_thermal_satisfaction()
        self.visual_satisfaction()
        self.adjust_acoustics()
        self.adjust_light()
        if self.thermalSatisfaction != "Thermally_Satisfied":
            print(f"thermal not satisfied")
            self.thermal_dissatisfaction()
            self.check_thermal_satisfaction()
            self.visual_satisfaction()
            self.adjust_light()
        else:
            print("thermal satisfied")
        if self.airQualitySatisfaction != "Air_Quality_Satisfied":
            print("air quality not satisfied")
            self.thermal_dissatisfaction()
            self.check_thermal_satisfaction()
            self.visual_satisfaction()
            self.adjust_light()
        if self.visualSatisfaction == "Sufficient_Light_With_View":
            print("visual not satisfied")
            self.ALdecisionMaking()
            self.thermal_dissatisfaction()
            self.check_thermal_satisfaction()
            self.visual_satisfaction()
            self.adjust_light()
        if self.acoustics != self.preferredAcoustics:
            print("acousariion not satisfied ")
            self.thermal_dissatisfaction()
            self.check_thermal_satisfaction()
            self.visual_satisfaction()
            self.adjust_light()
        else:
            print("accousation staisfied")

    def ALdecisionMaking(self):
        if (self.light != self.preferredLight):
            self.artificialLightStatus = "On"
            self.light = self.preferredLight
            self.visualSatisfaction = "Sufficient_Light_With_View"
            print(f"artificialLightStatus: {self.artificialLightStatus}")
            print(f"light : {self.light}")
        else:
            self.artificialLightStatus ="Off"
            print(f"artificialLightStatus: {self.artificialLightStatus}")
        return self.light,self.artificialLightStatus
    
class AgentAdjuster:
    def __init__(self, model):
        self.model = model


    def IEQ_conditiions(self):
        all_agents_at_preferred_state = True
        for agent in self.model.schedule.agents:
                    if agent.agent_type == "light":
                        agent.adjust_light()
                        if agent.preferredLight is not None and agent.light != agent.preferredLight:
                            all_agents_at_preferred_state = False
                    elif agent.agent_type == "temperature":
                        agent.check_thermal_satisfaction()
                        if agent.thermalSatisfaction != "Thermally_Satisfied":
                            all_agents_at_preferred_state = False
                        else:
                            if (self.thermalSatisfaction != "Thermally_Satisfied"):
                                agent.AcDecisionMaking()
                                agent.check_air_quality()
                                agent.adjust_light()
                                agent.check_thermal_satisfaction()
                                agent.adjust_acoustics()
                            
                            all_agents_at_preferred_state = False
                    elif agent.agent_type == "air_quality":
                        agent.check_air_quality()
                        if agent.airQualitySatisfaction != "Air_Quality_Satisfied":
                            all_agents_at_preferred_state = False
                        else:
                            agent.check_air_quality()
                            agent.check_light()
                            agent.check_thermal_satisfaction()
                            agent.adjust_acoustics()
                            all_agents_at_preferred_state = False
                    elif agent.agent_type == "acoustics":
                        agent.adjust_acoustics()
                        if agent.preferredAcoustics is not None and agent.acoustics == agent.preferredAcoustics:
                            all_agents_at_preferred_state = False
                        else:
                            agent.check_air_quality()
                            agent.adjust_light()
                            agent.check_thermal_satisfaction()
                            agent.adjust_acoustics()
                            all_agents_at_preferred_state = False
                    elif agent.agent_type == "window":
                        agent.adjust_window_status()
                        if agent.preferredWindowStatus is not None and agent.windowStatus == agent.preferredWindowStatus:
                            all_agents_at_preferred_state = False
                    elif agent.agent_type == "blind":
                        agent.adjust_blind_status()
                        if agent.preferredBlindStatus is not None and agent.blindStatus == agent.preferredBlindStatus:
                            all_agents_at_preferred_state = False
                    elif agent.agent_type == "visual_satisfaction":
                        agent.visual_satisfaction()
                        if agent.visualSatisfaction == "Sufficient_Light_With_View":
                            all_agents_at_preferred_state = False
                        else:
                            agent.visual_dissatisfaction()
                            agent.check_air_quality()
                            agent.adjust_light()
                            agent.check_thermal_satisfaction()
                            agent.adjust_acoustics()
                            all_agents_at_preferred_state = False

        return all_agents_at_preferred_state

class RoomModel(Model):

    def __init__(self, width, height, day_night_cycle, preferences):
        self.num_agents = 8  # Occupant, light, temperature, air quality, and acoustics
        self.grid = SingleGrid(width, height, True)
        self.day_night_cycle = day_night_cycle
        self.current_step = 0
        self.preferences = preferences
        self.schedule = RandomActivation(self)
        self.environment_data = pd.read_csv('updated_Dataset.csv')
        self.environment_data_index = 0  # To keep track of the current row
        
        self.preferences = preferences

        # Create agents using preferences
        occupant_config = preferences
        occupant = EnvironmentalAgent(0, self, "occupant", config=occupant_config)
        self.grid.place_agent(occupant, (3, 3))
        self.schedule.add(occupant)
        self.occupant = occupant

        temperature_config = preferences
        temperature = EnvironmentalAgent(1, self, "temperature", occupant, config=temperature_config)
        self.grid.place_agent(temperature, (1, 6))
        self.schedule.add(temperature)

        air_quality_config = preferences
        air_quality = EnvironmentalAgent(3, self, "air_quality", occupant, config=air_quality_config)
        self.grid.place_agent(air_quality, (2, 5))
        self.schedule.add(air_quality)

        acoustics_config = preferences
        acoustics = EnvironmentalAgent(4, self, "acoustics", occupant, config=acoustics_config)
        self.grid.place_agent(acoustics, (3, 5))
        self.schedule.add(acoustics)

        window_config = preferences
        window = EnvironmentalAgent(5, self, "window", occupant, config=window_config)
        self.grid.place_agent(window, (4, 5))
        self.schedule.add(window)

        blind_config = preferences
        blind = EnvironmentalAgent(6, self, "blind", occupant, config=blind_config)
        self.grid.place_agent(blind, (5, 5))
        self.schedule.add(blind)

        light_config = preferences
        light = EnvironmentalAgent(2, self, "light", occupant, config=light_config)
        self.grid.place_agent(light, (7, 5))
        self.schedule.add(light)

        visual_satisfaction_config = preferences
        visual_satisfaction = EnvironmentalAgent(7, self, "visual_satisfaction", self.occupant, config=visual_satisfaction_config)
        self.grid.place_agent(visual_satisfaction, (8, 5))
        self.schedule.add(visual_satisfaction)

        #  # Initialize OpenStudio model
        # # model_path = openstudio.path('/Users/shaikmohammadshaid/Documents/projects/samples/model.osm')
        # # self.openstudio_model = openstudio.model.Model.load(model_path).get()
        
        # # # Set the weather file
        # # weather_file_path = openstudio.path('/Users/shaikmohammadshaid/Documents/projects/samples/weatherfile.epw')
        # # epw_file = openstudio.EpwFile(weather_file_path)
        # # openstudio.model.WeatherFile.setWeatherFile(self.openstudio_model, epw_file)

        # # Create the occupant agent
        # occupant = EnvironmentalAgent(0, self, "occupant")
        # x, y = 3, 3  # Replace with your desired coordinates
        # self.grid.place_agent(occupant, (x, y))
        # self.schedule.add(occupant)
        # self.occupant = occupant  # Store reference to the occupant

        # # Create the temperature agent
        # temperature = EnvironmentalAgent(1, self, "temperature", occupant)
        # self.temperature_position = (1, 6)  # Position where the temperature agent is placed
        # self.grid.place_agent(temperature, self.temperature_position)
        # self.schedule.add(temperature)
        # self.temperature = temperature  # Store reference to the temperature agent

        # # Create the air quality agent
        # air_quality = EnvironmentalAgent(3, self, "air_quality", occupant)
        # self.air_quality_position = (2, 5)  # Choose appropriate position
        # self.grid.place_agent(air_quality, self.air_quality_position)
        # self.schedule.add(air_quality)
        # self.air_quality = air_quality  # Store reference to the air quality agent

        # # Create the acoustics agent
        # acoustics = EnvironmentalAgent(4, self, "acoustics", occupant)
        # self.acoustics_position = (3, 5)  # Choose appropriate position
        # self.grid.place_agent(acoustics, self.acoustics_position)
        # self.schedule.add(acoustics)
        # self.acoustics = acoustics  # Store reference to the acoustics agent

        # # Create the window agent
        # window = EnvironmentalAgent(5, self, "window", occupant)
        # self.window_position = (4, 5)  # Choose appropriate position
        # self.grid.place_agent(window, self.window_position)
        # self.schedule.add(window)
        # self.window = window  # Store reference to the window agent

        # # Create the blind agent
        # blind = EnvironmentalAgent(6, self, "blind", occupant)
        # self.blind_position = (5, 5)  # Choose appropriate position
        # self.grid.place_agent(blind, self.blind_position)
        # self.schedule.add(blind)
        # self.blind = blind  # Store reference to the blind agent

        # # ac =EnvironmentalAgent(9,self,"airConditionStatus",occupant)
        # # self.ac_position = (6,5)
        # # self.grid.place_agent(ac, self.ac_position)
        # # self.schedule.add(ac)
        # # self.airConditionStatus = ac

        # # Create the light agent
        # artificialLightStatus = EnvironmentalAgent(2, self, "light", occupant)
        # self.artificialLightStatus_position = (7, 5)  # Choose appropriate position
        # self.grid.place_agent(artificialLightStatus, self.artificialLightStatus_position)
        # self.schedule.add(artificialLightStatus)
        # self.light = artificialLightStatus  # Store reference to the light agent

        # # Create the visual satisfaction agent
        # visual_satisfaction = EnvironmentalAgent(7, self, "visual_satisfaction", self.occupant)
        # self.visualSatisfaction_position = (8, 5)  # Choose appropriate position
        # self.grid.place_agent(visual_satisfaction, self.visualSatisfaction_position)
        # self.schedule.add(visual_satisfaction)
        # self.visual_satisfaction = visual_satisfaction  # Store reference to the visual satisfaction agent

        # self.agent_adjuster = AgentAdjuster(self)

    def get_environmental_data(self):
        if self.environment_data_index < len(self.environment_data):
            row = self.environment_data.iloc[self.environment_data_index]
            self.environment_data_index += 1  # Move to the next row for the next step
            return row.to_dict()
        else:
            return None
    
    # def run_openstudio_simulation(self):
    #     # Prepare the simulation
    #     idf = openstudio.energyplus.ForwardTranslator().translateModel(self.openstudio_model)
    #     idf_path = os.path.join("/Users/shaikmohammadshaid/Documents/projects/samples/model/run", 'in.idf')
    #     idf.save(openstudio.path(idf_path), True)

    #     energyplus_path = "/Applications/EnergyPlus-24-1-0/energyplus"
    #     weather_file_path = "/Users/shaikmohammadshaid/Documents/projects/samples/weatherfile.epw"
    #     output_directory = "/Users/shaikmohammadshaid/Documents/projects/samples/output"
        
    #     # Run the simulation
    #     energyplus_cmd = [
    #         energyplus_path,
    #         '-w', weather_file_path,
    #         '-d', output_directory,
    #         idf_path
    #     ]
    #     subprocess.run(energyplus_cmd, check=True, capture_output=True, text=True)

    #     # Load results (example: temperature from output CSV)
    #     results_path = os.path.join(output_directory, 'eplusout.csv')
    #     results = pd.read_csv(results_path)

    #     # Update the model/environment based on the results
    #     # Here you would parse the results and update agent states
    #     # Example: setting temperature based on simulation results
    #     self.occupant.temperature = results['Temperature'].mean()

    # def run_openstudio_simulation(self):
    #     # Set up the simulation
    #     workspace = openstudio.workspaces.Workspace(self.openstudio_model.toIdfFile())
    #     run_manager = openstudio.runmanager.RunManager()
    #     job = run_manager.enqueue(workspace, openstudio.runmanager.JobType.EnergyPlus)
    #     run_manager.waitForFinished()

    #     # Retrieve results and update the model if necessary
    #     # For example, you can parse the results and update agents or environmental data


    def step(self):
        print("Step function called, Current Step:", self.current_step)
        environmental_data = self.get_environmental_data()

        if environmental_data:
            for agent in self.schedule.agents:
                if hasattr(agent, 'update_state'):
                    agent.update_state(environmental_data)
                    

            all_agents_at_preferred_state = False
            max_iterations = 3  # Set a maximum number of iterations to avoid infinite loops
            iteration = 0

            while not all_agents_at_preferred_state and iteration < max_iterations:
                all_agents_at_preferred_state = True  # comment this if function is used 
                iteration += 1
                # all_agents_at_preferred_state = self.agent_adjuster.IEQ_conditiions()
                for agent in self.schedule.agents:
                    # agent.IEQ_conditiions1()
                    all_agents_at_preferred_state = True
                    # print(f"light:{agent.light},visual_satisfaction:{agent.visualSatisfaction},air quality:{agent.airQuality},accosution:{agent.acoustics}")
                    # print(f"blind status :{agent.blindStatus}, window status :{agent.windowStatus}, air conditionar:{agent.airConditionStatus}")
                    agent.visual_satisfaction()
                    agent.check_air_quality()
                    agent.check_light()
                    agent.check_temperature()
                    agent.check_thermal_satisfaction()
                    agent.adjust_acoustics()
                    # print(f"light:{agent.light},visual_satisfaction:{agent.visualSatisfaction},air quality:{agent.airQuality},accosution:{agent.acoustics}")
                    # print(f"blind status :{agent.blindStatus}, window status :{agent.windowStatus}, air conditionar:{agent.airConditionStatus}")
                    if agent.agent_type == "temperature":
                        agent.check_thermal_satisfaction()
                        if agent.thermalSatisfaction != "Thermally_Satisfied":
                            agent.AcDecisionMaking()
                            agent.check_air_quality()
                            agent.check_light()
                            agent.check_temperature()
                            agent.adjust_acoustics()
                            all_agents_at_preferred_state = False
                        else:
                            all_agents_at_preferred_state = True

                    elif agent.agent_type == "air_quality":
                        agent.check_air_quality()
                        if agent.airQualitySatisfaction != "Air_Quality_Satisfied":
                            agent.check_air_quality()
                            agent.check_light()
                            agent.check_temperature()
                            agent.check_thermal_satisfaction()
                            agent.adjust_acoustics()
                            all_agents_at_preferred_state = False
                        else:
                            all_agents_at_preferred_state = True

                    elif agent.agent_type == "acoustics":
                        agent.adjust_acoustics()
                        if agent.preferredAcoustics is not None and agent.acoustics != agent.preferredAcoustics:
                            agent.check_air_quality()
                            agent.check_light()
                            agent.check_temperature()
                            agent.check_thermal_satisfaction()
                            agent.adjust_acoustics()
                            all_agents_at_preferred_state = False
                        else:
                            all_agents_at_preferred_state = True

                    elif agent.agent_type == "visual_satisfaction":
                        agent.visual_satisfaction()
                        if agent.visualSatisfaction != "Sufficient_Light_With_View":
                            agent.ALdecisionMaking()
                            agent.visual_dissatisfaction()
                            agent.check_air_quality()
                            agent.check_light()
                            agent.check_temperature()
                            agent.check_thermal_satisfaction()
                            agent.adjust_acoustics()
                            all_agents_at_preferred_state = False
                        else:
                            all_agents_at_preferred_state = True

                    # Other agent types can be similarly handled as needed

                    # if agent.agent_type == "light":
                    #     agent.adjust_light()
                    #     if agent.preferredLight is not None and agent.light == agent.preferredLight:
                    #         all_agents_at_preferred_state = False
                    #     else:
                    #         # agent.ALdecisionMaking()
                    #         all_agents_at_preferred_state = False
                    # elif agent.agent_type == "window":
                    #     agent.adjust_window_status()
                    #     if agent.preferredWindowStatus is not None and agent.windowStatus != agent.preferredWindowStatus:
                    #         all_agents_at_preferred_state = False
                    # elif agent.agent_type == "blind":
                    #     agent.adjust_blind_status()
                    #     if agent.preferredBlindStatus is not None and agent.blindStatus != agent.preferredBlindStatus:
                    #         all_agents_at_preferred_state = False
            print(f"temperature: {agent.temperature},light:{agent.light},visual_satisfaction:{agent.visualSatisfaction},air quality:{agent.airQuality},accosution:{agent.acoustics}")
            print(f"blind status :{agent.blindStatus}, window status :{agent.windowStatus}, air conditionar:{agent.airConditionStatus}")
                    
            if iteration >= max_iterations:
                print("Reached maximum iterations in while loop. Exiting to avoid infinite loop.")

            time.sleep(1)

        self.schedule.step()
        self.current_step += 1
        print(f"Step function called, Current Step: {self.current_step}")

def agent_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.5, "Layer": 0}
    if agent.agent_type == "occupant":
        portrayal["Color"] = "blue"
    elif agent.agent_type == "temperature":
        if agent.preferredTemperature is not None and agent.thermalSatisfaction == "Thermally_Satisfied":
            portrayal["Color"] = "green"
        elif agent.thermalSatisfaction == "Thermally_Hot":
            portrayal["Color"] = "gray"
        elif agent.thermalSatisfaction == "Thermally_Cold":
            portrayal["Color"] = "black"
    elif agent.agent_type == "air_quality":
        portrayal["Color"] = "yellow" if agent.airQualitySatisfaction == "Air_Quality_Satisfied" else "brown"
    elif agent.agent_type == "acoustics":
        portrayal["Color"] = "purple" if agent.acoustics == agent.preferredAcoustics else "orange"
    elif agent.agent_type == "window":
        portrayal = {"Shape": "rect", "Filled": "true", "w": 0.5, "h": 0.5, "Layer": 0}
        portrayal["Color"] = "black" if agent.windowStatus == "Open" else "gray"
    elif agent.agent_type == "blind":
        if agent.blindStatus == "Opened":
            portrayal["Color"] = "yellow" 
        elif  agent.blindStatus =="Closed":
            portrayal["Color"] = "black"
        else:
            portrayal["Color"] = "gray" 
    elif agent.agent_type == "light":
        portrayal["Color"] = "green" if agent.artificialLightStatus == "On" else "black"
    elif agent.agent_type == "visual_satisfaction":
        portrayal["Color"] = "pink" if agent.visualSatisfaction == "Sufficient_Light_With_View" else "black"
    elif agent.agent_type == "ac":
        portrayal["Color"] = "green" if agent.airConditionStatus == "On" else "black"
    portrayal["text"] = agent.name
    portrayal["text_color"] = "white"
    return portrayal

def main():
    # Parameters for the grid
    width, height = 10, 10
    day_night_cycle = 24  # Example value
    preferences = {
        "preferred_temperature": 72,
        "preferred_light": 300,
        "preferred_acoustics": 50,
        "preferred_air_quality": 500,
        "blind_attitude": 3,
        "blind_perceived_norm": 5,
        "blind_perceived_behavioral_conditions": 5
    }

    # Create the model
    model = RoomModel(width, height, day_night_cycle,preferences)

    # Define the portrayal method and the canvas grid
    grid = CanvasGrid(agent_portrayal, width, height, 500, 500)

    # Create the server for visualization
    server = ModularServer(
        RoomModel,
        [grid],
        "Room Model",
        {"width": width, "height": height, "day_night_cycle": day_night_cycle, "preferences":preferences}
    )

    # Launch the server
    server.port = 8521  # Set the port number to something unused
    server.launch()

if __name__ == "__main__":
    main()

